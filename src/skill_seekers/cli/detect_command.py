"""Read-only source detection command (``skill-seekers detect``)."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

from skill_seekers.cli.exit_codes import EXIT_SUCCESS, EXIT_VALIDATION
from skill_seekers.cli.source_detector import SourceDetector, SourceValidationError


class DetectCommand:
    """Report how ``skill-seekers create`` would interpret a source, without creating anything.

    Runs the same resolution stage as ``create`` (detect + validate) so the
    answer is what the real pipeline would do. Output contract:

    * success — human summary, or with ``--json`` the ``SourceInfo`` fields plus
      ``valid: true`` and ``validation_error: null``; exit 0.
    * detected but unusable (missing file, ...) — the same shape with
      ``valid: false`` and the message; exit 2 (``EXIT_VALIDATION``).
    * undetectable — ``{"error": ...}`` on stdout with ``--json`` (never an
      empty stdout), or ``Error: ...`` on stderr; exit 2.
    """

    def __init__(self, args) -> None:
        self.args = args

    def execute(self) -> int:
        as_json = bool(getattr(self.args, "json", False))
        try:
            source_info = SourceDetector.resolve(self.args.source, validate=False)
        except ValueError as exc:
            if as_json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"Error: {exc}", file=sys.stderr)
            return EXIT_VALIDATION

        validation_error: str | None = None
        try:
            SourceDetector.validate_source(source_info)
        except SourceValidationError as exc:
            validation_error = str(exc)

        payload = {
            **asdict(source_info),
            "valid": validation_error is None,
            "validation_error": validation_error,
        }
        if as_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Type: {source_info.type}")
            print(f"Suggested name: {source_info.suggested_name}")
            print("Parsed:")
            for key, value in source_info.parsed.items():
                print(f"  {key}: {value}")
            if validation_error:
                print(f"Validation: FAILED - {validation_error}")
            else:
                print("Validation: OK")
        return EXIT_SUCCESS if validation_error is None else EXIT_VALIDATION
