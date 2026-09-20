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
import signal
import contextlib
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
    artifacts: list[str] = field(default_factory=list)
    spec: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API payloads and persistence."""
        data = asdict(self)
        data.pop("spec", None)
        data["startedAt"] = self.started_at
        data["downloadableArtifacts"] = [
            i for i, path in enumerate(self.artifacts) if Path(path).is_file()
        ]
        return data


class JobManager:
    """Spawns and tracks runner subprocesses."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []
        self._lock = threading.RLock()
        self._procs: dict[str, subprocess.Popen] = {}
        self._hooks: list[Any] = []
        self._hook_keys: dict[str, Any] = {}
        self._load_history()

    def register_hook(self, fn: Any, key: str | None = None) -> None:
        """Register a callback invoked with each finished Job."""
        if key and key in self._hook_keys:
            self._hooks.remove(self._hook_keys[key])
        self._hooks.append(fn)
        if key:
            self._hook_keys[key] = fn

    # ── persistence ──────────────────────────────────────────────────────

    def _load_history(self) -> None:
        """Restore finished job history; mark interrupted jobs as failed."""
        data = read_json(JOBS_FILE, [])
        for raw in data if isinstance(data, list) else []:
            try:
                job = Job(**{k: v for k, v in raw.items() if k in Job.__dataclass_fields__})
            except TypeError:
                continue
            if job.status in ("running", "queued", "cancelling"):
                job.status = "failed"
                job.error = "interrupted: server stopped"
                job.log.append("[--] interrupted: server stopped")
            self._jobs.append(job)

    def _persist(self) -> None:
        # Snapshot under the job lock, write outside it: write_json takes the
        # state lock, and request handlers take the state lock before calling
        # into this manager, so holding both here would invert the lock order.
        with self._lock:
            active = [j for j in self._jobs if j.status in ("running", "queued", "cancelling")]
            finished = [j for j in self._jobs if j not in active][:MAX_HISTORY]
            keep = {j.id for j in active + finished}
            self._jobs = [j for j in self._jobs if j.id in keep]
            snapshot = [asdict(j) for j in self._jobs]
        write_json(JOBS_FILE, snapshot)

    # ── public API ───────────────────────────────────────────────────────

    def list(self, root: Path | None = None) -> list[dict[str, Any]]:
        """All jobs, newest first."""
        with self._lock:
            # Rows persisted before specs were recorded have no cwd; keep them
            # visible everywhere rather than silently dropping history.
            return [
                j.to_dict()
                for j in self._jobs
                if root is None or j.spec.get("cwd") in (None, str(root))
            ]

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
            started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            meta=meta or {},
            spec=spec,
        )
        job.log.append(f"[{job.started_at}] job accepted by seeker daemon")

        fd, filename = tempfile.mkstemp(prefix=f"seeker-job-{job.id}-", suffix=".json")
        spec_file = Path(filename)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(spec, stream)

        # Ensure the runner subprocess can import skill_seekers even when the
        # package is only importable via the parent's sys.path (e.g. editable
        # installs in user-site hidden by a redirected HOME in tests).
        import skill_seekers

        env = os.environ.copy()
        pkg_parent = str(Path(skill_seekers.__file__).resolve().parent.parent)
        env["PYTHONPATH"] = pkg_parent + os.pathsep + env.get("PYTHONPATH", "")

        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", "-m", "skill_seekers.web.runner", str(spec_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=spec.get("cwd") or None,
                env=env,
                start_new_session=os.name != "nt",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
        except OSError:
            spec_file.unlink(missing_ok=True)
            raise
        with self._lock:
            self._jobs.insert(0, job)
            self._procs[job.id] = proc
            job.status = "running"
            self._persist()

        threading.Thread(target=self._pump, args=(job.id, proc, spec_file), daemon=True).start()
        return job

    def cancel(self, job_id: str) -> bool:
        """Terminate a running job's subprocess."""
        with self._lock:
            proc = self._procs.get(job_id)
            job = next((j for j in self._jobs if j.id == job_id), None)
            if proc and proc.poll() is None and job:
                job.status = "cancelling"
                self._persist()
        if proc and proc.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGTERM)

                def force_stop():
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        with contextlib.suppress(ProcessLookupError):
                            os.killpg(proc.pid, signal.SIGKILL)

                threading.Thread(target=force_stop, daemon=True).start()
            return True
        return False

    def retry(self, job_id: str) -> Job:
        """Retry a finished job using its persisted specification."""
        with self._lock:
            previous = next((j for j in self._jobs if j.id == job_id), None)
            if not previous or not previous.spec:
                raise KeyError(job_id)
            if previous.status in ("running", "queued", "cancelling"):
                raise ValueError("Job is still active")
            return self.submit(
                previous.type,
                previous.label,
                previous.detail,
                previous.spec.copy(),
                previous.meta.copy(),
            )

    def shutdown(self, root: Path) -> None:
        """Cancel this workspace's children and wait for their output pumps."""
        with self._lock:
            ids = [
                j.id for j in self._jobs if j.spec.get("cwd") == str(root) and j.id in self._procs
            ]
        for job_id in ids:
            self.cancel(job_id)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with self._lock:
                if not any(i in self._procs for i in ids):
                    break
            time.sleep(0.05)

    # ── internals ────────────────────────────────────────────────────────

    def _pump(self, job_id: str, proc: subprocess.Popen, spec_file: Path) -> None:
        """Read runner stdout, updating progress/log until exit."""
        assert proc.stdout is not None
        code = 1
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
                    if line.startswith("[[ARTIFACT]] "):
                        with contextlib.suppress(ValueError):
                            path = json.loads(line.removeprefix("[[ARTIFACT]] "))
                            if isinstance(path, str) and path not in job.artifacts:
                                job.artifacts.append(path)
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
        except OSError as exc:
            with self._lock:
                job = next((j for j in self._jobs if j.id == job_id), None)
                if job:
                    job.log.append(f"Output reader failed: {exc}")
        finally:
            proc.stdout.close()  # unclosed pipe -> ResourceWarning during later GC
            spec_file.unlink(missing_ok=True)

        with self._lock:
            job = next((j for j in self._jobs if j.id == job_id), None)
            self._procs.pop(job_id, None)
            if job is not None:
                if job.status == "cancelling":
                    job.status = "cancelled"
                    job.error = "Cancelled by user"
                elif code == 0:
                    job.status = "done"
                    job.progress = 100.0
                    job.log.append(f"[{time.strftime('%H:%M:%S')}] ✓ finished")
                else:
                    job.status = "failed"
                    job.error = f"exit code {code}"
                    job.log.append(f"[{time.strftime('%H:%M:%S')}] ✗ failed (exit code {code})")
        try:
            self._persist()
        except OSError as exc:  # state lock/disk trouble must not lose the completion hooks
            with self._lock:
                if job is not None:
                    job.log.append(f"Could not persist job history: {exc}")
        if job is not None:
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
