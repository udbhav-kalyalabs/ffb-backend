"""
Hybrid analyzer combining object detection (precise boxes) with Claude (intelligent analysis)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.object_detector import create_detector, Detection
from services.bedrock_service import bedrock_service
from services.image_processor import image_processor
from prompts.oil_palm_prompts import build_system_prompt
from models.schemas import (
    CropAnalysis, FruitBunch, BoundingBox, StageSummary, PlantHealth,
    ImageMetadata, AnalysisResponse, CropType, FruitStage
)
from models.crop_configs import crop_config_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class HybridAnalyzer:
    """
    Combines object detection for precise bounding boxes with Claude for intelligent analysis
    """
    
    @staticmethod
    def _map_roboflow_class_to_stage(class_name: str) -> str:
        """
        Map Roboflow class names to ripeness stages
        
        Args:
            class_name: Class name from Roboflow (e.g., "Black FFB", "Red FFB")
            
        Returns:
            Ripeness stage string
        """
        class_name_lower = class_name.lower()
        
        # Mapping based on FFB color/class
        if "black" in class_name_lower or "dark" in class_name_lower:
            return "ripe"
        elif "red" in class_name_lower or "orange" in class_name_lower:
            return "overripe"
        elif "yellow" in class_name_lower or "mature" in class_name_lower:
            return "mature"
        elif "green" in class_name_lower or "young" in class_name_lower or "unripe" in class_name_lower:
            return "young"
        else:
            # Default to ripe if unknown
            logger.warning(f"Unknown Roboflow class: {class_name}, defaulting to 'ripe'")
            return "ripe"
    
    def __init__(self):
        """Initialize hybrid analyzer"""
        self.detector = None
        if settings.USE_OBJECT_DETECTION:
            try:
                detector_config = {
                    "yolo": {
                        "model_path": settings.YOLO_MODEL_PATH,
                        "use_api": settings.YOLO_USE_API,
                        "api_key": settings.YOLO_API_KEY
                    },
                    "roboflow": {
                        "api_key": settings.ROBOFLOW_API_KEY,
                        "model_id": settings.ROBOFLOW_MODEL_ID,
                        "version": settings.ROBOFLOW_VERSION
                    },
                    "custom": {
                        "endpoint_url": settings.CUSTOM_DETECTION_URL,
                        "api_key": settings.CUSTOM_DETECTION_API_KEY
                    },
                    "mock": {}
                }
                
                config = detector_config.get(settings.DETECTION_BACKEND, {})
                self.detector = create_detector(settings.DETECTION_BACKEND, **config)
                logger.info(f"Initialized {settings.DETECTION_BACKEND} object detector")
            except Exception as e:
                logger.warning(f"Failed to initialize object detector: {e}. Will use Claude-only mode.")
                self.detector = None
    
    def _build_analysis_prompt_for_detections(self, detections: List[Detection], 
                                             image_width: int, image_height: int) -> str:
        """
        Build a prompt that asks Claude to analyze pre-detected bunches
        """
        prompt = f"""You are an expert agricultural AI analyzing oil palm fruit bunches.

IMAGE SPECIFICATIONS:
- Dimensions: {image_width} x {image_height} pixels
- A detection model has already identified {len(detections)} potential fruit bunches

DETECTED BUNCHES (with precise locations):
"""
        
        for i, det in enumerate(detections, 1):
            bbox = det.bbox
            if len(bbox) == 4:
                if bbox[2] < bbox[0]:  # If width/height format [center_x, center_y, w, h]
                    center_x, center_y, w, h = bbox
                    x_min = int(center_x - w/2)
                    y_min = int(center_y - h/2)
                    x_max = int(center_x + w/2)
                    y_max = int(center_y + h/2)
                else:  # Corner format [x_min, y_min, x_max, y_max]
                    x_min, y_min, x_max, y_max = [int(v) for v in bbox]
                
                prompt += f"""
Bunch #{i}:
- Bounding box: [{x_min}, {y_min}, {x_max}, {y_max}]
- Detection confidence: {det.confidence:.2f}
- Location: Region from pixel ({x_min}, {y_min}) to ({x_max}, {y_max})
"""
        
        prompt += """

YOUR TASK:
For EACH detected bunch above, analyze and classify:

1. **Ripeness Stage**: Determine if it's young, mature, ripe, or overripe based on:
   - Color (green → yellow → orange → red/dark red)
   - Fruit looseness and development
   - Visual maturity indicators

2. **Confidence**: How confident are you in the ripeness classification (0.0-1.0)

3. **Visibility**: Is it fully_visible, partially_visible, or behind_fronds?

4. **Size**: Relative size assessment (small, medium, large)

