# AgriAI - Agricultural Analysis API

A production-ready AI-powered agricultural analysis system for detecting and analyzing oil palm fruit bunches with precise bounding box detection, ripeness classification, and health assessment.

---

## 🌳 FFB Multi-View Counting Project

**New Project:** Multi-view unique FFB counting using 3D triangulation  
**Documentation:** See [`docs/README.md`](docs/README.md)  
**Current Status:** Phase 1 - Data Annotation & Training  

For FFB project work: Start at [`docs/README.md`](docs/README.md)

---

## Features

- **Advanced Fruit Bunch Detection**: Uses Roboflow + Hybrid AI analysis for accurate detection
- **Ripeness Classification**: Classifies bunches into stages (young, mature, ripe, overripe)
- **Precise Bounding Box Localization**: Provides exact pixel coordinates for each detected bunch
- **Color-Coded Visualization**: Automatic color assignment for easy frontend rendering
- **Health & Quality Scoring**: Calculates tree health and fruit quality metrics
- **Smart Recommendations**: Provides actionable harvesting guidance based on analysis
- **Multi-Format Support**: Accepts file uploads and Base64-encoded images
- **Cloud Storage Integration**: AWS S3 for original and annotated image storage
- **Persistent Data**: MongoDB for storing analysis results
- **Extensible Architecture**: Easy to add new crop types and detection backends

## Technology Stack

### Core Framework
- **Backend**: FastAPI (Python 3.10+)
- **Server**: Uvicorn ASGI server
- **API Documentation**: Auto-generated Swagger UI at `/docs`

### AI & Detection
- **Primary AI Model**: Claude 3.5 Sonnet (Amazon Bedrock)
- **Object Detection**: Roboflow (trained oil palm detection model)
  - Model ID: `thesis-project-kbu79/palm-daffan`
  - Version: 1
  - Backend: Roboflow API
- **Alternative Detection**: YOLOv8 (optional local detection)
- **Inference**: AWS Bedrock with vision capabilities

### Cloud Services
- **AWS Bedrock**: Claude 3.5 Sonnet inference (ap-south-1 region)
- **AWS S3**: Image storage for originals and annotated versions
- **AWS IAM**: Authentication and authorization
- **AWS ECS**: Containerized deployment (optional)

### Data & Storage
- **Database**: MongoDB (async with Motor driver)
- **Cache**: Redis (optional, for performance optimization)
- **Image Processing**: Pillow (PIL), OpenCV, NumPy

### Development & Testing
- **Testing**: Pytest with async support
- **Image Analysis**: 12 sample images included for testing
- **Containerization**: Docker with multi-stage builds
- **Git**: SSH authentication for separate account management

## Project Structure

```
AgriAI/
├── config/
│   ├── __init__.py
│   └── settings.py                 # Configuration management
│
├── services/
│   ├── __init__.py
│   ├── bedrock_service.py          # AWS Bedrock Claude integration
│   ├── s3_service.py               # AWS S3 image storage
│   ├── mongodb_service.py          # MongoDB data persistence
│   ├── object_detector.py          # Multi-backend detection (Roboflow, YOLO)
│   ├── crop_analyzer.py            # Main orchestration
│   ├── hybrid_analyzer.py          # Combined detection + AI analysis
│   ├── image_processor.py          # Image compression & preprocessing
│   └── image_annotator.py          # Bounding box visualization
│
├── models/
│   ├── __init__.py
│   ├── schemas.py                  # Pydantic request/response models
│   └── crop_configs.py             # Crop-specific configurations
│
├── routes/
│   ├── __init__.py
│   └── analysis.py                 # API endpoints
│
├── prompts/
│   ├── __init__.py
│   └── oil_palm_prompts.py         # AI prompt templates
│
├── utils/
│   ├── __init__.py
│   ├── response_formatter.py       # Response formatting
│   └── validators.py               # Input validation
│
├── tests/
│   ├── __init__.py
│   └── test_with_samples.py        # Integration tests
│
├── oilpalm_samples/                # 12 sample images for testing
│
├── main.py                         # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── taskdef.json                    # AWS ECS task definition
├── .env                            # Environment variables (git-ignored)
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Installation

### 1. Clone or Navigate to Project Directory

```bash
cd AgriAI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create or update your `.env` file with:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1

