"""Background job manager for the Skill Seekers web UI.

Jobs run as isolated subprocesses (``python -m skill_seekers.web.runner``) so
long-running scrapes never block the HTTP server and can stream real worker
output. The runner emits log lines on stdout; lines prefixed with
``[[PROGRESS:nn]]`` update the job's progress percentage.

Job history is persisted to ``~/.skill-seekers/ui/jobs.json`` (bounded).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .paths import JOBS_FILE, read_json, write_json

PROGRESS_RE = re.compile(r"^\[\[PROGRESS:(\d+)\]\]\s?(.*)$")
MAX_HISTORY = 100
MAX_LOG_LINES = 500


@dataclass
class Job:
    """A background unit of work executed by the runner subprocess."""

    id: str
    type: str  # create | scan | package | enhance | port | fetch | publish | install
    label: str
    detail: str
    progress: float = 0.0
    status: str = "queued"  # queued | running | done | failed
    started_at: str = ""
    log: list[str] = field(default_factory=list)
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API payloads and persistence."""
        return asdict(self)


class JobManager:
    """Spawns and tracks runner subprocesses."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []
        self._lock = threading.Lock()
        self._procs: dict[str, subprocess.Popen] = {}
        self._hooks: list[Any] = []
        self._load_history()

    def register_hook(self, fn: Any) -> None:
        """Register a callback invoked with each finished Job."""
        self._hooks.append(fn)

    # ── persistence ──────────────────────────────────────────────────────

    def _load_history(self) -> None:
        """Restore finished job history; mark interrupted jobs as failed."""
        data = read_json(JOBS_FILE, [])
        for raw in data if isinstance(data, list) else []:
            try:
                job = Job(**{k: v for k, v in raw.items() if k in Job.__dataclass_fields__})
            except TypeError:
                continue
            if job.status in ("running", "queued"):
                job.status = "failed"
                job.error = "interrupted: server stopped"
                job.log.append("[--] interrupted: server stopped")
            self._jobs.append(job)

    def _persist(self) -> None:
        finished = [j for j in self._jobs if j.status in ("done", "failed")][-MAX_HISTORY:]
        write_json(JOBS_FILE, [j.to_dict() for j in finished])

    # ── public API ───────────────────────────────────────────────────────

    def list(self) -> list[dict[str, Any]]:
        """All jobs, newest first."""
        with self._lock:
            return [j.to_dict() for j in self._jobs]

    def get(self, job_id: str) -> dict[str, Any] | None:
        """One job by id."""
        with self._lock:
            for j in self._jobs:
                if j.id == job_id:
                    return j.to_dict()
        return None

    def running_count(self) -> int:
        """Number of currently running jobs."""
        with self._lock:
            return sum(1 for j in self._jobs if j.status == "running")

    def submit(
        self,
        job_type: str,
        label: str,
        detail: str,
        spec: dict[str, Any],
        meta: dict[str, Any] | None = None,
    ) -> Job:
        """Create a job and spawn its runner subprocess.

        Args:
            job_type: Category shown in the UI (create/scan/package/...).
            label: Short title.
            detail: One-line description of what will run.
            spec: JSON-serializable runner spec (see runner.py).

        Returns:
            The created Job.
        """
        job = Job(
            id=f"jb-{uuid.uuid4().hex[:8]}",
            type=job_type,
            label=label,
            detail=detail,
            started_at=time.strftime("%H:%M:%S"),
            meta=meta or {},
        )
        job.log.append(f"[{job.started_at}] job accepted by seeker daemon")

        spec_file = Path(tempfile.gettempdir()) / f"seeker-job-{job.id}.json"
        spec_file.write_text(json.dumps(spec), encoding="utf-8")

        # Ensure the runner subprocess can import skill_seekers even when the
        # package is only importable via the parent's sys.path (e.g. editable
        # installs in user-site hidden by a redirected HOME in tests).
        import skill_seekers

        env = os.environ.copy()
        pkg_parent = str(Path(skill_seekers.__file__).resolve().parent.parent)
        env["PYTHONPATH"] = pkg_parent + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.Popen(
            [sys.executable, "-m", "skill_seekers.web.runner", str(spec_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=spec.get("cwd") or None,
            env=env,
        )
        with self._lock:
            self._jobs.insert(0, job)
            self._procs[job.id] = proc
            job.status = "running"

        threading.Thread(target=self._pump, args=(job.id, proc, spec_file), daemon=True).start()
        return job

    def cancel(self, job_id: str) -> bool:
        """Terminate a running job's subprocess."""
        with self._lock:
            proc = self._procs.get(job_id)
        if proc and proc.poll() is None:
            proc.terminate()
            return True
        return False

    # ── internals ────────────────────────────────────────────────────────

    def _pump(self, job_id: str, proc: subprocess.Popen, spec_file: Path) -> None:
        """Read runner stdout, updating progress/log until exit."""
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                m = PROGRESS_RE.match(line)
                with self._lock:
                    job = next((j for j in self._jobs if j.id == job_id), None)
                    if job is None:
                        continue
                    if m:
                        job.progress = float(m.group(1))
                        text = m.group(2)
                        if text:
                            job.log.append(text)
                    else:
                        job.log.append(line)
                    if len(job.log) > MAX_LOG_LINES:
                        job.log = job.log[-MAX_LOG_LINES:]
            code = proc.wait()
        finally:
            spec_file.unlink(missing_ok=True)

        with self._lock:
            job = next((j for j in self._jobs if j.id == job_id), None)
            self._procs.pop(job_id, None)
            if job is not None:
                if code == 0:
                    job.status = "done"
                    job.progress = 100.0
                    job.log.append(f"[{time.strftime('%H:%M:%S')}] ✓ finished")
                else:
                    job.status = "failed"
                    job.error = f"exit code {code}"
                    job.log.append(f"[{time.strftime('%H:%M:%S')}] ✗ failed (exit code {code})")
        self._persist()
        if job is not None:
            import contextlib

            for hook in self._hooks:
                with contextlib.suppress(Exception):  # hooks must never kill the pump
                    hook(job)


_manager: JobManager | None = None
_manager_lock = threading.Lock()


def get_job_manager() -> JobManager:
    """Process-wide singleton JobManager."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = JobManager()
    return _manager
