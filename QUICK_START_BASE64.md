# Quick Start: Base64 Image Analysis

Get started with base64 image analysis in 5 minutes!

## 1️⃣ Start the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_ACCESS_KEY_ID="your_aws_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret"
export ROBOFLOW_API_KEY="your_roboflow_key"
export USE_OBJECT_DETECTION="true"
export DETECTION_BACKEND="roboflow"

# Run the server
python main.py
```

Server will start at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

---

## 2️⃣ Test with Sample Image

```bash
# Quick test with provided samples
python test_base64_api.py oilpalm_samples/sample1.jpg
```

**Expected Output:**
```
✓ Loaded image: 2847321 bytes
✓ Encoded to base64: 3796428 characters
📤 Sending request to API...
✅ Analysis SUCCESS

📊 ANALYSIS SUMMARY:
   Total Bunches: 3
   Detection Confidence: 85.0%
   Processing Time: 2847ms

🌴 STAGE BREAKDOWN:
   🟢 Young:    0
   🟡 Mature:   1
   🟠 Ripe:     1
   🔴 Overripe: 1

🖼️ ANNOTATED IMAGE:
   Saved to: annotated_sample1.jpg
```

---

## 3️⃣ Use in Your Code

### Python

```python
import requests
import base64

# 1. Load and encode image
with open("palm_tree.jpg", "rb") as f:
    image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

# 2. Send to API
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

# 3. Get results
print(f"Total bunches: {result['analysis']['total_bunches']}")
print(f"Ripe bunches: {result['analysis']['stage_summary']['ripe']}")

# 4. Save annotated image
if result['annotated_image']:
    annotated_bytes = base64.b64decode(result['annotated_image'])
    with open("result.jpg", "wb") as f:
        f.write(annotated_bytes)
```

### JavaScript

```javascript
// 1. Get file from input
const fileInput = document.getElementById('imageFile');
const file = fileInput.files[0];

// 2. Convert to base64
const reader = new FileReader();
reader.readAsDataURL(file);

reader.onload = async () => {
  // 3. Send to API
  const response = await fetch('http://localhost:8000/api/v1/analyze-base64', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      file: reader.result,  // Already includes data URI prefix
      filename: file.name,
      lat: "1.3521",
      long: "103.8198",
      uuid: "user-123"
    })
  });
  
  const result = await response.json();
  
  // 4. Display annotated image
  document.getElementById('resultImage').src = 
    `data:image/jpeg;base64,${result.annotated_image}`;
  
  // 5. Show analysis
  document.getElementById('totalBunches').textContent = 
    result.analysis.total_bunches;
};
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "file": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "filename": "palm_tree.jpg",
    "lat": "1.3521",
    "long": "103.8198",
    "uuid": "user-123"
  }'
```

---

## 4️⃣ Understand the Response

```json
{
  "success": true,
  "analysis": {
    "total_bunches": 3,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.92,
        "bounding_box": {
          "x_min": 1000,
          "y_min": 700,
          "x_max": 1400,
          "y_max": 1050
        }
      }
    ],
    "stage_summary": {
      "young": 0,
      "mature": 1,
      "ripe": 1,
      "overripe": 1
    },
    "recommendations": [
      "Harvest overripe bunch immediately"
    ]
  },
  "annotated_image": "/9j/4AAQSkZJRgABA..."
}
```

**Key Fields:**
- `analysis.total_bunches` - Number of fruit bunches detected
- `analysis.bunches[].stage` - "young", "mature", "ripe", or "overripe"
- `analysis.bunches[].bounding_box` - Pixel coordinates
- `analysis.recommendations` - Harvest advice
- `annotated_image` - Image with bounding boxes drawn (base64)

---

## 5️⃣ Display Results

### Save Annotated Image

**Python:**
```python
import base64

annotated_bytes = base64.b64decode(result['annotated_image'])
with open("result.jpg", "wb") as f:
    f.write(annotated_bytes)
```

**JavaScript:**
```javascript
// Display in browser
const img = document.getElementById('result');
img.src = `data:image/jpeg;base64,${result.annotated_image}`;
```

### Show Analysis Summary

```javascript
const analysis = result.analysis;

console.log(`Total Bunches: ${analysis.total_bunches}`);
console.log(`Ripe: ${analysis.stage_summary.ripe}`);
console.log(`Mature: ${analysis.stage_summary.mature}`);
console.log(`Young: ${analysis.stage_summary.young}`);
console.log(`Overripe: ${analysis.stage_summary.overripe}`);

analysis.recommendations.forEach(rec => {
  console.log(`• ${rec}`);
});
```

---

## 🎨 Annotated Image Features

The returned image includes:
- ✅ **Bounding boxes** around each bunch (colored by ripeness)
- ✅ **Labels** with ID, stage, and confidence
- ✅ **Segmentation masks** (semi-transparent overlays)
- ✅ **Summary panel** with total counts
- ✅ **Color coding**: 🟢 Young, 🟡 Mature, 🟠 Ripe, 🔴 Overripe

---

## 🔧 Configuration

### Minimum Required (.env file)

```bash
# AWS Credentials (for Claude AI)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=abc123...
AWS_REGION=us-east-1

# Roboflow (for object detection)
ROBOFLOW_API_KEY=your_key_here
ROBOFLOW_MODEL_ID=oil-palm-segmentation1
ROBOFLOW_VERSION=1

# Enable detection
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
```

### Optional Settings

```bash
# Confidence threshold (lower = more detections)
DETECTION_CONFIDENCE=0.40

# Image processing
MAX_IMAGE_SIZE_MB=10
MAX_IMAGE_DIMENSION=2400
```

---

## 📚 Next Steps

- **Full API Reference**: See `BASE64_API_GUIDE.md`
- **Integration Guide**: See `BASE64_INTEGRATION_SUMMARY.md`
- **API Documentation**: Visit `http://localhost:8000/docs`
- **Test Endpoint**: Try with your own images using `test_base64_api.py`

---

## ❓ Troubleshooting

**Server won't start?**
- Check AWS credentials are set
- Run `pip install -r requirements.txt`
- Check Python version (≥3.8)

**No detections?**
- Verify Roboflow API key
- Try lowering `DETECTION_CONFIDENCE` to 0.3
- Check image quality (not too blurry)

**Slow processing?**
- Resize images before sending (max 4000x3000)
- Use closest AWS region
- Check internet connection

**Import errors?**
- Install all dependencies: `pip install -r requirements.txt`
- For Roboflow: `pip install roboflow`
- For OpenCV: `pip install opencv-python numpy`

---

## 💡 Tips

1. **Image Size**: Keep images under 5MB for best performance
2. **Resolution**: 2000-4000px width works best
3. **Format**: JPEG or PNG both supported
4. **Lighting**: Clear, well-lit images give better results
5. **Angle**: Front-facing view of palm tree recommended

---

## 🚀 Ready to Go!

That's it! You now have:
- ✅ API server running
- ✅ Base64 image analysis working
- ✅ Annotated images with bounding boxes
- ✅ Integration examples for Python & JavaScript

For more details, check the full documentation in `BASE64_API_GUIDE.md`.