# AWS Bedrock (Claude 3.5 Sonnet)
SONNET_INFERENCE_PROFILE_ARN=arn:aws:bedrock:ap-south-1:YOUR_ACCOUNT_ID:inference-profile/apac.anthropic.claude-3-5-sonnet-20240620-v1:0
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0

# AWS S3 (Image Storage)
S3_BUCKET_NAME=ai-img-upload
S3_ORIGINAL_PREFIX=originals/
S3_ANNOTATED_PREFIX=annotated/

# MongoDB (Data Persistence)
MONGODB_URI=mongodb://username:password@host:port/
MONGO_DATABASE=dev
MONGO_COLLECTION=ai-image-data-fetch

# Object Detection (Roboflow)
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=roboflow
DETECTION_CONFIDENCE=0.80
ROBOFLOW_API_KEY=your_roboflow_api_key
ROBOFLOW_MODEL_ID=thesis-project-kbu79/palm-daffan
ROBOFLOW_VERSION=1

# Alternative: Local YOLO Detection (optional)
YOLO_MODEL_PATH=yolov8n.pt
YOLO_USE_API=false

# Optional Services
REDIS_ENDPOINT=your_redis_endpoint
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

## Usage

### Starting the API Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`

### Testing with Sample Images

Test a single sample:

```bash
python tests/test_with_samples.py 1
```

Test all 12 samples:

```bash
python tests/test_with_samples.py all
```

## API Endpoints

### 1. Analyze Crop Image (File Upload)

**POST** `/api/v1/analyze`

Analyze a crop image from file upload.

**Form Data**:
- `image` (file, required): Image file (JPEG/PNG, max 10MB)
- `crop_type` (string): Type of crop (default: `"oil_palm"`)
- `min_confidence` (float): Minimum confidence threshold 0.0-1.0 (default: 0.5)
- `include_recommendations` (boolean): Include recommendations (default: true)

**Example using curl**:

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "image=@oilpalm_samples/sample1.jpg" \
  -F "crop_type=oil_palm" \
  -F "min_confidence=0.6"
```

**Example using Python**:

```python
import requests

with open('oilpalm_samples/sample1.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'crop_type': 'oil_palm',
        'min_confidence': 0.6
    }
    response = requests.post('http://localhost:8000/api/v1/analyze', 
                            files=files, data=data)
    result = response.json()
    print(result)
```

### 2. Analyze Crop Image (Base64)

**POST** `/api/v1/analyze-base64`

Analyze a crop image from Base64-encoded data.

**Request Body**:

```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "crop_type": "oil_palm",
  "min_confidence": 0.6,
  "include_recommendations": true
}
```

**Example using Python**:

```python
import requests
import base64

