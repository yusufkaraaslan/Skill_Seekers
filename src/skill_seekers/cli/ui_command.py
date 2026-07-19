"""Launch the Skill Seekers HUD (web UI).

Starts a local FastAPI server that exposes the whole toolchain over HTTP and
serves the built single-page app from ``ui/dist`` when available.
"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

DEFAULT_PORT = 8770


class UiCommand:
    """Class-based CLI command: ``skill-seekers ui``."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def execute(self) -> int:
        """Start the UI server (blocks until Ctrl+C)."""
        try:
            import uvicorn  # noqa: PLC0415
        except ImportError:
            print(
                "The web UI requires FastAPI + uvicorn.\n"
                "Install them with: pip install 'skill-seekers[ui]'"
            )
            return 1

        from skill_seekers.web.app import create_app  # noqa: PLC0415

        root = Path(self.args.root).expanduser().resolve() if self.args.root else Path.cwd()
        port = int(self.args.port or DEFAULT_PORT)
        app = create_app(root)

        url = f"http://127.0.0.1:{port}"
        print(f"Seeker HUD · serving {root}")
        print(f"→ {url}")
        if not self.args.no_browser:
            webbrowser.open(url)

        uvicorn.run(app, host=self.args.host, port=port, log_level=self.args.log_level)
        return 0


def main(args: argparse.Namespace | None = None) -> int:
    """Standalone entry point (skill-seekers-ui)."""
    if args is None:
        parser = argparse.ArgumentParser(description="Launch the Skill Seekers HUD web UI")
        parser.add_argument("--port", type=int, default=DEFAULT_PORT)
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--root", default=None, help="workspace root (default: cwd)")
        parser.add_argument("--no-browser", action="store_true")
        parser.add_argument("--log-level", default="warning")
        args = parser.parse_args()
    return UiCommand(args).execute()


if __name__ == "__main__":
    raise SystemExit(main())
