"""
Shared boilerplate for MCP tool modules.

Single home for the things every tool module used to duplicate:
- the `TextContent` import with a graceful fallback when the external `mcp`
  package is not installed (e.g. during testing),
- the `CLI_DIR` path to the bundled CLI tools,
- tiny helpers for the ubiquitous `[TextContent(type="text", text=...)]` return.

Tool modules import from here (like `subprocess_utils.py`) so the boilerplate
lives in exactly one place.
"""

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