5. **Position**: Relative position on tree (front, middle, back, left, right, center)

6. **Description**: 2-3 sentences describing the bunch's characteristics and harvest readiness

ALSO PROVIDE:
- Overall plant health assessment (score 0-100)
- Frond condition
- Bunch development quality
- Any concerns or observations
- Harvest recommendations

OUTPUT FORMAT:
Return ONLY valid JSON in this format:

{
  "total_bunches": """ + str(len(detections)) + """,
  "detection_confidence": 0.85,
  "bunches": [
    {
      "id": 1,
      "stage": "ripe",
      "confidence": 0.92,
      "visibility": "fully_visible",
      "size": "large",
      "position": "front-center",
      "description": "Large ripe bunch with deep orange-red coloration..."
    }
  ],
  "plant_health": {
    "overall_score": 85.0,
    "frond_condition": "good",
    "bunch_development": "excellent",
    "observations": ["..."],
    "concerns": ["..."]
  },
  "recommendations": ["..."]
}

IMPORTANT:
- Analyze the ACTUAL visual appearance of each bunch in the provided bounding box
- DO NOT create additional bunches beyond those detected
- DO NOT change the bounding box coordinates
- Focus on accurate ripeness classification and health assessment

BEGIN YOUR ANALYSIS NOW:"""
        
        return prompt
    
    async def analyze_crop_image(
        self,
        file_content: bytes,
        content_type: str,
        crop_type: CropType = CropType.OIL_PALM,
        include_recommendations: bool = True,
        min_confidence: float = 0.5
    ) -> AnalysisResponse:
        """
        Hybrid analysis: Detection model for boxes, Claude for classification
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Get original image dimensions (before resizing)
            from PIL import Image
            import io
            original_image = Image.open(io.BytesIO(file_content))
            original_width, original_height = original_image.size
            logger.info(f"Original image dimensions: {original_width}x{original_height}")
            
            # Step 2: Process image for Claude (may resize)
            logger.info(f"Processing image for crop type: {crop_type}")
            base64_image, processed_width, processed_height, file_size_kb = image_processor.process_uploaded_image(
                file_content, content_type
            )
            logger.info(f"Processed image dimensions: {processed_width}x{processed_height}")
            
            # Step 3: Run object detection if available (uses ORIGINAL image)
            detections = []
            if self.detector and settings.USE_OBJECT_DETECTION:
                logger.info("Running object detection for precise bounding boxes...")
                try:
                    detections = self.detector.detect(file_content, settings.DETECTION_CONFIDENCE)
                    logger.info(f"Object detection found {len(detections)} potential bunches")
                    logger.info("Note: Detection coordinates are for the ORIGINAL image dimensions")
                except Exception as det_err:
                    logger.warning(f"Object detection failed ({det_err}); falling back to Claude-only mode")
                    detections = []
            
            if not detections:
                # Fallback to Claude-only analysis
                logger.warning("No detections from object detector, falling back to Claude-only mode")
                from services.crop_analyzer import crop_analyzer
                return await crop_analyzer.analyze_crop_image(
                    file_content, content_type, crop_type, include_recommendations, min_confidence
                )
            
            # Step 3: Build prompt for Claude to analyze detected bunches
            system_prompt = build_system_prompt()
            analysis_prompt = self._build_analysis_prompt_for_detections(detections, processed_width, processed_height)
            
            # Step 4: Get Claude's analysis
            logger.info("Requesting Claude analysis of detected bunches...")
            ai_response = bedrock_service.analyze_image(
                prompt=analysis_prompt,
                image_base64=base64_image,
                system_prompt=system_prompt
            )
            
            logger.info(f"Received AI analysis (length: {len(ai_response)} chars)")
            
            # Step 5: Parse Claude's response and combine with detection boxes
            import json
            
            # Extract JSON
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}')
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[start_idx:end_idx + 1]
            data = json.loads(json_str)
            
            # Step 6: Build bunches with detection boxes + Claude analysis
            bunches = []
            bunch_analyses = data.get("bunches", [])
            
            for idx, (det, analysis) in enumerate(zip(detections, bunch_analyses)):
                # Use detection model's precise bounding box
                bbox_coords = det.bbox
                if len(bbox_coords) == 4:
                    if bbox_coords[2] < bbox_coords[0]:  # width/height format
                        center_x, center_y, w, h = bbox_coords
                        x_min = int(center_x - w/2)
                        y_min = int(center_y - h/2)
                        x_max = int(center_x + w/2)
                        y_max = int(center_y + h/2)
                    else:  # corner format
                        x_min, y_min, x_max, y_max = [int(v) for v in bbox_coords]
                    
                    # Include segmentation data if available
                    bbox = BoundingBox.from_coordinates(
                        x_min, y_min, x_max, y_max,
                        segmentation=det.segmentation,
                        area=det.area
                    )
                    
                    # Prioritize Roboflow class mapping (more accurate for color-based ripeness)
                    # Then fall back to Claude's analysis
                    roboflow_class = det.class_name
                    stage_str = None
                    
                    if roboflow_class:
                        # Use Roboflow class mapping as primary source
                        stage_str = self._map_roboflow_class_to_stage(roboflow_class)
                        logger.info(f"Bunch #{idx+1}: Roboflow class '{roboflow_class}' → stage '{stage_str}'")
                    else:
                        # Fall back to Claude's classification
                        stage_str = analysis.get("stage", "young").lower()
                        logger.info(f"Bunch #{idx+1}: Using Claude's classification → stage '{stage_str}'")
                    
                    try:
                        stage = FruitStage(stage_str)
                    except ValueError:
                        logger.warning(f"Invalid stage '{stage_str}', defaulting to 'young'")
                        stage = FruitStage.YOUNG
                    
                    color_code = crop_config_manager.get_stage_color(crop_type.value, stage.value)
                    
                    bunch = FruitBunch(
                        id=analysis.get("id", idx + 1),
                        stage=stage,
                        confidence=analysis.get("confidence", det.confidence),
                        bounding_box=bbox,
                        color_code=color_code,
                        visibility=analysis.get("visibility"),
                        size=analysis.get("size"),
                        position=analysis.get("position"),
                        description=analysis.get("description", "")
                    )
                    bunches.append(bunch)
                    
                    logger.info(f"Bunch #{idx+1}: {stage.value} at [{x_min},{y_min},{x_max},{y_max}] (detection_conf: {det.confidence:.2f}, class_conf: {bunch.confidence:.2f})")
            
            # Step 7: Calculate stage summary
            stage_summary = StageSummary(young=0, mature=0, ripe=0, overripe=0)
            for bunch in bunches:
                if bunch.stage == FruitStage.YOUNG:
                    stage_summary.young += 1
                elif bunch.stage == FruitStage.MATURE:
                    stage_summary.mature += 1
                elif bunch.stage == FruitStage.RIPE:
                    stage_summary.ripe += 1
                elif bunch.stage == FruitStage.OVERRIPE:
                    stage_summary.overripe += 1
            
            # Step 8: Parse plant health
            plant_health = None
            if "plant_health" in data:
                ph_data = data["plant_health"]
                plant_health = PlantHealth(
                    overall_score=ph_data.get("overall_score", 75.0),
                    frond_condition=ph_data.get("frond_condition"),
                    bunch_development=ph_data.get("bunch_development"),
                    observations=ph_data.get("observations", []),
                    concerns=ph_data.get("concerns", [])
                )
            
            # Step 9: Create analysis result
            analysis = CropAnalysis(
                total_bunches=len(bunches),
                detection_confidence=data.get("detection_confidence"),
                bunches=bunches,
                stage_summary=stage_summary,
                plant_health=plant_health,
                recommendations=data.get("recommendations", [])
            )
            
            # Step 10: Create metadata
            # Use ORIGINAL dimensions since Roboflow coordinates are for original image
            image_metadata = ImageMetadata(
                width=original_width if detections else processed_width,
                height=original_height if detections else processed_height,
                analyzed_at=datetime.now().isoformat(),
                file_size_kb=file_size_kb
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response = AnalysisResponse(
                success=True,
                crop_type=crop_type,
                analysis=analysis,
                image_metadata=image_metadata,
                processing_time_ms=processing_time,
                error=None
            )
            
            logger.info(f"Hybrid analysis completed in {processing_time:.0f}ms")
            logger.info(f"Found {len(bunches)} bunches with precise locations: {stage_summary.dict()}")
            
            return response
            
        except Exception as e:
            logger.error(f"Hybrid analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            try:
                _, width, height, file_size_kb = image_processor.process_uploaded_image(
                    file_content, content_type
                )
                image_metadata = ImageMetadata(
                    width=width,
                    height=height,
                    analyzed_at=datetime.now().isoformat(),
                    file_size_kb=file_size_kb
                )
            except:
                image_metadata = ImageMetadata(
                    width=0,
                    height=0,
                    analyzed_at=datetime.now().isoformat(),
                    file_size_kb=None
                )
            
            return AnalysisResponse(
                success=False,
                crop_type=crop_type,
                analysis=None,
                image_metadata=image_metadata,
                processing_time_ms=processing_time,
                error=str(e)
            )


# Global instance
hybrid_analyzer = HybridAnalyzer()
