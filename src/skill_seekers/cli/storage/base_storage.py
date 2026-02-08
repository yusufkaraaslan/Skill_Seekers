"""
Base storage adaptor interface for cloud storage providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass


@dataclass
class StorageObject:
    """
    Represents a file/object in cloud storage.

    Attributes:
        key: Object key/path in storage
        size: Size in bytes
        last_modified: Last modification timestamp
        etag: ETag/hash of object
        metadata: Additional metadata
    """

    key: str
    size: int
    last_modified: str | None = None
    etag: str | None = None
    metadata: dict[str, str] | None = None


class BaseStorageAdaptor(ABC):
    """
    Abstract base class for cloud storage adaptors.

    Provides unified interface for different cloud storage providers.
    All adaptors must implement these methods.
    """

    def __init__(self, **kwargs):
        """
        Initialize storage adaptor.

        Args:
            **kwargs: Provider-specific configuration
        """
        self.config = kwargs

    @abstractmethod
    def upload_file(
        self, local_path: str, remote_path: str, metadata: dict[str, str] | None = None
    ) -> str:
        """
        Upload file to cloud storage.

        Args:
            local_path: Path to local file
            remote_path: Destination path in cloud storage
            metadata: Optional metadata to attach to file

        Returns:
            URL or identifier of uploaded file

        Raises:
            FileNotFoundError: If local file doesn't exist
            Exception: If upload fails
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download file from cloud storage.

        Args:
            remote_path: Path to file in cloud storage
            local_path: Destination path for downloaded file

        Raises:
            FileNotFoundError: If remote file doesn't exist
            Exception: If download fails
        """
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> None:
        """
        Delete file from cloud storage.

        Args:
            remote_path: Path to file in cloud storage

        Raises:
            FileNotFoundError: If remote file doesn't exist
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "", max_results: int = 1000) -> list[StorageObject]:
        """
        List files in cloud storage.

        Args:
            prefix: Prefix to filter files (directory path)
            max_results: Maximum number of results to return

        Returns:
            List of StorageObject instances

        Raises:
            Exception: If listing fails
        """
        pass

    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in cloud storage.

        Args:
            remote_path: Path to file in cloud storage

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """
        Generate signed URL for file access.

        Args:
            remote_path: Path to file in cloud storage
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for file access

        Raises:
            FileNotFoundError: If remote file doesn't exist
            Exception: If URL generation fails
        """
        pass

    def upload_directory(
        self, local_dir: str, remote_prefix: str = "", exclude_patterns: list[str] | None = None
    ) -> list[str]:
        """
        Upload entire directory to cloud storage.

        Args:
            local_dir: Path to local directory
            remote_prefix: Prefix for uploaded files
            exclude_patterns: Glob patterns to exclude files

        Returns:
            List of uploaded file paths

        Raises:
            NotADirectoryError: If local_dir is not a directory
            Exception: If upload fails
        """
        local_path = Path(local_dir)
        if not local_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {local_dir}")

        uploaded_files = []
        exclude_patterns = exclude_patterns or []

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                # Check exclusion patterns
                should_exclude = False
                for pattern in exclude_patterns:
                    if file_path.match(pattern):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                # Calculate relative path
                relative_path = file_path.relative_to(local_path)
                remote_path = f"{remote_prefix}/{relative_path}".lstrip("/")

                # Upload file
                self.upload_file(str(file_path), remote_path)
                uploaded_files.append(remote_path)

        return uploaded_files

    def download_directory(self, remote_prefix: str, local_dir: str) -> list[str]:
        """
        Download directory from cloud storage.

        Args:
            remote_prefix: Prefix of files to download
            local_dir: Destination directory

        Returns:
            List of downloaded file paths

        Raises:
            Exception: If download fails
        """
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        downloaded_files = []
        files = self.list_files(prefix=remote_prefix)

        for file_obj in files:
            # Calculate local path
            relative_path = file_obj.key.removeprefix(remote_prefix).lstrip("/")
            local_file_path = local_path / relative_path

            # Create parent directories
            local_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            self.download_file(file_obj.key, str(local_file_path))
            downloaded_files.append(str(local_file_path))

        return downloaded_files

    def get_file_size(self, remote_path: str) -> int:
        """
        Get size of file in cloud storage.

        Args:
            remote_path: Path to file in cloud storage

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If remote file doesn't exist
        """
        files = self.list_files(prefix=remote_path, max_results=1)
        if not files or files[0].key != remote_path:
            raise FileNotFoundError(f"File not found: {remote_path}")
        return files[0].size

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """
        Copy file within cloud storage.

        Default implementation downloads then uploads.
        Subclasses can override with provider-specific copy operations.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Raises:
            FileNotFoundError: If source file doesn't exist
            Exception: If copy fails
        """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            self.download_file(source_path, tmp_path)
            self.upload_file(tmp_path, dest_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
