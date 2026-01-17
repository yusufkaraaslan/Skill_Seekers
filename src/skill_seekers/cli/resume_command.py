"""
Resume Command for Skill Seekers

Allows users to resume interrupted scraping jobs from saved progress.
"""

import argparse
import sys

from .config_manager import get_config_manager


def list_resumable_jobs():
    """List all resumable jobs with details."""
    config = get_config_manager()
    jobs = config.list_resumable_jobs()

    if not jobs:
        print("\n📦 No resumable jobs found.\n")
        print("Jobs are automatically saved when:")
        print("  • You interrupt a scraping operation (Ctrl+C)")
        print("  • A rate limit is reached")
        print("  • An error occurs during scraping\n")
        return

    print(f"\n📦 Resumable Jobs ({len(jobs)} available):\n")

    for idx, job in enumerate(jobs, 1):
        job_id = job["job_id"]
        started = job.get("started_at", "Unknown")
        command = job.get("command", "Unknown")
        progress = job.get("progress", {})
        last_updated = job.get("last_updated", "Unknown")

        print(f"{idx}. Job ID: {job_id}")
        print(f"   Started: {started}")
        print(f"   Command: {command}")

        if progress:
            phase = progress.get("phase", "Unknown")
            files_processed = progress.get("files_processed", 0)
            files_total = progress.get("files_total", 0)

            print(f"   Progress: {phase}")
            if files_total > 0:
                percentage = (files_processed / files_total) * 100
                print(f"   Files: {files_processed}/{files_total} ({percentage:.1f}%)")

        print(f"   Last updated: {last_updated}")
        print()

    print("To resume a job:")
    print("  $ skill-seekers resume <job_id>\n")


def resume_job(job_id: str):
    """Resume a specific job."""
    config = get_config_manager()

    print(f"\n🔄 Resuming job: {job_id}\n")

    # Load progress
    progress = config.load_progress(job_id)

    if not progress:
        print(f"❌ Job '{job_id}' not found or cannot be resumed.\n")
        print("Use 'skill-seekers resume --list' to see available jobs.\n")
        return 1

    if not progress.get("can_resume", False):
        print(f"❌ Job '{job_id}' is not marked as resumable.\n")
        return 1

    # Extract job details
    command = progress.get("command", "")
    _job_config = progress.get("config", {})
    checkpoint = progress.get("progress", {}).get("last_checkpoint")

    print(f"Original command: {command}")
    print(f"Last checkpoint: {checkpoint or 'Unknown'}")
    print()

    # Reconstruct command
    if "github" in command:
        print("📌 Resuming GitHub scraping...")
        print("⚠️  Note: GitHub resume feature not yet implemented")
        print("   You can re-run the original command - it will use cached data where available.\n")
        print(f"   Command: {command}\n")
        return 1

    elif "scrape" in command:
        print("📌 Resuming documentation scraping...")
        print("⚠️  Note: Documentation scraping resume feature not yet implemented")
        print("   You can re-run the original command - it will use cached data where available.\n")
        print(f"   Command: {command}\n")
        return 1

    elif "unified" in command:
        print("📌 Resuming unified scraping...")
        print("⚠️  Note: Unified scraping resume feature not yet implemented")
        print("   You can re-run the original command - it will use cached data where available.\n")
        print(f"   Command: {command}\n")
        return 1

    else:
        print("❌ Unknown job type. Cannot resume.\n")
        return 1


def clean_old_jobs():
    """Clean up old progress files."""
    config = get_config_manager()

    print("\n🧹 Cleaning up old progress files...\n")

    jobs_before = len(config.list_resumable_jobs())
    config.cleanup_old_progress()
    jobs_after = len(config.list_resumable_jobs())

    deleted = jobs_before - jobs_after

    if deleted > 0:
        print(f"✅ Deleted {deleted} old job(s)")
    else:
        print("✅ No old jobs to clean up")

    if jobs_after > 0:
        print(f"📦 {jobs_after} job(s) remaining\n")
    else:
        print()


def main():
    """Main entry point for resume command."""
    parser = argparse.ArgumentParser(description="Resume interrupted Skill Seekers jobs")
    parser.add_argument("job_id", nargs="?", help="Job ID to resume")
    parser.add_argument("--list", action="store_true", help="List all resumable jobs")
    parser.add_argument("--clean", action="store_true", help="Clean up old progress files")

    args = parser.parse_args()

    # Handle options
    if args.list:
        list_resumable_jobs()
        return 0

    if args.clean:
        clean_old_jobs()
        return 0

    if not args.job_id:
        print("\n❌ Error: Job ID required or use --list to see available jobs\n")
        parser.print_help()
        return 1

    return resume_job(args.job_id)


if __name__ == "__main__":
    sys.exit(main())
