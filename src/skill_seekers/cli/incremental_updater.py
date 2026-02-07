#!/usr/bin/env python3
"""
Incremental Updates for Skills

Provides smart change detection and partial updates to avoid full rebuilds.
Tracks document versions and generates delta packages.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib


@dataclass
class DocumentVersion:
    """Version information for a document."""
    file_path: str
    content_hash: str
    size_bytes: int
    last_modified: float
    version: int


@dataclass
class ChangeSet:
    """Set of changes detected."""
    added: List[DocumentVersion]
    modified: List[DocumentVersion]
    deleted: List[str]
    unchanged: List[DocumentVersion]

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.added) > 0 or len(self.modified) > 0 or len(self.deleted) > 0

    @property
    def total_changes(self) -> int:
        """Count total changes."""
        return len(self.added) + len(self.modified) + len(self.deleted)


@dataclass
class UpdateMetadata:
    """Metadata for an incremental update."""
    timestamp: str
    previous_version: str
    new_version: str
    change_summary: Dict[str, int]
    total_documents: int


class IncrementalUpdater:
    """
    Manages incremental updates for skill documentation.

    Tracks document versions, detects changes, and generates
    delta packages for efficient updates.
    """

    def __init__(self, skill_dir: Path, version_file: str = ".skill_version.json"):
        """
        Initialize incremental updater.

        Args:
            skill_dir: Path to skill directory
            version_file: Name of version tracking file
        """
        self.skill_dir = Path(skill_dir)
        self.version_file = self.skill_dir / version_file
        self.current_versions: Dict[str, DocumentVersion] = {}
        self.previous_versions: Dict[str, DocumentVersion] = {}

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            print(f"⚠️  Warning: Failed to hash {file_path}: {e}")
            return ""

    def _scan_documents(self) -> Dict[str, DocumentVersion]:
        """
        Scan skill directory and build version map.

        Returns:
            Dictionary mapping file paths to versions
        """
        versions = {}

        # Scan SKILL.md
        skill_md = self.skill_dir / "SKILL.md"
        if skill_md.exists():
            versions["SKILL.md"] = DocumentVersion(
                file_path="SKILL.md",
                content_hash=self._compute_file_hash(skill_md),
                size_bytes=skill_md.stat().st_size,
                last_modified=skill_md.stat().st_mtime,
                version=1
            )

        # Scan references
        refs_dir = self.skill_dir / "references"
        if refs_dir.exists():
            for ref_file in refs_dir.glob("*.md"):
                if ref_file.is_file() and not ref_file.name.startswith("."):
                    rel_path = f"references/{ref_file.name}"
                    versions[rel_path] = DocumentVersion(
                        file_path=rel_path,
                        content_hash=self._compute_file_hash(ref_file),
                        size_bytes=ref_file.stat().st_size,
                        last_modified=ref_file.stat().st_mtime,
                        version=1
                    )

        return versions

    def load_previous_versions(self) -> bool:
        """
        Load previous version information from disk.

        Returns:
            True if versions loaded, False if no previous versions
        """
        if not self.version_file.exists():
            return False

        try:
            data = json.loads(self.version_file.read_text())

            for file_path, version_dict in data.get("documents", {}).items():
                self.previous_versions[file_path] = DocumentVersion(**version_dict)

            return True
        except Exception as e:
            print(f"⚠️  Warning: Failed to load versions: {e}")
            return False

    def save_current_versions(self) -> None:
        """Save current version information to disk."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "documents": {
                file_path: asdict(version)
                for file_path, version in self.current_versions.items()
            }
        }

        self.version_file.write_text(json.dumps(data, indent=2))

    def detect_changes(self) -> ChangeSet:
        """
        Detect changes between previous and current versions.

        Returns:
            ChangeSet describing all changes
        """
        # Scan current state
        self.current_versions = self._scan_documents()

        # Load previous state
        has_previous = self.load_previous_versions()

        if not has_previous:
            # First time - all files are "added"
            return ChangeSet(
                added=list(self.current_versions.values()),
                modified=[],
                deleted=[],
                unchanged=[]
            )

        # Detect changes
        added = []
        modified = []
        deleted = []
        unchanged = []

        current_files = set(self.current_versions.keys())
        previous_files = set(self.previous_versions.keys())

        # Added files
        for file_path in current_files - previous_files:
            added.append(self.current_versions[file_path])

        # Deleted files
        for file_path in previous_files - current_files:
            deleted.append(file_path)

        # Check for modifications
        for file_path in current_files & previous_files:
            current = self.current_versions[file_path]
            previous = self.previous_versions[file_path]

            if current.content_hash != previous.content_hash:
                # Increment version
                current.version = previous.version + 1
                modified.append(current)
            else:
                unchanged.append(current)

        return ChangeSet(
            added=added,
            modified=modified,
            deleted=deleted,
            unchanged=unchanged
        )

    def generate_update_package(
        self,
        change_set: ChangeSet,
        output_path: Path,
        include_content: bool = True
    ) -> Path:
        """
        Generate incremental update package.

        Args:
            change_set: Changes to include
            output_path: Output path for package
            include_content: Include full document content

        Returns:
            Path to created package
        """
        output_path = Path(output_path)

        # Build update package
        update_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "skill_name": self.skill_dir.name,
                "change_summary": {
                    "added": len(change_set.added),
                    "modified": len(change_set.modified),
                    "deleted": len(change_set.deleted),
                    "unchanged": len(change_set.unchanged)
                },
                "total_changes": change_set.total_changes
            },
            "changes": {}
        }

        # Include changed documents
        if include_content:
            # Added documents
            for doc in change_set.added:
                file_path = self.skill_dir / doc.file_path
                update_data["changes"][doc.file_path] = {
                    "action": "add",
                    "version": doc.version,
                    "content": file_path.read_text(encoding="utf-8"),
                    "hash": doc.content_hash,
                    "size": doc.size_bytes
                }

            # Modified documents
            for doc in change_set.modified:
                file_path = self.skill_dir / doc.file_path
                update_data["changes"][doc.file_path] = {
                    "action": "modify",
                    "version": doc.version,
                    "content": file_path.read_text(encoding="utf-8"),
                    "hash": doc.content_hash,
                    "size": doc.size_bytes
                }

            # Deleted documents
            for file_path in change_set.deleted:
                update_data["changes"][file_path] = {
                    "action": "delete"
                }

        # Write package
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(update_data, indent=2, ensure_ascii=False))

        return output_path

    def generate_diff_report(self, change_set: ChangeSet) -> str:
        """
        Generate human-readable diff report.

        Args:
            change_set: Changes to report

        Returns:
            Formatted report string
        """
        lines = ["=" * 60]
        lines.append("INCREMENTAL UPDATE REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append("📊 Summary:")
        lines.append(f"   Added: {len(change_set.added)} files")
        lines.append(f"   Modified: {len(change_set.modified)} files")
        lines.append(f"   Deleted: {len(change_set.deleted)} files")
        lines.append(f"   Unchanged: {len(change_set.unchanged)} files")
        lines.append(f"   Total changes: {change_set.total_changes}")
        lines.append("")

        # Added files
        if change_set.added:
            lines.append("➕ Added Files:")
            for doc in change_set.added:
                lines.append(f"   + {doc.file_path} ({doc.size_bytes:,} bytes)")
            lines.append("")

        # Modified files
        if change_set.modified:
            lines.append("📝 Modified Files:")
            for doc in change_set.modified:
                prev = self.previous_versions.get(doc.file_path)
                if prev:
                    size_diff = doc.size_bytes - prev.size_bytes
                    size_str = f"{size_diff:+,} bytes" if size_diff != 0 else "same size"
                    lines.append(f"   ~ {doc.file_path} (v{prev.version} → v{doc.version}, {size_str})")
                else:
                    lines.append(f"   ~ {doc.file_path} (v{doc.version})")
            lines.append("")

        # Deleted files
        if change_set.deleted:
            lines.append("🗑️  Deleted Files:")
            for file_path in change_set.deleted:
                lines.append(f"   - {file_path}")
            lines.append("")

        # Content diffs for modified files
        if change_set.modified:
            lines.append("📄 Content Changes:")
            for doc in change_set.modified:
                prev = self.previous_versions.get(doc.file_path)
                if prev:
                    lines.append(f"\n   File: {doc.file_path}")

                    # Read current content
                    current_path = self.skill_dir / doc.file_path
                    current_content = current_path.read_text(encoding="utf-8").splitlines()

                    # Generate diff (simplified)
                    lines.append(f"   Size: {prev.size_bytes:,} → {doc.size_bytes:,} bytes")
                    lines.append(f"   Hash: {prev.content_hash[:8]}... → {doc.content_hash[:8]}...")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def apply_update_package(self, package_path: Path) -> bool:
        """
        Apply an incremental update package.

        Args:
            package_path: Path to update package

        Returns:
            True if successful
        """
        try:
            update_data = json.loads(Path(package_path).read_text())

            print("📦 Applying incremental update...")
            print(f"   Timestamp: {update_data['metadata']['timestamp']}")
            print(f"   Changes: {update_data['metadata']['total_changes']}")

            # Apply changes
            for file_path, change in update_data["changes"].items():
                action = change["action"]
                full_path = self.skill_dir / file_path

                if action == "add":
                    print(f"   ➕ Adding: {file_path}")
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(change["content"], encoding="utf-8")

                elif action == "modify":
                    print(f"   📝 Modifying: {file_path}")
                    full_path.write_text(change["content"], encoding="utf-8")

                elif action == "delete":
                    print(f"   🗑️  Deleting: {file_path}")
                    if full_path.exists():
                        full_path.unlink()

            print("✅ Update applied successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to apply update: {e}")
            return False


def example_usage():
    """Example usage of incremental updater."""
    from pathlib import Path

    skill_dir = Path("output/react")

    # Initialize updater
    updater = IncrementalUpdater(skill_dir)

    # Detect changes
    print("🔍 Detecting changes...")
    change_set = updater.detect_changes()

    # Generate report
    report = updater.generate_diff_report(change_set)
    print(report)

    if change_set.has_changes:
        # Generate update package
        print("\n📦 Generating update package...")
        package_path = updater.generate_update_package(
            change_set,
            skill_dir.parent / f"{skill_dir.name}-update.json"
        )
        print(f"✅ Package created: {package_path}")

        # Save versions
        updater.save_current_versions()
        print(f"💾 Versions saved to: {updater.version_file}")
    else:
        print("\n✅ No changes detected - skill is up to date!")


if __name__ == "__main__":
    example_usage()
