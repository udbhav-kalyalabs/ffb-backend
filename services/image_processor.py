"""
Image processing utilities for preparing images for AI analysis
"""
import base64
import io
from PIL import Image
from typing import Tuple, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image preprocessing and encoding"""
    
    @staticmethod
    def validate_image(file_content: bytes, content_type: str) -> bool:
        """
        Validate image file
        
        Args:
            file_content: Raw file bytes
            content_type: MIME type
        
        Returns:
            True if valid
        
        Raises:
            ValueError if invalid
        """
        # Check file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {file_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")
        
        # Check content type
        if content_type not in settings.SUPPORTED_IMAGE_FORMATS:
            raise ValueError(f"Unsupported format: {content_type}. Supported: {settings.SUPPORTED_IMAGE_FORMATS}")
        
        # Try to open image
        try:
            img = Image.open(io.BytesIO(file_content))
            img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
        
        return True
    
    @staticmethod
    def resize_image_if_needed(image: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions
        
        Args:
            image: PIL Image object
        
        Returns:
            Resized image (or original if no resize needed)
        """
        width, height = image.size
        max_dim = settings.MAX_IMAGE_DIMENSION
        
        if width <= max_dim and height <= max_dim:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dim
            new_height = int((max_dim / width) * height)
        else:
            new_height = max_dim
            new_width = int((max_dim / height) * width)
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def encode_image_to_base64(file_content: bytes) -> Tuple[str, int, int, float]:
        """
        Encode image to base64 and extract metadata
        
        Args:
            file_content: Raw image bytes
        
        Returns:
            Tuple of (base64_string, width, height, file_size_kb)
        """
        try:
            # Open and process image
            image = Image.open(io.BytesIO(file_content))
            
            # Apply EXIF orientation transformation if present
            # This ensures the image orientation matches what will be displayed
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
                logger.debug("Applied EXIF orientation correction during image processing")
            except Exception as e:
                logger.debug(f"EXIF orientation handling: {e}")
            
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                logger.info(f"Converting image from {image.mode} to RGB")
                image = image.convert('RGB')
            
            # Resize if needed
            original_size = image.size
            image = ImageProcessor.resize_image_if_needed(image)
            
            if image.size != original_size:
                logger.info(f"Image resized from {original_size} to {image.size}")
            
            # Get dimensions
            width, height = image.size
            
            # Encode to base64 with quality adjustment to stay under 5MB limit
            quality = getattr(settings, 'IMAGE_QUALITY_START', 90)  # Start with high quality for detail
            max_base64_size = 5 * 1024 * 1024  # 5MB in bytes
            base64_size = 0  # Initialize
            
            while quality > 20:
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
                buffer.seek(0)
                
                image_bytes = buffer.read()
                base64_string = base64.b64encode(image_bytes).decode('utf-8')
                base64_size = len(base64_string.encode('utf-8'))
                
                # Check if base64 encoded size is under limit
                if base64_size <= max_base64_size:
                    file_size_kb = len(image_bytes) / 1024
                    logger.info(f"Image processed: {width}x{height}, {file_size_kb:.2f}KB (quality={quality}, base64={base64_size/1024/1024:.2f}MB)")
                    
                    # DEBUG: Save processed image for visualization debugging
                    try:
                        debug_path = "debug_processed_image.jpg"
                        with open(debug_path, 'wb') as f:
                            f.write(image_bytes)
                        logger.debug(f"Saved processed image to {debug_path} for debugging")
                    except Exception as e:
                        logger.debug(f"Could not save debug image: {e}")
                    
                    return base64_string, width, height, file_size_kb
                
                # Reduce quality and try again
                quality -= 10
                logger.info(f"Reducing quality to {quality} (base64 size: {base64_size/1024/1024:.2f}MB)")
            
            # If we get here, even at quality 20 it's too large
            raise ValueError(f"Cannot compress image to under 5MB (current: {base64_size/1024/1024:.2f}MB)")
            
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    @staticmethod
    def process_uploaded_image(
        file_content: bytes,
        content_type: str
    ) -> Tuple[str, int, int, float]:
        """
        Complete image processing pipeline
        
        Args:
            file_content: Raw file bytes
            content_type: MIME type
        
        Returns:
            Tuple of (base64_string, width, height, file_size_kb)
        """
        # Validate
        ImageProcessor.validate_image(file_content, content_type)
        
        # Process and encode
        return ImageProcessor.encode_image_to_base64(file_content)

# Global instance
image_processor = ImageProcessor()
