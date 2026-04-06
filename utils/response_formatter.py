"""
Response formatting utilities
"""
from typing import Dict, Any
from models.schemas import AnalysisResponse

def format_analysis_for_frontend(response: AnalysisResponse) -> Dict[str, Any]:
    """
    Format analysis response in a frontend-friendly format
    
    Args:
        response: AnalysisResponse object
    
    Returns:
        Dictionary with formatted data
    """
    if not response.success or not response.analysis:
        return {
            "success": False,
            "error": response.error,
            "processing_time_ms": response.processing_time_ms
        }
    
    analysis = response.analysis
    
    # Format bunches for easy rendering
    formatted_bunches = []
    for bunch in analysis.bunches:
        formatted_bunches.append({
            "id": bunch.id,
            "stage": bunch.stage.value,
            "confidence": round(bunch.confidence, 2),
            "box": {
                "x": bunch.bounding_box.x_min,
                "y": bunch.bounding_box.y_min,
                "width": bunch.bounding_box.x_max - bunch.bounding_box.x_min,
                "height": bunch.bounding_box.y_max - bunch.bounding_box.y_min,
                "centerX": bunch.bounding_box.center_x,
                "centerY": bunch.bounding_box.center_y
            },
            "color": bunch.color_code,
            "description": bunch.description
        })
    
    return {
        "success": True,
        "cropType": response.crop_type.value,
        "totalBunches": analysis.total_bunches,
        "bunches": formatted_bunches,
        "summary": {
            "young": analysis.stage_summary.young,
            "mature": analysis.stage_summary.mature,
            "ripe": analysis.stage_summary.ripe,
            "overripe": analysis.stage_summary.overripe
        },
        "healthScore": analysis.plant_health.overall_score if analysis.plant_health else None,
        "plantHealth": {
            "overallScore": analysis.plant_health.overall_score if analysis.plant_health else None,
            "frondCondition": analysis.plant_health.frond_condition if analysis.plant_health else None,
            "bunchDevelopment": analysis.plant_health.bunch_development if analysis.plant_health else None,
            "observations": analysis.plant_health.observations if analysis.plant_health else [],
            "concerns": analysis.plant_health.concerns if analysis.plant_health else []
        } if analysis.plant_health else None,
        "recommendations": analysis.recommendations or [],
        "imageInfo": {
            "width": response.image_metadata.width,
            "height": response.image_metadata.height,
            "analyzedAt": response.image_metadata.analyzed_at,
            "fileSizeKB": response.image_metadata.file_size_kb
        },
        "processingTimeMs": round(response.processing_time_ms or 0, 2)
    }
