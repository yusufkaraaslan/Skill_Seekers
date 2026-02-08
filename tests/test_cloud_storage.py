"""
Tests for cloud storage adaptors.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from skill_seekers.cli.storage import (
    get_storage_adaptor,
    BaseStorageAdaptor,
    S3StorageAdaptor,
    GCSStorageAdaptor,
    AzureStorageAdaptor,
    StorageObject,
)

# Check if cloud storage dependencies are available
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


# ========================================
# Factory Tests
# ========================================

@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
def test_get_storage_adaptor_s3():
    """Test S3 adaptor factory."""
    with patch('skill_seekers.cli.storage.s3_storage.boto3'):
        adaptor = get_storage_adaptor('s3', bucket='test-bucket')
        assert isinstance(adaptor, S3StorageAdaptor)


@pytest.mark.skipif(not GCS_AVAILABLE, reason="google-cloud-storage not installed")
def test_get_storage_adaptor_gcs():
    """Test GCS adaptor factory."""
    with patch('skill_seekers.cli.storage.gcs_storage.storage'):
        adaptor = get_storage_adaptor('gcs', bucket='test-bucket')
        assert isinstance(adaptor, GCSStorageAdaptor)


@pytest.mark.skipif(not AZURE_AVAILABLE, reason="azure-storage-blob not installed")
def test_get_storage_adaptor_azure():
    """Test Azure adaptor factory."""
    with patch('skill_seekers.cli.storage.azure_storage.BlobServiceClient'):
        adaptor = get_storage_adaptor(
            'azure',
            container='test-container',
            connection_string='DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key'
        )
        assert isinstance(adaptor, AzureStorageAdaptor)


def test_get_storage_adaptor_invalid_provider():
    """Test invalid provider raises error."""
    with pytest.raises(ValueError, match="Unsupported storage provider"):
        get_storage_adaptor('invalid', bucket='test')


# ========================================
# S3 Storage Tests
# ========================================

@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_s3_upload_file(mock_boto3):
    """Test S3 file upload."""
    # Setup mocks
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b'test content')
        tmp_path = tmp_file.name

    try:
        # Test upload
        result = adaptor.upload_file(tmp_path, 'test.txt')

        assert result == 's3://test-bucket/test.txt'
        mock_client.upload_file.assert_called_once()
    finally:
        Path(tmp_path).unlink()


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_s3_download_file(mock_boto3):
    """Test S3 file download."""
    # Setup mocks
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, 'downloaded.txt')

        # Test download
        adaptor.download_file('test.txt', local_path)

        mock_client.download_file.assert_called_once_with(
            'test-bucket', 'test.txt', local_path
        )


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_s3_list_files(mock_boto3):
    """Test S3 file listing."""
    # Setup mocks
    mock_client = Mock()
    mock_paginator = Mock()
    mock_page_iterator = [
        {
            'Contents': [
                {
                    'Key': 'file1.txt',
                    'Size': 100,
                    'LastModified': Mock(isoformat=lambda: '2024-01-01T00:00:00'),
                    'ETag': '"abc123"'
                }
            ]
        }
    ]

    mock_paginator.paginate.return_value = mock_page_iterator
    mock_client.get_paginator.return_value = mock_paginator
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    # Test list
    files = adaptor.list_files('prefix/')

    assert len(files) == 1
    assert files[0].key == 'file1.txt'
    assert files[0].size == 100
    assert files[0].etag == 'abc123'


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_s3_file_exists(mock_boto3):
    """Test S3 file existence check."""
    # Setup mocks
    mock_client = Mock()
    mock_client.head_object.return_value = {}
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    # Test exists
    assert adaptor.file_exists('test.txt') is True


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_s3_get_file_url(mock_boto3):
    """Test S3 presigned URL generation."""
    # Setup mocks
    mock_client = Mock()
    mock_client.generate_presigned_url.return_value = 'https://s3.amazonaws.com/signed-url'
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    # Test URL generation
    url = adaptor.get_file_url('test.txt', expires_in=7200)

    assert url == 'https://s3.amazonaws.com/signed-url'
    mock_client.generate_presigned_url.assert_called_once()


# ========================================
# GCS Storage Tests
# ========================================

@pytest.mark.skipif(not GCS_AVAILABLE, reason="google-cloud-storage not installed")
@patch('skill_seekers.cli.storage.gcs_storage.storage')
def test_gcs_upload_file(mock_storage):
    """Test GCS file upload."""
    # Setup mocks
    mock_client = Mock()
    mock_bucket = Mock()
    mock_blob = Mock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_storage.Client.return_value = mock_client

    adaptor = GCSStorageAdaptor(bucket='test-bucket')

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b'test content')
        tmp_path = tmp_file.name

    try:
        # Test upload
        result = adaptor.upload_file(tmp_path, 'test.txt')

        assert result == 'gs://test-bucket/test.txt'
        mock_blob.upload_from_filename.assert_called_once()
    finally:
        Path(tmp_path).unlink()


@pytest.mark.skipif(not GCS_AVAILABLE, reason="google-cloud-storage not installed")
@patch('skill_seekers.cli.storage.gcs_storage.storage')
def test_gcs_download_file(mock_storage):
    """Test GCS file download."""
    # Setup mocks
    mock_client = Mock()
    mock_bucket = Mock()
    mock_blob = Mock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_storage.Client.return_value = mock_client

    adaptor = GCSStorageAdaptor(bucket='test-bucket')

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, 'downloaded.txt')

        # Test download
        adaptor.download_file('test.txt', local_path)

        mock_blob.download_to_filename.assert_called_once()


@pytest.mark.skipif(not GCS_AVAILABLE, reason="google-cloud-storage not installed")
@patch('skill_seekers.cli.storage.gcs_storage.storage')
def test_gcs_list_files(mock_storage):
    """Test GCS file listing."""
    # Setup mocks
    mock_client = Mock()
    mock_blob = Mock()
    mock_blob.name = 'file1.txt'
    mock_blob.size = 100
    mock_blob.updated = Mock(isoformat=lambda: '2024-01-01T00:00:00')
    mock_blob.etag = 'abc123'
    mock_blob.metadata = {}

    mock_client.list_blobs.return_value = [mock_blob]
    mock_storage.Client.return_value = mock_client
    mock_client.bucket.return_value = Mock()

    adaptor = GCSStorageAdaptor(bucket='test-bucket')

    # Test list
    files = adaptor.list_files('prefix/')

    assert len(files) == 1
    assert files[0].key == 'file1.txt'
    assert files[0].size == 100


# ========================================
# Azure Storage Tests
# ========================================

@pytest.mark.skipif(not AZURE_AVAILABLE, reason="azure-storage-blob not installed")
@patch('skill_seekers.cli.storage.azure_storage.BlobServiceClient')
def test_azure_upload_file(mock_blob_service):
    """Test Azure file upload."""
    # Setup mocks
    mock_service_client = Mock()
    mock_container_client = Mock()
    mock_blob_client = Mock()

    mock_service_client.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client
    mock_blob_service.from_connection_string.return_value = mock_service_client

    connection_string = 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key'
    adaptor = AzureStorageAdaptor(container='test-container', connection_string=connection_string)

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b'test content')
        tmp_path = tmp_file.name

    try:
        # Test upload
        result = adaptor.upload_file(tmp_path, 'test.txt')

        assert 'test.blob.core.windows.net' in result
        mock_blob_client.upload_blob.assert_called_once()
    finally:
        Path(tmp_path).unlink()


@pytest.mark.skipif(not AZURE_AVAILABLE, reason="azure-storage-blob not installed")
@patch('skill_seekers.cli.storage.azure_storage.BlobServiceClient')
def test_azure_download_file(mock_blob_service):
    """Test Azure file download."""
    # Setup mocks
    mock_service_client = Mock()
    mock_container_client = Mock()
    mock_blob_client = Mock()
    mock_download_stream = Mock()
    mock_download_stream.readall.return_value = b'test content'

    mock_service_client.get_container_client.return_value = mock_container_client
    mock_container_client.get_blob_client.return_value = mock_blob_client
    mock_blob_client.download_blob.return_value = mock_download_stream
    mock_blob_service.from_connection_string.return_value = mock_service_client

    connection_string = 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key'
    adaptor = AzureStorageAdaptor(container='test-container', connection_string=connection_string)

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, 'downloaded.txt')

        # Test download
        adaptor.download_file('test.txt', local_path)

        assert Path(local_path).exists()
        assert Path(local_path).read_bytes() == b'test content'


@pytest.mark.skipif(not AZURE_AVAILABLE, reason="azure-storage-blob not installed")
@patch('skill_seekers.cli.storage.azure_storage.BlobServiceClient')
def test_azure_list_files(mock_blob_service):
    """Test Azure file listing."""
    # Setup mocks
    mock_service_client = Mock()
    mock_container_client = Mock()
    mock_blob = Mock()
    mock_blob.name = 'file1.txt'
    mock_blob.size = 100
    mock_blob.last_modified = Mock(isoformat=lambda: '2024-01-01T00:00:00')
    mock_blob.etag = 'abc123'
    mock_blob.metadata = {}

    mock_container_client.list_blobs.return_value = [mock_blob]
    mock_service_client.get_container_client.return_value = mock_container_client
    mock_blob_service.from_connection_string.return_value = mock_service_client

    connection_string = 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key'
    adaptor = AzureStorageAdaptor(container='test-container', connection_string=connection_string)

    # Test list
    files = adaptor.list_files('prefix/')

    assert len(files) == 1
    assert files[0].key == 'file1.txt'
    assert files[0].size == 100


# ========================================
# Base Adaptor Tests
# ========================================

def test_storage_object():
    """Test StorageObject dataclass."""
    obj = StorageObject(
        key='test.txt',
        size=100,
        last_modified='2024-01-01T00:00:00',
        etag='abc123',
        metadata={'key': 'value'}
    )

    assert obj.key == 'test.txt'
    assert obj.size == 100
    assert obj.metadata == {'key': 'value'}


def test_base_adaptor_abstract():
    """Test that BaseStorageAdaptor cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseStorageAdaptor(bucket='test')


