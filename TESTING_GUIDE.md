# AgriAI Testing Guide

## Quick Testing Commands

### Option 1: Direct JSON Output (Recommended for Testing)
Get clean JSON output exactly as frontend would receive:

```bash
# Test specific sample with JSON output
python test_json.py 1
python test_json.py 2
python test_json.py 3

# Or using the full command
python tests/test_with_samples.py 1 --json
python tests/test_with_samples.py 2 -j
```

### Option 2: Detailed Console Output
Get verbose output with analysis breakdown:

```bash
# Test specific sample with detailed output
python tests/test_with_samples.py 1
python tests/test_with_samples.py 2

# Test all samples
python tests/test_with_samples.py all
```

## JSON Output Format

The JSON output matches exactly what your frontend will receive from the API:

```json
{
  "success": true,
  "crop_type": "oil_palm",
  "analysis": {
    "total_bunches": 5,
    "detection_confidence": 0.89,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.95,
        "visibility": "fully_visible",
        "size": "large",
        "position": "front-center",
        "bounding_box": {
          "x_min": 720,
          "y_min": 1000,
          "x_max": 1080,
          "y_max": 1300,
          "center_x": 900,
          "center_y": 1150
        },
        "color_code": "#FF0000",
        "description": "Large, fully visible ripe bunch..."
      }
    ],
    "stage_summary": {
      "young": 1,
      "mature": 1,
      "ripe": 3,
      "overripe": 0
    },
    "plant_health": {
      "overall_score": 88.0,
      "frond_condition": "good",
      "bunch_development": "excellent",
      "observations": [...],
      "concerns": [...]
    },
    "recommendations": [...]
  },
  "image_metadata": {
    "width": 1800,
    "height": 2400,
    "analyzed_at": "2026-01-29T04:25:09.429915",
    "file_size_kb": 2033.56
  },
  "processing_time_ms": 24233.04,
  "error": null
}
```

## Available Test Samples

You have 10 oil palm sample images:
- `sample1.jpg` through `sample10.jpg`
- Located in `oilpalm_samples/` directory

## Testing Workflow

### 1. Quick Test (JSON Mode)
```bash
python test_json.py 1
```

This gives you clean JSON to:
- Copy/paste into your frontend
- Validate response structure
- Test frontend parsing logic
- Debug bounding box rendering

### 2. Detailed Analysis (Verbose Mode)
```bash
python tests/test_with_samples.py 1
```

This shows:
- Processing steps
- Detection details
- Plant health breakdown
- Recommendations
- Useful for understanding what the AI found

### 3. Save JSON to File
```bash
# Save for frontend testing
python test_json.py 1 > sample1_response.json
python test_json.py 2 > sample2_response.json

# Then use in your frontend
cat sample1_response.json
```

## Response Fields Explained

### Bunch Object
```json
{
  "id": 1,                          // Sequential ID
  "stage": "ripe",                  // young|mature|ripe|overripe
  "confidence": 0.95,               // 0.0-1.0
  "visibility": "fully_visible",    // Status of detection
  "size": "large",                  // Relative size
  "position": "front-center",       // Location on tree
  "bounding_box": {
    "x_min": 720,                   // Top-left corner
    "y_min": 1000,
    "x_max": 1080,                  // Bottom-right corner
    "y_max": 1300,
    "center_x": 900,                // Center point
    "center_y": 1150
  },
  "color_code": "#FF0000",          // Color for drawing box
  "description": "..."              // Detailed analysis
}
```

### Plant Health Object
```json
{
  "overall_score": 88.0,           // 0-100 health score
  "frond_condition": "good",       // Leaf health
  "bunch_development": "excellent", // Fruit production
  "observations": [                // Positive notes
    "Healthy dark green fronds...",
    "Multiple bunches at various stages..."
  ],
  "concerns": [                    // Issues found
    "Dense frond arrangement...",
    "Some older fronds..."
  ]
}
```

## Frontend Integration Examples

### Using the JSON Response

