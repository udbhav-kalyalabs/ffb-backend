# Camera Calibration & 3D Triangulation - Technical Deep Dive

## Quick Reference: Your iPhone 15 Setup

### Camera Specifications (from EXIF)
```
Wide-angle (A images):    4284 × 5712 pixels,  26mm equivalent focal length
3x Zoom (B images):       3024 × 4032 pixels,  52mm equivalent focal length
Sensor:                   1/1.28" (f/1.6 aperture)
```

### Key Insight 🔑
Your dual-focal-length setup is OPTIMAL for triangulation:
- **A images (wide)**: Lower magnification → shows context, larger FOV
- **B images (zoom)**: Higher magnification → precise bunch localization

**This difference helps deduplication because:**
1. Same physical bunch appears at DIFFERENT pixel locations in A vs B
2. More variation = better triangulation accuracy
3. Easier to distinguish closely-spaced bunches

---

## Part 1: Camera Calibration Mathematics

### What is Calibration?

Camera calibration answers: **"How does a 3D world point map to 2D image pixels?"**

The mapping equation:
```
[u]     [fx   0  cx] [X]
[v]  =  [ 0  fy  cy] [Y]  × [R|t]
[1]     [ 0   0   1] [Z]
              K          1
        Intrinsic     Extrinsic  World
        (camera)      (position)  point
```

### Intrinsic Matrix K (Camera Properties - FIXED)

```
K = [fx   0  cx]
    [ 0  fy  cy]
    [ 0   0   1]

Where:
- fx, fy = focal length in PIXELS (not mm)
- cx, cy = principal point (image center)
```

**For your iPhone 15:**

**Wide (A images):**
```
Image width: 4284 pixels
Focal length: 26mm (35mm equivalent)
Sensor width: 6.86mm

fx = (image_width × focal_length_mm) / sensor_width_mm
   = (4284 × 26) / 6.86
   ≈ 16,270 pixels

K_wide = [16270     0  2142]
         [    0 16270  2856]
         [    0     0     1]
```

**Zoom (B images):**
```
Image width: 3024 pixels
Focal length: 52mm (3x zoom)

fx = (3024 × 52) / 6.86
   ≈ 22,900 pixels

K_zoom = [22900     0  1512]
         [    0 22900  2016]
         [    0     0     1]
```

**Why different K for A vs B?**
- Different resolution
- Different focal length (different zoom)
- Different principal point (image center shifts slightly)

### Extrinsic Matrix [R|t] (Camera Position & Orientation - VARIES per position)

```
[R|t] = [rotation_matrix (3×3)]  [translation (3×1)]
        [      0   0   0        ]  [      1           ]

Physical meaning:
- R = how camera is rotated (which direction it's pointing)
- t = where camera is located in world coordinates
```

**Your 4 positions (North, East, South, West):**

Assuming camera always at 2.0m distance, 1.5m height:

```
Position 1 (North):  Camera at (0, -2.0, 0) looking South toward tree
Position 2 (East):   Camera at (2.0, 0, 0) looking West toward tree
Position 3 (South):  Camera at (0, 2.0, 0) looking North toward tree
Position 4 (West):   Camera at (-2.0, 0, 0) looking East toward tree

Tree center at origin (0, 0, 1.5) - height of bunch concentration
```

The rotation matrices handle the yaw (0°, 90°, 180°, 270°) to point at tree.

---

## Part 2: 3D Triangulation Algorithm (Direct Linear Transform)

### Problem Statement

Given:
- Bunch detected at pixel (u1, v1) in image 1
- Same bunch detected at pixel (u2, v2) in image 2
- Camera projection matrices P1, P2

Find: 3D world coordinates [X, Y, Z]

### The Math: Direct Linear Transform (DLT)

The projection equation gives us constraints for each view:
```
λ₁ × [u₁, v₁, 1]ᵀ = P₁ × [X, Y, Z, 1]ᵀ
λ₂ × [u₂, v₂, 1]ᵀ = P₂ × [X, Y, Z, 1]ᵀ

Where λᵢ is scale factor (unknown)
```

This is non-linear because of unknown scales. Transform it:
```
u × (P[2,:] · P_world) = P[0,:] · P_world
v × (P[2,:] · P_world) = P[1,:] · P_world
```

This gives us **2 linear equations per view**. With N views, we have 2N equations in 4 unknowns (Xh, Yh, Zh, Wh).

This is an **overdetermined homogeneous system** A·X = 0.

**Solution via SVD:**
```
1. Stack all equations into matrix A (2N × 4)
2. Compute SVD: A = U·Σ·Vᵀ
3. Solution X = last column of V (corresponding to smallest singular value)
4. Convert from homogeneous: [X, Y, Z] = [X_h, Y_h, Z_h] / W_h
```

### Example Calculation

Suppose we have a bunch in 2 views:

**View 1A (wide):**
```
Detected at pixel: u=2142, v=2856
P_1A = [16270     0  2142  0  ]  × [R₁|t₁]
       [    0 16270  2856  0  ]
       [    0     0     1   0  ]
```

**View 1B (zoom):**
```
Detected at pixel: u=1512, v=2016
P_1B = [22900     0  1512  0  ]  × [R₁|t₁]
       [    0 22900  2016  0  ]
       [    0     0     1   0  ]
```

