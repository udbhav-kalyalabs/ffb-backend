# 🎨 Frontend Developer Quick Reference

## 🚀 Main Workflow

### 1️⃣ User Uploads Image → Analyze
```javascript
POST /api/v1/analyze-base64

// Send:
{
  file: "data:image/jpeg;base64,...",
  filename: "image.jpg",
  uuid: "user-123",
  lat: "51.5074",
  long: "-0.1278"
}

// Receive:
{
  success: true,
  analysis: { total_bunches, bunches, recommendations, ... },
  annotated_image: "base64_string",  // ← Display this!
  annotated_image_format: "jpeg",
  image_id: "20260129_...",
  original_image_url: "s3://...",
  annotated_image_url: "s3://...",
  database_id: "65c1..."
}
```

**Use Case:** Side-by-side comparison of original vs annotated image

---

### 2️⃣ Display Gallery of All Analyses
```javascript
GET /api/v1/analyses/all?limit=50&skip=0

// Receive:
{
  success: true,
  total: 150,
  count: 50,
  data: [
    {
      image_id: "...",
      filename: "palm.jpg",
      crop_type: "oil_palm",
      total_bunches: 5,
      original_image_presigned_url: "https://...",  // ← Display this!
      annotated_image_presigned_url: "https://...", // ← Display this!
      created_at: "2026-01-29T..."
    },
    // ...
  ]
}
```

**Use Case:** Gallery/dashboard showing all saved analyses

---

### 3️⃣ Show User's History
```javascript
GET /api/v1/analyses/user/{user_uuid}?limit=50

// Same response format as /analyses/all
```

**Use Case:** User profile, personal history page

---

### 4️⃣ View Specific Analysis Details
```javascript
GET /api/v1/analysis/{image_id}

// Receive:
{
  id: "...",
  image_id: "...",
  user_uuid: "...",
  filename: "...",
  latitude: "51.5074",    // ← GPS coordinates here!
  longitude: "-0.1278",   // ← GPS coordinates here!
  analysis: { ... },
  original_image_presigned_url: "https://...",
  annotated_image_presigned_url: "https://...",
  created_at: "..."
}
```

**Use Case:** Details page with full analysis + GPS info

---

### 5️⃣ Dashboard Stats
```javascript
GET /api/v1/statistics

// Receive:
{
  total_analyses: 150,
  unique_users: 25,
  crop_distribution: { oil_palm: 150 },
  total_original_images: 150,
  total_annotated_images: 150
}
```

**Use Case:** Admin dashboard, system metrics

---

## 📋 All Available Endpoints

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/analyze-base64` | POST | **Upload & analyze image** |
| 2 | `/analysis/{image_id}` | GET | Get single analysis details |
| 3 | `/analyses/all` | GET | **Get all analyses (gallery)** ⭐ |
| 4 | `/analyses/user/{uuid}` | GET | Get user's analyses |
| 5 | `/statistics` | GET | System statistics |
| 6 | `/health` | GET | Health check |
| 7 | `/supported-crops` | GET | List crop types |

---

## 🎯 Key Points

### ✅ DO's
- ✅ Use `/analyze-base64` for uploading (NOT `/analyze`)
- ✅ Use `annotated_image` from response for immediate display
- ✅ Use `/analyses/all` for gallery/dashboard
- ✅ Presigned URLs expire in 1 hour (regenerate if needed)
- ✅ Store `image_id` for later retrieval

### ❌ DON'Ts
- ❌ Don't use `/analyze` endpoint (removed - outdated)
- ❌ Don't try to access S3 URLs directly without presigning
- ❌ Don't expect GPS coordinates in analyze response (fetch via `/analysis/{id}`)

---

## 💡 Common Use Cases

### Side-by-Side Image Comparison
```javascript
// After analysis
const originalSrc = URL.createObjectURL(uploadedFile);
const annotatedSrc = `data:image/jpeg;base64,${response.annotated_image}`;

<div className="comparison">
  <img src={originalSrc} alt="Original" />
  <img src={annotatedSrc} alt="Analyzed" />
</div>
```

### Gallery Grid
```javascript
const analyses = await fetch('/api/v1/analyses/all?limit=20').then(r => r.json());

<div className="gallery">
  {analyses.data.map(item => (
    <div key={item.image_id}>
      <img src={item.annotated_image_presigned_url} />
      <p>{item.filename}</p>
      <p>Bunches: {item.total_bunches}</p>
    </div>
  ))}
</div>
```

### Analysis Details with GPS
```javascript
const analysis = await fetch(`/api/v1/analysis/${imageId}`).then(r => r.json());

<div>
  <h2>{analysis.filename}</h2>
  <p>Location: {analysis.latitude}, {analysis.longitude}</p>
  <p>Bunches: {analysis.analysis.analysis.total_bunches}</p>
  <img src={analysis.annotated_image_presigned_url} />
</div>
```

---

## 🔗 Documentation
- **Full Guide:** `API_ENDPOINTS_GUIDE.md`
- **Interactive Docs:** `http://your-api-url/docs`
- **Implementation Guide:** `S3_MONGODB_INTEGRATION.md`

---

## ⚡ Quick Test

```bash
# Test analyze endpoint
curl -X POST http://localhost:8000/api/v1/analyze-base64 \
  -H "Content-Type: application/json" \
  -d '{
    "file": "data:image/jpeg;base64,...",
    "filename": "test.jpg",
    "uuid": "user-123"
  }'

# Test gallery endpoint
curl http://localhost:8000/api/v1/analyses/all?limit=10
```

---

**Need more details? Check `API_ENDPOINTS_GUIDE.md` for complete examples!**

