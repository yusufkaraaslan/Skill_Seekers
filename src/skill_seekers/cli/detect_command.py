"""Read-only source detection command."""

from __future__ import annotations

import json
from dataclasses import asdict

from skill_seekers.cli.source_detector import SourceDetector


class DetectCommand:
    """Display how the create command would interpret a source."""

    def __init__(self, args) -> None:
        self.args = args

    def execute(self) -> int:
        source_info = SourceDetector.detect(self.args.source)
        payload = asdict(source_info)

        if self.args.json:
            print(json.dumps(payload, indent=2))
            return 0

        print(f"Type: {source_info.type}")
        print(f"Suggested name: {source_info.suggested_name}")
        print("Parsed:")
        for key, value in source_info.parsed.items():
            print(f"  {key}: {value}")
        return 0
