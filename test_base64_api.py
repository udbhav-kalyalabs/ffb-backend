"""
Test script for base64 image analysis API
Demonstrates how to:
1. Convert image to base64 (with data URI prefix)
2. Send to API
3. Receive and save annotated image
"""
import requests
import base64
import json
from pathlib import Path
import sys

def test_base64_api(image_path: str, api_url: str = "http://localhost:8000/api/v1/analyze-base64"):
    """
    Test the base64 analysis endpoint
    
    Args:
        image_path: Path to image file
        api_url: API endpoint URL
    """
    print(f"Testing Base64 API with image: {image_path}")
    print(f"API URL: {api_url}\n")
    
    # Read and encode image
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"Error: Image not found: {image_path}")
        return
    
    with open(image_file, "rb") as f:
        image_bytes = f.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"✓ Loaded image: {len(image_bytes)} bytes")
    print(f"✓ Encoded to base64: {len(base64_image)} characters")
    
    # Prepare request (matching the user's format)
    payload = {
        "file": f"data:image/jpeg;base64,{base64_image}",
        "filename": image_file.name,
        "lat": "1.3521",
        "long": "103.8198",
        "uuid": "user-456-uuid",
        "crop_type": "oil_palm",
        "include_recommendations": True,
        "min_confidence": 0.5,
        "use_detection": True,
        "return_annotated_image": True
    }
    
    print(f"\n📤 Sending request to API...")
    print(f"   Payload size: {len(json.dumps(payload))} bytes\n")
    
    # Send request
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Process response
    print("="*80)
    print("📥 RESPONSE RECEIVED")
    print("="*80)
    
    if result.get('success'):
        print("✅ Analysis SUCCESS\n")
        
        analysis = result['analysis']
        
        # Print summary
        print("📊 ANALYSIS SUMMARY:")
        print(f"   Total Bunches: {analysis['total_bunches']}")
        print(f"   Detection Confidence: {analysis.get('detection_confidence', 0):.1%}")
        print(f"   Processing Time: {result['processing_time_ms']:.0f}ms\n")
        
        # Print stage breakdown
        print("🌴 STAGE BREAKDOWN:")
        summary = analysis['stage_summary']
        print(f"   🟢 Young:    {summary['young']}")
        print(f"   🟡 Mature:   {summary['mature']}")
        print(f"   🟠 Ripe:     {summary['ripe']}")
        print(f"   🔴 Overripe: {summary['overripe']}\n")
        
        # Print each bunch
        print("📦 DETECTED BUNCHES:")
        for bunch in analysis['bunches']:
            bbox = bunch['bounding_box']
            print(f"   Bunch #{bunch['id']}: {bunch['stage'].upper()}")
            print(f"      Confidence: {bunch['confidence']:.1%}")
            print(f"      Location: [{bbox['x_min']}, {bbox['y_min']}, {bbox['x_max']}, {bbox['y_max']}]")
            print(f"      Size: {bunch.get('size', 'unknown')}, Visibility: {bunch.get('visibility', 'unknown')}")
            if bunch.get('description'):
                print(f"      → {bunch['description'][:80]}...")
            print()
        
        # Print health assessment
        if analysis.get('plant_health'):
            health = analysis['plant_health']
            print("🏥 PLANT HEALTH:")
            print(f"   Overall Score: {health['overall_score']:.0f}/100")
            print(f"   Frond Condition: {health.get('frond_condition', 'N/A')}")
            print(f"   Bunch Development: {health.get('bunch_development', 'N/A')}")
            
            if health.get('concerns'):
                print(f"   ⚠️  Concerns: {', '.join(health['concerns'])}")
            print()
        
        # Print recommendations
        if analysis.get('recommendations'):
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"   {i}. {rec}")
            print()
        
        # Save annotated image
        if result.get('annotated_image'):
            output_path = Path(f"annotated_{image_file.stem}.jpg")
            annotated_bytes = base64.b64decode(result['annotated_image'])
            
            with open(output_path, "wb") as f:
                f.write(annotated_bytes)
            
            print(f"🖼️  ANNOTATED IMAGE:")
            print(f"   Saved to: {output_path.absolute()}")
            print(f"   Size: {len(annotated_bytes)/1024:.2f}KB")
            print(f"   Format: {result.get('annotated_image_format', 'unknown').upper()}\n")
        
        # Image metadata
        metadata = result['image_metadata']
        print("📐 IMAGE METADATA:")
        print(f"   Dimensions: {metadata['width']}x{metadata['height']}")
        print(f"   File Size: {metadata.get('file_size_kb', 0):.2f}KB")
        print(f"   Analyzed At: {metadata['analyzed_at']}\n")
        
        print("="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
    else:
        print("❌ Analysis FAILED\n")
        print(f"Error: {result.get('error', 'Unknown error')}\n")
        print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_base64_api.py <image_path> [api_url]")
        print("\nExamples:")
        print("  python test_base64_api.py oilpalm_samples/sample1.jpg")
        print("  python test_base64_api.py my_image.jpg http://localhost:8000/api/v1/analyze-base64")
        sys.exit(1)
    
    image_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/api/v1/analyze-base64"
    
    test_base64_api(image_path, api_url)

