"""
Pydantic models for request/response schemas
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class CropType(str, Enum):
    """Supported crop types"""
    OIL_PALM = "oil_palm"
    # Future crops can be added here
    # RUBBER = "rubber"
    # COFFEE = "coffee"

class FruitStage(str, Enum):
    """Fruit ripeness stages"""
    YOUNG = "young"
    MATURE = "mature"
    RIPE = "ripe"
    OVERRIPE = "overripe"

class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects"""
    # Support both formats: corners (old) and center+size (new)
    x_min: Optional[int] = Field(None, description="Left coordinate (corner format)")
    y_min: Optional[int] = Field(None, description="Top coordinate (corner format)")
    x_max: Optional[int] = Field(None, description="Right coordinate (corner format)")
    y_max: Optional[int] = Field(None, description="Bottom coordinate (corner format)")
    center_x: Optional[int] = Field(None, description="Center X coordinate")
    center_y: Optional[int] = Field(None, description="Center Y coordinate")
    
    # New normalized format (0.0-1.0)
    center_x_norm: Optional[float] = Field(None, description="Center X as percentage (0-1)")
    center_y_norm: Optional[float] = Field(None, description="Center Y as percentage (0-1)")
    width_norm: Optional[float] = Field(None, description="Width as percentage (0-1)")
    height_norm: Optional[float] = Field(None, description="Height as percentage (0-1)")
    
    # Segmentation data (for precise contours)
    segmentation: Optional[List[List[float]]] = Field(None, description="List of [x, y] points forming contour")
    area: Optional[float] = Field(None, description="Actual area in pixels (for segmentation)")
    
    @classmethod
    def from_coordinates(cls, x_min: int, y_min: int, x_max: int, y_max: int,
                        segmentation: Optional[List[List[float]]] = None,
                        area: Optional[float] = None):
        """Create BoundingBox with calculated center and optional segmentation data"""
        return cls(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            center_x=(x_min + x_max) // 2,
            center_y=(y_min + y_max) // 2,
            segmentation=segmentation,
            area=area
        )
    
    @classmethod
    def from_center_size_normalized(cls, center_x: float, center_y: float, 
                                   width: float, height: float,
                                   image_width: int, image_height: int):
        """Create BoundingBox from normalized center+size format"""
        # Convert normalized to pixel coordinates
        center_x_px = int(center_x * image_width)
        center_y_px = int(center_y * image_height)
        width_px = int(width * image_width)
        height_px = int(height * image_height)
        
        # Calculate corners
        x_min = max(0, center_x_px - width_px // 2)
        y_min = max(0, center_y_px - height_px // 2)
        x_max = min(image_width, center_x_px + width_px // 2)
        y_max = min(image_height, center_y_px + height_px // 2)
        
        return cls(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            center_x=center_x_px,
            center_y=center_y_px,
            center_x_norm=center_x,
            center_y_norm=center_y,
            width_norm=width,
            height_norm=height
        )

class FruitBunch(BaseModel):
    """Individual fruit bunch detection with detailed analysis"""
    id: int = Field(..., description="Unique identifier for this bunch")
    stage: FruitStage = Field(..., description="Ripeness stage")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bounding_box: BoundingBox = Field(..., description="Location in image")
    color_code: str = Field(..., description="Hex color for visualization")
    visibility: Optional[str] = Field(None, description="Visibility status: fully_visible, partially_visible, behind_fronds, background")
    size: Optional[str] = Field(None, description="Relative size: large, medium, small")
    position: Optional[str] = Field(None, description="Position in tree: front, back, left, right, center, etc.")
    description: Optional[str] = Field(None, description="Detailed analysis of this bunch")

class StageSummary(BaseModel):
    """Summary of fruit stages"""
    young: int = Field(default=0, description="Count of young bunches")
    mature: int = Field(default=0, description="Count of mature bunches")
    ripe: int = Field(default=0, description="Count of ripe bunches")
    overripe: int = Field(default=0, description="Count of overripe bunches")

class ImageMetadata(BaseModel):
    """Metadata about analyzed image"""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    analyzed_at: str = Field(..., description="Analysis timestamp")
    file_size_kb: Optional[float] = Field(None, description="File size in KB")

class PlantHealth(BaseModel):
    """Detailed plant health assessment"""
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score")
    frond_condition: Optional[str] = Field(None, description="Frond health status")
    bunch_development: Optional[str] = Field(None, description="Bunch development assessment")
    observations: Optional[List[str]] = Field(None, description="Detailed health observations")
    concerns: Optional[List[str]] = Field(None, description="Any health concerns or issues")

class CropAnalysis(BaseModel):
    """Main analysis results with comprehensive details"""
    total_bunches: int = Field(..., description="Total number of bunches detected")
    detection_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall detection confidence")
    bunches: List[FruitBunch] = Field(..., description="Individual bunch details")
    stage_summary: StageSummary = Field(..., description="Summary by stage")
    plant_health: Optional[PlantHealth] = Field(None, description="Comprehensive plant health assessment")
    recommendations: Optional[List[str]] = Field(None, description="Actionable recommendations")

class AnalysisResponse(BaseModel):
    """Complete API response"""
    success: bool = Field(..., description="Whether analysis succeeded")
    crop_type: CropType = Field(..., description="Type of crop analyzed")
    analysis: Optional[CropAnalysis] = Field(None, description="Analysis results")
    image_metadata: ImageMetadata = Field(..., description="Image information")
    processing_time_ms: Optional[float] = Field(None, description="Processing duration")
    error: Optional[str] = Field(None, description="Error message if failed")

class AnalysisRequest(BaseModel):
    """Request parameters for analysis"""
    crop_type: CropType = Field(CropType.OIL_PALM, description="Type of crop to analyze")
    include_recommendations: bool = Field(True, description="Include harvesting recommendations")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")

class Base64AnalysisRequest(BaseModel):
    """Request for analysis with base64 encoded image"""
    file: str = Field(..., description="Base64 encoded image (with or without data URI prefix)")
    filename: str = Field(..., description="Original filename")
    lat: Optional[str] = Field(None, description="Latitude coordinate")
    long: Optional[str] = Field(None, description="Longitude coordinate")
    uuid: Optional[str] = Field(None, description="User UUID")
    crop_type: str = Field("oil_palm", description="Type of crop to analyze")
    include_recommendations: bool = Field(True, description="Include harvesting recommendations")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")
    use_detection: bool = Field(True, description="Use object detection for precise boxes")
    return_annotated_image: bool = Field(True, description="Return annotated image with bounding boxes")

class AnnotatedAnalysisResponse(BaseModel):
    """Response with analysis and annotated image"""
    success: bool = Field(..., description="Whether analysis succeeded")
    crop_type: CropType = Field(..., description="Type of crop analyzed")
    analysis: Optional[CropAnalysis] = Field(None, description="Analysis results")
    image_metadata: ImageMetadata = Field(..., description="Image information")
    processing_time_ms: Optional[float] = Field(None, description="Processing duration")
    error: Optional[str] = Field(None, description="Error message if failed")
    annotated_image: Optional[str] = Field(None, description="Base64 encoded annotated image")
    annotated_image_format: Optional[str] = Field(None, description="Format of annotated image (jpeg/png)")
    
    # S3 and Database fields
    image_id: Optional[str] = Field(None, description="Unique image identifier")
    original_image_url: Optional[str] = Field(None, description="S3 URL for original image")
    annotated_image_url: Optional[str] = Field(None, description="S3 URL for annotated image")
    database_id: Optional[str] = Field(None, description="MongoDB document ID")

class AnalysisRecord(BaseModel):
    """Database record for a single analysis"""
    id: str = Field(..., description="MongoDB document ID", alias="_id")
    image_id: str = Field(..., description="Unique image identifier")
    user_uuid: str = Field(..., description="User's unique identifier")
    filename: str = Field(..., description="Original filename")
    latitude: Optional[str] = Field(None, description="GPS latitude")
    longitude: Optional[str] = Field(None, description="GPS longitude")
    original_image_url: str = Field(..., description="S3 URL for original image")
    annotated_image_url: str = Field(..., description="S3 URL for annotated image")
    analysis: dict = Field(..., description="Complete analysis results")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"populate_by_name": True}

class FetchAnalysisResponse(BaseModel):
    """Response for fetching a single historical analysis"""
    id: str = Field(..., description="MongoDB document ID", alias="_id")
    image_id: str = Field(..., description="Unique image identifier")
    user_uuid: str = Field(..., description="User's unique identifier")
    filename: str = Field(..., description="Original filename")
    latitude: Optional[str] = Field(None, description="GPS latitude")
    longitude: Optional[str] = Field(None, description="GPS longitude")
    analysis: dict = Field(..., description="Complete analysis results")
    original_image_presigned_url: str = Field(..., description="Presigned URL for original image")
    annotated_image_presigned_url: str = Field(..., description="Presigned URL for annotated image")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = {"populate_by_name": True}

class SimplifiedAnalysisSummary(BaseModel):
    """Simplified summary for listing all analyses"""
    id: str = Field(..., description="MongoDB document ID", alias="_id")
    image_id: str = Field(..., description="Unique image identifier")
    user_uuid: str = Field(..., description="User's unique identifier")
    filename: str = Field(..., description="Original filename")
    crop_type: str = Field(..., description="Type of crop analyzed")
    total_bunches: int = Field(..., description="Total bunches detected")
    created_at: datetime = Field(..., description="Creation timestamp")
    original_image_presigned_url: str = Field(..., description="Presigned URL for original image")
    annotated_image_presigned_url: str = Field(..., description="Presigned URL for annotated image")
    
    model_config = {"populate_by_name": True}

class PaginatedAnalysisResponse(BaseModel):
    """Paginated list of analyses"""
    success: bool = Field(True, description="Request success status")
    total: int = Field(..., description="Total number of analyses in database")
    count: int = Field(..., description="Number of analyses returned in this response")
    limit: int = Field(..., description="Maximum results per page")
    skip: int = Field(..., description="Number of results skipped")
    data: List[SimplifiedAnalysisSummary] = Field(..., description="List of analysis summaries")

class DatabaseStatsResponse(BaseModel):
    """Database statistics response"""
    success: bool = Field(True, description="Request success status")
    total_analyses: int = Field(..., description="Total number of analyses")
    unique_users: int = Field(..., description="Number of unique users")
    crop_distribution: dict = Field(..., description="Distribution of analyses by crop type")
    total_original_images: int = Field(..., description="Total original images in S3")
    total_annotated_images: int = Field(..., description="Total annotated images in S3")