with open('oilpalm_samples/sample1.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode()

payload = {
    "image_base64": f"data:image/jpeg;base64,{image_base64}",
    "crop_type": "oil_palm",
    "min_confidence": 0.6
}

response = requests.post('http://localhost:8000/api/v1/analyze-base64', 
                        json=payload)
result = response.json()
print(result)
```

### 3. Retrieve Analysis Result

**GET** `/api/v1/analysis/{image_id}`

Retrieve a previously stored analysis result by image ID.

### 4. Get User Analyses

**GET** `/api/v1/analyses/user/{user_uuid}`

Get all analyses for a specific user.

### 5. Health Check

**GET** `/api/v1/health`

Check API health and configuration status.

### 6. Supported Crops

**GET** `/api/v1/supported-crops`

Get list of supported crop types and their configurations.

### 7. Statistics

**GET** `/api/v1/statistics`

Get system statistics and analysis metrics.

## Response Format

```json
{
  "success": true,
  "crop_type": "oil_palm",
  "analysis": {
    "total_bunches": 3,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.95,
        "bounding_box": {
          "x_min": 520,
          "y_min": 650,
          "x_max": 780,
          "y_max": 850,
          "center_x": 650,
          "center_y": 750
        },
        "color_code": "#FF0000",
        "description": "Large ripe bunch ready for harvest"
      }
    ],
    "stage_summary": {
      "young": 0,
      "mature": 1,
      "ripe": 2,
      "overripe": 0
    },
    "health_score": 85.0,
    "recommendations": [
      "Harvest 2 ripe bunches immediately",
      "Monitor 1 mature bunch for optimal timing"
    ]
  },
  "image_metadata": {
    "width": 1536,
    "height": 2048,
    "analyzed_at": "2026-04-06T10:30:00",
    "file_size_kb": 1302.0
  },
  "processing_time_ms": 9500
}
```

## Detection System: Roboflow Integration

The system uses **Roboflow** as the primary object detection backend for identifying fruit bunches:

### How It Works

1. **Image Upload**: Image is received and validated
2. **Roboflow Detection**: Image is sent to Roboflow API for bunch localization
   - Model: `thesis-project-kbu79/palm-daffan` (v1)
   - Returns: Bounding boxes with confidence scores
3. **AI Analysis**: Detected bunches are analyzed with Claude 3.5 Sonnet
   - Determines ripeness stage (young, mature, ripe, overripe)
   - Generates health scores and recommendations
   - Validates and refines bounding boxes
4. **Response**: Combined results with visualization-ready bounding boxes and color codes

### Roboflow Configuration

```python
# In config/settings.py
DETECTION_BACKEND = "roboflow"
DETECTION_CONFIDENCE = 0.80  # 80% minimum confidence threshold
ROBOFLOW_API_KEY = "your_api_key"
ROBOFLOW_MODEL_ID = "thesis-project-kbu79/palm-daffan"
ROBOFLOW_VERSION = 1
```

### Alternative: Local YOLO Detection

If you prefer local detection without API calls:

```env
USE_OBJECT_DETECTION=true
DETECTION_BACKEND=yolo
YOLO_MODEL_PATH=yolov8n.pt
YOLO_USE_API=false
```

## Frontend Integration

### Drawing Bounding Boxes

Use the bounding box coordinates to visualize detections on the image:

```javascript
// Example using HTML Canvas
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Load and draw image
const img = new Image();
img.onload = () => {
  ctx.drawImage(img, 0, 0);
  
  // Draw bounding boxes for each bunch
  response.analysis.bunches.forEach(bunch => {
    const box = bunch.bounding_box;
    
    // Draw rectangle with stage color
    ctx.strokeStyle = bunch.color_code;
    ctx.lineWidth = 3;
    ctx.strokeRect(
      box.x_min,
      box.y_min,
      box.x_max - box.x_min,
      box.y_max - box.y_min
    );
    
    // Draw label with stage and confidence
    ctx.fillStyle = bunch.color_code;
    ctx.font = "14px Arial";
    ctx.fillText(
      `${bunch.stage} (${(bunch.confidence * 100).toFixed(0)}%)`,
      box.x_min,
      box.y_min - 5
    );
  });
};
img.src = 'analyzed-image.jpg';
```

### Color Coding Reference

| Stage | Color | Hex Code | Meaning |
|-------|-------|----------|---------|
| Young | Light Green | `#90EE90` | Unripe, not ready for harvest |
| Mature | Orange | `#FFA500` | Approaching harvest (1-2 weeks) |
| Ripe | Red | `#FF0000` | Ready for immediate harvest |
| Overripe | Dark Red | `#8B0000` | Past optimal harvest time |

## Adding New Crop Types

To extend the system for additional crops:

### 1. Add Crop Enum

In `models/schemas.py`:

```python
class CropType(str, Enum):
    OIL_PALM = "oil_palm"
    RUBBER = "rubber"  # New crop
    COFFEE = "coffee"  # New crop
```

