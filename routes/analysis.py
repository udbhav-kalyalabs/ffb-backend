"""
API routes for crop analysis with S3 and MongoDB integration
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
import base64
import re

from services.crop_analyzer import crop_analyzer
from services.hybrid_analyzer import hybrid_analyzer
from services.image_annotator import image_annotator
from services.s3_service import s3_service
from services.mongodb_service import mongodb_service
from models.schemas import (
    CropType,
    Base64AnalysisRequest, AnnotatedAnalysisResponse,
    FetchAnalysisResponse, PaginatedAnalysisResponse,
    SimplifiedAnalysisSummary, DatabaseStatsResponse
)
from config.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])

@router.post("/analyze-base64", response_model=AnnotatedAnalysisResponse)
async def analyze_base64_image(request: Base64AnalysisRequest = Body(...)):
    """
    Analyze a base64-encoded crop image and save to S3 + MongoDB
    
    Accepts JSON with base64-encoded image and returns analysis + annotated image.
    Also saves original image, annotated image to S3 and analysis data to MongoDB.
    
    **Request Body:**
    ```json
    {
        "file": "data:image/jpeg;base64,/9j/4AAQ...",
        "filename": "palm_tree.jpg",
        "lat": "51.5074",
        "long": "-0.1278",
        "uuid": "user-123",
        "crop_type": "oil_palm",
        "use_detection": true,
        "return_annotated_image": true
    }
    ```
    
    **Returns:**
    - Analysis results (bunches, stages, recommendations)
    - Annotated image with bounding boxes (as base64)
    - S3 URLs for original and annotated images
    - MongoDB document ID
    - GPS coordinates and metadata
    """
    try:
        # Generate unique image ID at the start
        image_id = s3_service.generate_image_id()
        logger.info(f"Processing analysis request with image_id={image_id}")
        # Validate crop type
        try:
            crop_type_enum = CropType(request.crop_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid crop type: {request.crop_type}. Supported: {[e.value for e in CropType]}"
            )
        
        # Validate confidence
        if not 0.0 <= request.min_confidence <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="min_confidence must be between 0.0 and 1.0"
            )
        
        # Parse base64 image
        logger.info(f"Received base64 analysis request for {request.crop_type}, file: {request.filename}")
        
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        base64_data = request.file
        if base64_data.startswith('data:'):
            # Extract the actual base64 data after the comma
            match = re.match(r'data:image/[^;]+;base64,(.+)', base64_data)
            if match:
                base64_data = match.group(1)
            else:
                raise HTTPException(status_code=400, detail="Invalid data URI format")
        
        # Decode base64 to bytes
        try:
            file_content = base64.b64decode(base64_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {str(e)}")
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty image data")
        
        # Determine content type from filename
        content_type = "image/jpeg"
        if request.filename.lower().endswith('.png'):
            content_type = "image/png"
        elif request.filename.lower().endswith('.jpg') or request.filename.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        
        logger.info(f"Decoded base64 image: {len(file_content)} bytes, type: {content_type}")
        
        # Perform analysis - use hybrid analyzer if detection is enabled
        if request.use_detection and settings.USE_OBJECT_DETECTION:
            logger.info("Using hybrid analyzer (detection + Claude)")
            result = await hybrid_analyzer.analyze_crop_image(
                file_content=file_content,
                content_type=content_type,
                crop_type=crop_type_enum,
                include_recommendations=request.include_recommendations,
                min_confidence=request.min_confidence
            )
        else:
            logger.info("Using Claude-only analyzer")
            result = await crop_analyzer.analyze_crop_image(
                file_content=file_content,
                content_type=content_type,
                crop_type=crop_type_enum,
                include_recommendations=request.include_recommendations,
                min_confidence=request.min_confidence
            )
        
        # Generate annotated image if requested and analysis succeeded
        annotated_image_base64 = None
        annotated_image_bytes = None
        annotated_format = None
        
        if request.return_annotated_image and result.success and result.analysis:
            try:
                logger.info("Generating annotated image with bounding boxes...")
                
                # Convert AnalysisResponse to dict for annotation
                result_dict = result.dict()
                
                # Annotate and encode
                annotated_image_base64 = image_annotator.annotate_and_encode(
                    image_bytes=file_content,
                    analysis_result=result_dict,
                    output_format='JPEG',
                    quality=90
                )
                annotated_format = 'jpeg'
                
                # Convert base64 back to bytes for S3 upload
                annotated_image_bytes = base64.b64decode(annotated_image_base64)
                
                logger.info(f"Successfully generated annotated image ({len(annotated_image_base64)} chars)")
            except Exception as e:
                logger.error(f"Failed to generate annotated image: {str(e)}")
                # Continue without annotated image rather than failing entire request
        
        # Upload images to S3
        original_image_url = None
        annotated_image_url = None
        database_id = None
        
        try:
            # Upload original image to S3
            logger.info("Uploading original image to S3...")
            original_image_url = s3_service.upload_original_image(
                image_bytes=file_content,
                image_id=image_id,
                filename=request.filename,
                content_type=content_type
            )
            
            # Upload annotated image to S3 if available
            if annotated_image_bytes:
                logger.info("Uploading annotated image to S3...")
                annotated_image_url = s3_service.upload_annotated_image(
                    image_bytes=annotated_image_bytes,
                    image_id=image_id,
                    filename=request.filename,
                    content_type=content_type
                )
            
            # Save analysis to MongoDB
            logger.info("Saving analysis to MongoDB...")
            database_id = await mongodb_service.save_analysis(
                image_id=image_id,
                user_uuid=request.uuid or "anonymous",
                filename=request.filename,
                original_image_url=original_image_url,
                annotated_image_url=annotated_image_url or "",
                analysis_result=result.dict(),
                latitude=request.lat,
                longitude=request.long
            )
            logger.info(f"Successfully saved to database with ID: {database_id}")
            
        except Exception as e:
            logger.error(f"Failed to save to S3/MongoDB: {str(e)}")
            # Continue even if storage fails - user still gets analysis
        
        # Build enhanced response
        response = AnnotatedAnalysisResponse(
            success=result.success,
            crop_type=result.crop_type,
            analysis=result.analysis,
            image_metadata=result.image_metadata,
            processing_time_ms=result.processing_time_ms,
            error=result.error,
            annotated_image=annotated_image_base64,
            annotated_image_format=annotated_format,
            image_id=image_id,
            original_image_url=original_image_url,
            annotated_image_url=annotated_image_url,
            database_id=database_id
        )
        
        logger.info(f"Analysis complete. Success: {response.success}, Bunches: {result.analysis.total_bunches if result.analysis else 0}, Image ID: {image_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in base64 analyze endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AgriAI Analysis API"}

@router.get("/supported-crops")
async def get_supported_crops():
    """Get list of supported crop types"""
    from models.crop_configs import crop_config_manager
    
    crops = crop_config_manager.list_available_crops()
    details = {}
    
    for crop in crops:
        config = crop_config_manager.get_config(crop)
        details[crop] = {
            "name": config.crop_name,
            "scientific_name": config.scientific_name,
            "stages": [stage.name for stage in config.stages],
            "min_confidence": config.min_confidence
        }
    
    return {
        "supported_crops": crops,
        "details": details
    }

# ============================================================================
# DATA RETRIEVAL ENDPOINTS
# ============================================================================

@router.get("/analysis/{image_id}", response_model=FetchAnalysisResponse)
async def get_analysis_by_id(image_id: str):
    """
    Get a specific analysis by image ID
    
    Returns the complete analysis with presigned URLs for image access.
    Presigned URLs are valid for 1 hour by default.
    
    **Path Parameters:**
    - **image_id**: Unique image identifier
    
    **Returns:**
    - Complete analysis data
    - Presigned URLs for original and annotated images
    - Metadata (GPS coordinates, timestamps, etc.)
    """
    try:
        logger.info(f"Fetching analysis for image_id={image_id}")
        
        # Get analysis from MongoDB
        doc = await mongodb_service.get_analysis_by_id(image_id)
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis not found for image_id: {image_id}"
            )
        
        # Generate presigned URLs for images
        original_presigned = s3_service.get_presigned_url(doc['original_image_url'])
        annotated_presigned = s3_service.get_presigned_url(doc['annotated_image_url'])
        
        response = FetchAnalysisResponse(
            id=doc['_id'],
            image_id=doc['image_id'],
            user_uuid=doc['user_uuid'],
            filename=doc['filename'],
            latitude=doc.get('latitude'),
            longitude=doc.get('longitude'),
            analysis=doc['analysis'],
            original_image_presigned_url=original_presigned,
            annotated_image_presigned_url=annotated_presigned,
            created_at=doc['created_at']
        )
        
        logger.info(f"Successfully fetched analysis for image_id={image_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {str(e)}")

@router.get("/analyses/user/{user_uuid}", response_model=PaginatedAnalysisResponse)
async def get_user_analyses(
    user_uuid: str,
    limit: int = 50,
    skip: int = 0
):
    """
    Get all analyses for a specific user
    
    Returns a paginated list of all analyses created by the specified user.
    
    **Path Parameters:**
    - **user_uuid**: User's unique identifier
    
    **Query Parameters:**
    - **limit**: Maximum number of results (default: 50, max: 100)
    - **skip**: Number of results to skip for pagination (default: 0)
    
    **Returns:**
    - Paginated list of analysis summaries
    - Presigned URLs for each image
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        
        logger.info(f"Fetching analyses for user={user_uuid} (limit={limit}, skip={skip})")
        
        # Get user's analyses
        documents = await mongodb_service.get_analyses_by_user(user_uuid, limit, skip)
        
        # Get total count for this user
        total_count = await mongodb_service.count_user_analyses(user_uuid)
        
        # Convert to simplified summaries with presigned URLs
        summaries = []
        for doc in documents:
            original_presigned = s3_service.get_presigned_url(doc['original_image_url'])
            annotated_presigned = s3_service.get_presigned_url(doc['annotated_image_url'])
            
            # Extract crop type and total bunches from analysis
            analysis_data = doc.get('analysis', {})
            crop_type = analysis_data.get('crop_type', 'unknown')
            total_bunches = 0
            if 'analysis' in analysis_data and analysis_data['analysis']:
                total_bunches = analysis_data['analysis'].get('total_bunches', 0)
            
            summaries.append(SimplifiedAnalysisSummary(
                id=doc['_id'],
                image_id=doc['image_id'],
                user_uuid=doc['user_uuid'],
                filename=doc['filename'],
                crop_type=crop_type,
                total_bunches=total_bunches,
                created_at=doc['created_at'],
                original_image_presigned_url=original_presigned,
                annotated_image_presigned_url=annotated_presigned
            ))
        
        response = PaginatedAnalysisResponse(
            success=True,
            total=total_count,
            count=len(summaries),
            limit=limit,
            skip=skip,
            data=summaries
        )
        
        logger.info(f"Returning {len(summaries)} analyses for user={user_uuid}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to fetch user analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analyses: {str(e)}")

