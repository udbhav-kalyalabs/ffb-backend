"""
S3 service for image storage
"""
import boto3
import uuid
from typing import Optional
from datetime import datetime
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    """Service for managing image uploads and downloads from S3"""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = settings.S3_BUCKET_NAME
        logger.info(f"S3Service initialized with bucket: {self.bucket}")
    
    def generate_image_id(self) -> str:
        """
        Generate unique image ID with timestamp prefix
        Format: YYYYMMDD_HHMMSS_<uuid>
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:12]
        return f"{timestamp}_{unique_id}"
    
    def upload_original_image(
        self,
        image_bytes: bytes,
        image_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload original image to S3
        
        Args:
            image_bytes: Image data as bytes
            image_id: Unique identifier for this image
            filename: Original filename
            content_type: MIME type of the image
            
        Returns:
            S3 URL of uploaded image
        """
        try:
            key = f"{settings.S3_ORIGINAL_PREFIX}{image_id}/{filename}"
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=image_bytes,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'image_id': image_id
                }
            )
            
            url = f"s3://{self.bucket}/{key}"
            logger.info(f"Uploaded original image: {url} ({len(image_bytes)} bytes)")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload original image: {str(e)}")
            raise
    
    def upload_annotated_image(
        self,
        image_bytes: bytes,
        image_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload annotated image to S3
        
        Args:
            image_bytes: Annotated image data as bytes
            image_id: Unique identifier (same as original)
            filename: Original filename
            content_type: MIME type of the image
            
        Returns:
            S3 URL of uploaded annotated image
        """
        try:
            # Add 'annotated_' prefix to filename
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'jpg'
            annotated_filename = f"annotated_{base_name}.{extension}"
            
            key = f"{settings.S3_ANNOTATED_PREFIX}{image_id}/{annotated_filename}"
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=image_bytes,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'annotated_filename': annotated_filename,
                    'annotated_timestamp': datetime.utcnow().isoformat(),
                    'image_id': image_id
                }
            )
            
            url = f"s3://{self.bucket}/{key}"
            logger.info(f"Uploaded annotated image: {url} ({len(image_bytes)} bytes)")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload annotated image: {str(e)}")
            raise
    
    def get_presigned_url(self, s3_url: str, expiration: Optional[int] = None) -> str:
        """
        Generate presigned URL for S3 object
        
        Args:
            s3_url: S3 URL (s3://bucket/key format)
            expiration: URL expiration time in seconds (default from settings)
            
        Returns:
            Presigned URL for direct access
        """
        try:
            if expiration is None:
                expiration = settings.S3_PRESIGNED_URL_EXPIRATION
            
            # Parse s3:// URL to extract key
            s3_path = s3_url.replace(f"s3://{self.bucket}/", "")
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': s3_path
                },
                ExpiresIn=expiration
            )
            
            logger.debug(f"Generated presigned URL for {s3_path} (expires in {expiration}s)")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise
    
    def download_image(self, s3_url: str) -> bytes:
        """
        Download image from S3
        
        Args:
            s3_url: S3 URL (s3://bucket/key format)
            
        Returns:
            Image data as bytes
        """
        try:
            s3_path = s3_url.replace(f"s3://{self.bucket}/", "")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=s3_path
            )
            
            image_bytes = response['Body'].read()
            logger.info(f"Downloaded image from {s3_path} ({len(image_bytes)} bytes)")
            return image_bytes
            
        except Exception as e:
            logger.error(f"Failed to download image: {str(e)}")
            raise
    
    def check_bucket_exists(self) -> bool:
        """
        Check if the S3 bucket exists and is accessible
        
        Returns:
            True if bucket exists and is accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} is accessible")
            return True
        except Exception as e:
            logger.error(f"Bucket {self.bucket} is not accessible: {str(e)}")
            return False
    
    def list_images_by_prefix(self, prefix: str, max_keys: int = 1000) -> list:
        """
        List images in S3 by prefix
        
        Args:
            prefix: S3 key prefix to search
            max_keys: Maximum number of results
            
        Returns:
            List of S3 object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                keys = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Found {len(keys)} objects with prefix {prefix}")
                return keys
            else:
                logger.info(f"No objects found with prefix {prefix}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list objects: {str(e)}")
            raise

# Singleton instance
s3_service = S3Service()

