# AgriAI Quick Start Guide

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify your `.env` file** (already configured):
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_REGION=us-east-1
   ```

## Run the API Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

Visit `http://localhost:8000/docs` for interactive API documentation.

## Test with Sample Images

### Test Single Image
```bash
python tests/test_with_samples.py 1
```

This will analyze `oilpalm_samples/sample1.jpg` and display results.

### Test All Samples
```bash
python tests/test_with_samples.py all
```

This will analyze all 10 sample images in the `oilpalm_samples/` directory.

## API Usage Examples

### Using curl
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "image=@oilpalm_samples/sample1.jpg" \
  -F "crop_type=oil_palm" \
  -F "min_confidence=0.6"
```

### Using Python
```python
import requests

with open('oilpalm_samples/sample1.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/analyze',
        files={'image': f},
        data={'crop_type': 'oil_palm', 'min_confidence': 0.5}
    )
    result = response.json()
    
    if result['success']:
        print(f"Found {result['analysis']['total_bunches']} bunches")
        for bunch in result['analysis']['bunches']:
            print(f"  - {bunch['stage']} at confidence {bunch['confidence']:.2f}")
```

### Using JavaScript (Frontend)
```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('crop_type', 'oil_palm');
formData.append('min_confidence', '0.5');

fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Total bunches:', data.analysis.total_bunches);
    // Draw bounding boxes using the coordinates
    data.analysis.bunches.forEach(bunch => {
      drawBoundingBox(
        bunch.bounding_box,
        bunch.color_code,
        bunch.stage
      );
    });
  }
});
```

## Understanding the Response

The API returns a detailed JSON response:

```json
{
  "success": true,
  "crop_type": "oil_palm",
  "analysis": {
    "total_bunches": 5,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",           // young, mature, ripe, overripe
        "confidence": 0.92,         // 0.0 to 1.0
        "bounding_box": {
          "x_min": 120,            // Top-left corner
          "y_min": 200,
          "x_max": 250,            // Bottom-right corner
          "y_max": 320,
          "center_x": 185,         // Center point
          "center_y": 260
        },
        "color_code": "#FF0000"    // For visualization
      }
    ],
    "stage_summary": {
      "young": 1,
      "mature": 2,
      "ripe": 2,
      "overripe": 0
    },
    "health_score": 85.5,
    "recommendations": [
      "2 bunches are ripe and ready for harvest"
    ]
  },
  "processing_time_ms": 2450.5
}
```

## Drawing Bounding Boxes

Use the coordinates to draw boxes on your frontend:

```javascript
function drawBoundingBox(box, color, label) {
  const ctx = canvas.getContext('2d');
  
  // Draw rectangle
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.strokeRect(
    box.x_min,
    box.y_min,
    box.x_max - box.x_min,  // width
    box.y_max - box.y_min   // height
  );
  
  // Draw label
  ctx.fillStyle = color;
  ctx.font = '16px Arial';
  ctx.fillText(label, box.x_min, box.y_min - 5);
}
```

## Stage Colors

- **Young** (Green): `#90EE90` - Not ready for harvest
- **Mature** (Orange): `#FFA500` - Approaching harvest time
- **Ripe** (Red): `#FF0000` - Ready for harvest
- **Overripe** (Dark Red): `#8B0000` - Past optimal harvest

## Next Steps

1. Start the server: `python main.py`
2. Test with samples: `python tests/test_with_samples.py 1`
3. Build your frontend to call the API
4. Draw bounding boxes on images using the coordinates

For more details, see the full [README.md](README.md).
