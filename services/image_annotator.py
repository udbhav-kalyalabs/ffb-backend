"""
Image annotation service for drawing bounding boxes on detection results
"""
import cv2
import numpy as np
import base64
import io
from typing import Dict, Any, Tuple
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class ImageAnnotator:
    """Service for annotating images with detection results"""
    
    @staticmethod
    def hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to BGR for OpenCV"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (rgb[2], rgb[1], rgb[0])  # BGR format
    
    @staticmethod
    def draw_bounding_boxes(
        image_bytes: bytes,
        analysis_result: Dict[str, Any]
    ) -> np.ndarray:
        """
        Draw bounding boxes on image based on analysis results
        
        Args:
            image_bytes: Raw image bytes
            analysis_result: Analysis result dict with bunches
        
        Returns:
            Annotated image as numpy array
        """
        # Decode image with EXIF orientation handling (matches test script behavior)
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            try:
                from PIL import ImageOps
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception:
                pass
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception:
            # Fallback to raw decode
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")
        
        original_height, original_width = img.shape[:2]
        
        # Get analysis data
        if not analysis_result.get('success') or not analysis_result.get('analysis'):
            logger.warning("No analysis data available for annotation")
            return img
        
        analysis = analysis_result['analysis']
        bunches = analysis.get('bunches', [])
        
        logger.info(f"Drawing {len(bunches)} bounding boxes on {original_width}x{original_height} image")
        
        # Calculate scale factor if image sizes differ
        analyzed_width = analysis_result['image_metadata']['width']
        analyzed_height = analysis_result['image_metadata']['height']
        scale_x = original_width / analyzed_width
        scale_y = original_height / analyzed_height
        
        logger.info(f"Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
        
        # Draw each bunch
        for bunch in bunches:
            # Get coordinates and scale them
            bbox = bunch['bounding_box']
            x_min = int(bbox['x_min'] * scale_x)
            y_min = int(bbox['y_min'] * scale_y)
            x_max = int(bbox['x_max'] * scale_x)
            y_max = int(bbox['y_max'] * scale_y)
            
            # Get color
            color_bgr = ImageAnnotator.hex_to_bgr(bunch['color_code'])
            
            # Draw segmentation mask if available
            if bbox.get('segmentation'):
                try:
                    points = np.array(bbox['segmentation'], dtype=np.int32)
                    # Scale points
                    points[:, 0] = (points[:, 0] * scale_x).astype(np.int32)
                    points[:, 1] = (points[:, 1] * scale_y).astype(np.int32)
                    
                    # Draw filled polygon with transparency
                    overlay = img.copy()
                    cv2.fillPoly(overlay, [points], color_bgr)
                    cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
                    
                    # Draw contour
                    cv2.polylines(img, [points], True, color_bgr, 2)
                    logger.debug(f"Drew segmentation mask for bunch #{bunch['id']}")
                except Exception as e:
                    logger.warning(f"Could not draw segmentation for bunch #{bunch['id']}: {e}")
            
            # Draw rectangle (bounding box)
            thickness = max(2, int(min(original_width, original_height) / 400))
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color_bgr, thickness)
            
            # Prepare label
            stage = bunch['stage'].upper()
            confidence = bunch['confidence']
            visibility = bunch.get('visibility', 'unknown')
            label = f"#{bunch['id']}: {stage} ({confidence:.0%})"
            
            # Add visibility indicator
            if visibility == 'partially_visible':
                label += " [PARTIAL]"
            elif visibility == 'behind_fronds':
                label += " [HIDDEN]"
            
            # Calculate label size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.5, min(original_width, original_height) / 2000)
            font_thickness = max(1, int(font_scale * 2))
            (label_width, label_height), baseline = cv2.getTextSize(
                label, font, font_scale, font_thickness
            )
            
            # Draw label background
            label_y = max(y_min - 10, label_height + 10)
            cv2.rectangle(
                img,
                (x_min, label_y - label_height - baseline - 5),
                (x_min + label_width + 10, label_y + baseline),
                color_bgr,
                -1
            )
            
            # Draw label text
            cv2.putText(
                img, label,
                (x_min + 5, label_y - baseline),
                font, font_scale, (255, 255, 255), font_thickness
            )
            
            # Draw center point
            center_x = int(bbox['center_x'] * scale_x)
            center_y = int(bbox['center_y'] * scale_y)
            cv2.circle(img, (center_x, center_y), 5, color_bgr, -1)
            cv2.circle(img, (center_x, center_y), 5, (255, 255, 255), 1)
            
            logger.debug(f"Bunch #{bunch['id']}: {stage} at [{x_min}, {y_min}, {x_max}, {y_max}]")
        
        # Add summary overlay
        summary_y = 30
        summary_font_scale = max(0.6, min(original_width, original_height) / 1500)
        summary_thickness = max(1, int(summary_font_scale * 2))
        
        # Calculate summary box size
        summary_lines = [
            f"Total Bunches: {analysis['total_bunches']}",
            f"Confidence: {analysis.get('detection_confidence', 0):.0%}",
            f"Ripe: {analysis['stage_summary']['ripe']}, Mature: {analysis['stage_summary']['mature']}",
            f"Young: {analysis['stage_summary']['young']}, Overripe: {analysis['stage_summary']['overripe']}"
        ]
        
        max_text_width = 0
        for line in summary_lines:
            (text_width, _), _ = cv2.getTextSize(line, font, summary_font_scale, summary_thickness)
            max_text_width = max(max_text_width, text_width)
        
        box_width = max_text_width + 20
        box_height = len(summary_lines) * 25 + 20
        
        # Background for summary
        cv2.rectangle(img, (10, 10), (10 + box_width, 10 + box_height), (0, 0, 0), -1)
        cv2.rectangle(img, (10, 10), (10 + box_width, 10 + box_height), (255, 255, 255), 2)
        
        # Summary text
        for i, line in enumerate(summary_lines):
            cv2.putText(
                img, line,
                (20, summary_y + i * 25),
                font, summary_font_scale, (255, 255, 255), summary_thickness
            )
        
        logger.info(f"Successfully annotated image with {len(bunches)} detections")
        return img
    
    @staticmethod
    def annotate_and_encode(
        image_bytes: bytes,
        analysis_result: Dict[str, Any],
        output_format: str = 'JPEG',
        quality: int = 90
    ) -> str:
        """
        Annotate image and return as base64 string
        
        Args:
            image_bytes: Raw image bytes
            analysis_result: Analysis result dict
            output_format: Output format (JPEG or PNG)
            quality: JPEG quality (1-100)
        
        Returns:
            Base64 encoded annotated image
        """
        try:
            # Draw bounding boxes
            annotated_img = ImageAnnotator.draw_bounding_boxes(image_bytes, analysis_result)
            
            # Convert to PIL Image for encoding
            img_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # Encode to base64
            buffer = io.BytesIO()
            if output_format.upper() == 'JPEG':
                pil_img.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                pil_img.save(buffer, format='PNG', optimize=True)
            
            buffer.seek(0)
            image_bytes = buffer.read()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info(f"Encoded annotated image: {len(image_bytes)/1024:.2f}KB as base64")
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Error annotating image: {str(e)}")
            raise


# Global instance
image_annotator = ImageAnnotator()

