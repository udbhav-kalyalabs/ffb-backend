# 🚀 GCP GPU Training Setup

**Status:** Ready to train on Google Cloud  
**GPU:** Tesla T4 (or equivalent)  
**Cost:** ~$0.35/hr with preemptible instance  
**Training Time:** 4-6 hours

---

## Step 1: Create GCP VM with GPU

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

**Note:** Remove `--preemptible` for on-demand (more expensive but stable)

---

## Step 2: SSH into VM

```bash
gcloud compute ssh ffb-training --zone=us-central1-a
```

---

## Step 3: Upload Training Data

### Option A: Using gsutil (recommended)

```bash
# On your local machine:
gsutil -m cp -r data/yolo_dataset gs://YOUR-BUCKET-NAME/ffb-data/
gsutil -m cp data/dataset.yaml gs://YOUR-BUCKET-NAME/ffb-data/
gsutil -m cp data/train_yolo.py gs://YOUR-BUCKET-NAME/ffb-data/
```

### Option B: Direct SCP

```bash
# Upload entire data folder
gcloud compute scp --recurse data/ ffb-training:/root/ --zone=us-central1-a
```

---

## Step 4: Setup Python Environment on VM

```bash
# SSH into VM first
gcloud compute ssh ffb-training --zone=us-central1-a

# Inside VM:
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics opencv-python pillow numpy pyyaml
```

---

## Step 5: Verify Data Structure on VM

```bash
# Inside VM, verify structure:
ls -la /root/data/yolo_dataset/images/
ls -la /root/data/yolo_dataset/labels/
cat /root/data/dataset.yaml
```

Should show:
```
images/train/  (55 images)
images/val/    (8 images)
labels/train/  (55 .txt files)
labels/val/    (8 .txt files)
dataset.yaml
```

---

## Step 6: Start Training

```bash
# Inside VM:
cd /root
python data/train_yolo.py
```

Expected output:
```
🚀 Starting YOLOv8 Training for FFB Detection
📦 Loading YOLOv8 Large model...
⚙️  Training Configuration:
  Model: YOLOv8 Large
  Epochs: 100
  Batch Size: 16
  ...
```

Training will take **4-6 hours**. Monitor progress:
```bash
# Watch logs in real-time
tail -f /root/runs/detect/ffb_yolov8l_v1/train.log
```

---

## Step 7: Download Trained Model

Once training completes:

```bash
# From local machine:
gcloud compute scp ffb-training:/root/runs/detect/ffb_yolov8l_v1/weights/best.pt \
  weights/yolov8l_ffb_v1.pt \
  --zone=us-central1-a
```

Or via gsutil:
```bash
gsutil cp gs://YOUR-BUCKET-NAME/ffb-data/runs/detect/ffb_yolov8l_v1/weights/best.pt weights/
```

---

## 📊 Troubleshooting

| Issue | Solution |
|-------|----------|
| `cuda out of memory` | Reduce batch size: change `batch=16` to `batch=8` in train_yolo.py |
| `dataset.yaml not found` | Check file exists on VM: `cat /root/data/dataset.yaml` |
| `No images found` | Verify structure: `ls -la /root/data/yolo_dataset/images/train/` |
| `GPU not detected` | Run: `nvidia-smi` on VM to check GPU availability |

---

## 🎯 Expected Results

After training:
- **mAP50:** > 0.75 (target)
- **mAP50-95:** > 0.50
- **Model file:** `best.pt` (~200MB)

---

## ⏹️ Stop/Delete VM After Training

```bash
# Stop VM (keeps data, cheaper):
gcloud compute instances stop ffb-training --zone=us-central1-a

# Delete VM (removes everything):
gcloud compute instances delete ffb-training --zone=us-central1-a
```

---

**Ready? Follow steps 1-6 and let me know when training starts!** 🚀
