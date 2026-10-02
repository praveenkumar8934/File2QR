import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.bucket_name = settings.R2_BUCKET_NAME
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL if settings.R2_ENDPOINT_URL else None,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID if settings.R2_ACCESS_KEY_ID else None,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY if settings.R2_SECRET_ACCESS_KEY else None,
            config=Config(signature_version='s3v4'),
            region_name='auto'  # Cloudflare R2 uses 'auto'
        )

    def get_client(self):
        return self.s3_client

    def generate_upload_url(self, storage_key: str, content_type: str, expires_in: int = 3600) -> str:
        """Generates a presigned URL for direct PUT upload to R2."""
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating upload URL: {e}")
            raise

    def generate_download_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Generates a presigned URL for secure GET download from R2."""
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key,
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise

    def verify_object(self, storage_key: str) -> dict:
        """
        Verifies if an object exists in R2 and returns its metadata (like size).
        Raises an exception if the object does not exist.
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return {
                'content_length': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', '')
            }
        except ClientError as e:
            logger.error(f"Error verifying object: {e}")
            raise

    def delete_object(self, storage_key: str) -> bool:
        """Deletes an object from R2."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting object: {e}")
            return False
