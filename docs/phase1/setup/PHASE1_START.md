# 🚀 PHASE 1 START - Quick Setup Guide

**Status:** Ready to annotate images  
**Time to setup:** ~30 minutes (mostly waiting for Label Studio to start)  
**Your task:** Annotate 16 FFB across 64 images

---

## Step 1️⃣: Start Label Studio

### On Windows:
```bash
# Option A: Run the batch script (easiest)
setup_phase1.bat

# Option B: Run Docker command directly
docker run -d -p 8080:8080 -v %USERPROFILE%\label-studio-data:/label-studio/data ^
  --name label-studio heartexlabs/label-studio:latest
```

### On Mac/Linux:
```bash
# Run the shell script
bash setup_phase1.sh

# Or Docker command directly
docker run -d -p 8080:8080 -v ~/label-studio-data:/label-studio/data \
  --name label-studio heartexlabs/label-studio:latest
```

**Wait 20-30 seconds for Label Studio to start, then:**

---

## Step 2️⃣: Open Label Studio UI

**Open in browser:** http://localhost:8080

**Login with default credentials:**
- Email: `admin@heartex.com`
- Password: `password`

---

## Step 3️⃣: Create New Project

1. Click **"Create"** button
2. Click **"New Project"**
3. Fill in:
   - **Project Name:** `FFB Detection Phase 1`
   - **Description:** `Annotating 64 images for YOLOv8 training`
4. Click **"Create"**

---

## Step 4️⃣: Upload Images

1. In the new project, click **"Upload Data"** or **"Add Data"**
2. Select **"File"** as data source
3. Click **"Choose Files"** or drag-and-drop
4. Navigate to: `SG9-RW010SS-10T-40P-070326 - SMTF1/`
5. Select **ALL 64 IMAGES** (8 trees × 8 images each)
6. Click **"Upload Files"**
7. Wait for upload to complete (~2-3 minutes)

---

## Step 5️⃣: Configure Annotation Template

1. After images upload, go to **"Setup"** tab
2. Under "Labeling Interface", paste this XML:

```xml
<View>
  <Image name="image" value="$image"/>
  <RectangleLabeler name="label" toName="image">
    <Choice value="FFB"/>
    <Choice value="Overripe"/>
  </RectangleLabeler>
</View>
```

3. Click **"Save"**

---

## Step 6️⃣: Start Annotating

1. Go to **"Label"** tab
2. For each image:
   - **Draw rectangles** around each fruit-bearing branch (FFB)
   - Label as **"FFB"** (or "Overripe" if clearly overripe)
   - Click **"Submit"** to move to next image

### Ground Truth to Match:
```
T1: 0 annotations
T2: 0 annotations
T3: 7 annotations ← Find 7 FFB in T3's 8 images
T4: 3 annotations ← Find 3 FFB in T4's 8 images
T5: 2 annotations
T6: 3 annotations
T7: 1 annotation (likely overripe)
T8: 0 annotations (this is your test set - skip it)

Total: 16 bounding boxes across 64 images
```

---

## 📊 Annotation Tips

✅ **DO:**
- Draw tight boxes around each bunch
- Label all visible FFB in every image
- Use zoom feature to spot small bunches
- Mark clearly overripe bunches as "Overripe"

❌ **DON'T:**
- Draw huge boxes that include leaves/branches
- Skip small or obscured bunches
- Mix up FFB with other foliage

---

## ⏱️ Timeline

- **Annotating all 64 images:** 8-10 hours
  - Can spread over several days
  - Do a few images at a time
  - ~5-7 minutes per image average

---

## 🎯 What's Next After Annotation?

1. Export annotations to **YOLO format**
2. Upload to Google Cloud
3. Run training script
4. **Model training time: 4-6 hours** (on GPU)

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to localhost:8080 | Wait 30 seconds, refresh browser, check `docker ps` |
| Label Studio won't start | Check Docker Desktop is running, run `docker logs label-studio` |
| Images won't upload | Try uploading fewer images at once (e.g., 8 at a time) |
| Template paste didn't work | Make sure you're in Setup tab, click in editor area first |

---

## 📞 Need Help?

- **Label Studio docs:** https://labelstud.io/guide/
- **Docker issues:** Check you have Docker Desktop running (Windows/Mac) or daemon running (Linux)
- **Questions?** Refer to `PHASE1_IMPLEMENTATION.md` for detailed explanations

---

## 📝 Track Your Progress

**Use this file:** `PHASE1_CHECKLIST.md`
- Updates as you complete annotation
- Shows overall progress
- Tracks your GCP/training setup

---

**Ready? Run the setup script now!** 🚀

```bash
# Windows
setup_phase1.bat

# Mac/Linux
bash setup_phase1.sh
```
