"""
Google Cloud Storage (GCS) adaptor implementation.
"""

import os
from pathlib import Path
from datetime import timedelta

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

from .base_storage import BaseStorageAdaptor, StorageObject


class GCSStorageAdaptor(BaseStorageAdaptor):
    """
    Google Cloud Storage adaptor.

    Configuration:
        bucket: GCS bucket name (required)
        project: GCP project ID (optional, uses default)
        credentials_path: Path to service account JSON (optional)

    Environment Variables:
        GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON
        GOOGLE_CLOUD_PROJECT: GCP project ID

    Examples:
        # Using environment variables
        adaptor = GCSStorageAdaptor(bucket='my-bucket')

        # With explicit credentials
        adaptor = GCSStorageAdaptor(
            bucket='my-bucket',
            project='my-project',
            credentials_path='/path/to/credentials.json'
        )

        # Using default credentials
        adaptor = GCSStorageAdaptor(
            bucket='my-bucket',
            project='my-project'
        )
    """

    def __init__(self, **kwargs):
        """
        Initialize GCS storage adaptor.

        Args:
            bucket: GCS bucket name (required)
            **kwargs: Additional GCS configuration
        """
        super().__init__(**kwargs)

        if not GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is required for GCS storage. "
                "Install with: pip install google-cloud-storage"
            )

        if "bucket" not in kwargs:
            raise ValueError("bucket parameter is required for GCS storage")

        self.bucket_name = kwargs["bucket"]
        self.project = kwargs.get("project", os.getenv("GOOGLE_CLOUD_PROJECT"))

        # Initialize GCS client
        client_kwargs = {}
        if self.project:
            client_kwargs["project"] = self.project

        if "credentials_path" in kwargs:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = kwargs["credentials_path"]

        self.storage_client = storage.Client(**client_kwargs)
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def upload_file(
        self, local_path: str, remote_path: str, metadata: dict[str, str] | None = None
    ) -> str:
        """Upload file to GCS."""
        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            blob = self.bucket.blob(remote_path)

            if metadata:
                blob.metadata = metadata

            blob.upload_from_filename(str(local_file))
            return f"gs://{self.bucket_name}/{remote_path}"
        except Exception as e:
            raise Exception(f"GCS upload failed: {e}") from e

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from GCS."""
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            blob = self.bucket.blob(remote_path)
            blob.download_to_filename(str(local_file))
        except NotFound:
            raise FileNotFoundError(f"Remote file not found: {remote_path}") from None
        except Exception as e:
            raise Exception(f"GCS download failed: {e}") from e

    def delete_file(self, remote_path: str) -> None:
        """Delete file from GCS."""
        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
        except NotFound:
            raise FileNotFoundError(f"Remote file not found: {remote_path}") from None
        except Exception as e:
            raise Exception(f"GCS deletion failed: {e}") from e

    def list_files(self, prefix: str = "", max_results: int = 1000) -> list[StorageObject]:
        """List files in GCS bucket."""
        try:
            blobs = self.storage_client.list_blobs(
                self.bucket_name, prefix=prefix, max_results=max_results
            )

            files = []
            for blob in blobs:
                files.append(
                    StorageObject(
                        key=blob.name,
                        size=blob.size,
                        last_modified=blob.updated.isoformat() if blob.updated else None,
                        etag=blob.etag,
                        metadata=blob.metadata,
                    )
                )

            return files
        except Exception as e:
            raise Exception(f"GCS listing failed: {e}") from e

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in GCS."""
        try:
            blob = self.bucket.blob(remote_path)
            return blob.exists()
        except Exception as e:
            raise Exception(f"GCS file existence check failed: {e}") from e

    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Generate signed URL for GCS object."""
        try:
            blob = self.bucket.blob(remote_path)

            if not blob.exists():
                raise FileNotFoundError(f"Remote file not found: {remote_path}")

            url = blob.generate_signed_url(
                version="v4", expiration=timedelta(seconds=expires_in), method="GET"
            )
            return url
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"GCS signed URL generation failed: {e}") from e

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """Copy file within GCS bucket (server-side copy)."""
        try:
            source_blob = self.bucket.blob(source_path)

            if not source_blob.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            self.bucket.copy_blob(source_blob, self.bucket, dest_path)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"GCS copy failed: {e}") from e
