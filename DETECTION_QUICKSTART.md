# Quick Setup Examples for Object Detection

## 1. Install YOLO (Recommended for Local Detection)

```bash
pip install ultralytics
```

Then update `.env`:
```env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=yolo
YOLO_MODEL_PATH=yolov8n.pt
YOLO_USE_API=false
```

Test:
```bash
python tests/test_with_samples.py 1 --viz
```

---

## 2. Setup Roboflow (Cloud API)

```bash
pip install roboflow
```

Get API key from https://roboflow.com → Settings → API

Update `.env`:
```env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
ROBOFLOW_API_KEY=your_api_key_here
ROBOFLOW_MODEL_ID=workspace/project-name
ROBOFLOW_VERSION=1
```

Test:
```bash
python tests/test_with_samples.py 1 --viz
```

---

## 3. Use Custom API

Update `.env`:
```env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=custom
CUSTOM_DETECTION_URL=https://your-api.com/detect
CUSTOM_DETECTION_API_KEY=your_key  # optional
```

Test:
```bash
python tests/test_with_samples.py 1 --viz
```

---

## Environment Variables Reference

Create/edit `.env` file in project root:

```env
# AWS Credentials (required)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
SONNET_INFERENCE_PROFILE_ARN=your_inference_profile_arn

# Object Detection (optional)
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=mock  # Options: mock, yolo, roboflow, custom
DETECTION_CONFIDENCE=0.25

# YOLO Configuration (if using YOLO)
YOLO_MODEL_PATH=yolov8n.pt
YOLO_USE_API=false
# YOLO_API_KEY=  # Only if using Ultralytics HUB

# Roboflow Configuration (if using Roboflow)
# ROBOFLOW_API_KEY=your_roboflow_key
# ROBOFLOW_MODEL_ID=workspace/project
# ROBOFLOW_VERSION=1

# Custom API Configuration (if using custom endpoint)
# CUSTOM_DETECTION_URL=https://api.example.com/detect
# CUSTOM_DETECTION_API_KEY=your_custom_api_key
```

---

## Testing Each Backend

### Mock (Default - No Setup)
```bash
# Already works! No installation needed
python tests/test_with_samples.py 1 --viz
```

### YOLO
```bash
# Install
pip install ultralytics

# Set in .env
# DETECTION_BACKEND=yolo

# Test
python tests/test_with_samples.py 1 --viz
```

### Roboflow
```bash
# Install
pip install roboflow

# Set in .env with your credentials
# DETECTION_BACKEND=roboflow
# ROBOFLOW_API_KEY=...

# Test
python tests/test_with_samples.py 1 --viz
```

### Custom API
```bash
# No extra installation needed (uses httpx)

# Set in .env with your endpoint
# DETECTION_BACKEND=custom
# CUSTOM_DETECTION_URL=...

# Test
python tests/test_with_samples.py 1 --viz
```

---

## Verifying Detection Works

After running the test, check these files:

1. **`debug_annotated_processed.jpg`** - Shows detection on 1800x2400 processed image
   - ✅ Boxes should align with actual bunches
   - ✅ No boxes on ground/vegetation
   
2. **`annotated_sample1.jpg`** - Shows detection on full 3072x4096 original image
   - ✅ Boxes should scale correctly to original size

If boxes are accurate on `debug_annotated_processed.jpg`, the system works! 🎉

---

## Common Issues

### "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### "No module named 'roboflow'"
```bash
pip install roboflow
```

### "API authentication failed"
- Check API keys in `.env`
- Verify no extra spaces/quotes
- Ensure `.env` is in project root

### "No detections found"
- Lower `DETECTION_CONFIDENCE` (try 0.10)
- Check if image has actual oil palm bunches
- Verify model is loaded correctly

### YOLO downloading models
First run downloads model (~6MB for yolov8n). This is normal.

---

## Performance Comparison

| Backend | Speed | Accuracy | Setup | Cost |
|---------|-------|----------|-------|------|
| Mock | ⚡⚡⚡ Instant | ❌ N/A | ✅ None | Free |
| YOLO (pretrained) | ⚡⚡ ~0.5s | ⭐⭐⭐ Good | Easy | Free |
| YOLO (custom) | ⚡⚡ ~0.5s | ⭐⭐⭐⭐⭐ Excellent | Hard | Free |
| Roboflow | ⚡ ~1-2s | ⭐⭐⭐⭐ Very Good | Easy | $49/mo |
| Custom API | ⚡ Varies | ⭐⭐⭐⭐⭐ Varies | Easy | Varies |

---

## Next Steps

1. Choose a backend and install it
2. Update `.env` with configuration
3. Run test: `python tests/test_with_samples.py 1 --viz`
4. Check annotated images
5. If accurate, deploy to production!

For detailed training guides, see `DETECTION_SETUP.md`.


