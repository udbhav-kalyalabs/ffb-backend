# Base64 Image Analysis API Guide

This guide explains how to use the new base64 image analysis endpoint that accepts JSON input and returns annotated images.

## Overview

The `/api/v1/analyze-base64` endpoint accepts:
- **Input**: JSON with base64-encoded image
- **Output**: JSON with analysis results + base64-encoded annotated image

This is perfect for integrating with frontend applications or other services that work with base64 image data.

---

## API Endpoint

### POST `/api/v1/analyze-base64`

**Content-Type**: `application/json`

---

## Request Format

### Request Body Schema

```json
{
  "file": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "filename": "palm_tree.jpg",
  "lat": "51.5074",
  "long": "-0.1278",
  "uuid": "user-123-uuid",
  "crop_type": "oil_palm",
  "include_recommendations": true,
  "min_confidence": 0.5,
  "use_detection": true,
  "return_annotated_image": true
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | string | ✅ Yes | - | Base64 encoded image (with or without data URI prefix) |
| `filename` | string | ✅ Yes | - | Original filename (used to determine image type) |
| `lat` | string | ❌ No | null | Latitude coordinate (for GPS tracking) |
| `long` | string | ❌ No | null | Longitude coordinate (for GPS tracking) |
| `uuid` | string | ❌ No | null | User UUID (for tracking/logging) |
| `crop_type` | string | ❌ No | "oil_palm" | Type of crop ("oil_palm" currently supported) |
| `include_recommendations` | boolean | ❌ No | true | Include harvest recommendations |
| `min_confidence` | float | ❌ No | 0.5 | Minimum confidence threshold (0.0-1.0) |
| `use_detection` | boolean | ❌ No | true | Use object detection for precise boxes |
| `return_annotated_image` | boolean | ❌ No | true | Return image with drawn bounding boxes |

### Image Format

The `file` parameter accepts two formats:

**1. With Data URI prefix (recommended):**
```
data:image/jpeg;base64,/9j/4AAQSkZJRg...
```

**2. Raw base64 string:**
```
/9j/4AAQSkZJRg...
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "crop_type": "oil_palm",
  "processing_time_ms": 2847.3,
  
  "analysis": {
    "total_bunches": 3,
    "detection_confidence": 0.85,
    
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.92,
        "bounding_box": {
          "x_min": 1000,
          "y_min": 700,
          "x_max": 1400,
          "y_max": 1050,
          "center_x": 1200,
          "center_y": 875,
          "segmentation": [[x1,y1], [x2,y2], ...],
          "area": 125340.5
        },
        "color_code": "#FF4500",
        "visibility": "fully_visible",
        "size": "large",
        "position": "front-center",
        "description": "Large ripe bunch with deep orange-red coloration..."
      }
    ],
    
    "stage_summary": {
      "young": 0,
      "mature": 1,
      "ripe": 1,
      "overripe": 1
    },
    
    "plant_health": {
      "overall_score": 85.0,
      "frond_condition": "good",
      "bunch_development": "excellent",
      "observations": ["Healthy frond color", "Multiple bunches visible"],
      "concerns": ["One overripe bunch needs immediate harvest"]
    },
    
    "recommendations": [
      "Harvest the overripe bunch (ID: 2) immediately",
      "Monitor ripe bunch (ID: 1) for harvest in 2-3 days"
    ]
  },
  
  "image_metadata": {
    "width": 4032,
    "height": 3024,
    "analyzed_at": "2026-01-29T15:30:45.123456",
    "file_size_kb": 2847.3
  },
  
  "annotated_image": "/9j/4AAQSkZJRgABA...",
  "annotated_image_format": "jpeg",
  "error": null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether analysis succeeded |
| `crop_type` | string | Type of crop analyzed |
| `processing_time_ms` | float | Processing duration in milliseconds |
| `analysis` | object | Detailed analysis results (see below) |
| `image_metadata` | object | Image dimensions and metadata |
| `annotated_image` | string | Base64 encoded image with bounding boxes drawn |
| `annotated_image_format` | string | Format of annotated image ("jpeg" or "png") |
| `error` | string | Error message (null if successful) |

### Analysis Object

- **`total_bunches`**: Total number of fruit bunches detected
- **`detection_confidence`**: Overall detection confidence score
- **`bunches`**: Array of detected bunches with:
  - `id`: Unique bunch identifier
  - `stage`: Ripeness stage ("young", "mature", "ripe", "overripe")
  - `confidence`: Classification confidence (0.0-1.0)
  - `bounding_box`: Pixel coordinates and optional segmentation mask
  - `color_code`: Hex color for visualization
  - `visibility`, `size`, `position`: Additional attributes
  - `description`: Detailed analysis text
- **`stage_summary`**: Count of bunches by ripeness stage
- **`plant_health`**: Overall health assessment
- **`recommendations`**: Actionable harvest recommendations

---

## Example Usage

### cURL Example

```bash
curl --location 'http://localhost:8000/api/v1/analyze-base64' \
--header 'Content-Type: application/json' \
--data '{
    "file": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
    "filename": "palm_tree.jpg",
    "lat": "1.3521",
    "long": "103.8198",
    "uuid": "user-456-uuid",
    "crop_type": "oil_palm",
    "use_detection": true,
    "return_annotated_image": true
}'
```

### Python Example

