# Base64 Image Analysis - Integration Summary

## 🎯 Overview

This document explains how the base64 image analysis works end-to-end in the AgriAI codebase, specifically for your integration where images arrive as base64-encoded JSON.

---

## 📥 INPUT: What You Send

### Your API Format
```bash
curl --location 'https://your-api.execute-api.ap-south-1.amazonaws.com/dev/upload' \
--header 'Content-Type: application/json' \
--data '{
    "file": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "filename": "base64_test.jpg",
    "lat": "51.5074",
    "long": "-0.1278",
    "uuid": "user-456-uuid"
}'
```

### What Happens

1. **Request arrives at**: `POST /api/v1/analyze-base64`
2. **Content-Type**: `application/json`
3. **File format**: Base64 string with data URI prefix

---

## 🔄 PROCESSING FLOW

### Step 1: Parse Base64 Data
**File**: `routes/analysis.py` → `analyze_base64_image()`

```python
# Extract base64 from data URI
"data:image/jpeg;base64,/9j/4AAQ..." 
  ↓
"/9j/4AAQ..."  # Pure base64 string

# Decode to bytes
base64_string → bytes (raw image data)
```

### Step 2: Route to Analyzer
**Files**: `routes/analysis.py` → `services/hybrid_analyzer.py`

```python
if use_detection and USE_OBJECT_DETECTION:
    # Use Hybrid Analyzer (Roboflow + Claude)
    hybrid_analyzer.analyze_crop_image(file_content, ...)
else:
    # Use Claude-only
    crop_analyzer.analyze_crop_image(file_content, ...)
```

### Step 3: Hybrid Analysis Pipeline
**File**: `services/hybrid_analyzer.py`

```python
# 3a. Get original image dimensions
original_image = Image.open(BytesIO(file_content))
original_width, original_height = original_image.size

# 3b. Process image for Claude (may resize)
base64_image, processed_width, processed_height = image_processor.process(...)

# 3c. Run Roboflow detection (uses ORIGINAL image)
detections = detector.detect(file_content, confidence_threshold)
# Returns: [{bbox: [x_min, y_min, x_max, y_max], confidence: 0.89, class_name: "Black FFB"}]

# 3d. Map Roboflow classes to ripeness stages
"Black FFB" → "ripe"
"Red FFB" → "overripe"
"Yellow FFB" → "mature"
"Green FFB" → "young"

# 3e. Send to Claude AI for analysis
prompt = build_analysis_prompt(detections, dimensions)
claude_response = bedrock_service.analyze_image(prompt, base64_image)
# Returns: JSON with stage classification, health, recommendations

# 3f. Merge results
bunches = [
    {
        id: 1,
        stage: roboflow_stage,  # Primary source
        confidence: claude_confidence,
        bounding_box: roboflow_bbox,  # Precise coordinates
        description: claude_description
    }
]
```

### Step 4: Generate Annotated Image
**File**: `services/image_annotator.py`

```python
# Draw on original image
annotated_img = draw_bounding_boxes(file_content, analysis_result)

# Draws:
- Bounding boxes (colored by stage)
- Segmentation masks (semi-transparent)
- Labels with ID, stage, confidence
- Summary overlay with counts
- Center points

# Encode back to base64
annotated_base64 = base64.b64encode(annotated_img_bytes).decode('utf-8')
```

---

## 📤 OUTPUT: What You Get

