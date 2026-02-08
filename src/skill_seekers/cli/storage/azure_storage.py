"""
Azure Blob Storage adaptor implementation.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

try:
    from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
    from azure.core.exceptions import ResourceNotFoundError

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from .base_storage import BaseStorageAdaptor, StorageObject


class AzureStorageAdaptor(BaseStorageAdaptor):
    """
    Azure Blob Storage adaptor.

    Configuration:
        container: Azure container name (required)
        account_name: Storage account name (optional, uses env)
        account_key: Storage account key (optional, uses env)
        connection_string: Connection string (optional, alternative to account_name/key)

    Environment Variables:
        AZURE_STORAGE_CONNECTION_STRING: Azure storage connection string
        AZURE_STORAGE_ACCOUNT_NAME: Storage account name
        AZURE_STORAGE_ACCOUNT_KEY: Storage account key

    Examples:
        # Using connection string
        adaptor = AzureStorageAdaptor(
            container='my-container',
            connection_string='DefaultEndpointsProtocol=https;...'
        )

        # Using account name and key
        adaptor = AzureStorageAdaptor(
            container='my-container',
            account_name='myaccount',
            account_key='mykey'
        )

        # Using environment variables
        adaptor = AzureStorageAdaptor(container='my-container')
    """

    def __init__(self, **kwargs):
        """
        Initialize Azure storage adaptor.

        Args:
            container: Azure container name (required)
            **kwargs: Additional Azure configuration
        """
        super().__init__(**kwargs)

        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob is required for Azure storage. "
                "Install with: pip install azure-storage-blob"
            )

        if "container" not in kwargs:
            raise ValueError("container parameter is required for Azure storage")

        self.container_name = kwargs["container"]

        # Initialize BlobServiceClient
        if "connection_string" in kwargs:
            connection_string = kwargs["connection_string"]
        else:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            # Extract account name from connection string
            self.account_name = None
            self.account_key = None
            for part in connection_string.split(";"):
                if part.startswith("AccountName="):
                    self.account_name = part.split("=", 1)[1]
                elif part.startswith("AccountKey="):
                    self.account_key = part.split("=", 1)[1]
        else:
            account_name = kwargs.get("account_name", os.getenv("AZURE_STORAGE_ACCOUNT_NAME"))
            account_key = kwargs.get("account_key", os.getenv("AZURE_STORAGE_ACCOUNT_KEY"))

            if not account_name or not account_key:
                raise ValueError(
                    "Either connection_string or (account_name + account_key) "
                    "must be provided for Azure storage"
                )

            self.account_name = account_name
            self.account_key = account_key
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url, credential=account_key
            )

        self.container_client = self.blob_service_client.get_container_client(self.container_name)

    def upload_file(
        self, local_path: str, remote_path: str, metadata: dict[str, str] | None = None
    ) -> str:
        """Upload file to Azure Blob Storage."""
        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            blob_client = self.container_client.get_blob_client(remote_path)

            with open(local_file, "rb") as data:
                blob_client.upload_blob(data, overwrite=True, metadata=metadata)

            return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{remote_path}"
        except Exception as e:
            raise Exception(f"Azure upload failed: {e}") from e

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from Azure Blob Storage."""
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            blob_client = self.container_client.get_blob_client(remote_path)

            with open(local_file, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}") from None
        except Exception as e:
            raise Exception(f"Azure download failed: {e}") from e

    def delete_file(self, remote_path: str) -> None:
        """Delete file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(remote_path)
            blob_client.delete_blob()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Remote file not found: {remote_path}") from None
        except Exception as e:
            raise Exception(f"Azure deletion failed: {e}") from e

    def list_files(self, prefix: str = "", max_results: int = 1000) -> list[StorageObject]:
        """List files in Azure container."""
        try:
            blobs = self.container_client.list_blobs(
                name_starts_with=prefix, results_per_page=max_results
            )

            files = []
            for blob in blobs:
                files.append(
                    StorageObject(
                        key=blob.name,
                        size=blob.size,
                        last_modified=blob.last_modified.isoformat()
                        if blob.last_modified
                        else None,
                        etag=blob.etag,
                        metadata=blob.metadata,
                    )
                )

            return files
        except Exception as e:
            raise Exception(f"Azure listing failed: {e}") from e

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(remote_path)
            return blob_client.exists()
        except Exception as e:
            raise Exception(f"Azure file existence check failed: {e}") from e

    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Generate SAS URL for Azure blob."""
        try:
            blob_client = self.container_client.get_blob_client(remote_path)

            if not blob_client.exists():
                raise FileNotFoundError(f"Remote file not found: {remote_path}")

            if not self.account_name or not self.account_key:
                raise ValueError("Account name and key are required for SAS URL generation")

            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=remote_path,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires_in),
            )

            return f"{blob_client.url}?{sas_token}"
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Azure SAS URL generation failed: {e}") from e

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """Copy file within Azure container (server-side copy)."""
        try:
            source_blob = self.container_client.get_blob_client(source_path)

            if not source_blob.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            dest_blob = self.container_client.get_blob_client(dest_path)

            # Start copy operation
            dest_blob.start_copy_from_url(source_blob.url)

            # Wait for copy to complete
            properties = dest_blob.get_blob_properties()
            while properties.copy.status == "pending":
                import time

                time.sleep(0.1)
                properties = dest_blob.get_blob_properties()

            if properties.copy.status != "success":
                raise Exception(f"Copy failed with status: {properties.copy.status}")

        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Azure copy failed: {e}") from e
