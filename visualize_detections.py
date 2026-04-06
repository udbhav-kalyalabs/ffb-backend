"""
Visualize bounding box detections on oil palm images
"""
import cv2
import numpy as np
from pathlib import Path
import json
import sys

def hex_to_bgr(hex_color):
    """Convert hex color to BGR for OpenCV"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[2], rgb[1], rgb[0])  # BGR format

def draw_bounding_boxes(image_path, analysis_result, output_path=None):
    """
    Draw bounding boxes on image based on analysis results
    
    Args:
        image_path: Path to the image file
        analysis_result: Analysis result dict with bunches
        output_path: Optional path to save annotated image
    
    Returns:
        Annotated image (numpy array)
    """
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    original_height, original_width = img.shape[:2]
    
    # Get analysis data
    if not analysis_result.get('success') or not analysis_result.get('analysis'):
        print("No analysis data available")
        return img
    
    analysis = analysis_result['analysis']
    bunches = analysis.get('bunches', [])
    
    print(f"\nDrawing {len(bunches)} bounding boxes on image...")
    print(f"Image size: {original_width}x{original_height}")
    print(f"Analysis expects: {analysis_result['image_metadata']['width']}x{analysis_result['image_metadata']['height']}")
    
    # Calculate scale factor if image sizes differ
    analyzed_width = analysis_result['image_metadata']['width']
    analyzed_height = analysis_result['image_metadata']['height']
    scale_x = original_width / analyzed_width
    scale_y = original_height / analyzed_height
    
    print(f"Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
    
    # Draw each bunch
    for bunch in bunches:
        # Get coordinates and scale them
        bbox = bunch['bounding_box']
        x_min = int(bbox['x_min'] * scale_x)
        y_min = int(bbox['y_min'] * scale_y)
        x_max = int(bbox['x_max'] * scale_x)
        y_max = int(bbox['y_max'] * scale_y)
        
        # Get color
        color_bgr = hex_to_bgr(bunch['color_code'])
        
        # Draw rectangle
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
        
        print(f"  Bunch #{bunch['id']}: {stage} at [{x_min}, {y_min}, {x_max}, {y_max}]")
    
    # Add summary overlay
    summary_y = 30
    summary_font_scale = max(0.6, min(original_width, original_height) / 1500)
    summary_thickness = max(1, int(summary_font_scale * 2))
    
    # Background for summary
    cv2.rectangle(img, (10, 10), (400, 120), (0, 0, 0), -1)
    cv2.rectangle(img, (10, 10), (400, 120), (255, 255, 255), 2)
    
    # Summary text
    summary_lines = [
        f"Total Bunches: {analysis['total_bunches']}",
        f"Confidence: {analysis.get('detection_confidence', 0):.0%}",
        f"Ripe: {analysis['stage_summary']['ripe']}, Mature: {analysis['stage_summary']['mature']}",
        f"Young: {analysis['stage_summary']['young']}, Overripe: {analysis['stage_summary']['overripe']}"
    ]
    
    for i, line in enumerate(summary_lines):
        cv2.putText(
            img, line,
            (20, summary_y + i * 25),
            font, summary_font_scale, (255, 255, 255), summary_thickness
        )
    
    # Save if output path provided
    if output_path:
        cv2.imwrite(str(output_path), img)
        print(f"\nAnnotated image saved to: {output_path}")
    
    return img

def show_image(img, window_name="Bunch Detection Results"):
    """Display image in a window"""
    # Resize if too large
    height, width = img.shape[:2]
    max_dimension = 1200
    
    if width > max_dimension or height > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))
        print(f"Resized for display: {new_width}x{new_height}")
    
    cv2.imshow(window_name, img)
    print("\n" + "="*80)
    print("Press any key to close the image window...")
    print("="*80)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python visualize_detections.py <image_path> <json_response>")
        print("  or: python visualize_detections.py <sample_number> <json_response>")
        sys.exit(1)
    
    # Parse arguments
    arg1 = sys.argv[1]
    json_path = sys.argv[2]
    
    # Determine image path
    if arg1.isdigit():
        # Sample number provided
        sample_num = int(arg1)
        image_path = Path(f"oilpalm_samples/sample{sample_num}.jpg")
    else:
        # Full path provided
        image_path = Path(arg1)
    
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)
    
    # Load JSON response
    if json_path == '-':
        # Read from stdin
        analysis_result = json.load(sys.stdin)
    else:
        with open(json_path, 'r') as f:
            analysis_result = json.load(f)
    
    # Draw and display
    annotated_img = draw_bounding_boxes(image_path, analysis_result)
    
    # Save annotated version
    output_path = Path(f"annotated_{image_path.name}")
    cv2.imwrite(str(output_path), annotated_img)
    print(f"\nAnnotated image saved: {output_path}")
    
    # Display
    show_image(annotated_img)