### Complete Response Structure

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
        "description": "Large ripe bunch..."
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
      "observations": [...],
      "concerns": [...]
    },
    
    "recommendations": [
      "Harvest overripe bunch immediately",
      "Monitor ripe bunch for harvest in 2-3 days"
    ]
  },
  
  "image_metadata": {
    "width": 4032,
    "height": 3024,
    "analyzed_at": "2026-01-29T15:30:45",
    "file_size_kb": 2847.3
  },
  
  "annotated_image": "/9j/4AAQSkZJRgABA...",
  "annotated_image_format": "jpeg",
  "error": null
}
```

---

## 🖼️ Annotated Image Details

### What's Drawn on the Image

1. **Bounding Boxes**
   - Colored rectangles around each detected bunch
   - Color-coded by ripeness stage
   - Thickness scales with image size

2. **Segmentation Masks** (if available)
   - Semi-transparent colored overlay showing exact bunch shape
   - More precise than rectangular boxes

3. **Labels**
   - Bunch ID, stage name, confidence percentage
   - Visibility indicators [PARTIAL], [HIDDEN]
   - White text on colored background

4. **Center Points**
   - Small circle marking the center of each bunch
   - Useful for robotic harvesting systems

5. **Summary Overlay**
   - Top-left corner box with statistics
   - Total count, overall confidence
   - Breakdown by ripeness stage

### Color Coding

| Stage | Color | Hex Code | Meaning |
|-------|-------|----------|---------|
| Young | 🟢 Green | #32CD32 | Not ready, wait |
| Mature | 🟡 Yellow | #FFD700 | Almost ready, monitor |
| Ripe | 🟠 Orange | #FF4500 | Ready to harvest |
| Overripe | 🔴 Red | #DC143C | Harvest urgently |

---

## 🔧 Key Components

### 1. Routes (`routes/analysis.py`)

**Endpoint**: `POST /api/v1/analyze-base64`
- Validates input
- Parses base64 data
- Routes to analyzer
- Generates annotated image
- Returns combined response

### 2. Hybrid Analyzer (`services/hybrid_analyzer.py`)

**Purpose**: Combines object detection + AI analysis
- Runs Roboflow detection for precise boxes
- Maps Roboflow classes to ripeness stages
- Sends to Claude for intelligent analysis
- Merges results for best of both worlds

### 3. Image Annotator (`services/image_annotator.py`)

**Purpose**: Draws bounding boxes and labels
- Reads image from bytes
- Draws boxes, masks, labels, summary
- Encodes back to base64

### 4. Object Detector (`services/object_detector.py`)

**Purpose**: Detects bunches with bounding boxes
- Supports: Roboflow, YOLO, Custom API, Mock
- Returns: Coordinates, confidence, class names
- Includes segmentation masks when available

### 5. Bedrock Service (`services/bedrock_service.py`)

**Purpose**: Claude AI analysis
- Connects to AWS Bedrock
- Sends image + prompt to Claude
- Returns: Classification, health, recommendations

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│  Your System    │
│  (Base64 JSON)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  AgriAI API                         │
│  POST /api/v1/analyze-base64        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Parse Base64   │ ← Remove data URI prefix
│  Decode to Bytes│ ← Convert to raw image
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Hybrid Analyzer                    │
├─────────────────────────────────────┤
│  1. Image Processing                │
│     • Get dimensions                │
│     • Resize if needed              │
│     • Convert to base64             │
├─────────────────────────────────────┤
│  2. Roboflow Detection              │
│     • Detect bunches                │
│     • Get bounding boxes            │
│     • Get class names               │
│     • Get segmentation masks        │
├─────────────────────────────────────┤
│  3. Class Mapping                   │
│     • "Black FFB" → "ripe"          │
│     • "Red FFB" → "overripe"        │
│     • etc.                          │
├─────────────────────────────────────┤
│  4. Claude AI Analysis              │
│     • Validate stages               │
│     • Assess visibility             │
│     • Evaluate health               │
│     • Generate recommendations      │
├─────────────────────────────────────┤
│  5. Merge Results                   │
│     • Combine detection + AI        │
│     • Calculate summaries           │
│     • Format response               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Image Annotator                    │
│  • Draw bounding boxes              │
│  • Draw segmentation masks          │
│  • Add labels & summary             │
│  • Encode to base64                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Response                           │
│  {                                  │
│    analysis: {...},                 │
│    annotated_image: "base64...",    │
│    ...                              │
│  }                                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Your System    │
│  (Display/Save) │
└─────────────────┘
```

---

## 🚀 How to Use in Your System

### 1. Start the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export ROBOFLOW_API_KEY="your_roboflow_key"
export USE_OBJECT_DETECTION="true"
export DETECTION_BACKEND="roboflow"

# Run server
python main.py
```

Server starts at: `http://localhost:8000`

### 2. Send Base64 Image

**Python:**
```python
import requests
import base64

# Encode image
with open("palm_tree.jpg", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')

# Send request
response = requests.post(
    "http://localhost:8000/api/v1/analyze-base64",
    json={
        "file": f"data:image/jpeg;base64,{base64_image}",
        "filename": "palm_tree.jpg",
        "lat": "1.3521",
        "long": "103.8198",
        "uuid": "user-123"
    }
)

result = response.json()
```

