# 🚀 PHASE 1: Data Annotation & Model Training - Implementation Guide

**Status:** ✅ Ready to Start  
**Ground Truth Validated:** 16 FFB across 8 trees  
**GPU Provider:** Google Cloud (recommended for cost)  
**Annotation Tool:** Label Studio  
**Estimated Duration:** 1-2 weeks (mostly manual annotation time)

---

## 📋 Phase 1 Tasks Breakdown

| Task | Time | Status |
|------|------|--------|
| Set up Label Studio locally | 30 min | ⏳ TODO |
| Prepare 64 images | 15 min | ⏳ TODO |
| Annotate bounding boxes (FFB) | 8-10 hours | ⏳ TODO |
| Export annotations to YOLO format | 15 min | ⏳ TODO |
| Set up Google Cloud GPU VM | 30 min | ⏳ TODO |
| Create training dataset | 30 min | ⏳ TODO |
| Train YOLOv8 model on GCP | 4-6 hours | ⏳ TODO |
| Validate on T8 (test set) | 1 hour | ⏳ TODO |

---

## 🔧 Step 1: Set Up Label Studio (30 minutes)

### Option A: Docker (Recommended - Easiest)
```bash
# Install Docker if needed
# Then run:
docker run -it -p 8080:8080 -v ~/label-studio-data:/label-studio/data \
  heartexlabs/label-studio:latest
```

### Option B: Direct Installation
```bash
pip install label-studio
label-studio start
```

Then open: `http://localhost:8080`

**Default credentials:**
- Email: `admin@heartex.com`
- Password: `password`

---

## 📊 Step 2: Create Label Studio Project

1. Go to `http://localhost:8080`
2. Click **"Create"** → **"New Project"**
3. **Project Name:** `FFB Detection Phase 1`
4. **Description:** `Annotating 64 images for YOLOv8 training`
5. **Data:** Upload all 64 images from dataset
   - Source: `SG9-RW010SS-10T-40P-070326 - SMTF1/` 
   - 8 trees × 8 images each

---

## 🏷️ Step 3: Configure Annotation Template

Use this XML template in Label Studio:

```xml
<View>
  <Image name="image" value="$image"/>
  <RectangleLabeler name="label" toName="image">
    <Choice value="FFB"/>
    <Choice value="Overripe"/>
  </RectangleLabeler>
</View>
```

**Steps:**
1. After creating project → **"Setup"** tab
2. Choose **"Computer Vision"** → **"Object Detection"**
3. Replace template with XML above
4. Save

---

## ✏️ Step 4: Annotate Images (8-10 hours)

### Your Annotation Task:

For each of 64 images:
1. Open image in Label Studio
2. Draw bounding boxes around each FFB (fruit-bearing branch)
3. Label as **"FFB"** (or **"Overripe"** if clearly overripe - like T7)
4. Save annotation

### Ground Truth to Match:
```
T1: 0 FFB    (no annotations needed)
T2: 0 FFB    (no annotations needed)
T3: 7 FFB    (7 bounding boxes)
T4: 3 FFB    (3 bounding boxes)
T5: 2 FFB    (2 bounding boxes)
T6: 3 FFB    (3 bounding boxes)
T7: 1 FFB    (1 bounding box - overripe)
T8: 0 FFB    (no annotations needed - this is test set)
```

**Total annotations needed: 16 bounding boxes across 64 images**

### Tips for Annotation:
- Be consistent with box size (should tightly fit the fruit bunch)
- Include all visible FFB in the image
- If same FFB appears in multiple images, draw box in each image
- Use different zoom levels to spot small FFBs

---

## 💾 Step 5: Export to YOLO Format

1. After annotating all images → **"Export"** button
2. Select format: **"YOLO"**
3. Download ZIP file
4. Extract to: `data/annotations/`

Expected structure:
```
data/
├── images/
│   ├── train/  (56 images: T1-T7, 8 images each)
│   └── val/    (8 images: T8, for validation)
└── labels/
    ├── train/  (YOLO .txt files)
    └── val/    (YOLO .txt files)
```

---

## ☁️ Step 6: Set Up Google Cloud GPU VM

### Create GCP Project (First Time Only):
1. Go to: https://console.cloud.google.com/
2. Create new project: `FFB-YOLOv8-Training`
3. Enable APIs: **Compute Engine**, **Cloud Storage**

### Create VM with GPU:
```bash
gcloud compute instances create ffb-training \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=50GB \
  --preemptible
```

**Cost estimate:** ~$0.35/hour with preemptible GPU (saves 70% vs on-demand)

### SSH into VM:
```bash
gcloud compute ssh ffb-training --zone=us-central1-a
```

---

