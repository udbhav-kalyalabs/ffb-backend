# S3 + MongoDB Integration Guide

## Overview

This document describes the complete integration of S3 storage and MongoDB persistence for the AgriAI API.

## 🎯 Features Implemented

### 1. **S3 Image Storage**
- ✅ Original images stored in S3 with unique IDs
- ✅ Annotated images stored separately with prefix
- ✅ Presigned URLs for secure image access (1 hour expiration)
- ✅ Organized folder structure: `originals/{image_id}/` and `annotated/{image_id}/`

### 2. **MongoDB Data Persistence**
- ✅ Complete analysis results stored in MongoDB
- ✅ User tracking with UUID
- ✅ GPS coordinates (latitude/longitude) storage
- ✅ Timestamps for audit trail
- ✅ Indexed for fast queries

### 3. **Data Retrieval APIs**
- ✅ Fetch single analysis by image ID
- ✅ Fetch all analyses with pagination
- ✅ Fetch user-specific analyses
- ✅ Database statistics endpoint
- ✅ All endpoints return presigned URLs for images

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `motor>=3.3.0` - Async MongoDB driver
- `pymongo>=4.6.0` - MongoDB sync driver

### 2. Environment Configuration

Add these variables to your `.env` file:

```env
# AWS S3 Configuration
S3_BUCKET_NAME=agriai-images
S3_ORIGINAL_PREFIX=originals/
S3_ANNOTATED_PREFIX=annotated/
S3_PRESIGNED_URL_EXPIRATION=3600

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DATABASE=agriai_db
MONGO_COLLECTION=analyses
```

### 3. S3 Bucket Setup

Create an S3 bucket with the following structure:
```
agriai-images/
├── originals/
│   └── {image_id}/
│       └── {filename}
└── annotated/
    └── {image_id}/
        └── annotated_{filename}
```

**Bucket Policy (Optional):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:user/YOUR_USER"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::agriai-images/*"
    }
  ]
}
```

### 4. MongoDB Setup

1. Create a MongoDB cluster (MongoDB Atlas recommended)
2. Create a database named `agriai_db`
3. Collection `analyses` will be auto-created with indexes

**Indexes Created Automatically:**
- `image_id` (unique)
- `user_uuid`
- `created_at` (descending)
- Compound: `user_uuid` + `created_at`

---

## 🔌 API Endpoints

### Analysis Endpoint (Enhanced)

#### POST `/api/v1/analyze-base64`

**Request:**
```json
{
  "file": "data:image/jpeg;base64,/9j/4AAQ...",
  "filename": "palm_tree.jpg",
  "lat": "51.5074",
  "long": "-0.1278",
  "uuid": "user-456-uuid",
  "crop_type": "oil_palm",
  "use_detection": true,
  "return_annotated_image": true
}
```

**Response (Enhanced):**
```json
{
  "success": true,
  "crop_type": "oil_palm",
  "analysis": {
    "total_bunches": 5,
    "bunches": [...],
    "stage_summary": {...}
  },
  "image_metadata": {...},
  "processing_time_ms": 2345,
  "annotated_image": "base64_string...",
  "annotated_image_format": "jpeg",
  
  // NEW FIELDS
  "image_id": "20260129_143522_a1b2c3d4e5f6",
  "original_image_url": "s3://agriai-images/originals/20260129_143522_a1b2c3d4e5f6/palm_tree.jpg",
  "annotated_image_url": "s3://agriai-images/annotated/20260129_143522_a1b2c3d4e5f6/annotated_palm_tree.jpg",
  "database_id": "65c1a2b3c4d5e6f7g8h9i0j1"
}
```

### Data Retrieval Endpoints

#### 1. GET `/api/v1/analysis/{image_id}`
Fetch a specific analysis by image ID.

**Response:**
```json
{
  "_id": "65c1a2b3c4d5e6f7g8h9i0j1",
  "image_id": "20260129_143522_a1b2c3d4e5f6",
  "user_uuid": "user-456-uuid",
  "filename": "palm_tree.jpg",
  "latitude": "51.5074",
  "longitude": "-0.1278",
  "analysis": {...},
  "original_image_presigned_url": "https://agriai-images.s3.amazonaws.com/...",
  "annotated_image_presigned_url": "https://agriai-images.s3.amazonaws.com/...",
  "created_at": "2026-01-29T14:35:22.123Z"
}
```

#### 2. GET `/api/v1/analyses/all`
**🌟 MAIN RETRIEVAL ENDPOINT FOR UI**

Fetch all analyses from all users (paginated, simplified view).

**Query Parameters:**
- `limit` (default: 100, max: 200)
- `skip` (default: 0)
- `sort_by` (default: "created_at")
- `sort_order` (default: "desc")

**Response:**
```json
{
  "success": true,
  "total": 150,
  "count": 100,
  "limit": 100,
  "skip": 0,
  "data": [
    {
      "_id": "65c1a2b3c4d5e6f7g8h9i0j1",
      "image_id": "20260129_143522_a1b2c3d4e5f6",
      "user_uuid": "user-456-uuid",
      "filename": "palm_tree.jpg",
      "crop_type": "oil_palm",
      "total_bunches": 5,
      "created_at": "2026-01-29T14:35:22.123Z",
      "original_image_presigned_url": "https://...",
      "annotated_image_presigned_url": "https://..."
    },
    ...
  ]
}
```

**Use Cases:**
- Display gallery of all analyzed images in UI
- Show recent analyses dashboard
- Export data for reporting
- Build analytics visualizations

#### 3. GET `/api/v1/analyses/user/{user_uuid}`
Fetch all analyses for a specific user.

**Query Parameters:**
- `limit` (default: 50, max: 100)
- `skip` (default: 0)

**Response:** Same format as `/analyses/all`

#### 4. GET `/api/v1/statistics`
Get database and S3 storage statistics.

**Response:**
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

---

## 🧪 Testing

### Run Test Script

```bash
python test_full_flow.py
```

This will test:
1. ✅ Health check
2. ✅ Image analysis with S3/MongoDB storage
3. ✅ Fetch analysis by ID
4. ✅ Fetch all analyses
5. ✅ Fetch user analyses
6. ✅ Database statistics

### Manual cURL Tests

**1. Analyze Image:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze-base64 \
  -H "Content-Type: application/json" \
  -d '{
    "file": "data:image/jpeg;base64,/9j/4AAQ...",
    "filename": "test.jpg",
    "lat": "51.5074",
    "long": "-0.1278",
    "uuid": "user-123"
  }'
```