# ========================================
# Integration-style Tests
# ========================================

@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_upload_directory(mock_boto3):
    """Test directory upload."""
    # Setup mocks
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    # Create temporary directory with files
    with tempfile.TemporaryDirectory() as tmp_dir:
        (Path(tmp_dir) / 'file1.txt').write_text('content1')
        (Path(tmp_dir) / 'file2.txt').write_text('content2')
        (Path(tmp_dir) / 'subdir').mkdir()
        (Path(tmp_dir) / 'subdir' / 'file3.txt').write_text('content3')

        # Test upload directory
        uploaded_files = adaptor.upload_directory(tmp_dir, 'skills/')

        assert len(uploaded_files) == 3
        assert mock_client.upload_file.call_count == 3


@pytest.mark.skipif(not BOTO3_AVAILABLE, reason="boto3 not installed")
@patch('skill_seekers.cli.storage.s3_storage.boto3')
def test_download_directory(mock_boto3):
    """Test directory download."""
    # Setup mocks
    mock_client = Mock()
    mock_paginator = Mock()
    mock_page_iterator = [
        {
            'Contents': [
                {
                    'Key': 'skills/file1.txt',
                    'Size': 100,
                    'LastModified': Mock(isoformat=lambda: '2024-01-01T00:00:00'),
                    'ETag': '"abc"'
                },
                {
                    'Key': 'skills/file2.txt',
                    'Size': 200,
                    'LastModified': Mock(isoformat=lambda: '2024-01-01T00:00:00'),
                    'ETag': '"def"'
                }
            ]
        }
    ]

    mock_paginator.paginate.return_value = mock_page_iterator
    mock_client.get_paginator.return_value = mock_paginator
    mock_boto3.client.return_value = mock_client
    mock_boto3.resource.return_value = Mock()

    adaptor = S3StorageAdaptor(bucket='test-bucket')

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Test download directory
        downloaded_files = adaptor.download_directory('skills/', tmp_dir)

        assert len(downloaded_files) == 2
        assert mock_client.download_file.call_count == 2


def test_missing_dependencies():
    """Test graceful handling of missing dependencies."""
    # Test S3 without boto3
    with patch.dict('sys.modules', {'boto3': None}):
        with pytest.raises(ImportError, match="boto3 is required"):
            from skill_seekers.cli.storage.s3_storage import S3StorageAdaptor
            S3StorageAdaptor(bucket='test')

    # Test GCS without google-cloud-storage
    with patch.dict('sys.modules', {'google.cloud.storage': None}):
        with pytest.raises(ImportError, match="google-cloud-storage is required"):
            from skill_seekers.cli.storage.gcs_storage import GCSStorageAdaptor
            GCSStorageAdaptor(bucket='test')

    # Test Azure without azure-storage-blob
    with patch.dict('sys.modules', {'azure.storage.blob': None}):
        with pytest.raises(ImportError, match="azure-storage-blob is required"):
            from skill_seekers.cli.storage.azure_storage import AzureStorageAdaptor
            AzureStorageAdaptor(container='test', connection_string='test')
