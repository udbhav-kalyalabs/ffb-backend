# 🚀 Quick Start - Deployment & Usage Guide

## ⚡ Setup in 5 Minutes

### Step 1: Environment Variables
Create/update your `.env` file:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=agriai-images
S3_ORIGINAL_PREFIX=originals/
S3_ANNOTATED_PREFIX=annotated/

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DATABASE=agriai_db
MONGO_COLLECTION=analyses

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# Roboflow (if using)
ROBOFLOW_API_KEY=your_roboflow_key
ROBOFLOW_MODEL_ID=oil-palm-segmentation1
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://agriai-images
```

Or create manually in AWS Console with default settings.

### Step 4: Run the API
```bash
python main.py
```

API will be available at: `http://localhost:8000`
Documentation at: `http://localhost:8000/docs`

---

## 🧪 Test the Integration

```bash
python test_full_flow.py
```

Make sure you have a test image in `oilpalm_samples/sample1.jpg` or update the script path.

---

## 📡 API Usage

### 1. Analyze Image (POST)

**Lambda/Client Request Format:**

```bash
curl -X POST http://your-ecs-url/api/v1/analyze-base64 \
  --header 'Content-Type: application/json' \
  --data '{
    "file": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "filename": "palm_tree.jpg",
    "lat": "51.5074",
    "long": "-0.1278",
    "uuid": "user-456-uuid",
    "crop_type": "oil_palm",
    "use_detection": true,
    "return_annotated_image": true
  }'
```

**Response:**
```json
{
  "success": true,
  "image_id": "20260129_143522_a1b2c3d4e5f6",
  "original_image_url": "s3://agriai-images/originals/...",
  "annotated_image_url": "s3://agriai-images/annotated/...",
  "database_id": "65c1a2b3c4d5e6f7g8h9i0j1",
  "analysis": {
    "total_bunches": 5,
    "stage_summary": {...}
  }
}
```

### 2. Fetch All Analyses (GET) - **Main UI Endpoint**

```bash
curl http://your-ecs-url/api/v1/analyses/all?limit=50
```

**Response:**
```json
{
  "success": true,
  "total": 150,
  "count": 50,
  "data": [
    {
      "image_id": "20260129_143522_a1b2c3d4e5f6",
      "filename": "palm_tree.jpg",
      "crop_type": "oil_palm",
      "total_bunches": 5,
      "original_image_presigned_url": "https://s3.amazonaws.com/...",
      "annotated_image_presigned_url": "https://s3.amazonaws.com/...",
      "created_at": "2026-01-29T14:35:22.123Z"
    }
  ]
}
```

### 3. Fetch Single Analysis (GET)

```bash
curl http://your-ecs-url/api/v1/analysis/{image_id}
```

### 4. Fetch User's Analyses (GET)

```bash
curl http://your-ecs-url/api/v1/analyses/user/{user_uuid}
```

### 5. Get Statistics (GET)

```bash
curl http://your-ecs-url/api/v1/statistics
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run
```bash
# Build
docker build -t agriai-api .

# Run
docker run -p 8000:8000 --env-file .env agriai-api
```

---

## ☁️ AWS ECS Deployment

### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name agriai-api
```

### 2. Push Docker Image
```bash
# Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag agriai-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agriai-api:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agriai-api:latest
```

### 3. Create ECS Task Definition

**task-definition.json:**
```json
{
  "family": "agriai-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "agriai-api",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agriai-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "S3_BUCKET_NAME", "value": "agriai-images"},
        {"name": "MONGO_DATABASE", "value": "agriai_db"}
      ],
      "secrets": [
        {"name": "AWS_ACCESS_KEY_ID", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "MONGODB_URI", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agriai-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 4. Create ECS Service
```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name agriai-api \
  --task-definition agriai-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### 5. Setup Load Balancer (Optional)
Create an Application Load Balancer and target group pointing to the ECS service on port 8000.

---

## 🔗 Lambda Integration

### Lambda Function Example

```python
import json
import requests
import base64

def lambda_handler(event, context):
    """
    Lambda function to call ECS-hosted AgriAI API
    """
    
    # ECS service URL (from Load Balancer or Service Discovery)
    api_url = "http://your-alb-url.us-east-1.elb.amazonaws.com/api/v1/analyze-base64"
    
    # Extract data from Lambda event
    image_data = event.get('image_base64')
    filename = event.get('filename', 'image.jpg')
    user_uuid = event.get('user_id', 'anonymous')
    latitude = event.get('latitude')
    longitude = event.get('longitude')
    
    # Prepare request
    payload = {
        "file": f"data:image/jpeg;base64,{image_data}",
        "filename": filename,
        "uuid": user_uuid,
        "lat": latitude,
        "long": longitude,
        "crop_type": "oil_palm",
        "use_detection": True,
        "return_annotated_image": True
    }
    
    # Call API
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'image_id': result['image_id'],
                'database_id': result['database_id'],
                'total_bunches': result['analysis']['total_bunches'] if result.get('analysis') else 0,
                'original_url': result['original_image_url'],
                'annotated_url': result['annotated_image_url']
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

## 🎨 UI Integration

### React Example

```jsx
import React, { useState, useEffect } from 'react';