**2. Get All Analyses (UI Endpoint):**
```bash
curl http://localhost:8000/api/v1/analyses/all?limit=10
```

**3. Get Specific Analysis:**
```bash
curl http://localhost:8000/api/v1/analysis/{image_id}
```

**4. Get User's Analyses:**
```bash
curl http://localhost:8000/api/v1/analyses/user/user-123
```

**5. Get Statistics:**
```bash
curl http://localhost:8000/api/v1/statistics
```

---

## 📊 Database Schema

### MongoDB Document Structure

```javascript
{
  "_id": ObjectId("65c1a2b3c4d5e6f7g8h9i0j1"),
  "image_id": "20260129_143522_a1b2c3d4e5f6",
  "user_uuid": "user-456-uuid",
  "filename": "palm_tree.jpg",
  "original_image_url": "s3://agriai-images/originals/.../palm_tree.jpg",
  "annotated_image_url": "s3://agriai-images/annotated/.../annotated_palm_tree.jpg",
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
    },
    "image_metadata": {...},
    "processing_time_ms": 2345
  },
  "created_at": ISODate("2026-01-29T14:35:22.123Z"),
  "updated_at": ISODate("2026-01-29T14:35:22.123Z")
}
```

---

## 🚀 AWS ECS Deployment

### Environment Variables for ECS

Set these in your ECS Task Definition:

```json
{
  "environment": [
    {"name": "AWS_ACCESS_KEY_ID", "value": "your_key"},
    {"name": "AWS_SECRET_ACCESS_KEY", "value": "your_secret"},
    {"name": "AWS_REGION", "value": "us-east-1"},
    {"name": "S3_BUCKET_NAME", "value": "agriai-images"},
    {"name": "MONGODB_URI", "value": "mongodb+srv://..."},
    {"name": "MONGO_DATABASE", "value": "agriai_db"},
    {"name": "MONGO_COLLECTION", "value": "analyses"},
    {"name": "BEDROCK_MODEL_ID", "value": "anthropic.claude-3-5-sonnet-20240620-v1:0"},
    {"name": "ROBOFLOW_API_KEY", "value": "your_roboflow_key"}
  ]
}
```

