"""
Cloud storage adaptors for Skill Seekers.

Provides unified interface for multiple cloud storage providers:
- AWS S3
- Google Cloud Storage (GCS)
- Azure Blob Storage

Usage:
    from skill_seekers.cli.storage import get_storage_adaptor

    # Get adaptor for specific provider
    adaptor = get_storage_adaptor('s3', bucket='my-bucket')

    # Upload file
    adaptor.upload_file('local/path/skill.zip', 'skills/skill.zip')

    # Download file
    adaptor.download_file('skills/skill.zip', 'local/path/skill.zip')

    # List files
    files = adaptor.list_files('skills/')
"""

from .base_storage import BaseStorageAdaptor, StorageObject
from .s3_storage import S3StorageAdaptor
from .gcs_storage import GCSStorageAdaptor
from .azure_storage import AzureStorageAdaptor


def get_storage_adaptor(provider: str, **kwargs) -> BaseStorageAdaptor:
    """
    Factory function to get storage adaptor for specified provider.

    Args:
        provider: Storage provider name ('s3', 'gcs', 'azure')
        **kwargs: Provider-specific configuration

    Returns:
        Storage adaptor instance

    Raises:
        ValueError: If provider is not supported

    Examples:
        # AWS S3
        adaptor = get_storage_adaptor('s3',
                                     bucket='my-bucket',
                                     region='us-west-2')

        # Google Cloud Storage
        adaptor = get_storage_adaptor('gcs',
                                     bucket='my-bucket',
                                     project='my-project')

        # Azure Blob Storage
        adaptor = get_storage_adaptor('azure',
                                     container='my-container',
                                     account_name='myaccount')
    """
    adaptors = {
        "s3": S3StorageAdaptor,
        "gcs": GCSStorageAdaptor,
        "azure": AzureStorageAdaptor,
    }

    provider_lower = provider.lower()
    if provider_lower not in adaptors:
        supported = ", ".join(adaptors.keys())
        raise ValueError(
            f"Unsupported storage provider: {provider}. Supported providers: {supported}"
        )

    return adaptors[provider_lower](**kwargs)


__all__ = [
    "BaseStorageAdaptor",
    "StorageObject",
    "S3StorageAdaptor",
    "GCSStorageAdaptor",
    "AzureStorageAdaptor",
    "get_storage_adaptor",
]
