# Phase 1 Quick Start Guide: Data Annotation & YOLOv8 Training

## 🎯 Goal
Create a trained YOLOv8 model on your 8 trees that can detect FFB with ≥92% accuracy.

---

## Step 1️⃣: Install Label Studio (Recommended)

### Option A: Docker (Easiest)
```bash
docker run -it -p 8080:8080 -v $(pwd)/label-studio:/label-studio heartexlabs/label-studio:latest
```

Then open: `http://localhost:8080`

### Option B: Python Installation
```bash
pip install label-studio
label-studio start
```

---

## Step 2️⃣: Setup Annotation Project

**In Label Studio Web UI:**

1. Click "Create" → New Project
2. Name: "FFB Detection"
3. Select "Computer Vision" → "Object Detection"
4. Upload all 64 images:
   - T1: T1_1A.jpg, T1_1B.jpg, T1_2A.jpg, T1_2B.jpg, T1_3A.jpg, T1_3B.jpg, T1_4A.jpg, T1_4B.jpg
   - T2-T8: Similar structure
5. Label: Create one class called "bunch"
6. Start annotating!

---

## Step 3️⃣: Annotate Images

**For each image:**
1. Click "Label" to open image
2. Use rectangle tool to draw box around each FFB
3. Label as "bunch"
4. Keyboard shortcuts:
   - `R` = Rectangle tool
   - `D` = Done
   - `N` = Next image

**Annotation tips:**
- Draw tight boxes around each bunch
- Include entire bunch, not just the center
- Don't worry about perfect precision (YOLO is forgiving)
- Typical time: 7-10 minutes per image

**Expected output per tree:** ~50-80 bunches total across 8 images

---

## Step 4️⃣: Export to YOLO Format

**In Label Studio:**
1. Go to "Export" tab
2. Select "YOLO" format
3. Download `.zip` file
4. Extract to your project folder

**Structure after extraction:**
```
yolo_export/
├── images/
│   ├── T1_1A.jpg
│   ├── T1_1B.jpg
│   └── ... (all 64 images)
└── labels/
    ├── T1_1A.txt
    ├── T1_1B.txt
    └── ... (all 64 txt files)
```

---

## Step 5️⃣: Organize Training Dataset

**Create folder structure:**
```bash
cd ~/ffb-dataset

# Create directories
mkdir -p images/{train,val,test}
mkdir -p labels/{train,val,test}

# Copy files (70/15/15 split)
# T1-T6: Training (48 images)
cp yolo_export/images/T[1-6]_*.jpg images/train/
cp yolo_export/labels/T[1-6]_*.txt labels/train/

# T7: Validation (8 images)
cp yolo_export/images/T7_*.jpg images/val/
cp yolo_export/labels/T7_*.txt labels/val/

# T8: Test (8 images)
cp yolo_export/images/T8_*.jpg images/test/
cp yolo_export/labels/T8_*.txt labels/test/
```

**Create `dataset.yaml`:**
```yaml
path: /full/path/to/ffb-dataset
train: images/train
val: images/val
test: images/test

nc: 1
names: ['bunch']
```

---

## Step 6️⃣: Setup YOLOv8 Training Environment

**Install dependencies:**
```bash
pip install ultralytics opencv-python matplotlib torch torchvision
```

**Check GPU availability:**
```python
import torch
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

---

## Step 7️⃣: Create Training Notebook

**File: `notebooks/train_yolov8.ipynb`**

```python
# Cell 1: Imports
from ultralytics import YOLO
import matplotlib.pyplot as plt
from pathlib import Path

# Cell 2: Load model
model = YOLO('yolov8l.pt')  # Load pretrained YOLOv8 Large

# Cell 3: Train
results = model.train(
    data='path/to/dataset.yaml',  # CHANGE THIS PATH
    epochs=100,
    imgsz=1280,
    batch=16,
    device=0,
    patience=20,
    save=True,
    project='runs/detect',
    name='ffb_v1',
    # Augmentation
    augment=True,
    mosaic=1.0,
    mixup=0.1,
    fliplr=0.5,
    scale=0.5,
    # Optimizer
    optimizer='SGD',
    momentum=0.937,
    weight_decay=0.0005,
)

# Cell 4: Validate on test set
metrics = model.val()
print(f"mAP@0.5: {metrics.box.map50}")
print(f"mAP@0.5:0.95: {metrics.box.map}")

# Cell 5: Test predictions on sample image
results = model.predict(
    source='path/to/sample_image.jpg',
    conf=0.25,
    save=True
)

# Cell 6: Export best model
best_model = YOLO('runs/detect/ffb_v1/weights/best.pt')
print("Model saved to: runs/detect/ffb_v1/weights/best.pt")
```

---

## Step 8️⃣: Run Training

**In Jupyter or Python:**

```bash
# If using Jupyter
jupyter notebook notebooks/train_yolov8.ipynb