**JavaScript:**
```javascript
// From file input
const file = document.getElementById('fileInput').files[0];
const reader = new FileReader();

reader.onload = async () => {
  const base64Image = reader.result; // Includes data URI prefix
  
  const response = await fetch('http://localhost:8000/api/v1/analyze-base64', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      file: base64Image,
      filename: file.name,
      lat: "1.3521",
      long: "103.8198",
      uuid: "user-123"
    })
  });
  
  const result = await response.json();
  
  // Display annotated image
  document.getElementById('result').src = 
    `data:image/jpeg;base64,${result.annotated_image}`;
};

reader.readAsDataURL(file);
```

### 3. Display Results

**Show Annotated Image:**
```html
<img id="result" src="" />

<script>
// From API response
document.getElementById('result').src = 
  `data:image/jpeg;base64,${result.annotated_image}`;
</script>
```

**Show Analysis:**
```javascript
console.log(`Total Bunches: ${result.analysis.total_bunches}`);
console.log(`Ripe: ${result.analysis.stage_summary.ripe}`);
console.log(`Recommendations:`, result.analysis.recommendations);

// Display each bunch
result.analysis.bunches.forEach(bunch => {
  console.log(`Bunch #${bunch.id}: ${bunch.stage} (${bunch.confidence})`);
});
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# AWS Bedrock (Claude AI)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Object Detection
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
DETECTION_CONFIDENCE=0.40

# Roboflow
ROBOFLOW_API_KEY=your_api_key
ROBOFLOW_MODEL_ID=oil-palm-segmentation1
ROBOFLOW_VERSION=1
```

### Detection Backends

| Backend | When to Use | Configuration |
|---------|-------------|---------------|
| `roboflow` | Production (recommended) | Requires API key + model ID |
| `yolo` | Local processing | Requires model weights file |
| `mock` | Testing without model | No configuration needed |
| `custom` | Your own API | Requires endpoint URL |

---

## 📈 Performance Metrics

| Metric | Typical Value |
|--------|---------------|
| Processing Time | 2-4 seconds |
| Accuracy | 85-95% |
| Max Image Size | 10MB (before base64) |
| Recommended Resolution | 2000x1500 to 4000x3000 |
| Base64 Overhead | +33% file size |
| Concurrent Requests | Depends on server resources |

---

## 🐛 Troubleshooting

### Common Issues

**1. "Invalid base64 encoding"**
- Check that base64 string is properly formatted
- Remove any whitespace or newlines
- Ensure data URI prefix is correct

**2. "No detections from object detector"**
- Check Roboflow API key is valid
- Verify image quality (not too blurry)
- Lower `DETECTION_CONFIDENCE` threshold

**3. "Annotated image not returned"**
- Check `return_annotated_image: true` in request
- Verify analysis succeeded (`success: true`)
- Check server logs for errors

**4. Slow processing**
- Resize images before sending (max 4000x3000)
- Check AWS region (use closest)
- Ensure adequate server resources

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `routes/analysis.py` | API endpoints |
| `services/hybrid_analyzer.py` | Main analysis logic |
| `services/image_annotator.py` | Draw bounding boxes |
| `services/object_detector.py` | Detection backends |
| `services/bedrock_service.py` | Claude AI integration |
| `models/schemas.py` | Data models |
| `config/settings.py` | Configuration |
| `BASE64_API_GUIDE.md` | Detailed API docs |
| `test_base64_api.py` | Test script |

---

## ✅ Testing

```bash
# Test with sample image
python test_base64_api.py oilpalm_samples/sample1.jpg

# Expected output:
# ✓ Loaded image: 2847321 bytes
# ✓ Encoded to base64: 3796428 characters
# 📤 Sending request to API...
# ✅ Analysis SUCCESS
# 📊 Total Bunches: 3
# 🖼️ Annotated image saved: annotated_sample1.jpg
```

---

## 🎓 Summary

**You Send:**
- JSON with base64 image
- GPS coordinates
- User UUID

**You Get:**
- Analysis results (bunches, stages, health)
- Recommendations for harvest
- Annotated image with bounding boxes
- All as JSON response

**Key Benefits:**
- ✅ Simple JSON format (easy to integrate)
- ✅ Precise bounding boxes from Roboflow
- ✅ Intelligent analysis from Claude AI
- ✅ Visual feedback with annotated images
- ✅ Production-ready with proper error handling

---

For more details, see `BASE64_API_GUIDE.md` or test with `test_base64_api.py`.

