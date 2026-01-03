#!/usr/bin/env python3
"""
Check Enhancement Status

Monitor the status of background/daemon enhancement processes.

Usage:
    skill-seekers enhance-status output/react/
    skill-seekers enhance-status output/react/ --watch
    skill-seekers enhance-status output/react/ --json
"""

import os
import sys
import json
import time
from pathlib import Path


def read_status(skill_dir):
    """Read enhancement status from file.

    Args:
        skill_dir: Path to skill directory

    Returns:
        dict: Status data or None if not found
    """
    status_file = Path(skill_dir) / ".enhancement_status.json"

    if not status_file.exists():
        return None

    try:
        return json.loads(status_file.read_text(encoding='utf-8'))
    except Exception as e:
        return {"error": f"Failed to read status: {e}"}


def format_status(status):
    """Format status for display.

    Args:
        status: Status dict

    Returns:
        str: Formatted status string
    """
    if not status:
        return "❌ No enhancement in progress (no status file found)"

    if "error" in status:
        return f"❌ {status['error']}"

    # Status emoji mapping
    status_emojis = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌"
    }

    emoji = status_emojis.get(status.get('status', ''), '❓')
    status_text = status.get('status', 'unknown').upper()
    message = status.get('message', '')
    progress = status.get('progress', 0.0)
    timestamp = status.get('timestamp', 'unknown')
    error = status.get('error')
    pid = status.get('pid')

    # Build output
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"ENHANCEMENT STATUS: {status_text}")
    lines.append(f"{'='*60}\n")

    lines.append(f"{emoji} Status: {status_text}")

    if message:
        lines.append(f"   Message: {message}")

    if progress > 0:
        progress_pct = int(progress * 100)
        progress_bar = '█' * (progress_pct // 5) + '░' * (20 - progress_pct // 5)
        lines.append(f"   Progress: [{progress_bar}] {progress_pct}%")

    if pid:
        lines.append(f"   PID: {pid}")

    lines.append(f"   Timestamp: {timestamp}")

    if error:
        lines.append(f"\n❌ Error: {error}")

    lines.append("")

    return '\n'.join(lines)


def watch_status(skill_dir, interval=2):
    """Watch status in real-time.

    Args:
        skill_dir: Path to skill directory
        interval: Update interval in seconds
    """
    print(f"👀 Watching enhancement status for: {skill_dir}")
    print(f"   Update interval: {interval} seconds")
    print(f"   Press Ctrl+C to stop\n")

    try:
        last_status = None

        while True:
            status = read_status(skill_dir)

            # Only print if status changed
            if status != last_status:
                # Clear screen (optional, comment out if you don't want this)
                # os.system('clear' if os.name != 'nt' else 'cls')

                print(format_status(status))
                last_status = status

                # Exit if completed or failed
                if status and status.get('status') in ['completed', 'failed']:
                    break

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching")
        sys.exit(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Check enhancement status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check status once
  skill-seekers enhance-status output/react/

  # Watch status in real-time
  skill-seekers enhance-status output/react/ --watch

  # Get JSON output (for scripts)
  skill-seekers enhance-status output/react/ --json
"""
    )

    parser.add_argument(
        'skill_directory',
        help='Path to skill directory (e.g., output/react/)'
    )

    parser.add_argument(
        '--watch', '-w',
        action='store_true',
        help='Watch status in real-time (updates every 2 seconds)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON (for scripting)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=2,
        help='Watch update interval in seconds (default: 2)'
    )

    args = parser.parse_args()

    # Watch mode
    if args.watch:
        watch_status(args.skill_directory, args.interval)
        return

    # Read status
    status = read_status(args.skill_directory)

    # JSON output
    if args.json:
        print(json.dumps(status, indent=2))
        return

    # Human-readable output
    print(format_status(status))

    # Exit code based on status
    if not status:
        sys.exit(2)  # No status found
    elif status.get('status') == 'completed':
        sys.exit(0)  # Success
    elif status.get('status') == 'failed':
        sys.exit(1)  # Failed
    else:
        sys.exit(0)  # In progress


if __name__ == "__main__":
    main()