### Lambda Integration

Your Lambda can now hit the ECS service URL:

```python
import requests

# Lambda function example
def lambda_handler(event, context):
    ecs_url = "http://your-ecs-service.amazonaws.com/api/v1/analyze-base64"
    
    payload = {
        "file": event['base64_image'],
        "filename": event['filename'],
        "uuid": event['user_id'],
        "lat": event.get('latitude'),
        "long": event.get('longitude')
    }
    
    response = requests.post(ecs_url, json=payload)
    return response.json()
```

---

## 🎨 UI Integration Example

### Fetch and Display All Analyses

```javascript
// React/Vue/Angular example
async function fetchAllAnalyses(page = 0, limit = 20) {
  const response = await fetch(
    `http://your-api-url/api/v1/analyses/all?limit=${limit}&skip=${page * limit}`
  );
  
  const data = await response.json();
  
  return {
    total: data.total,
    analyses: data.data.map(item => ({
      id: item.image_id,
      filename: item.filename,
      cropType: item.crop_type,
      bunches: item.total_bunches,
      originalImageUrl: item.original_image_presigned_url,
      annotatedImageUrl: item.annotated_image_presigned_url,
      createdAt: new Date(item.created_at)
    }))
  };
}

// Usage
const { total, analyses } = await fetchAllAnalyses(0, 20);
console.log(`Showing ${analyses.length} of ${total} total analyses`);
```

### Display Image Gallery

```html
<div class="gallery">
  {analyses.map(analysis => (
    <div class="card">
      <img src={analysis.originalImageUrl} alt={analysis.filename} />
      <div class="info">
        <h3>{analysis.filename}</h3>
        <p>Bunches: {analysis.bunches}</p>
        <p>Crop: {analysis.cropType}</p>
        <p>Date: {analysis.createdAt.toLocaleDateString()}</p>
      </div>
      <button onclick="viewDetails('{analysis.id}')">View Details</button>
    </div>
  ))}
</div>
```

---

## 📈 Performance Considerations

### MongoDB Indexes
- Auto-created on startup for optimal query performance
- `image_id` unique index for fast lookups
- Compound indexes for user + time queries

### S3 Presigned URLs
- Valid for 1 hour (configurable)
- No authentication required for access during validity period
- Automatically generated on retrieval

### Pagination
- Default limit: 100 (adjustable up to 200)
- Use `skip` parameter for pagination
- MongoDB efficiently handles pagination with indexes

---

## 🔒 Security Considerations

1. **S3 Access**: Only your AWS credentials can upload/delete
2. **Presigned URLs**: Temporary access (1 hour)
3. **MongoDB**: Use connection string with authentication
4. **API**: Consider adding authentication middleware for production
5. **CORS**: Update CORS settings in `main.py` for production

---

## 📝 Summary

### What's New:
✅ **Storage**: All images saved to S3 with organized structure
✅ **Persistence**: Complete analysis data in MongoDB
✅ **Retrieval**: 4 new endpoints for data access
✅ **UI-Ready**: `/analyses/all` endpoint perfect for gallery view
✅ **Secure**: Presigned URLs for image access
✅ **Scalable**: Indexed MongoDB + S3 storage
✅ **Tested**: Comprehensive test script included

### Key Endpoint for UI:
🌟 **GET `/api/v1/analyses/all`** - Fetch all saved analyses with images

This endpoint provides everything needed to build a UI dashboard showing:
- Total number of analyses
- Grid/list view of all analyzed images
- Thumbnails with presigned URLs
- Basic metadata (filename, crop type, bunches)
- Pagination support

---

## 🆘 Troubleshooting

### MongoDB Connection Issues
```bash
# Test connection
mongosh "mongodb+srv://your-connection-string"
```

### S3 Access Issues
```bash
# Test AWS credentials
aws s3 ls s3://agriai-images/
```

### API Issues
```bash
# Check logs
# The startup event will log MongoDB and S3 connection status
```

---

## 📞 Support

For issues or questions:
1. Check API logs for error messages
2. Verify environment variables are set correctly
3. Test MongoDB and S3 access independently
4. Use the test script to identify issues

---

**Last Updated:** January 29, 2026
**Version:** 1.0.0

