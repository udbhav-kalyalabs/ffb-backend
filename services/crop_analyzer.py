"""
Main crop analysis service that orchestrates the analysis pipeline
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from services.bedrock_service import bedrock_service
from services.image_processor import image_processor
from prompts.oil_palm_prompts import build_oil_palm_analysis_prompt, build_system_prompt
from models.schemas import (
    CropAnalysis, FruitBunch, BoundingBox, StageSummary, PlantHealth,
    ImageMetadata, AnalysisResponse, CropType, FruitStage
)
from models.crop_configs import crop_config_manager

logger = logging.getLogger(__name__)

class CropAnalyzer:
    """Main service for analyzing crop images"""
    
    @staticmethod
    def parse_ai_response(response_text: str, crop_type: str, image_width: int = 1800, image_height: int = 2400) -> CropAnalysis:
        """
        Parse AI model's JSON response into structured format
        
        Args:
            response_text: Raw text response from AI model
            crop_type: Type of crop analyzed
        
        Returns:
            CropAnalysis object
        """
        try:
            # Extract JSON from response (in case there's extra text)
            # Find the first { and last }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx + 1]
            data = json.loads(json_str)
            
            # Parse bunches
            bunches = []
            for idx, bunch_data in enumerate(data.get("bunches", [])):
                bbox_data = bunch_data.get("bounding_box", {})
                
                # Check which format we received
                if 'center_x' in bbox_data and 'width' in bbox_data:
                    # New normalized center+size format
                    center_x = bbox_data.get("center_x", 0.5)
                    center_y = bbox_data.get("center_y", 0.5)
                    width = bbox_data.get("width", 0.2)
                    height = bbox_data.get("height", 0.15)
                    
                    # Create bounding box from center+size
                    bbox = BoundingBox.from_center_size_normalized(
                        center_x=center_x,
                        center_y=center_y,
                        width=width,
                        height=height,
                        image_width=image_width,
                        image_height=image_height
                    )
                    logger.info(f"Bunch #{idx+1}: Converted normalized coords (center: {center_x:.2f}, {center_y:.2f}) to pixels ({bbox.x_min}, {bbox.y_min}, {bbox.x_max}, {bbox.y_max})")
                else:
                    # Old corner format (fallback)
                    bbox = BoundingBox.from_coordinates(
                        x_min=bbox_data.get("x_min", 0),
                        y_min=bbox_data.get("y_min", 0),
                        x_max=bbox_data.get("x_max", 0),
                        y_max=bbox_data.get("y_max", 0)
                    )
                    logger.info(f"Bunch #{idx+1}: Using corner format ({bbox.x_min}, {bbox.y_min}, {bbox.x_max}, {bbox.y_max})")
                
                # Get stage and color
                stage_str = bunch_data.get("stage", "young").lower()
                try:
                    stage = FruitStage(stage_str)
                except ValueError:
                    logger.warning(f"Invalid stage '{stage_str}', defaulting to 'young'")
                    stage = FruitStage.YOUNG
                
                color_code = crop_config_manager.get_stage_color(crop_type, stage.value)
                
                bunch = FruitBunch(
                    id=bunch_data.get("id", idx + 1),
                    stage=stage,
                    confidence=bunch_data.get("confidence", 0.8),
                    bounding_box=bbox,
                    color_code=color_code,
                    visibility=bunch_data.get("visibility"),
                    size=bunch_data.get("size"),
                    position=bunch_data.get("position"),
                    description=bunch_data.get("description", "")
                )
                bunches.append(bunch)
            
            # Calculate stage summary
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
            
            # Parse plant health if available
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
            
            # Create analysis result
            analysis = CropAnalysis(
                total_bunches=data.get("total_bunches", len(bunches)),
                detection_confidence=data.get("detection_confidence"),
                bunches=bunches,
                stage_summary=stage_summary,
                plant_health=plant_health,
                recommendations=data.get("recommendations", [])
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from AI model: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            raise
    
    @staticmethod
    async def analyze_crop_image(
        file_content: bytes,
        content_type: str,
        crop_type: CropType = CropType.OIL_PALM,
        include_recommendations: bool = True,
        min_confidence: float = 0.5
    ) -> AnalysisResponse:
        """
        Main method to analyze a crop image
        
        Args:
            file_content: Raw image bytes
            content_type: MIME type of image
            crop_type: Type of crop to analyze
            include_recommendations: Whether to include recommendations
            min_confidence: Minimum confidence threshold
        
        Returns:
            AnalysisResponse with analysis results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Process image
            logger.info(f"Processing image for crop type: {crop_type}")
            base64_image, width, height, file_size_kb = image_processor.process_uploaded_image(
                file_content, content_type
            )
            
            # Step 2: Build prompt
            if crop_type == CropType.OIL_PALM:
                prompt = build_oil_palm_analysis_prompt(width, height)
            else:
                raise ValueError(f"Unsupported crop type: {crop_type}")
            
            system_prompt = build_system_prompt()
            
            # Step 3: Call AI model
            logger.info("Invoking AI model for analysis")
            ai_response = bedrock_service.analyze_image(
                prompt=prompt,
                image_base64=base64_image,
                system_prompt=system_prompt
            )
            
            logger.info(f"Received AI response (length: {len(ai_response)} chars)")
            
            # Step 4: Parse response
            analysis = CropAnalyzer.parse_ai_response(ai_response, crop_type.value, width, height)
            
            # Filter by confidence if needed
            if min_confidence > 0:
                original_count = len(analysis.bunches)
                analysis.bunches = [b for b in analysis.bunches if b.confidence >= min_confidence]
                analysis.total_bunches = len(analysis.bunches)
                
                if len(analysis.bunches) < original_count:
                    logger.info(f"Filtered {original_count - len(analysis.bunches)} bunches below confidence threshold")
                    
                    # Recalculate stage summary
                    stage_summary = StageSummary(young=0, mature=0, ripe=0, overripe=0)
                    for bunch in analysis.bunches:
                        if bunch.stage == FruitStage.YOUNG:
                            stage_summary.young += 1
                        elif bunch.stage == FruitStage.MATURE:
                            stage_summary.mature += 1
                        elif bunch.stage == FruitStage.RIPE:
                            stage_summary.ripe += 1
                        elif bunch.stage == FruitStage.OVERRIPE:
                            stage_summary.overripe += 1
                    analysis.stage_summary = stage_summary
            
            # Step 5: Create metadata
            image_metadata = ImageMetadata(
                width=width,
                height=height,
                analyzed_at=datetime.now().isoformat(),
                file_size_kb=file_size_kb
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Step 6: Build response
            response = AnalysisResponse(
                success=True,
                crop_type=crop_type,
                analysis=analysis,
                image_metadata=image_metadata,
                processing_time_ms=processing_time,
                error=None
            )
            
            logger.info(f"Analysis completed successfully in {processing_time:.0f}ms")
            logger.info(f"Found {analysis.total_bunches} bunches: {analysis.stage_summary.dict()}")
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            
            # Return error response
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Try to get image dimensions even if analysis failed
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
crop_analyzer = CropAnalyzer()
