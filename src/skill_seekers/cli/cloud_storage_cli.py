#!/usr/bin/env python3
"""
Cloud storage CLI for Skill Seekers.

Upload, download, and manage skills in cloud storage (S3, GCS, Azure).
"""

import sys
import argparse
from pathlib import Path

from .storage import get_storage_adaptor


def upload_command(args):
    """Handle upload subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    if Path(args.local_path).is_dir():
        print(f"📁 Uploading directory: {args.local_path}")
        uploaded_files = adaptor.upload_directory(
            args.local_path, args.remote_path, exclude_patterns=args.exclude
        )
        print(f"✅ Uploaded {len(uploaded_files)} files")
        if args.verbose:
            for file_path in uploaded_files:
                print(f"  - {file_path}")
    else:
        print(f"📄 Uploading file: {args.local_path}")
        url = adaptor.upload_file(args.local_path, args.remote_path)
        print(f"✅ Upload complete: {url}")


def download_command(args):
    """Handle download subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    # Check if remote path is a directory (ends with /)
    if args.remote_path.endswith("/"):
        print(f"📁 Downloading directory: {args.remote_path}")
        downloaded_files = adaptor.download_directory(args.remote_path, args.local_path)
        print(f"✅ Downloaded {len(downloaded_files)} files")
        if args.verbose:
            for file_path in downloaded_files:
                print(f"  - {file_path}")
    else:
        print(f"📄 Downloading file: {args.remote_path}")
        adaptor.download_file(args.remote_path, args.local_path)
        print(f"✅ Download complete: {args.local_path}")


def list_command(args):
    """Handle list subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    print(f"📋 Listing files: {args.prefix or '(root)'}")
    files = adaptor.list_files(args.prefix, args.max_results)

    if not files:
        print("  (no files found)")
        return

    print(f"\nFound {len(files)} files:\n")

    # Calculate column widths
    max_size_width = max(len(format_size(f.size)) for f in files)

    for file_obj in files:
        size_str = format_size(file_obj.size).rjust(max_size_width)
        print(f"  {size_str}  {file_obj.key}")

        if args.verbose and file_obj.last_modified:
            print(f"           Modified: {file_obj.last_modified}")
            if file_obj.metadata:
                print(f"           Metadata: {file_obj.metadata}")
            print()


def delete_command(args):
    """Handle delete subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    if not args.force:
        response = input(f"⚠️  Delete {args.remote_path}? [y/N]: ")
        if response.lower() != "y":
            print("❌ Deletion cancelled")
            return

    print(f"🗑️  Deleting: {args.remote_path}")
    adaptor.delete_file(args.remote_path)
    print("✅ Deletion complete")


def url_command(args):
    """Handle url subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    print(f"🔗 Generating signed URL: {args.remote_path}")
    url = adaptor.get_file_url(args.remote_path, args.expires_in)
    print(f"\n{url}\n")
    print(f"⏱️  Expires in: {args.expires_in} seconds ({args.expires_in // 3600}h)")


def copy_command(args):
    """Handle copy subcommand."""
    adaptor = get_storage_adaptor(
        args.provider, bucket=args.bucket, container=args.container, **parse_extra_args(args.extra)
    )

    print(f"📋 Copying: {args.source_path} → {args.dest_path}")
    adaptor.copy_file(args.source_path, args.dest_path)
    print("✅ Copy complete")


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def parse_extra_args(extra: list | None) -> dict:
    """Parse extra arguments into dictionary."""
    if not extra:
        return {}

    result = {}
    for arg in extra:
        if "=" in arg:
            key, value = arg.split("=", 1)
            result[key.lstrip("-")] = value
        else:
            result[arg.lstrip("-")] = True

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cloud storage operations for Skill Seekers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload skill to S3
  skill-seekers-cloud upload --provider s3 --bucket my-bucket \\
    --local-path output/react/ --remote-path skills/react/

  # Download from GCS
  skill-seekers-cloud download --provider gcs --bucket my-bucket \\
    --remote-path skills/react/ --local-path output/react/

  # List files in Azure
  skill-seekers-cloud list --provider azure --container my-container \\
    --prefix skills/

  # Generate signed URL
  skill-seekers-cloud url --provider s3 --bucket my-bucket \\
    --remote-path skills/react.zip --expires-in 7200

Provider-specific options:
  S3:    --region=us-west-2 --endpoint-url=https://...
  GCS:   --project=my-project --credentials-path=/path/to/creds.json
  Azure: --account-name=myaccount --account-key=...
        """,
    )

    # Global arguments
    parser.add_argument(
        "--provider", choices=["s3", "gcs", "azure"], required=True, help="Cloud storage provider"
    )
    parser.add_argument("--bucket", help="S3/GCS bucket name (for S3/GCS)")
    parser.add_argument("--container", help="Azure container name (for Azure)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload file or directory")
    upload_parser.add_argument("local_path", help="Local file or directory path")
    upload_parser.add_argument("remote_path", help="Remote path in cloud storage")
    upload_parser.add_argument(
        "--exclude", action="append", help="Glob patterns to exclude (for directories)"
    )
    upload_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download file or directory")
    download_parser.add_argument("remote_path", help="Remote path in cloud storage")
    download_parser.add_argument("local_path", help="Local destination path")
    download_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    # List command
    list_parser = subparsers.add_parser("list", help="List files in cloud storage")
    list_parser.add_argument("--prefix", default="", help="Prefix to filter files")
    list_parser.add_argument(
        "--max-results", type=int, default=1000, help="Maximum number of results"
    )
    list_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete file from cloud storage")
    delete_parser.add_argument("remote_path", help="Remote path in cloud storage")
    delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )
    delete_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    # URL command
    url_parser = subparsers.add_parser("url", help="Generate signed URL")
    url_parser.add_argument("remote_path", help="Remote path in cloud storage")
    url_parser.add_argument(
        "--expires-in",
        type=int,
        default=3600,
        help="URL expiration time in seconds (default: 3600)",
    )
    url_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    # Copy command
    copy_parser = subparsers.add_parser("copy", help="Copy file within cloud storage")
    copy_parser.add_argument("source_path", help="Source path")
    copy_parser.add_argument("dest_path", help="Destination path")
    copy_parser.add_argument("extra", nargs="*", help="Provider-specific options (--key=value)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Validate bucket/container based on provider
    if args.provider in ["s3", "gcs"] and not args.bucket:
        print(f"❌ Error: --bucket is required for {args.provider.upper()}", file=sys.stderr)
        sys.exit(1)
    elif args.provider == "azure" and not args.container:
        print("❌ Error: --container is required for Azure", file=sys.stderr)
        sys.exit(1)

    try:
        # Execute command
        if args.command == "upload":
            upload_command(args)
        elif args.command == "download":
            download_command(args)
        elif args.command == "list":
            list_command(args)
        elif args.command == "delete":
            delete_command(args)
        elif args.command == "url":
            url_command(args)
        elif args.command == "copy":
            copy_command(args)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
