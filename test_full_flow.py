"""
Test script for complete S3 + MongoDB integration flow

This script tests:
1. Analyze endpoint with base64 image
2. Storage in S3 and MongoDB
3. Retrieval of analysis by image ID
4. Retrieval of all analyses
5. User-specific analyses
6. Database statistics

Usage:
    python test_full_flow.py
"""

import requests
import base64
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "/api/v1"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_analyze_base64(image_path: str, user_uuid: str = "test-user-123"):
    """
    Test the analyze-base64 endpoint
    
    Args:
        image_path: Path to test image
        user_uuid: User UUID for testing
        
    Returns:
        Response data with image_id
    """
    print_section("TEST 1: Analyze Base64 Image with S3 + MongoDB Storage")
    
    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        print(f"✓ Loaded test image: {image_path}")
        print(f"  Image size: {len(image_data)} characters (base64)")
    except FileNotFoundError:
        print(f"✗ Error: Image file not found: {image_path}")
        return None
    
    # Prepare request
    payload = {
        "file": f"data:image/jpeg;base64,{image_data}",
        "filename": Path(image_path).name,
        "lat": "51.5074",
        "long": "-0.1278",
        "uuid": user_uuid,
        "crop_type": "oil_palm",
        "use_detection": True,
        "return_annotated_image": True,
        "include_recommendations": True
    }
    
    print(f"\nSending request to: {BASE_URL}{API_VERSION}/analyze-base64")
    print(f"User UUID: {user_uuid}")
    print(f"Filename: {payload['filename']}")
    
    # Make request
    try:
        response = requests.post(
            f"{BASE_URL}{API_VERSION}/analyze-base64",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Analysis successful!")
            print(f"  Image ID: {data.get('image_id')}")
            print(f"  Database ID: {data.get('database_id')}")
            print(f"  Original Image URL: {data.get('original_image_url')}")
            print(f"  Annotated Image URL: {data.get('annotated_image_url')}")
            print(f"  Processing Time: {data.get('processing_time_ms')}ms")
            
            if data.get('analysis'):
                analysis = data['analysis']
                print(f"\n  Analysis Results:")
                print(f"    - Total Bunches: {analysis.get('total_bunches')}")
                print(f"    - Detection Confidence: {analysis.get('detection_confidence')}")
                if analysis.get('stage_summary'):
                    stage_summary = analysis['stage_summary']
                    print(f"    - Stage Summary:")
                    print(f"        Young: {stage_summary.get('young')}")
                    print(f"        Mature: {stage_summary.get('mature')}")
                    print(f"        Ripe: {stage_summary.get('ripe')}")
                    print(f"        Overripe: {stage_summary.get('overripe')}")
            
            return data
        else:
            print(f"\n✗ Request failed with status code: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n✗ Exception occurred: {str(e)}")
        return None

def test_get_analysis(image_id: str):
    """Test fetching a specific analysis by image ID"""
    print_section(f"TEST 2: Fetch Analysis by Image ID: {image_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_VERSION}/analysis/{image_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Successfully fetched analysis")
            print(f"  Image ID: {data.get('image_id')}")
            print(f"  User UUID: {data.get('user_uuid')}")
            print(f"  Filename: {data.get('filename')}")
            print(f"  Created At: {data.get('created_at')}")
            print(f"  Latitude: {data.get('latitude')}")
            print(f"  Longitude: {data.get('longitude')}")
            print(f"\n  Presigned URLs (valid for 1 hour):")
            print(f"    Original: {data.get('original_image_presigned_url')[:80]}...")
            print(f"    Annotated: {data.get('annotated_image_presigned_url')[:80]}...")
            return data
        elif response.status_code == 404:
            print(f"✗ Analysis not found")
            return None
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Exception occurred: {str(e)}")
        return None

def test_get_all_analyses(limit: int = 10):
    """Test fetching all analyses"""
    print_section(f"TEST 3: Fetch All Analyses (limit={limit})")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_VERSION}/analyses/all",
            params={"limit": limit, "skip": 0},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully fetched analyses")
            print(f"  Total in Database: {data.get('total')}")
            print(f"  Returned: {data.get('count')}")
            print(f"  Limit: {data.get('limit')}")
            print(f"  Skip: {data.get('skip')}")
            
            if data.get('data'):
                print(f"\n  Recent Analyses:")
                for i, item in enumerate(data['data'][:5], 1):  # Show first 5
                    print(f"    {i}. {item.get('filename')}")
                    print(f"       - Image ID: {item.get('image_id')}")
                    print(f"       - User: {item.get('user_uuid')}")
                    print(f"       - Crop: {item.get('crop_type')}, Bunches: {item.get('total_bunches')}")
                    print(f"       - Created: {item.get('created_at')}")
            
            return data
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Exception occurred: {str(e)}")
        return None