### 2. Create Crop Configuration

In `models/crop_configs.py`:

```python
rubber_stages = [
    StageConfig(name="young", color_code="#90EE90", ...),
    StageConfig(name="mature", color_code="#FFA500", ...),
    # ... other stages
]

self.configs["rubber"] = CropConfig(
    crop_type="rubber",
    stages=rubber_stages,
    # ... other config
)
```

### 3. Create Prompt Template

In `prompts/`:

```python
# rubber_prompts.py
RUBBER_ANALYSIS_PROMPT = """
You are an expert in rubber tree analysis...
"""
```

### 4. Update Analyzer

In `services/crop_analyzer.py`, add handling for the new crop type and its prompt.

## Configuration

Key settings are managed in `config/settings.py`:

### Image Processing
- `MAX_IMAGE_SIZE_MB`: Maximum file size (10MB)
- `MAX_IMAGE_DIMENSION`: Maximum width/height (2048px)
- `JPEG_QUALITY`: Compression quality (85%)
- `BASE64_SIZE_LIMIT_MB`: Max Base64 size (5MB)

### AI Model
- `BEDROCK_MODEL_ID`: Claude 3.5 Sonnet model ID
- `BEDROCK_TEMPERATURE`: Inference temperature (0.1 for consistency)
- `BEDROCK_MAX_TOKENS`: Maximum response tokens (4096)

### Detection
- `DETECTION_CONFIDENCE`: Minimum confidence threshold (0.80)
- `USE_OBJECT_DETECTION`: Enable Roboflow detection (true)
- `DETECTION_BACKEND`: Choose backend ("roboflow" or "yolo")

## Performance Characteristics

- **Processing Time**: 9-10 seconds per image (includes Bedrock inference)
- **Detection Accuracy**: 85-95% confidence on average
- **Image Support**: Up to 10MB, auto-resized to 2048x2048 maximum
- **Concurrent Requests**: Scales with Bedrock quota
- **Response Format**: Consistent JSON with precise bounding boxes

## Docker Deployment

### Build Image

```bash
docker build -t agriai-api:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=ap-south-1 \
  -e BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0 \
  -e SONNET_INFERENCE_PROFILE_ARN=your_arn \
  -e ROBOFLOW_API_KEY=your_key \
  agriai-api:latest
```

## AWS ECS Deployment

Use `taskdef.json` for AWS ECS deployment:

```bash
aws ecs register-task-definition --cli-input-json file://taskdef.json
```

## Troubleshooting

### AWS Bedrock Errors
- Ensure AWS credentials are valid and have Bedrock access
- Verify Bedrock model is available in your region (ap-south-1)
- Check inference profile ARN is correct

### Roboflow Detection Issues
- Verify Roboflow API key is valid
- Ensure model ID and version are correct
- Check internet connectivity for API calls

### Image Processing Errors
- Verify image format is JPEG or PNG
- Ensure image is not corrupted
- Check file size is under 10MB

### MongoDB Connection
- Verify MongoDB URI in `.env`
- Check database credentials
- Ensure database is accessible from your network

## Git Configuration

This repository uses SSH authentication with a separate GitHub account:

- **SSH Key**: `~/.ssh/id_ed25519_udbhav`
- **Git User**: `udbhav-kalya`
- **Remote Host**: `github-udbhav`

To clone or push:

```bash
git clone git@github-udbhav:udbhav-kalyalabs/ffb-backend.git
git push origin master
```

## Future Enhancements

- [ ] Batch processing for multiple images
- [ ] Disease and pest detection
- [ ] Historical trend analysis and reporting
- [ ] Real-time monitoring with IoT device integration
- [ ] Mobile app support
- [ ] Multi-language recommendations
- [ ] Advanced analytics dashboard
- [ ] Custom model training pipeline

## License

Proprietary - AgriAI Project by Kalya Labs

## Support

For issues, questions, or feature requests, contact the AgriAI development team at udbhav@kalyalabs.com