function AnalysisGallery() {
  const [analyses, setAnalyses] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchAnalyses();
  }, []);
  
  const fetchAnalyses = async (page = 0, limit = 20) => {
    const response = await fetch(
      `http://your-api-url/api/v1/analyses/all?limit=${limit}&skip=${page * limit}`
    );
    const data = await response.json();
    
    setAnalyses(data.data);
    setTotal(data.total);
    setLoading(false);
  };
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="gallery">
      <h1>All Analyses ({total})</h1>
      <div className="grid">
        {analyses.map(analysis => (
          <div key={analysis.image_id} className="card">
            <img src={analysis.annotated_image_presigned_url} alt={analysis.filename} />
            <div className="info">
              <h3>{analysis.filename}</h3>
              <p>Bunches: {analysis.total_bunches}</p>
              <p>Crop: {analysis.crop_type}</p>
              <p>User: {analysis.user_uuid}</p>
              <p>Date: {new Date(analysis.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalysisGallery;
```

---

## 📊 Data Flow

```
┌─────────────┐
│   Lambda    │
│  or Client  │
└──────┬──────┘
       │ POST /analyze-base64
       │ (base64 image + metadata)
       ▼
┌─────────────────────────────┐
│     ECS/FastAPI Service     │
│  1. Analyze with AI         │
│  2. Upload to S3            │
│  3. Save to MongoDB         │
└──────┬──────────────────────┘
       │
       ├─────► S3 Bucket
       │       ├─ originals/
       │       └─ annotated/
       │
       └─────► MongoDB
               └─ analyses collection
       
       
┌─────────────┐
│  UI Client  │
└──────┬──────┘
       │ GET /analyses/all
       ▼
┌─────────────────────────────┐
│     ECS/FastAPI Service     │
│  1. Query MongoDB           │
│  2. Generate presigned URLs │
│  3. Return data + URLs      │
└──────┬──────────────────────┘
       │
       ▼
  ┌──────────────┐
  │  UI displays │
  │  images from │
  │  presigned   │
  │  S3 URLs     │
  └──────────────┘
```

---

## 🔍 Monitoring

### Check Service Health
```bash
curl http://your-api-url/api/v1/health
```

### View Statistics
```bash
curl http://your-api-url/api/v1/statistics
```

### CloudWatch Logs
- Log Group: `/ecs/agriai-api`
- Check for MongoDB connection status
- Check for S3 access status

---

## ⚠️ Troubleshooting

### Issue: MongoDB Connection Failed
```bash
# Test connection string
mongosh "your-mongodb-uri"
```

**Solution:** Check:
- MongoDB URI is correct
- IP whitelist includes ECS NAT Gateway IPs
- Username/password are correct

### Issue: S3 Access Denied
```bash
# Test S3 access
aws s3 ls s3://agriai-images/ --profile your-profile
```

**Solution:** Check:
- AWS credentials are correct
- IAM user has S3 permissions
- Bucket exists in correct region

### Issue: Presigned URLs Not Working
**Solution:** 
- Check S3 bucket region matches AWS_REGION
- Verify bucket name is correct
- Ensure images exist in S3

---

## 📈 Scaling Considerations

### ECS Auto Scaling
```bash
# Setup target tracking
aws application-autoscaling put-scaling-policy \
  --policy-name cpu80 \
  --service-namespace ecs \
  --resource-id service/your-cluster/agriai-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    "TargetValue=80.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}"
```

### MongoDB Atlas Auto-Scaling
Enable auto-scaling in Atlas UI for storage and compute tier.

### S3 Performance
S3 automatically scales - no configuration needed.

---

## 💰 Cost Optimization

1. **S3 Lifecycle Policies**: Archive old images to Glacier
2. **ECS Spot Instances**: Use Fargate Spot for cost savings
3. **MongoDB**: Right-size cluster based on usage
4. **CloudWatch Logs**: Set retention period

---

## ✅ Production Checklist

- [ ] Environment variables secured (use AWS Secrets Manager)
- [ ] MongoDB IP whitelist configured
- [ ] S3 bucket encryption enabled
- [ ] CloudWatch logging enabled
- [ ] CORS configured for your domain
- [ ] Health check endpoint monitored
- [ ] Auto-scaling configured
- [ ] Backup strategy for MongoDB
- [ ] S3 lifecycle policies configured
- [ ] API authentication added (if needed)

---

## 📞 Support

**API Documentation:** `http://your-api-url/docs`

**Key Endpoints:**
- Analysis: `/api/v1/analyze-base64`
- Fetch All: `/api/v1/analyses/all` ⭐
- Statistics: `/api/v1/statistics`

---

**Quick Start Complete! 🎉**

You now have:
✅ API deployed on ECS
✅ Images stored in S3
✅ Data persisted in MongoDB
✅ UI-ready retrieval endpoint
✅ Lambda integration ready