## 🎓 Step 7: Train YOLOv8 on GCP

### Install Dependencies:
```bash
# On GCP VM:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics opencv-python pillow numpy
```

### Upload Training Data:
```bash
# On your local machine:
gsutil -m cp -r data/annotations gs://YOUR-BUCKET-NAME/ffb-training/
gsutil -m cp -r SG9-RW010SS-10T-40P-070326\ -\ SMTF1 gs://YOUR-BUCKET-NAME/ffb-training/images/
```

### Create Training Script (`train_yolo.py`):
```python
from ultralytics import YOLO
import yaml

# Create dataset.yaml
dataset_config = {
    'path': '/home/training/data',
    'train': 'images/train',
    'val': 'images/val',
    'nc': 1,  # 1 class: FFB
    'names': {0: 'FFB'}
}

with open('/home/training/dataset.yaml', 'w') as f:
    yaml.dump(dataset_config, f)

# Load model
model = YOLO('yolov8l.pt')  # Large model

# Train
results = model.train(
    data='/home/training/dataset.yaml',
    epochs=100,
    imgsz=640,
    device=0,  # GPU
    patience=10,  # Early stopping
    batch=16,
    save=True,
    project='runs/detect',
    name='ffb_v1'
)

# Validate
metrics = model.val()
print(f"mAP50: {metrics.box.map50}")
print(f"mAP50-95: {metrics.box.map}")
```

### Run Training:
```bash
# On GCP VM:
python train_yolo.py
```

Expected output: `runs/detect/ffb_v1/weights/best.pt` (trained model)

---

## ✅ Step 8: Validate Results

### Download Model Locally:
```bash
gsutil cp gs://YOUR-BUCKET-NAME/ffb-training/runs/detect/ffb_v1/weights/best.pt ./weights/
```

### Create Validation Script (`validate_model.py`):
```python
from ultralytics import YOLO
from services.multiview_processor import MultiViewProcessor
from config.camera_calibration import iPhone15Calibration

# Load trained model
model = YOLO('weights/best.pt')

# Load calibration
calib = iPhone15Calibration()

# Create processor
processor = MultiViewProcessor(
    model=model,
    calibration=calib,
    clustering_threshold=0.15
)

# Test on each tree (except T8 which was in test set)
for tree_id in ['T3', 'T4', 'T5', 'T6', 'T7']:
    predictions = processor.process_tree(tree_id)
    print(f"{tree_id}: Predicted {len(predictions)} FFB")

# Validate on T8 (test set - should be close to 0)
t8_predictions = processor.process_tree('T8')
print(f"T8 (test): Predicted {len(t8_predictions)} FFB (expected ~0)")
```

---

## 📈 Success Criteria

✅ Phase 1 is complete when:
- [ ] All 64 images annotated
- [ ] Annotations exported to YOLO format
- [ ] YOLOv8 Large model trained on GCP
- [ ] Validation metrics: mAP50 > 0.75
- [ ] Test set (T8): ≈0 false positives

---

## 📅 Timeline Estimate

```
Week 1:
  Day 1-2: Set up Label Studio (1 hour)
  Day 2-5: Annotate 64 images (40-50 hours over week)
  Day 5-6: Export & prepare data (1 hour)

Week 2:
  Day 1: Set up GCP VM (30 min)
  Day 1-3: Train YOLOv8 (4-6 hours runtime, but spread over days)
  Day 3-5: Validate & iterate if needed (2-3 hours)

Total human time: ~8-12 hours
Total compute time: ~5-7 hours
```

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Label Studio won't connect | Check `http://localhost:8080` and verify Docker running |
| Images not uploading | Reduce image resolution or upload batch by batch |
| GCP quota exceeded | Request quota increase or use smaller machine type |
| Training OOM error | Reduce batch size to 8 |
| Low validation accuracy | Annotate more carefully, ensure tight bounding boxes |

---

## 🎯 Next Steps

**Immediate (Today):**
1. Set up Label Studio (Docker is easiest)
2. Create project & import 64 images
3. Start annotating (do a few test images first)

**This Week:**
4. Complete all 64 image annotations
5. Export to YOLO format
6. Set up GCP VM

**Next Week:**
7. Upload data to GCP
8. Run training
9. Validate results

---

## 📞 Questions?

If anything is unclear:
- Label Studio docs: https://labelstud.io/
- YOLO format: https://docs.ultralytics.com/datasets/detect/
- GCP setup: https://cloud.google.com/compute/docs/instances/create-start-instance

**Once training is complete → Phase 2 begins (pipeline integration)**

---

**Created:** 2026-04-18  
**Updated:** 2026-04-18  
**Status:** Ready to Start ✅