def test_get_user_analyses(user_uuid: str):
    """Test fetching user-specific analyses"""
    print_section(f"TEST 4: Fetch User Analyses for: {user_uuid}")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_VERSION}/analyses/user/{user_uuid}",
            params={"limit": 50, "skip": 0},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully fetched user analyses")
            print(f"  Total for User: {data.get('total')}")
            print(f"  Returned: {data.get('count')}")
            
            if data.get('data'):
                print(f"\n  User's Analyses:")
                for i, item in enumerate(data['data'], 1):
                    print(f"    {i}. {item.get('filename')}")
                    print(f"       - Image ID: {item.get('image_id')}")
                    print(f"       - Bunches: {item.get('total_bunches')}")
                    print(f"       - Created: {item.get('created_at')}")
            
            return data
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Exception occurred: {str(e)}")
        return None

def test_get_statistics():
    """Test fetching database statistics"""
    print_section("TEST 5: Database Statistics")
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_VERSION}/statistics",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Successfully fetched statistics")
            print(f"\n  Database Metrics:")
            print(f"    - Total Analyses: {data.get('total_analyses')}")
            print(f"    - Unique Users: {data.get('unique_users')}")
            print(f"    - Original Images in S3: {data.get('total_original_images')}")
            print(f"    - Annotated Images in S3: {data.get('total_annotated_images')}")
            
            if data.get('crop_distribution'):
                print(f"\n  Crop Distribution:")
                for crop, count in data['crop_distribution'].items():
                    print(f"    - {crop}: {count}")
            
            return data
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Exception occurred: {str(e)}")
        return None

def test_health():
    """Test health endpoint"""
    print_section("TEST 0: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}{API_VERSION}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"  Status: {data.get('status')}")
            print(f"  Service: {data.get('service')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Cannot connect to API: {str(e)}")
        print(f"  Make sure the API is running at {BASE_URL}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  AgriAI Full Flow Integration Test")
    print("="*80)
    print(f"\n  Base URL: {BASE_URL}")
    print(f"  API Version: {API_VERSION}")
    
    # Check for test image
    test_images = [
        "oilpalm_samples/sample1.jpg",
        "oilpalm_samples/sample2.jpg",
        "test_image.jpg",
        "sample.jpg"
    ]
    
    test_image = None
    for img in test_images:
        if Path(img).exists():
            test_image = img
            break
    
    if not test_image:
        print(f"\n✗ No test image found. Tried: {test_images}")
        print("  Please provide a test image and update the script.")
        return
    
    # Test 0: Health check
    if not test_health():
        print("\n⚠️  API is not accessible. Exiting.")
        return
    
    # Test 1: Analyze image
    user_uuid = "test-user-123"
    analyze_result = test_analyze_base64(test_image, user_uuid)
    
    if not analyze_result:
        print("\n⚠️  Analysis failed. Cannot continue with retrieval tests.")
        return
    
    image_id = analyze_result.get('image_id')
    
    # Test 2: Fetch by image ID
    if image_id:
        test_get_analysis(image_id)
    
    # Test 3: Fetch all analyses
    test_get_all_analyses(limit=10)
    
    # Test 4: Fetch user's analyses
    test_get_user_analyses(user_uuid)
    
    # Test 5: Get statistics
    test_get_statistics()
    
    # Final summary
    print_section("TEST SUMMARY")
    print("✓ All tests completed!")
    print("\nKey endpoints tested:")
    print("  1. POST /analyze-base64 - ✓")
    print("  2. GET /analysis/{image_id} - ✓")
    print("  3. GET /analyses/all - ✓")
    print("  4. GET /analyses/user/{uuid} - ✓")
    print("  5. GET /statistics - ✓")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