```python
import requests
import base64
import json
from pathlib import Path

# Read and encode image
image_path = "palm_tree.jpg"
with open(image_path, "rb") as f:
    image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

# Prepare request
url = "http://localhost:8000/api/v1/analyze-base64"
payload = {
    "file": f"data:image/jpeg;base64,{base64_image}",
    "filename": "palm_tree.jpg",
    "lat": "1.3521",
    "long": "103.8198",
    "uuid": "user-123",
    "crop_type": "oil_palm",
    "use_detection": True,
    "return_annotated_image": True
}

# Send request
response = requests.post(url, json=payload)
result = response.json()

# Save annotated image
if result['success'] and result['annotated_image']:
    annotated_bytes = base64.b64decode(result['annotated_image'])
    with open("annotated_result.jpg", "wb") as f:
        f.write(annotated_bytes)
    print(f"Saved annotated image: annotated_result.jpg")

# Print analysis
print(f"Total bunches: {result['analysis']['total_bunches']}")
print(f"Stage summary: {result['analysis']['stage_summary']}")
print(f"Recommendations: {result['analysis']['recommendations']}")
```

### JavaScript Example (Frontend)

```javascript
// Convert image file to base64
async function analyzeImage(file) {
  // Read file as base64
  const reader = new FileReader();
  reader.readAsDataURL(file);
  
  const base64Image = await new Promise((resolve) => {
    reader.onload = () => resolve(reader.result);
  });
  
  // Prepare request
  const payload = {
    file: base64Image,  // Already includes "data:image/jpeg;base64," prefix
    filename: file.name,
    lat: "1.3521",
    long: "103.8198",
    uuid: "user-123",
    crop_type: "oil_palm",
    use_detection: true,
    return_annotated_image: true
  };
  
  // Send request
  const response = await fetch('http://localhost:8000/api/v1/analyze-base64', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });
  
  const result = await response.json();
  
  // Display annotated image
  if (result.success && result.annotated_image) {
    const imgElement = document.getElementById('result-image');
    imgElement.src = `data:image/jpeg;base64,${result.annotated_image}`;
  }
  
  // Display analysis
  console.log('Total bunches:', result.analysis.total_bunches);
  console.log('Recommendations:', result.analysis.recommendations);
  
  return result;
}

// Usage
const fileInput = document.getElementById('image-upload');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const result = await analyzeImage(file);
  // Handle result...
});
```

---

## Annotated Image

When `return_annotated_image: true`, the response includes a `annotated_image` field containing a base64-encoded JPEG image with:

✅ **Bounding boxes** around each detected bunch (colored by ripeness)
✅ **Segmentation masks** (semi-transparent overlays showing exact bunch shape)
✅ **Labels** showing bunch ID, stage, and confidence
✅ **Summary overlay** with total counts and statistics
✅ **Color coding**:
  - 🟢 **Green**: Young bunches
  - 🟡 **Yellow**: Mature bunches
  - 🟠 **Orange**: Ripe bunches
  - 🔴 **Red**: Overripe bunches

### Displaying Annotated Image

**HTML:**
```html
<img id="annotated-image" />
```

**JavaScript:**
```javascript
// Set from API response
const imgElement = document.getElementById('annotated-image');
imgElement.src = `data:image/jpeg;base64,${result.annotated_image}`;
```

**Python:**
```python
# Save to file
annotated_bytes = base64.b64decode(result['annotated_image'])
with open("result.jpg", "wb") as f:
    f.write(annotated_bytes)
```

---

## Error Handling

### Error Response

```json
{
  "success": false,
  "crop_type": "oil_palm",
  "analysis": null,
  "image_metadata": {
    "width": 0,
    "height": 0,
    "analyzed_at": "2026-01-29T15:30:45",
    "file_size_kb": null
  },
  "processing_time_ms": 145.2,
  "annotated_image": null,
  "annotated_image_format": null,
  "error": "Invalid base64 encoding: Incorrect padding"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid base64 encoding` | Corrupted base64 data | Check base64 encoding is valid |
| `Invalid data URI format` | Malformed data URI | Use format: `data:image/jpeg;base64,{data}` |
| `Empty image data` | Empty file parameter | Ensure image data is not empty |
| `Invalid crop type` | Unsupported crop | Use "oil_palm" (only supported type) |
| `Image too large` | File exceeds limit | Resize image before encoding |

---

## Performance

- **Average processing time**: 2-4 seconds
- **Maximum image size**: 10MB (before base64 encoding)
- **Recommended image dimensions**: 2000x1500 to 4000x3000 pixels
- **Base64 overhead**: ~33% larger than original file

---

## Comparison: Multipart vs Base64 Endpoint

| Feature | `/analyze` (Multipart) | `/analyze-base64` (JSON) |
|---------|----------------------|-------------------------|
| Input Format | File upload | JSON with base64 |
| Frontend Integration | Standard form upload | Easy with fetch/axios |
| Metadata Support | Via form fields | Via JSON fields |
| Annotated Image | Not included | Included in response |
| Mobile Apps | Requires multipart handling | Simple JSON handling |
| Best For | Traditional file uploads | API integrations, SPAs |

---

## Next Steps

1. **Deploy the API** to your server (AWS Lambda, EC2, etc.)
2. **Configure environment variables** (AWS keys, Roboflow API key)
3. **Test with sample images** from `oilpalm_samples/`
4. **Integrate with your frontend** using the JavaScript example above

For questions or issues, check the main `README.md` or open an issue.

