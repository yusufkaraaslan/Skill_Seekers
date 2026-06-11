"""
Shared boilerplate for MCP tool modules.

Single home for the things every tool module used to duplicate:
- the `TextContent` import with a graceful fallback when the external `mcp`
  package is not installed (e.g. during testing),
- the `CLI_DIR` path to the bundled CLI tools,
- tiny helpers for the ubiquitous `[TextContent(type="text", text=...)]` return,
- `run_cli_main()`, the in-process replacement for shelling out to
  `python -m skill_seekers.cli.<module>` (Phase 5d).

Tool modules import from here (like `subprocess_utils.py`) so the boilerplate
lives in exactly one place.
"""

import contextlib
import contextvars
import io
import logging
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from mcp.types import TextContent
except ImportError:
    # Graceful degradation: a minimal fallback so modules import without `mcp`.
    class TextContent:
        """Fallback TextContent for when MCP is not installed."""

        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text


# Path to the bundled CLI tools (src/skill_seekers/cli), resolved relative to
# this module which lives at src/skill_seekers/mcp/tools/.
CLI_DIR = Path(__file__).parent.parent.parent / "cli"


def text_response(message: str) -> list[Any]:
    """Wrap a message in the standard single-TextContent list return shape."""
    return [TextContent(type="text", text=message)]


# Per-call token so concurrent run_cli_main calls (which all attach a handler
# to the shared "skill_seekers" logger) only capture their OWN log records.
# Same pattern as scraping_tools._run_converter.
_cli_capture_token: contextvars.ContextVar = contextvars.ContextVar(
    "ss_cli_capture_token", default=None
)

# sys.argv and the sys.stdout/sys.stderr redirection are process-global, so
# in-process CLI calls are serialized. Tool coroutines run the call
# synchronously on the event loop (no awaits inside the critical section), but
# if the server ever executes tools on worker threads this lock keeps one
# call's argv/streams from leaking into another's.
_run_cli_main_lock = threading.Lock()


def run_cli_main(
    main_func: Callable[[], Any], argv: list[str], prog: str = "skill-seekers"
) -> tuple[str, str, int]:
    """Run a CLI module's ``main()`` in-process (Phase 5d).

    Drop-in replacement for
    ``run_subprocess_with_streaming([sys.executable, "-m", <module>, *argv])``:
    ``sys.argv`` is patched to ``[prog, *argv]`` for the duration, so the SAME
    argv list is parsed by the command's REAL parser (every command's
    ``main()`` falls back to parsing ``sys.argv``). Running in the server
    process preserves ExecutionContext, structured errors, and warm imports,
    and skips interpreter startup.

    Unlike the old subprocess path there is NO timeout: in-process calls run
    unbounded (same precedent as converter scrapes via
    ``scraping_tools._run_converter``).

    Capture:
    - stdout/stderr via ``contextlib.redirect_stdout``/``redirect_stderr``;
    - records from the "skill_seekers" logger via a per-call handler gated by
      a contextvar token (the ``_run_converter`` pattern), appended to the
      captured stderr — mirroring the subprocess world, where logging went to
      the child's stderr.

    Containment (a module exit must not kill the MCP server):
    - ``SystemExit``: int codes pass through (``None`` → 0); non-int codes are
      printed to stderr and map to 1, matching CPython's behavior.
    - ``KeyboardInterrupt`` maps to 130.
    - Any other exception prints ``TypeName: message`` to stderr and maps to 1.

    Returns:
        ``(stdout, stderr, returncode)`` — the same tuple shape as
        ``run_subprocess_with_streaming``.
    """
    stdout_io = io.StringIO()
    stderr_io = io.StringIO()
    token = object()
    _cli_capture_token.set(token)
    handler = logging.StreamHandler(stderr_io)
    handler.setLevel(logging.INFO)
    handler.addFilter(lambda _record: _cli_capture_token.get() is token)
    sk_logger = logging.getLogger("skill_seekers")
    sk_logger.addHandler(handler)
    try:
        with _run_cli_main_lock:
            original_argv = sys.argv
            sys.argv = [prog, *argv]
            try:
                with (
                    contextlib.redirect_stdout(stdout_io),
                    contextlib.redirect_stderr(stderr_io),
                ):
                    try:
                        returncode = main_func()
                    except SystemExit as exc:
                        if exc.code is None:
                            returncode = 0
                        elif isinstance(exc.code, int):
                            returncode = exc.code
                        else:
                            # sys.exit("message"): CPython prints the message
                            # to stderr and exits 1.
                            print(exc.code, file=stderr_io)
                            returncode = 1
                    except KeyboardInterrupt:
                        print("Interrupted", file=stderr_io)
                        returncode = 130
                    except Exception as exc:
                        print(f"{type(exc).__name__}: {exc}", file=stderr_io)
                        returncode = 1
            finally:
                sys.argv = original_argv
    finally:
        sk_logger.removeHandler(handler)

    if returncode is None:
        returncode = 0
    return stdout_io.getvalue(), stderr_io.getvalue(), returncode
