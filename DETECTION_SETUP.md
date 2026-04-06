# Object Detection Setup Guide

This guide explains how to set up different object detection backends for precise bounding box detection.

## Option 1: Mock Detector (Default - For Testing)

**Status**: ✅ Already configured

No setup needed! The mock detector generates realistic dummy boxes for testing the system.

```python
# In .env or config
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=mock
```

**Pros**: 
- No installation
- Fast testing
- No API costs

**Cons**: 
- Not real detection
- Fixed positions

---

## Option 2: YOLO (Ultralytics) - Local Detection

### Installation

```bash
pip install ultralytics
```

### Option A: Use Pre-trained COCO Model (General Objects)

The default YOLOv8 model can detect general objects. While not specifically trained on oil palm, it can detect "fruit" or similar objects.

```python
# In .env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=yolo
YOLO_MODEL_PATH=yolov8n.pt  # nano (fastest), or yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
YOLO_USE_API=false
```

First run will automatically download the model (~6MB for nano).

### Option B: Train Custom YOLO Model for Oil Palm

**1. Prepare Dataset**

Collect and annotate oil palm images:
- Use [Roboflow](https://roboflow.com) for annotation
- Or use [CVAT](https://cvat.org)
- Or [LabelImg](https://github.com/HumanSignal/labelImg)

Format: YOLO format with labels
```
images/
  train/
    image1.jpg
    image2.jpg
  val/
    image3.jpg
labels/
  train/
    image1.txt  # class_id center_x center_y width height (normalized)
    image2.txt
  val/
    image3.txt
```

**2. Create dataset.yaml**

```yaml
path: /path/to/dataset
train: images/train
val: images/val

nc: 4  # number of classes
names: ['young', 'mature', 'ripe', 'overripe']  # or just ['bunch']
```

**3. Train the Model**

```python
from ultralytics import YOLO

# Load a pretrained model
model = YOLO('yolov8n.pt')

# Train
results = model.train(
    data='dataset.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='oil_palm_detector'
)

# Results will be in runs/detect/oil_palm_detector/
```

**4. Use Custom Model**

```python
# In .env
YOLO_MODEL_PATH=/path/to/runs/detect/oil_palm_detector/weights/best.pt
```

### Option C: Use Ultralytics HUB (Cloud Training)

1. Sign up at [Ultralytics HUB](https://hub.ultralytics.com)
2. Upload your dataset
3. Train in the cloud
4. Get API key

```python
# In .env
YOLO_USE_API=true
YOLO_API_KEY=your_api_key_here
```

### Testing YOLO

```bash
python tests/test_with_samples.py 1 --viz
```

---

## Option 3: Roboflow (Cloud Detection API)

### Setup

**1. Sign up for Roboflow**

- Go to [Roboflow](https://roboflow.com)
- Create account (free tier available)

**2. Options:**

#### A. Use Existing Oil Palm Model

Search Roboflow Universe for oil palm models:
- https://universe.roboflow.com
- Search "oil palm" or "palm fruit"
- Copy the model ID

#### B. Train Your Own

1. Upload images to Roboflow
2. Annotate (or auto-annotate)
3. Generate dataset
4. Train model (free GPU hours available)
5. Deploy

**3. Get API Credentials**

```
Workspace ID: your-workspace
Project ID: oil-palm-detection
Version: 1
API Key: xxxxxxxxxxxxx
```

**4. Install Roboflow**

```bash
pip install roboflow
```

**5. Configure**

```python
# In .env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
ROBOFLOW_API_KEY=xxxxxxxxxxxxx
ROBOFLOW_MODEL_ID=your-workspace/oil-palm-detection
ROBOFLOW_VERSION=1
```

**6. Test**

```bash
python tests/test_with_samples.py 1 --viz
```

### Pricing

- Free tier: 1,000 API calls/month
- Pro: $49/month for 10,000 calls
- Enterprise: Custom pricing

---

## Option 4: Custom API Endpoint

If you have an existing detection service (like the one you mentioned), integrate it:

**1. Configure Endpoint**

```python
# In .env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=custom
CUSTOM_DETECTION_URL=https://your-api.com/detect
CUSTOM_DETECTION_API_KEY=your_api_key  # optional
```

**2. API Format Expected**

The API should accept POST request with image file and return:

```json
{
  "success": true,
  "num_detections": 5,
  "detections": [
    {
      "id": 0,
      "bbox": [x_min, y_min, x_max, y_max],  // or [center_x, center_y, width, height]
      "confidence": 0.85,
      "class_id": 0,
      "class_name": "bunch"
    }
  ]
}
```

**3. Modify Custom Detector (if needed)**

Edit `services/object_detector.py` → `CustomAPIDetector` class to match your API's exact format.

---

## Comparison

| Backend | Accuracy | Speed | Cost | Setup |
|---------|----------|-------|------|-------|
| **Mock** | ❌ N/A | ⚡ Instant | ✅ Free | ✅ None |
| **YOLO (Local)** | ⭐⭐⭐ Good | ⚡⚡ Fast | ✅ Free | ⚙️ Medium |
| **YOLO (Trained)** | ⭐⭐⭐⭐⭐ Excellent | ⚡⚡ Fast | ✅ Free | ⚙️⚙️ Complex |
| **Roboflow** | ⭐⭐⭐⭐ Very Good | ⚡ Moderate | 💰 Paid | ✅ Easy |
| **Custom API** | ⭐⭐⭐⭐⭐ Excellent | ⚡ Depends | 💰 Varies | ⚙️ Easy |

---

## Recommendation

**For Production**: 
1. Train custom YOLO model with your oil palm dataset (best accuracy, no ongoing costs)
2. Or use Roboflow if you prefer cloud + want quick setup

**For Development/Testing**:
1. Use Mock detector initially
2. Try pre-trained YOLO (yolov8n.pt) to see if general detection works

---

## Troubleshooting

### YOLO Issues

```bash
# Error: No module named 'ultralytics'
pip install ultralytics

# Error: Model file not found
# First run downloads automatically, ensure internet connection

# Slow detection
# Use smaller model: yolov8n.pt instead of yolov8x.pt
```

### Roboflow Issues

```bash
# Error: No module named 'roboflow'
pip install roboflow

# Error: Authentication failed
# Check API key in Roboflow dashboard

# Error: Model not found
# Verify model ID format: workspace/project
```

### Custom API Issues

```bash
# Error: Connection refused
# Check endpoint URL is accessible

# Error: Response format mismatch
# Edit CustomAPIDetector.detect() to match your API format
```

---

## Next Steps

After setting up detection:

1. Test on sample images:
   ```bash
   python tests/test_with_samples.py 1 --viz
   ```

2. Check `debug_annotated_processed.jpg` - boxes should align with actual bunches

3. If boxes are accurate, you're done! 🎉

4. If boxes need adjustment, fine-tune your detection model

---

## Support

For issues or questions:
- YOLO: https://docs.ultralytics.com
- Roboflow: https://docs.roboflow.com
- This project: Check the codebase or documentation