@router.get("/analyses/all", response_model=PaginatedAnalysisResponse)
async def get_all_analyses(
    limit: int = 100,
    skip: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """
    Get all analyses from the database (simplified view for UI)
    
    This endpoint returns ALL analyses from all users with a simplified summary.
    Perfect for displaying in a UI dashboard or gallery view.
    
    **Query Parameters:**
    - **limit**: Maximum number of results (default: 100, max: 200)
    - **skip**: Number of results to skip for pagination (default: 0)
    - **sort_by**: Field to sort by (default: "created_at")
    - **sort_order**: Sort order "asc" or "desc" (default: "desc")
    
    **Returns:**
    - Total count of all analyses in database
    - Paginated list of analysis summaries with:
        - Basic metadata (filename, user, timestamps)
        - Analysis summary (crop type, total bunches)
        - Presigned URLs for images (valid for 1 hour)
    
    **Use Cases:**
    - Display gallery of all analyzed images
    - Show recent analyses across all users
    - Export data for reporting
    """
    try:
        # Validate and cap limit
        if limit > 200:
            limit = 200
        
        # Convert sort order to MongoDB format
        sort_order_int = -1 if sort_order.lower() == "desc" else 1
        
        logger.info(f"Fetching all analyses (limit={limit}, skip={skip}, sort={sort_by} {sort_order})")
        
        # Get all analyses with pagination
        documents = await mongodb_service.get_all_analyses(
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_order=sort_order_int
        )
        
        # Get total count
        total_count = await mongodb_service.count_all_analyses()
        
        # Convert to simplified summaries with presigned URLs
        summaries = []
        for doc in documents:
            try:
                original_presigned = s3_service.get_presigned_url(doc['original_image_url'])
                annotated_presigned = s3_service.get_presigned_url(doc['annotated_image_url'])
                
                # Extract crop type and total bunches from nested analysis structure
                analysis_data = doc.get('analysis', {})
                crop_type = analysis_data.get('crop_type', 'unknown')
                total_bunches = 0
                
                # Handle nested structure: analysis.analysis.total_bunches
                if 'analysis' in analysis_data and analysis_data['analysis']:
                    total_bunches = analysis_data['analysis'].get('total_bunches', 0)
                
                summaries.append(SimplifiedAnalysisSummary(
                    id=doc['_id'],
                    image_id=doc['image_id'],
                    user_uuid=doc['user_uuid'],
                    filename=doc['filename'],
                    crop_type=crop_type,
                    total_bunches=total_bunches,
                    created_at=doc['created_at'],
                    original_image_presigned_url=original_presigned,
                    annotated_image_presigned_url=annotated_presigned
                ))
            except Exception as e:
                logger.warning(f"Skipping document {doc.get('_id')} due to error: {str(e)}")
                continue
        
        response = PaginatedAnalysisResponse(
            success=True,
            total=total_count,
            count=len(summaries),
            limit=limit,
            skip=skip,
            data=summaries
        )
        
        logger.info(f"Returning {len(summaries)} analyses out of {total_count} total")
        return response
        
    except Exception as e:
        logger.error(f"Failed to fetch all analyses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch analyses: {str(e)}")

@router.get("/statistics", response_model=DatabaseStatsResponse)
async def get_database_statistics():
    """
    Get database and storage statistics
    
    Returns comprehensive statistics about:
    - Total number of analyses
    - Number of unique users
    - Distribution by crop type
    - Total images in S3 storage
    
    **Returns:**
    - Database statistics
    - S3 storage statistics
    - Distribution metrics
    """
    try:
        logger.info("Fetching database statistics")
        
        # Get MongoDB statistics
        stats = await mongodb_service.get_statistics()
        
        # Count S3 images
        original_images = s3_service.list_images_by_prefix(settings.S3_ORIGINAL_PREFIX)
        annotated_images = s3_service.list_images_by_prefix(settings.S3_ANNOTATED_PREFIX)
        
        response = DatabaseStatsResponse(
            success=True,
            total_analyses=stats['total_analyses'],
            unique_users=stats['unique_users'],
            crop_distribution=stats['crop_distribution'],
            total_original_images=len(original_images),
            total_annotated_images=len(annotated_images)
        )
        
        logger.info(f"Statistics: {stats['total_analyses']} analyses, {stats['unique_users']} users")
        return response
        
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")
