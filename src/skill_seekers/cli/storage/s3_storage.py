"""
AWS S3 storage adaptor implementation.
"""

import os
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .base_storage import BaseStorageAdaptor, StorageObject


class S3StorageAdaptor(BaseStorageAdaptor):
    """
    AWS S3 storage adaptor.

    Configuration:
        bucket: S3 bucket name (required)
        region: AWS region (optional, default: us-east-1)
        aws_access_key_id: AWS access key (optional, uses env/credentials)
        aws_secret_access_key: AWS secret key (optional, uses env/credentials)
        endpoint_url: Custom endpoint URL (optional, for S3-compatible services)

    Environment Variables:
        AWS_ACCESS_KEY_ID: AWS access key
        AWS_SECRET_ACCESS_KEY: AWS secret key
        AWS_DEFAULT_REGION: AWS region

    Examples:
        # Using environment variables
        adaptor = S3StorageAdaptor(bucket='my-bucket')

        # With explicit credentials
        adaptor = S3StorageAdaptor(
            bucket='my-bucket',
            region='us-west-2',
            aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
            aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        )

        # S3-compatible service (MinIO, DigitalOcean Spaces)
        adaptor = S3StorageAdaptor(
            bucket='my-bucket',
            endpoint_url='https://nyc3.digitaloceanspaces.com',
            aws_access_key_id='...',
            aws_secret_access_key='...'
        )
    """

    def __init__(self, **kwargs):
        """
        Initialize S3 storage adaptor.

        Args:
            bucket: S3 bucket name (required)
            **kwargs: Additional S3 configuration
        """
        super().__init__(**kwargs)

        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")

        if "bucket" not in kwargs:
            raise ValueError("bucket parameter is required for S3 storage")

        self.bucket = kwargs["bucket"]
        self.region = kwargs.get("region", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

        # Initialize S3 client
        client_kwargs = {
            "region_name": self.region,
        }

        if "endpoint_url" in kwargs:
            client_kwargs["endpoint_url"] = kwargs["endpoint_url"]

        if "aws_access_key_id" in kwargs:
            client_kwargs["aws_access_key_id"] = kwargs["aws_access_key_id"]

        if "aws_secret_access_key" in kwargs:
            client_kwargs["aws_secret_access_key"] = kwargs["aws_secret_access_key"]

        self.s3_client = boto3.client("s3", **client_kwargs)
        self.s3_resource = boto3.resource("s3", **client_kwargs)

    def upload_file(
        self, local_path: str, remote_path: str, metadata: dict[str, str] | None = None
    ) -> str:
        """Upload file to S3."""
        local_file = Path(local_path)
        if not local_file.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        extra_args = {}
        if metadata:
            extra_args["Metadata"] = metadata

        try:
            self.s3_client.upload_file(
                str(local_file),
                self.bucket,
                remote_path,
                ExtraArgs=extra_args if extra_args else None,
            )
            return f"s3://{self.bucket}/{remote_path}"
        except ClientError as e:
            raise Exception(f"S3 upload failed: {e}") from e

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from S3."""
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.s3_client.download_file(self.bucket, remote_path, str(local_file))
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"Remote file not found: {remote_path}") from e
            raise Exception(f"S3 download failed: {e}") from e

    def delete_file(self, remote_path: str) -> None:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=remote_path)
        except ClientError as e:
            raise Exception(f"S3 deletion failed: {e}") from e

    def list_files(self, prefix: str = "", max_results: int = 1000) -> list[StorageObject]:
        """List files in S3 bucket."""
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket, Prefix=prefix, PaginationConfig={"MaxItems": max_results}
            )

            files = []
            for page in page_iterator:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    files.append(
                        StorageObject(
                            key=obj["Key"],
                            size=obj["Size"],
                            last_modified=obj["LastModified"].isoformat(),
                            etag=obj.get("ETag", "").strip('"'),
                        )
                    )

            return files
        except ClientError as e:
            raise Exception(f"S3 listing failed: {e}") from e

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=remote_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise Exception(f"S3 head_object failed: {e}") from e

    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": remote_path},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise Exception(f"S3 presigned URL generation failed: {e}") from e

    def copy_file(self, source_path: str, dest_path: str) -> None:
        """Copy file within S3 bucket (server-side copy)."""
        try:
            copy_source = {"Bucket": self.bucket, "Key": source_path}
            self.s3_client.copy_object(CopySource=copy_source, Bucket=self.bucket, Key=dest_path)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"Source file not found: {source_path}") from e
            raise Exception(f"S3 copy failed: {e}") from e
