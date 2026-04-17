#!/usr/bin/env python3
"""
YOLOv8 Training Script for FFB Detection
Run this on Google Cloud VM for GPU training
"""

from ultralytics import YOLO
import os
import sys

def train_yolo():
    """Train YOLOv8 Large model on FFB dataset"""

    print("🚀 Starting YOLOv8 Training for FFB Detection")
    print("=" * 50)

    # Dataset path (assumes data is in /root/data/yolo_dataset on GCP)
    dataset_yaml = '/root/data/yolo_dataset/dataset.yaml'

    # Check if dataset exists
    if not os.path.exists(dataset_yaml):
        print(f"❌ ERROR: Dataset config not found at {dataset_yaml}")
        print("Make sure data/dataset.yaml exists on GCP VM")
        sys.exit(1)

    # Load YOLOv8 Large model
    print("\n📦 Loading YOLOv8 Large model...")
    model = YOLO('yolov8l.pt')

    # Train configuration
    print("\n⚙️  Training Configuration:")
    print(f"  Model: YOLOv8 Large")
    print(f"  Dataset: {dataset_yaml}")
    print(f"  Epochs: 100")
    print(f"  Batch Size: 16")
    print(f"  Image Size: 640x640")
    print(f"  Device: GPU (CUDA)")
    print(f"  Early Stopping: 10 epochs patience")
    print("")

    # Train
    results = model.train(
        data=dataset_yaml,
        epochs=100,
        imgsz=640,
        device=0,  # GPU device 0
        batch=16,  # Batch size (adjust if OOM: try 8)
        patience=10,  # Early stopping
        save=True,
        project='runs/detect',
        name='ffb_yolov8l_v1',
        verbose=True,
        plots=True
    )

    # Print results
    print("\n" + "=" * 50)
    print("✅ Training Complete!")
    print("=" * 50)
    print(f"\n📊 Final Metrics:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")
    print(f"\n💾 Model saved to: runs/detect/ffb_yolov8l_v1/weights/best.pt")
    print("\n📋 Next steps:")
    print("  1. Download best.pt from GCP VM")
    print("  2. Run validation locally")
    print("  3. Proceed to Phase 2: Pipeline Integration")

    return results

if __name__ == "__main__":
    try:
        results = train_yolo()
    except Exception as e:
        print(f"\n❌ Training failed with error:")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)
