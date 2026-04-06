# 📡 AgriAI API - Complete Endpoints Guide

## Base URL
```
http://your-api-url/api/v1
```

---

## 📋 Table of Contents
1. [Analysis Endpoint](#1-analyze-image-with-storage)
2. [Get Single Analysis](#2-get-single-analysis)
3. [Get All Analyses](#3-get-all-analyses-main-ui-endpoint)
4. [Get User Analyses](#4-get-user-analyses)
5. [Get Statistics](#5-get-statistics)
6. [Health Check](#6-health-check)
7. [Supported Crops](#7-supported-crops)

---

## 1. Analyze Image with Storage

**The main endpoint for image analysis with automatic S3 and MongoDB storage.**

### Endpoint
```
POST /api/v1/analyze-base64
```

### Purpose
- Analyze crop images using AI (AWS Bedrock + Object Detection)
- Automatically save original image to S3
- Automatically save annotated image to S3
- Store analysis results in MongoDB
- Return both immediate results AND storage URLs

### Frontend Usage

#### Request
```javascript
const response = await fetch('http://your-api-url/api/v1/analyze-base64', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    file: "data:image/jpeg;base64,/9j/4AAQSkZJRg...",  // Base64 encoded image
    filename: "palm_tree.jpg",
    lat: "51.5074",        // GPS latitude (optional)
    long: "-0.1278",       // GPS longitude (optional)
    uuid: "user-456-uuid", // User identifier
    crop_type: "oil_palm",
    use_detection: true,
    return_annotated_image: true,
    include_recommendations: true,
    min_confidence: 0.5
  })
});

const data = await response.json();
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | ✅ | Base64 encoded image (with or without data URI prefix) |
| `filename` | string | ✅ | Original filename |
| `lat` | string | ❌ | GPS latitude |
| `long` | string | ❌ | GPS longitude |
| `uuid` | string | ❌ | User UUID (defaults to "anonymous") |
| `crop_type` | string | ❌ | Crop type (default: "oil_palm") |
| `use_detection` | boolean | ❌ | Use object detection (default: true) |
| `return_annotated_image` | boolean | ❌ | Return annotated image as base64 (default: true) |
| `include_recommendations` | boolean | ❌ | Include AI recommendations (default: true) |
| `min_confidence` | float | ❌ | Minimum confidence threshold 0.0-1.0 (default: 0.5) |

#### Response
```json
{
  "success": true,
  "crop_type": "oil_palm",
  
  "analysis": {
    "total_bunches": 5,
    "detection_confidence": 0.85,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.92,
        "bounding_box": {
          "x_min": 100,
          "y_min": 200,
          "x_max": 300,
          "y_max": 400,
          "center_x": 200,
          "center_y": 300
        },
        "color_code": "#FF0000",
        "visibility": "fully_visible",
        "size": "large",
        "position": "center",
        "description": "Detailed AI analysis of this bunch..."
      }
    ],
    "stage_summary": {
      "young": 1,
      "mature": 2,
      "ripe": 1,
      "overripe": 1
    },
    "plant_health": {
      "overall_score": 85.0,
      "frond_condition": "good",
      "bunch_development": "excellent",
      "observations": ["..."],
      "concerns": ["..."]
    },
    "recommendations": [
      "Harvest ripe bunches within 3-5 days",
      "..."
    ]
  },
  
  "image_metadata": {
    "width": 3072,
    "height": 4096,
    "analyzed_at": "2026-01-29T18:39:35.139449",
    "file_size_kb": 2263.09
  },
  
  "processing_time_ms": 17922.33,
  
  "annotated_image": "base64_string_of_annotated_image...",
  "annotated_image_format": "jpeg",
  
  "image_id": "20260129_183935_a1b2c3d4e5f6",
  "original_image_url": "s3://agriai-images/originals/20260129_183935_a1b2c3d4e5f6/palm_tree.jpg",
  "annotated_image_url": "s3://agriai-images/annotated/20260129_183935_a1b2c3d4e5f6/annotated_palm_tree.jpg",
  "database_id": "65c1a2b3c4d5e6f7g8h9i0j1",
  
  "error": null
}
```

#### Response Fields Explanation
| Field | Description | Frontend Usage |
|-------|-------------|----------------|
| `analysis` | Complete AI analysis with bunches, stages, recommendations | Display metrics and insights |
| `annotated_image` | Base64 annotated image with bounding boxes | **Display immediately for side-by-side comparison** |
| `annotated_image_format` | Image format (jpeg/png) | Use for data URI: `data:image/${format};base64,...` |
| `image_id` | Unique identifier for this image | Store for later retrieval |
| `original_image_url` | S3 URL for original image | Reference for storage (not directly accessible) |
| `annotated_image_url` | S3 URL for annotated image | Reference for storage (not directly accessible) |
| `database_id` | MongoDB document ID | Use for fetching full details later |

### Frontend Implementation Example

```javascript
// Upload and Analyze
async function analyzeImage(imageFile, userUuid, latitude, longitude) {
  // Convert file to base64
  const base64 = await fileToBase64(imageFile);
  
  // Send to API
  const response = await fetch('/api/v1/analyze-base64', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file: `data:image/jpeg;base64,${base64}`,
      filename: imageFile.name,
      uuid: userUuid,
      lat: latitude,
      long: longitude
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Display side-by-side comparison
    displayComparison(
      imageFile,  // Original from user's upload
      result.annotated_image,  // Annotated from API
      result.annotated_image_format
    );
    
    // Display analysis metrics
    displayMetrics(result.analysis);
    
    // Save IDs for later retrieval
    saveToLocalStorage({
      imageId: result.image_id,
      databaseId: result.database_id
    });
  }
}

// Display side-by-side
function displayComparison(originalFile, annotatedBase64, format) {
  const originalUrl = URL.createObjectURL(originalFile);
  const annotatedUrl = `data:image/${format};base64,${annotatedBase64}`;
  
  // Render in UI
  return (
    <div className="comparison">
      <div className="image-container">
        <h3>Original Image</h3>
        <img src={originalUrl} alt="Original" />
      </div>
      <div className="image-container">
        <h3>AI Analysis (Annotated)</h3>
        <img src={annotatedUrl} alt="Annotated" />
      </div>
    </div>
  );
}
```

---

## 2. Get Single Analysis

**Retrieve a specific analysis by image ID with presigned S3 URLs.**

### Endpoint
```
GET /api/v1/analysis/{image_id}
```

### Purpose
- Fetch complete analysis for a specific image
- Get presigned URLs for S3 images (valid for 1 hour)
- Retrieve GPS coordinates and metadata

### Frontend Usage

#### Request
```javascript
const imageId = "20260129_183935_a1b2c3d4e5f6";

const response = await fetch(
  `http://your-api-url/api/v1/analysis/${imageId}`
);

const data = await response.json();
```

#### Response
```json
{
  "id": "65c1a2b3c4d5e6f7g8h9i0j1",
  "image_id": "20260129_183935_a1b2c3d4e5f6",
  "user_uuid": "user-456-uuid",
  "filename": "palm_tree.jpg",
  "latitude": "51.5074",
  "longitude": "-0.1278",
  "analysis": {
    "success": true,
    "crop_type": "oil_palm",
    "analysis": {
      "total_bunches": 5,
      "bunches": [...],
      "stage_summary": {...},
      "plant_health": {...},
      "recommendations": [...]
    }
  },
  "original_image_presigned_url": "https://agriai-images.s3.amazonaws.com/originals/...?X-Amz-...",
  "annotated_image_presigned_url": "https://agriai-images.s3.amazonaws.com/annotated/...?X-Amz-...",
  "created_at": "2026-01-29T18:39:35.139449"
}
```

#### Frontend Implementation
```javascript
async function fetchAnalysis(imageId) {
  const response = await fetch(`/api/v1/analysis/${imageId}`);
  const data = await response.json();
  
  // Display images from S3 presigned URLs
  return (
    <div>
      <h3>Analysis Details</h3>
      <p>Created: {new Date(data.created_at).toLocaleString()}</p>
      <p>Location: {data.latitude}, {data.longitude}</p>
      
      <div className="images">
        <img src={data.original_image_presigned_url} alt="Original" />
        <img src={data.annotated_image_presigned_url} alt="Annotated" />
      </div>
      
      <div className="metrics">
        <p>Total Bunches: {data.analysis.analysis.total_bunches}</p>
        {/* Display other metrics */}
      </div>
    </div>
  );
}
```

---

## 3. Get All Analyses (Main UI Endpoint)

**⭐ PRIMARY ENDPOINT FOR DISPLAYING GALLERY/DASHBOARD**

### Endpoint
```
GET /api/v1/analyses/all
```

### Purpose
- Fetch all analyses from all users
- Display gallery/dashboard of analyzed images
- Show recent activity across the system
- Export data for reporting

### Frontend Usage

#### Request
```javascript
const response = await fetch(
  'http://your-api-url/api/v1/analyses/all?limit=50&skip=0&sort_order=desc'
);

const data = await response.json();
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum results (max: 200) |
| `skip` | integer | 0 | Number to skip (for pagination) |
| `sort_by` | string | "created_at" | Field to sort by |
| `sort_order` | string | "desc" | Sort order: "asc" or "desc" |

#### Response
```json
{
  "success": true,
  "total": 150,
  "count": 50,
  "limit": 50,
  "skip": 0,
  "data": [
    {
      "id": "65c1a2b3c4d5e6f7g8h9i0j1",
      "image_id": "20260129_183935_a1b2c3d4e5f6",
      "user_uuid": "user-456-uuid",
      "filename": "palm_tree.jpg",
      "crop_type": "oil_palm",
      "total_bunches": 5,
      "created_at": "2026-01-29T18:39:35.139449",
      "original_image_presigned_url": "https://s3.amazonaws.com/...",
      "annotated_image_presigned_url": "https://s3.amazonaws.com/..."
    },
    // ... more analyses
  ]
}
```

#### Frontend Implementation - Gallery View
```javascript
function AnalysisGallery() {
  const [analyses, setAnalyses] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  
  const ITEMS_PER_PAGE = 20;
  
  useEffect(() => {
    fetchAnalyses(page);
  }, [page]);
  
  async function fetchAnalyses(pageNum) {
    setLoading(true);
    const skip = pageNum * ITEMS_PER_PAGE;
    
    const response = await fetch(
      `/api/v1/analyses/all?limit=${ITEMS_PER_PAGE}&skip=${skip}&sort_order=desc`
    );
    const data = await response.json();
    
    setAnalyses(data.data);
    setTotal(data.total);
    setLoading(false);
  }
  
  if (loading) return <Loader />;
  
  return (
    <div className="gallery-container">
      <h1>All Analyses ({total})</h1>
      
      <div className="gallery-grid">
        {analyses.map((analysis) => (
          <div key={analysis.image_id} className="analysis-card">
            <img 
              src={analysis.annotated_image_presigned_url} 
              alt={analysis.filename}
              className="thumbnail"
            />
            <div className="card-info">
              <h3>{analysis.filename}</h3>
              <p>Bunches: {analysis.total_bunches}</p>
              <p>Crop: {analysis.crop_type}</p>
              <p>User: {analysis.user_uuid}</p>
              <p>Date: {new Date(analysis.created_at).toLocaleDateString()}</p>
              <button onClick={() => viewDetails(analysis.image_id)}>
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <Pagination 
        currentPage={page}
        totalItems={total}
        itemsPerPage={ITEMS_PER_PAGE}
        onPageChange={setPage}
      />
    </div>
  );
}
```

#### Dashboard Implementation
```javascript
function Dashboard() {
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  
  useEffect(() => {
    // Fetch 10 most recent
    fetch('/api/v1/analyses/all?limit=10&skip=0')
      .then(res => res.json())
      .then(data => setRecentAnalyses(data.data));
  }, []);
  
  return (
    <div className="dashboard">
      <h2>Recent Activity</h2>
      <div className="recent-list">
        {recentAnalyses.map(analysis => (
          <div key={analysis.image_id} className="recent-item">
            <img 
              src={analysis.annotated_image_presigned_url} 
              alt={analysis.filename}
              className="thumbnail-small"
            />
            <div>
              <p>{analysis.filename}</p>
              <small>{new Date(analysis.created_at).toLocaleString()}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 4. Get User Analyses

**Fetch all analyses for a specific user.**

### Endpoint
```
GET /api/v1/analyses/user/{user_uuid}
```

### Purpose
- Show user's analysis history
- Display user's uploaded images
- User-specific dashboard

### Frontend Usage

#### Request
```javascript
const userUuid = "user-456-uuid";

const response = await fetch(
  `http://your-api-url/api/v1/analyses/user/${userUuid}?limit=50&skip=0`
);

const data = await response.json();
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum results (max: 100) |
| `skip` | integer | 0 | Number to skip (for pagination) |

#### Response
Same format as `/analyses/all` but filtered for the user.

#### Frontend Implementation
```javascript
function UserHistory({ userId }) {
  const [analyses, setAnalyses] = useState([]);
  const [total, setTotal] = useState(0);
  
  useEffect(() => {
    fetch(`/api/v1/analyses/user/${userId}?limit=50`)
      .then(res => res.json())
      .then(data => {
        setAnalyses(data.data);
        setTotal(data.total);
      });
  }, [userId]);
  
  return (
    <div className="user-history">
      <h2>Your Analysis History ({total})</h2>
      <div className="history-grid">
        {analyses.map(analysis => (
          <div key={analysis.image_id} className="history-card">
            <img src={analysis.annotated_image_presigned_url} alt={analysis.filename} />
            <p>{analysis.filename}</p>
            <p>Bunches: {analysis.total_bunches}</p>
            <small>{new Date(analysis.created_at).toLocaleDateString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 5. Get Statistics

**Get system-wide statistics about analyses and storage.**

### Endpoint
```
GET /api/v1/statistics
```

### Purpose
- Display system metrics
- Admin dashboard
- Monitoring and analytics

### Frontend Usage

#### Request
```javascript
const response = await fetch('http://your-api-url/api/v1/statistics');
const data = await response.json();
```

#### Response
```json
{
  "success": true,
  "total_analyses": 150,
  "unique_users": 25,
  "crop_distribution": {
    "oil_palm": 150
  },
  "total_original_images": 150,
  "total_annotated_images": 150
}
```

#### Frontend Implementation
```javascript
function SystemStats() {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch('/api/v1/statistics')
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);
  
  if (!stats) return <Loader />;
  
  return (
    <div className="stats-dashboard">
      <h2>System Statistics</h2>
      <div className="stat-cards">
        <div className="stat-card">
          <h3>{stats.total_analyses}</h3>
          <p>Total Analyses</p>
        </div>
        <div className="stat-card">
          <h3>{stats.unique_users}</h3>
          <p>Unique Users</p>
        </div>
        <div className="stat-card">
          <h3>{stats.total_original_images}</h3>
          <p>Images in Storage</p>
        </div>
      </div>
      
      <div className="crop-distribution">
        <h3>Crop Distribution</h3>
        {Object.entries(stats.crop_distribution).map(([crop, count]) => (
          <div key={crop}>
            <span>{crop}:</span>
            <span>{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 6. Health Check

**Verify API is running.**

### Endpoint
```
GET /api/v1/health
```

### Purpose
- Monitor API status
- Load balancer health checks
- Uptime monitoring

### Frontend Usage

#### Request
```javascript
const response = await fetch('http://your-api-url/api/v1/health');
const data = await response.json();
```

#### Response
```json
{
  "status": "healthy",
  "service": "AgriAI Analysis API"
}
```

---

## 7. Supported Crops

**Get list of supported crop types.**

### Endpoint
```
GET /api/v1/supported-crops
```

### Purpose
- Display available crop types to users
- Validate crop selection

### Frontend Usage

#### Request
```javascript
const response = await fetch('http://your-api-url/api/v1/supported-crops');
const data = await response.json();
```

#### Response
```json
{
  "supported_crops": ["oil_palm"],
  "details": {
    "oil_palm": {
      "name": "Oil Palm",
      "scientific_name": "Elaeis guineensis",
      "stages": ["young", "mature", "ripe", "overripe"],
      "min_confidence": 0.5
    }
  }
}
```

---

## 🔄 Complete Frontend Flow Example

### 1. Upload and Analyze
```javascript
// User uploads image
const file = event.target.files[0];
const base64 = await fileToBase64(file);

// Analyze
const response = await fetch('/api/v1/analyze-base64', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file: `data:image/jpeg;base64,${base64}`,
    filename: file.name,
    uuid: currentUser.id,
    lat: userLocation.lat,
    long: userLocation.long
  })
});

const result = await response.json();

// Display side-by-side comparison
showComparison(file, result.annotated_image, result.analysis);

// Save for later
localStorage.setItem('lastImageId', result.image_id);
```

### 2. View Gallery
```javascript
// Show all analyses
const gallery = await fetch('/api/v1/analyses/all?limit=20');
const data = await gallery.json();

renderGallery(data.data);
```

### 3. View User History
```javascript
// Show user's analyses
const history = await fetch(`/api/v1/analyses/user/${userId}`);
const data = await history.json();

renderHistory(data.data);
```

### 4. View Details
```javascript
// Get specific analysis
const details = await fetch(`/api/v1/analysis/${imageId}`);
const data = await details.json();

showDetailsPage(data);
```

---

## 📊 Summary Table

| Endpoint | Method | Purpose | Frontend Use Case |
|----------|--------|---------|-------------------|
| `/analyze-base64` | POST | Analyze image + save to S3/MongoDB | Upload and analyze new images |
| `/analysis/{id}` | GET | Get single analysis with presigned URLs | View specific analysis details |
| `/analyses/all` | GET | Get all analyses (paginated) | **Gallery, dashboard, reports** |
| `/analyses/user/{uuid}` | GET | Get user's analyses | User history, profile page |
| `/statistics` | GET | System statistics | Admin dashboard, metrics |
| `/health` | GET | Health check | Monitoring, status |
| `/supported-crops` | GET | List crop types | Dropdown options, validation |

---

## 🎯 Key Points for Frontend Developer

1. **Main Upload Endpoint:** Use `POST /analyze-base64` with base64 images
2. **Immediate Display:** Use `annotated_image` field from response for instant side-by-side
3. **Gallery Endpoint:** Use `GET /analyses/all` to show all saved analyses
4. **Presigned URLs:** Valid for 1 hour, images load directly from S3
5. **GPS Coordinates:** Saved in MongoDB, retrieved via analysis endpoints
6. **Image IDs:** Store these for fetching details later

---

**📞 Questions? Check `/docs` endpoint for interactive API documentation!**

