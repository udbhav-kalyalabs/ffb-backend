"""
Test script for analyzing sample oil palm images
"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import os

from services.crop_analyzer import crop_analyzer
from services.hybrid_analyzer import hybrid_analyzer
from models.schemas import CropType
from config.settings import settings
import logging

# Import visualization if available
try:
    import cv2
    import numpy as np
    from PIL import Image
    import io
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Check if JSON output mode is requested
JSON_OUTPUT = '--json' in sys.argv or '-j' in sys.argv
VISUALIZE = '--viz' in sys.argv or '-v' in sys.argv

# Configure logging - suppress if JSON mode
if JSON_OUTPUT and not VISUALIZE:
    logging.basicConfig(level=logging.ERROR)
else:
    logging.basicConfig(level=logging.INFO)
    
logger = logging.getLogger(__name__)

def hex_to_bgr(hex_color):
    """Convert hex color to BGR for OpenCV"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])

def visualize_on_processed_image(analysis_result: dict):
    """
    Draw bounding boxes on the processed image (1800x2400) that the AI analyzed.
    This helps verify if the AI coordinates are correct before scaling.
    """
    try:
        # Try to load the debug processed image
        debug_img_path = "debug_processed_image.jpg"
        if not os.path.exists(debug_img_path):
            logger.warning(f"Debug processed image not found at {debug_img_path}")
            return
        
        img = cv2.imread(debug_img_path)
        if img is None:
            logger.warning("Could not load debug processed image")
            return
        
        height, width = img.shape[:2]
        logger.info(f"\n=== DEBUGGING: Drawing on processed image ({width}x{height}) ===")
        
        analysis = analysis_result.get('analysis', {})
        bunches = analysis.get('bunches', [])
        
        # Draw boxes using raw coordinates (no scaling)
        for bunch in bunches:
            bbox = bunch['bounding_box']
            x_min = int(bbox['x_min'])
            y_min = int(bbox['y_min'])
            x_max = int(bbox['x_max'])
            y_max = int(bbox['y_max'])
            
            color_bgr = hex_to_bgr(bunch['color_code'])
            
            # Draw rectangle
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color_bgr, 3)
            
            # Draw label
            label = f"#{bunch['id']}: {bunch['stage'].upper()}"
            cv2.putText(img, label, (x_min, y_min - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2)
        
        # Save
        output_path = "debug_annotated_processed.jpg"
        cv2.imwrite(output_path, img)
        logger.info(f"Saved annotated processed image to {output_path}")
        logger.info("Check this image to see if AI coordinates are correct on the processed 1800x2400 image")
        logger.info("If boxes are correct here but wrong on original, it's a scaling issue.")
        logger.info("If boxes are wrong here too, the AI is giving incorrect coordinates.\n")
        
    except Exception as e:
        logger.error(f"Error visualizing on processed image: {e}")

def process_image_like_analyzer(image_path: str):
    """
    Process image exactly like the image processor does:
    1. Open with PIL
    2. Apply EXIF orientation
    3. Convert to RGB
    4. Resize if needed (same logic as image processor)
    
    Returns: (PIL Image, width, height)
    """
    from PIL import ImageOps
    from config.settings import settings
    
    # Read image
    image = Image.open(image_path)
    
    # Apply EXIF orientation (same as image processor)
    try:
        image = ImageOps.exif_transpose(image)
        logger.debug("Applied EXIF orientation correction")
    except Exception as e:
        logger.debug(f"EXIF orientation handling: {e}")
    
    # Convert to RGB (same as image processor)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if needed (same logic as image processor)
    width, height = image.size
    max_dim = settings.MAX_IMAGE_DIMENSION
    
    if width > max_dim or height > max_dim:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dim
            new_height = int((max_dim / width) * height)
        else:
            new_height = max_dim
            new_width = int((max_dim / height) * width)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = new_width, new_height
        logger.info(f"Image resized to {width}x{height} for processing")
    
    return image, width, height

def visualize_result(image_path: str, analysis_result: dict):
    """Draw bounding boxes and display image"""
    if not VISUALIZATION_AVAILABLE:
        logger.warning("OpenCV not available. Install with: pip install opencv-python")
        return
    
    # Read original image with EXIF correction (same as image processor does initially)
    try:
        from PIL import ImageOps
        original_pil_image = Image.open(image_path)
        original_size_before_exif = original_pil_image.size
        
        # Apply EXIF orientation transformation (same as image processor)
        original_pil_image = ImageOps.exif_transpose(original_pil_image)
        original_size_after_exif = original_pil_image.size
        
        if original_size_before_exif != original_size_after_exif:
            logger.info(f"EXIF orientation changed image size from {original_size_before_exif} to {original_size_after_exif}")
        else:
            logger.info("Applied EXIF orientation correction (no size change)")
        
        # Convert to RGB (same as image processor)
        if original_pil_image.mode != 'RGB':
            original_pil_image = original_pil_image.convert('RGB')
        
        # Convert to OpenCV format (BGR) - we'll draw on the original full-resolution image
        img_array = np.array(original_pil_image)
        img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        display_height, display_width = img.shape[:2]
        logger.info(f"Original image loaded with dimensions: {display_width}x{display_height} (after EXIF correction)")
        
    except Exception as e:
        logger.warning(f"Failed to read image with PIL, falling back to OpenCV: {e}")
        # Fallback
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return
        display_height, display_width = img.shape[:2]
    
    original_height, original_width = display_height, display_width
    
    if not analysis_result.get('success') or not analysis_result.get('analysis'):
        logger.warning("No analysis data to visualize")
        return
    
    analysis = analysis_result['analysis']
    bunches = analysis.get('bunches', [])
    
    # Calculate scale factor from analyzed image size to original image size
    analyzed_width = analysis_result['image_metadata']['width']
    analyzed_height = analysis_result['image_metadata']['height']
    scale_x = display_width / analyzed_width
    scale_y = display_height / analyzed_height
    
    logger.info(f"\nVisualizing {len(bunches)} detections...")
    logger.info(f"Original image size: {display_width}x{display_height}")
    logger.info(f"Analyzed image size: {analyzed_width}x{analyzed_height}")
    logger.info(f"Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
    
    # Check if coordinates might be normalized (0-1 range)
    if bunches:
        first_bbox = bunches[0]['bounding_box']
        max_coord = max(first_bbox['x_min'], first_bbox['y_min'], first_bbox['x_max'], first_bbox['y_max'])
        if max_coord <= 1.0:
            logger.warning(f"WARNING: Coordinates appear to be normalized (0-1). Max coordinate: {max_coord}")
            logger.warning("This suggests the AI returned normalized coordinates instead of pixel coordinates.")
            logger.warning("The visualization will attempt to handle this, but results may be incorrect.")
    
    # Draw each bunch
    for bunch in bunches:
        bbox = bunch['bounding_box']
        
        # Get raw coordinates
        raw_x_min = bbox['x_min']
        raw_y_min = bbox['y_min']
        raw_x_max = bbox['x_max']
        raw_y_max = bbox['y_max']
        
        # Debug: log raw coordinates from AI
        logger.info(f"  Bunch #{bunch['id']} raw coords: x_min={raw_x_min}, y_min={raw_y_min}, x_max={raw_x_max}, y_max={raw_y_max}")
        
        # Check if coordinates are normalized (0-1 range)
        # If max coordinate is <= 1.0, assume normalized
        max_raw_coord = max(abs(raw_x_min), abs(raw_y_min), abs(raw_x_max), abs(raw_y_max))
        if max_raw_coord <= 1.0 and max_raw_coord > 0:
            logger.warning(f"  Bunch #{bunch['id']}: Coordinates appear normalized (0-1), converting to pixel coordinates")
            # Convert normalized to pixel coordinates in analyzed image space
            raw_x_min = raw_x_min * analyzed_width
            raw_y_min = raw_y_min * analyzed_height
            raw_x_max = raw_x_max * analyzed_width
            raw_y_max = raw_y_max * analyzed_height
        
        # Validate coordinates are within analyzed image bounds
        if raw_x_min < 0 or raw_y_min < 0 or raw_x_max > analyzed_width or raw_y_max > analyzed_height:
            logger.warning(f"  Bunch #{bunch['id']}: Coordinates out of bounds for analyzed image ({analyzed_width}x{analyzed_height})")
            logger.warning(f"    Coords: [{raw_x_min}, {raw_y_min}, {raw_x_max}, {raw_y_max}]")
            # Clamp to bounds
            raw_x_min = max(0, min(raw_x_min, analyzed_width))
            raw_y_min = max(0, min(raw_y_min, analyzed_height))
            raw_x_max = max(0, min(raw_x_max, analyzed_width))
            raw_y_max = max(0, min(raw_y_max, analyzed_height))
        
        # Scale coordinates from analyzed image size to original image size
        x_min = int(raw_x_min * scale_x)
        y_min = int(raw_y_min * scale_y)
        x_max = int(raw_x_max * scale_x)
        y_max = int(raw_y_max * scale_y)
        
        # Calculate box dimensions for verification
        box_width = x_max - x_min
        box_height = y_max - y_min
        raw_box_width = raw_x_max - raw_x_min
        raw_box_height = raw_y_max - raw_y_min
        
        # Validate scaled coordinates against display image
        if x_min < 0 or y_min < 0 or x_max > display_width or y_max > display_height:
            logger.warning(f"  Bunch #{bunch['id']}: Coordinates out of bounds for display image ({display_width}x{display_height})")
            logger.warning(f"    Coords: [{x_min}, {y_min}, {x_max}, {y_max}]")
            # Clamp to bounds
            x_min = max(0, min(x_min, display_width))
            y_min = max(0, min(y_min, display_height))
            x_max = max(0, min(x_max, display_width))
            y_max = max(0, min(y_max, display_height))
        
        logger.info(f"  Bunch #{bunch['id']} final coords: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
        logger.info(f"  Bunch #{bunch['id']} box size: {box_width}x{box_height} (raw: {raw_box_width}x{raw_box_height}, scaled by {scale_x:.3f})")
        
        color_bgr = hex_to_bgr(bunch['color_code'])
        thickness = max(3, int(min(display_width, display_height) / 300))
        
        # Check if segmentation contour is available
        segmentation = bbox.get('segmentation')
        if segmentation and len(segmentation) > 2:
            # Draw segmentation contour (exact shape)
            logger.info(f"  Bunch #{bunch['id']}: Drawing segmentation contour with {len(segmentation)} points")
            
            # Scale segmentation points from analyzed image to display image
            scaled_points = []
            for point in segmentation:
                scaled_x = int(point[0] * scale_x)
                scaled_y = int(point[1] * scale_y)
                scaled_points.append([scaled_x, scaled_y])
            
            # Convert to numpy array for OpenCV
            contour = np.array(scaled_points, dtype=np.int32)
            
            # Draw the contour (outline only)
            cv2.polylines(img, [contour], isClosed=True, color=color_bgr, thickness=thickness)
            
            # Optional: Fill with semi-transparent color for better visibility
            overlay = img.copy()
            cv2.fillPoly(overlay, [contour], color_bgr)
            cv2.addWeighted(overlay, 0.2, img, 0.8, 0, img)  # 20% overlay transparency
            
            # Calculate and display actual area if available
            area = bbox.get('area')
            if area:
                area_scaled = area * scale_x * scale_y  # Scale area to display resolution
                logger.info(f"  Bunch #{bunch['id']}: Segmentation area = {area_scaled:.0f} pixels")
        else:
            # Fall back to bounding box rectangle
            logger.info(f"  Bunch #{bunch['id']}: Drawing bounding box (no segmentation data)")
            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color_bgr, thickness)
        
        # Prepare label
        stage = bunch['stage'].upper()
        confidence = bunch['confidence']
        visibility = bunch.get('visibility', '')
        label = f"#{bunch['id']}: {stage} {confidence:.0%}"
        
        if visibility == 'partially_visible':
            label += " [PARTIAL]"
        elif visibility == 'behind_fronds':
            label += " [HIDDEN]"
        
        # Draw label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.6, min(display_width, display_height) / 1800)
        font_thickness = max(2, int(font_scale * 2))
        
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        label_y = max(y_min - 10, th + 15)
        cv2.rectangle(img, (x_min, label_y - th - 10), 
                     (x_min + tw + 10, label_y + 5), color_bgr, -1)
        cv2.putText(img, label, (x_min + 5, label_y - 5),
                   font, font_scale, (255, 255, 255), font_thickness)
        
        # Draw center point (recalculate from scaled coordinates to ensure accuracy)
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        cv2.circle(img, (center_x, center_y), 6, color_bgr, -1)
        cv2.circle(img, (center_x, center_y), 6, (255, 255, 255), 2)
    
    # Add summary overlay
    cv2.rectangle(img, (10, 10), (450, 140), (0, 0, 0), -1)
    cv2.rectangle(img, (10, 10), (450, 140), (255, 255, 255), 3)
    
    font_scale = max(0.7, min(display_width, display_height) / 1500)
    thickness = max(2, int(font_scale * 2))
    
    summary = [
        f"Total Bunches: {analysis['total_bunches']}",
        f"Detection Confidence: {analysis.get('detection_confidence', 0):.0%}",
        f"Ripe: {analysis['stage_summary']['ripe']}  Mature: {analysis['stage_summary']['mature']}",
        f"Young: {analysis['stage_summary']['young']}  Overripe: {analysis['stage_summary']['overripe']}"
    ]
    
    for i, line in enumerate(summary):
        cv2.putText(img, line, (20, 40 + i * 30),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    # Save annotated image
    output_path = f"annotated_sample{Path(image_path).stem[-1]}.jpg"
    cv2.imwrite(output_path, img)
    logger.info(f"\nAnnotated image saved: {output_path}")
    
    # Resize for display if too large
    height, width = img.shape[:2]
    max_display = 1400
    if width > max_display or height > max_display:
        scale = max_display / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))
    
    # Display (skip on systems without GUI support)
    try:
        cv2.imshow('AgriAI - Bunch Detection Results (Press any key to close)', img)
        logger.info("\n" + "="*80)
        logger.info("IMAGE DISPLAYED - Press any key in the image window to close...")
        logger.info("="*80 + "\n")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except cv2.error as e:
        logger.info("\n" + "="*80)
        logger.info("Note: Image display not available (GUI not supported)")
        logger.info("✓ Image saved successfully - please open manually to view")
        logger.info("="*80 + "\n")

async def test_sample_image(image_path: str, json_output: bool = False, use_hybrid: bool = True):
    """Test analysis on a single sample image"""
    if not json_output:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing with: {image_path}")
        if use_hybrid and settings.USE_OBJECT_DETECTION:
            logger.info(f"Using: Hybrid Analyzer (Detection: {settings.DETECTION_BACKEND} + Claude)")
        else:
            logger.info(f"Using: Claude-only Analyzer")
        logger.info(f"{'='*80}")
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        # Analyze
        if use_hybrid and settings.USE_OBJECT_DETECTION:
            result = await hybrid_analyzer.analyze_crop_image(
                file_content=file_content,
                content_type="image/jpeg",
                crop_type=CropType.OIL_PALM,
                include_recommendations=True,
                min_confidence=0.5
            )
        else:
            result = await crop_analyzer.analyze_crop_image(
                file_content=file_content,
                content_type="image/jpeg",
                crop_type=CropType.OIL_PALM,
                include_recommendations=True,
                min_confidence=0.5
            )
        
        # Output results
        if json_output or VISUALIZE:
            # Convert to JSON format
            output = {
                "success": result.success,
                "crop_type": result.crop_type.value,
                "analysis": {
                    "total_bunches": result.analysis.total_bunches,
                    "detection_confidence": result.analysis.detection_confidence,
                    "bunches": [
                        {
                            "id": bunch.id,
                            "stage": bunch.stage.value,
                            "confidence": bunch.confidence,
                            "visibility": bunch.visibility,
                            "size": bunch.size,
                            "position": bunch.position,
                            "bounding_box": {
                                "x_min": bunch.bounding_box.x_min,
                                "y_min": bunch.bounding_box.y_min,
                                "x_max": bunch.bounding_box.x_max,
                                "y_max": bunch.bounding_box.y_max,
                                "center_x": bunch.bounding_box.center_x,
                                "center_y": bunch.bounding_box.center_y
                            },
                            "color_code": bunch.color_code,
                            "description": bunch.description
                        }
                        for bunch in result.analysis.bunches
                    ],
                    "stage_summary": {
                        "young": result.analysis.stage_summary.young,
                        "mature": result.analysis.stage_summary.mature,
                        "ripe": result.analysis.stage_summary.ripe,
                        "overripe": result.analysis.stage_summary.overripe
                    },
                    "plant_health": {
                        "overall_score": result.analysis.plant_health.overall_score,
                        "frond_condition": result.analysis.plant_health.frond_condition,
                        "bunch_development": result.analysis.plant_health.bunch_development,
                        "observations": result.analysis.plant_health.observations,
                        "concerns": result.analysis.plant_health.concerns
                    } if result.analysis.plant_health else None,
                    "recommendations": result.analysis.recommendations
                } if result.analysis else None,
                "image_metadata": {
                    "width": result.image_metadata.width,
                    "height": result.image_metadata.height,
                    "analyzed_at": result.image_metadata.analyzed_at,
                    "file_size_kb": result.image_metadata.file_size_kb
                },
                "processing_time_ms": result.processing_time_ms,
                "error": result.error
            }
            
            if json_output:
                print(json.dumps(output, indent=2))
            
            # Visualize if requested
            if VISUALIZE:
                # First, draw on the processed image to debug AI coordinates
                visualize_on_processed_image(output)
                # Then draw on the original image with scaling
                visualize_result(image_path, output)
            
            return result
        
        # Regular detailed output
        if result.success and result.analysis:
            logger.info(f"\n✓ Analysis successful!")
            logger.info(f"Processing time: {result.processing_time_ms:.0f}ms")
            logger.info(f"Image dimensions: {result.image_metadata.width}x{result.image_metadata.height}")
            
            if result.analysis.detection_confidence:
                logger.info(f"Overall detection confidence: {result.analysis.detection_confidence:.2f}")
            
            logger.info(f"\nTotal bunches detected: {result.analysis.total_bunches}")
            logger.info(f"\nStage breakdown:")
            logger.info(f"  - Young: {result.analysis.stage_summary.young}")
            logger.info(f"  - Mature: {result.analysis.stage_summary.mature}")
            logger.info(f"  - Ripe: {result.analysis.stage_summary.ripe}")
            logger.info(f"  - Overripe: {result.analysis.stage_summary.overripe}")
            
            # Plant health
            if result.analysis.plant_health:
                ph = result.analysis.plant_health
                logger.info(f"\n=== PLANT HEALTH ASSESSMENT ===")
                logger.info(f"Overall score: {ph.overall_score:.1f}/100")
                if ph.frond_condition:
                    logger.info(f"Frond condition: {ph.frond_condition}")
                if ph.bunch_development:
                    logger.info(f"Bunch development: {ph.bunch_development}")
                
                if ph.observations:
                    logger.info(f"\nObservations:")
                    for obs in ph.observations:
                        logger.info(f"  • {obs}")
                
                if ph.concerns:
                    logger.info(f"\nConcerns:")
                    for concern in ph.concerns:
                        logger.info(f"  ⚠ {concern}")
            
            # Detailed bunch info
            logger.info(f"\n=== DETECTED BUNCHES (Detailed) ===")
            for bunch in result.analysis.bunches:
                info = f"Bunch #{bunch.id}: {bunch.stage.value.upper()} (conf: {bunch.confidence:.2f})"
                if bunch.visibility:
                    info += f" [{bunch.visibility}]"
                if bunch.size:
                    info += f" - Size: {bunch.size}"
                if bunch.position:
                    info += f" - Pos: {bunch.position}"
                
                logger.info(f"\n{info}")
                logger.info(f"  Location: [{bunch.bounding_box.x_min}, {bunch.bounding_box.y_min}, "
                          f"{bunch.bounding_box.x_max}, {bunch.bounding_box.y_max}]")
                logger.info(f"  Color: {bunch.color_code}")
                if bunch.description:
                    logger.info(f"  Analysis: {bunch.description}")
            
            # Recommendations
            if result.analysis.recommendations:
                logger.info(f"\n=== RECOMMENDATIONS ===")
                for rec in result.analysis.recommendations:
                    logger.info(f"  ➤ {rec}")
        else:
            logger.error(f"\n✗ Analysis failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_all_samples():
    """Test all sample images in the oilpalm_samples directory"""
    samples_dir = Path(__file__).parent.parent / "oilpalm_samples"
    
    if not samples_dir.exists():
        logger.error(f"Samples directory not found: {samples_dir}")
        return
    
    # Get all jpg files
    image_files = sorted(samples_dir.glob("*.jpg"))
    
    if not image_files:
        logger.error("No .jpg files found in oilpalm_samples directory")
        return
    
    logger.info(f"Found {len(image_files)} sample images")
    
    results = []
    for image_path in image_files:
        result = await test_sample_image(str(image_path))
        results.append(result)
        await asyncio.sleep(1)
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    
    successful = sum(1 for r in results if r and r.success)
    logger.info(f"Successfully analyzed: {successful}/{len(results)} images")
    
    if successful > 0:
        total_bunches = sum(r.analysis.total_bunches for r in results if r and r.success and r.analysis)
        avg_processing_time = sum(r.processing_time_ms for r in results if r and r.success) / successful
        logger.info(f"Total bunches detected across all images: {total_bunches}")
        logger.info(f"Average processing time: {avg_processing_time:.0f}ms")

async def test_single_sample(sample_number: int = 1, json_output: bool = False):
    """Test a specific sample image by number"""
    samples_dir = Path(__file__).parent.parent / "oilpalm_samples"
    image_path = samples_dir / f"sample{sample_number}.jpg"
    
    if not image_path.exists():
        if not json_output:
            logger.error(f"Sample image not found: {image_path}")
        else:
            print(json.dumps({"error": f"Sample image not found: {image_path}"}))
        return
    
    await test_sample_image(str(image_path), json_output)

if __name__ == "__main__":
    # Filter out flags
    args = [arg for arg in sys.argv[1:] if arg not in ['--json', '-j', '--viz', '-v']]
    
    # Default to JSON output (like the API)
    output_json = JSON_OUTPUT if '--json' in sys.argv or '-j' in sys.argv else True
    
    if len(args) > 0:
        if args[0] == "all":
            asyncio.run(test_all_samples())
        else:
            try:
                sample_num = int(args[0])
                asyncio.run(test_single_sample(sample_num, output_json))
            except ValueError:
                if not output_json:
                    print("Usage: python test_with_samples.py [sample_number|all] [--viz|-v]")
                    print("  sample_number: Test specific sample (1-10)")
                    print("  all: Test all samples")
                    print("  --viz or -v: Visualize bounding boxes on image")
                    print("\nExamples:")
                    print("  python test_with_samples.py 1          # JSON output (default)")
                    print("  python test_with_samples.py 1 --viz    # JSON + save annotated image")
    else:
        asyncio.run(test_single_sample(1, output_json))