Build equations:
```
A[0,:] = 2142 × P_1A[2,:] - P_1A[0,:]
A[1,:] = 2856 × P_1A[2,:] - P_1A[1,:]
A[2,:] = 1512 × P_1B[2,:] - P_1B[0,:]
A[3,:] = 2016 × P_1B[2,:] - P_1B[1,:]

SVD(A) → X_homogeneous = [X_h, Y_h, Z_h, W_h]

Result: [X, Y, Z] = [X_h/W_h, Y_h/W_h, Z_h/W_h]
        ≈ [0.5, -0.3, 1.2] meters (world coordinates)
```

### Accuracy Considerations

**Why triangulation works better with multiple views:**
```
1 view:  Can only say "point is on this ray from camera"
2 views: Two rays intersect at point
3+ views: Overdetermined system, average out noise
```

**Error sources:**
- Detection noise (pixel-level imprecision ~1-2 pixels)
- Camera calibration errors (if K, R, t are inaccurate)
- Lens distortion (not modeled in simple calibration)
- Non-planar subject (bunch is 3D, we treat as point)

**With your data:**
- 8 images per tree (4 angles × 2 zoom levels)
- Most bunches visible in 3-4 images
- Multiple confirmations reduce triangulation error

---

## Part 3: Deduplication via DBSCAN Clustering

### Why Clustering?

After triangulation, we have hundreds of 3D points (one per detection). But:
- Same physical bunch detected multiple times
- Need to count UNIQUE bunches
- Need to handle occlusion (some bunches seen fewer times)

### DBSCAN Algorithm

```
DBSCAN(eps=0.15m, min_samples=1):

For each point P:
  1. Find all points within distance eps (0.15m)
  2. If ≥ min_samples neighbors: start new cluster
  3. Add all reachable neighbors to cluster
  4. Repeat until all points processed
```

**For your data:**
- eps = 0.15m (15cm) - bunches closer than this likely same bunch
- min_samples = 1 - even single-view detections get their own cluster

### Example

```
Triangulated detections:
  bunch_001_view1A: [0.50, -0.30, 1.20]
  bunch_001_view1B: [0.51, -0.29, 1.19]
  bunch_001_view2A: [0.49, -0.31, 1.21]
  bunch_002_view1A: [0.80, 0.50, 1.15]
  bunch_002_view2B: [0.81, 0.51, 1.14]

DBSCAN with eps=0.15m:
  Cluster 0: [bunch_001_view1A, bunch_001_view1B, bunch_001_view2A]
             → Unique bunch at (0.50, -0.30, 1.20)
  Cluster 1: [bunch_002_view1A, bunch_002_view2B]
             → Unique bunch at (0.80, 0.50, 1.15)

Result: 2 unique bunches (correct!)
```

---

## Part 4: Complete Pipeline

```
Raw images (8 per tree)
        ↓
    YOLOv8 Detection
    (2D pixel locations)
        ↓
    Establish Correspondences
    (which detections = same bunch?)
        ↓
    Triangulation (DLT)
    (convert 2D → 3D world coords)
        ↓
    DBSCAN Clustering
    (group nearby 3D points)
        ↓
    Unique Bunch Count
```

### Correspondence Matching

This is the link between "detection in image 1A" and "detection in image 1B":

**Approach 1: Spatial Proximity (Recommended for FFB)**
```
If (u_1A - u_1B) < threshold AND (v_1A - v_1B) < threshold:
    → Likely same bunch
```

**Approach 2: Feature Matching (For complex scenes)**
```
Extract descriptors around each detection (SIFT, ORB)
Match descriptors between images
→ More robust but slower
```

For FFB which are relatively distinctive, spatial proximity works well.

---

## Implementation in Code

### File: config/camera_calibration.py
- iPhone15Calibration class
- Computes K matrices for wide and zoom
- Sets up extrinsic matrices for 4 positions
- get_projection_matrix(image_name) → P = K × [R|t]

### File: services/triangulation.py
- Triangulation class
- triangulate_point(detections_per_view) → [X, Y, Z]
- cluster_bunches_3d(points_3d, eps=0.15) → unique bunches

### File: services/multiview_processor.py (to create)
- MultiViewProcessor class
- Orchestrates: detect → triangulate → cluster
- Produces: unique bunch count

---

## Validation Checklist

Before production, verify:

- [ ] K_wide and K_zoom computed correctly from EXIF data
- [ ] Extrinsic matrices reflect actual photography rig
- [ ] Triangulation produces points near tree center (within ~5m)
- [ ] Clusters have reasonable radii (<0.5m)
- [ ] Unique bunch count matches ground truth (within ±2%)
- [ ] Processing time <20 seconds per tree

---

## Limitations & Future Improvements

### Current Limitations
1. **Fixed distance assumption**: Assumes 2.0m from tree, but varies per position
2. **No lens distortion**: iPhone has barrel distortion, not modeled
3. **Assumes co-planar camera axes**: All cameras at same height
4. **Manual correspondence**: Relies on spatial proximity for matching

### Phase 2 Enhancements
1. **Dynamic calibration**: Extract distance and angle from image analysis
2. **Lens distortion correction**: Use cv2.undistort() with distortion coefficients
3. **Advanced correspondence**: Feature matching (SIFT, SuperPoint)
4. **Bundle adjustment**: Refine K, R, t using ground truth measurements
5. **Per-tree calibration**: Learn optimal parameters per tree
