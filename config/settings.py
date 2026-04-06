"""
Configuration settings for AgriAI application
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    BEDROCK_INFERENCE_PROFILE_ARN: Optional[str] = os.getenv("SONNET_INFERENCE_PROFILE_ARN", None)
    BEDROCK_USE_INFERENCE_PROFILE: bool = bool(os.getenv("SONNET_INFERENCE_PROFILE_ARN"))
    BEDROCK_MAX_TOKENS: int = 4096
    BEDROCK_TEMPERATURE: float = 0.1  # Low temperature for consistent analysis
    BEDROCK_TOP_P: float = 0.9
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    SUPPORTED_IMAGE_FORMATS: list = ["image/jpeg", "image/png", "image/jpg"]
    MAX_IMAGE_DIMENSION: int = 2400  # Max width or height (balanced for detail vs 5MB limit)
    IMAGE_QUALITY_START: int = 90  # Starting quality for compression (higher for better detail)
    
    # Object Detection Configuration
    USE_OBJECT_DETECTION: bool = os.getenv("USE_OBJECT_DETECTION", "true").lower() == "true"
    DETECTION_BACKEND: str = os.getenv("DETECTION_BACKEND", "roboflow")  # Options: mock, yolo, roboflow, custom
    DETECTION_CONFIDENCE: float = float(os.getenv("DETECTION_CONFIDENCE", "0.40"))  # Confidence threshold
    
    # YOLO Configuration (if using YOLO)
    YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")  # Path to YOLO weights
    YOLO_USE_API: bool = os.getenv("YOLO_USE_API", "false").lower() == "true"
    YOLO_API_KEY: Optional[str] = os.getenv("YOLO_API_KEY")
    
    # Roboflow Configuration (if using Roboflow)
    # Default to the provided palm-daffan model (version 3) and API key
    ROBOFLOW_API_KEY: Optional[str] = os.getenv("ROBOFLOW_API_KEY", "gHTl52aLCP3ycLg0FI3e")
    ROBOFLOW_MODEL_ID: Optional[str] = os.getenv("ROBOFLOW_MODEL_ID", "thesis-project-kbu79/palm-daffan")  # workspace/project format
    ROBOFLOW_VERSION: int = int(os.getenv("ROBOFLOW_VERSION", "1"))
    
    # Custom API Configuration (if using custom endpoint)
    CUSTOM_DETECTION_URL: Optional[str] = os.getenv("CUSTOM_DETECTION_URL")
    CUSTOM_DETECTION_API_KEY: Optional[str] = os.getenv("CUSTOM_DETECTION_API_KEY")
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "agriai-images")
    S3_ORIGINAL_PREFIX: str = os.getenv("S3_ORIGINAL_PREFIX", "originals/")
    S3_ANNOTATED_PREFIX: str = os.getenv("S3_ANNOTATED_PREFIX", "annotated/")
    S3_PRESIGNED_URL_EXPIRATION: int = int(os.getenv("S3_PRESIGNED_URL_EXPIRATION", "3600"))  # 1 hour default
    
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "agriai_db")
    MONGO_COLLECTION: str = os.getenv("MONGO_COLLECTION", "analyses")
    
    # API Configuration
    API_TITLE: str = "AgriAI - Agricultural Analysis API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered crop analysis using Amazon Bedrock"
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        if not cls.AWS_ACCESS_KEY_ID:
            raise ValueError("AWS_ACCESS_KEY_ID not found in environment")
        if not cls.AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS_SECRET_ACCESS_KEY not found in environment")
        if not cls.AWS_REGION:
            raise ValueError("AWS_REGION not found in environment")
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI not found in environment")
        if not cls.S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME not found in environment")
        return True

settings = Settings()