# Or directly
python -c "
from ultralytics import YOLO
model = YOLO('yolov8l.pt')
results = model.train(data='dataset.yaml', epochs=100, imgsz=1280, batch=16, device=0)
"
```

**What to expect:**
- Training time: 4-6 hours on RTX 3090 (or similar GPU)
- Progress shown in console with live metrics
- Saves checkpoints every 10 epochs
- Best weights saved to `runs/detect/ffb_v1/weights/best.pt`

**Output files:**
```
runs/detect/ffb_v1/
├── weights/
│   ├── best.pt       ← Use this!
│   ├── last.pt
│   └── ...
├── results.csv       ← Training metrics
├── confusion_matrix.png
├── val_batch*.jpg
└── ...
```

---

## Step 9️⃣: Validate Results

**Check training metrics:**
```python
import pandas as pd

# Load training results
results = pd.read_csv('runs/detect/ffb_v1/results.csv')

# Plot key metrics
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].plot(results['epoch'], results['metrics/mAP50(B)'])
axes[0, 0].set_title('mAP@0.5')
axes[0, 0].set_xlabel('Epoch')

axes[0, 1].plot(results['epoch'], results['train/loss'])
axes[0, 1].set_title('Training Loss')
axes[0, 1].set_xlabel('Epoch')

axes[1, 0].plot(results['epoch'], results['val/box_loss'])
axes[1, 0].set_title('Validation Loss')
axes[1, 0].set_xlabel('Epoch')

axes[1, 1].plot(results['epoch'], results['metrics/precision(B)'])
axes[1, 1].set_title('Precision')
axes[1, 1].set_xlabel('Epoch')

plt.tight_layout()
plt.savefig('training_summary.png')
plt.show()
```

**Success criteria:**
- ✅ mAP@0.5 ≥ 0.92
- ✅ mAP@0.5:0.95 ≥ 0.85
- ✅ Precision ≥ 0.90
- ✅ Recall ≥ 0.90

---

## 🔟 Test on Held-Out Tree (T8)

**Validate accuracy vs ground truth:**

```python
from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO('runs/detect/ffb_v1/weights/best.pt')

# Get all T8 images
tree_images = ['T8_1A.jpg', 'T8_1B.jpg', 'T8_2A.jpg', 'T8_2B.jpg', 
               'T8_3A.jpg', 'T8_3B.jpg', 'T8_4A.jpg', 'T8_4B.jpg']

total_detections = 0

for img_path in tree_images:
    results = model.predict(source=img_path, conf=0.25, verbose=False)
    num_bunches = len(results[0].boxes)
    total_detections += num_bunches
    print(f"{img_path}: {num_bunches} bunches detected")

print(f"\nTotal detections (raw): {total_detections}")
print(f"Ground truth (manual count): ???")  # You fill this in
```

---

## 📊 Expected Results

After training on 6 trees (~48 images with ~40-50 bunches each = ~2,400 bunches):

```
Training metrics:
  mAP@0.5:       0.93 ± 0.02
  mAP@0.5:0.95:  0.87 ± 0.03
  Precision:     0.92 ± 0.02
  Recall:        0.91 ± 0.03

Inference speed: 1.8s per image

Validation (T7):  36 bunches detected
Ground truth:     35 bunches → 2.9% error ✓

Test (T8):        42 bunches detected  
Ground truth:     41 bunches → 2.4% error ✓
```

---

## ⚠️ Troubleshooting

### Problem: "CUDA out of memory"
**Solution:** Reduce batch size
```python
results = model.train(..., batch=8, ...)  # Instead of 16
```

### Problem: "File not found: dataset.yaml"
**Solution:** Use absolute path
```python
results = model.train(data='/full/path/to/dataset.yaml', ...)
```

### Problem: "mAP is too low (< 0.85)"
**Solution:** 
- Train for more epochs: `epochs=150`
- Improve annotations (ensure all bunches are labeled)
- Use augmentation: `augment=True, mosaic=1.0`

### Problem: "Training is very slow"
**Solution:**
- Check GPU is being used: `nvidia-smi`
- Reduce image size: `imgsz=960` (instead of 1280)
- Reduce batch size: `batch=8` (instead of 16)

---

## ✅ Checklist Before Moving to Phase 2

- [ ] All 64 images annotated in Label Studio
- [ ] Annotations exported to YOLO format (.txt files)
- [ ] Dataset split: 48 train / 8 val / 8 test
- [ ] `dataset.yaml` created and paths correct
- [ ] YOLOv8 training completed (100 epochs)
- [ ] Validation metrics ≥ success criteria
- [ ] `best.pt` model saved and tested
- [ ] Ground truth comparison on T8: error ≤ 3%

---

## 🚀 Once Training Complete

Move to **Phase 2: Multi-View Processing Pipeline**

Your trained model (`best.pt`) will be used by:
1. `services/multiview_processor.py` 
2. `services/triangulation.py`
3. `config/camera_calibration.py`

To run the full pipeline:
```python
from services.multiview_processor import MultiViewProcessor
import cv2

processor = MultiViewProcessor(
    model_path='runs/detect/ffb_v1/weights/best.pt'
)

tree_images = {
    '1A': cv2.imread('T1_1A.jpg'),
    '1B': cv2.imread('T1_1B.jpg'),
    # ... 6 more
}

result = processor.process_tree(tree_images, tree_id='T1')
print(f"Unique bunches: {result['unique_bunch_count']}")
```

---

**Estimated timeline:**
- Annotation: 2-3 days (64 images × 7-10 min each)
- Training: 1 day (4-6 hours GPU time)
- Validation: 1-2 hours

**Total Phase 1: ~4 days**

Good luck! 🚀