```javascript
// Parse response
const data = JSON.parse(response);

if (data.success) {
  // Display summary
  console.log(`Found ${data.analysis.total_bunches} bunches`);
  console.log(`Health: ${data.analysis.plant_health.overall_score}/100`);
  
  // Draw bounding boxes
  data.analysis.bunches.forEach(bunch => {
    drawBox(
      bunch.bounding_box.x_min,
      bunch.bounding_box.y_min,
      bunch.bounding_box.x_max,
      bunch.bounding_box.y_max,
      bunch.color_code,
      `${bunch.stage.toUpperCase()} (${(bunch.confidence * 100).toFixed(0)}%)`
    );
  });
  
  // Display recommendations
  data.analysis.recommendations.forEach(rec => {
    addRecommendation(rec);
  });
}
```

### Drawing Bounding Boxes

```javascript
function drawBox(x_min, y_min, x_max, y_max, color, label) {
  const ctx = canvas.getContext('2d');
  
  // Draw rectangle
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.strokeRect(x_min, y_min, x_max - x_min, y_max - y_min);
  
  // Draw label background
  ctx.fillStyle = color;
  ctx.fillRect(x_min, y_min - 25, 180, 25);
  
  // Draw label text
  ctx.fillStyle = 'white';
  ctx.font = 'bold 14px Arial';
  ctx.fillText(label, x_min + 5, y_min - 8);
}
```

## Comparing Results

### Test Multiple Samples
```bash
# Test and compare
python test_json.py 1 > sample1.json
python test_json.py 2 > sample2.json
python test_json.py 3 > sample3.json

# Compare bunch counts
cat sample*.json | grep "total_bunches"
```

### Batch Testing
```bash
# Test all samples at once
python tests/test_with_samples.py all
```

## Expected Results

### Sample 1 (Reference)
- **Total Bunches**: 5
- **Stages**: 3 ripe, 1-2 mature, 0-1 young
- **Detection Confidence**: ~0.85-0.89
- **Processing Time**: ~20-25 seconds
- **Special**: Contains hidden bunches at back (40% and 30% visible)

### Typical Processing Times
- **Small images**: 15-20 seconds
- **Medium images**: 20-25 seconds
- **Large images**: 25-30 seconds

*Note: Processing time includes thorough 5-pass analysis for maximum accuracy*

## Error Handling

If analysis fails, you'll get:
```json
{
  "success": false,
  "error": "Error message here",
  "analysis": null
}
```

Common errors:
- Image too large (>10MB)
- Invalid format (not JPEG/PNG)
- Corrupted image file

## Tips for Testing

1. **Start with JSON mode** - Easiest to work with
2. **Test sample 1 first** - Contains all bunch types and hidden bunches
3. **Save responses** - Keep JSON files for frontend development
4. **Check confidence scores** - Lower confidence = partially visible bunches
5. **Validate coordinates** - Ensure they're within image dimensions
6. **Test error cases** - Try invalid images to test error handling

## Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| Detection Rate | 90-100% of visible bunches |
| Confidence (visible) | 0.85-0.95 |
| Confidence (hidden) | 0.65-0.84 |
| Processing Time | 20-30 seconds |
| Image Resolution | 1800x2400 pixels |
| Base64 Size | <3MB (under 5MB limit) |

## Troubleshooting

### Issue: Slow Processing
**Normal**: 20-30 seconds is expected for thorough analysis
**Solution**: Processing time trades for accuracy (100% detection rate)

### Issue: JSON Parse Error
**Cause**: Using wrong command
**Solution**: Use `python test_json.py 1` or add `--json` flag

### Issue: Bunch Not Detected
**Check**: 
- Is bunch visible in image?
- Is it at least 20% visible?
- Try verbose mode to see what was found

### Issue: Low Confidence Score
**Normal**: Partially visible bunches get 0.65-0.75
**Expected**: System is transparent about visibility challenges

## Next Steps

1. ✅ Test all samples with JSON mode
2. ✅ Validate JSON structure matches your frontend needs
3. ✅ Test bounding box rendering on canvas
4. ✅ Implement error handling for failed analyses
5. ✅ Build UI components based on response structure

---

**Quick Commands Summary:**

```bash
# JSON output (for frontend)
python test_json.py 1

# Detailed output (for analysis)
python tests/test_with_samples.py 1

# Save JSON to file
python test_json.py 1 > response.json

# Test all samples
python tests/test_with_samples.py all
```

Perfect for frontend development and integration testing!
