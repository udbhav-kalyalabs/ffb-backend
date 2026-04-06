# AgriAI - Agricultural Analysis API

An intelligent AI-powered system for analyzing agricultural crops using Amazon Bedrock's Llama 4 Maverick model. Currently specialized in oil palm tree fruit bunch detection and ripeness classification.

## Features

- **Fruit Bunch Detection**: Automatically detects and counts fruit bunches in crop images
- **Ripeness Classification**: Classifies bunches into stages (young, mature, ripe, overripe)
- **Precise Localization**: Provides bounding box coordinates for each detected bunch
- **Visual Markers**: Assigns color codes for easy visualization on frontend
- **Health Assessment**: Calculates overall tree health scores
- **Actionable Recommendations**: Provides harvesting recommendations based on analysis
- **Extensible Design**: Easily add support for new crop types

## Technology Stack

- **Backend**: Python 3.10+ with FastAPI
- **AI Model**: Amazon Bedrock - meta.llama4-maverick-17b-instruct-v1:0
- **Image Processing**: Pillow (PIL)
- **Cloud**: AWS (Bedrock Runtime)

## Project Structure

```
AgriAI/
├── config/              # Configuration and settings
├── services/            # Core business logic
│   ├── bedrock_service.py    # AWS Bedrock integration
│   ├── image_processor.py    # Image preprocessing
│   └── crop_analyzer.py      # Main analysis orchestration
├── models/              # Data models and schemas
│   ├── schemas.py            # Pydantic models
│   └── crop_configs.py       # Crop-specific configurations
├── routes/              # API endpoints
├── prompts/             # AI prompt templates
├── utils/               # Utility functions
├── tests/               # Test scripts
└── oilpalm_samples/     # Sample images for testing
```

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Your `.env` file should already contain:
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_REGION=us-east-1
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

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Testing with Sample Images

Test a single sample image:
```bash
python tests/test_with_samples.py 1
```

Test all sample images:
```bash
python tests/test_with_samples.py all
```

### API Endpoints

#### 1. Analyze Crop Image
**POST** `/api/v1/analyze`

Upload an image for analysis.

**Form Data**:
- `image` (file): Image file (JPEG/PNG)
- `crop_type` (string): Type of crop (default: "oil_palm")
- `include_recommendations` (boolean): Include recommendations (default: true)
- `min_confidence` (float): Minimum confidence threshold 0.0-1.0 (default: 0.5)

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
        'min_confidence': 0.5
    }
    response = requests.post('http://localhost:8000/api/v1/analyze', files=files, data=data)
    result = response.json()
    print(result)
```

**Response Format**:
```json
{
  "success": true,
  "crop_type": "oil_palm",
  "analysis": {
    "total_bunches": 5,
    "bunches": [
      {
        "id": 1,
        "stage": "ripe",
        "confidence": 0.92,
        "bounding_box": {
          "x_min": 120,
          "y_min": 200,
          "x_max": 250,
          "y_max": 320,
          "center_x": 185,
          "center_y": 260
        },
        "color_code": "#FF0000",
        "description": "Large ripe bunch ready for harvest"
      }
    ],
    "stage_summary": {
      "young": 1,
      "mature": 2,
      "ripe": 2,
      "overripe": 0
    },
    "health_score": 85.5,
    "recommendations": [
      "2 bunches are ripe and ready for immediate harvest",
      "Monitor mature bunches for optimal harvest timing"
    ]
  },
  "image_metadata": {
    "width": 1920,
    "height": 1080,
    "analyzed_at": "2026-01-29T03:50:00",
    "file_size_kb": 3102.5
  },
  "processing_time_ms": 2450.5
}
```

#### 2. Health Check
**GET** `/api/v1/health`

Check API health status.

#### 3. Supported Crops
**GET** `/api/v1/supported-crops`

Get list of supported crop types and their configurations.

## Frontend Integration

### Drawing Bounding Boxes

Use the bounding box coordinates to draw rectangles on your image:

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
    ctx.strokeStyle = bunch.color_code;
    ctx.lineWidth = 3;
    ctx.strokeRect(
      box.x_min,
      box.y_min,
      box.x_max - box.x_min,
      box.y_max - box.y_min
    );
    
    // Add label
    ctx.fillStyle = bunch.color_code;
    ctx.fillText(
      `${bunch.stage} (${(bunch.confidence * 100).toFixed(0)}%)`,
      box.x_min,
      box.y_min - 5
    );
  });
};
img.src = 'your-image.jpg';
```

### Color Coding

The API assigns color codes based on ripeness stage:

- **Young** (Unripe): `#90EE90` (Light Green)
- **Mature**: `#FFA500` (Orange)
- **Ripe**: `#FF0000` (Red)
- **Overripe**: `#8B0000` (Dark Red)

## Adding New Crop Types

To add support for a new crop type:

1. **Add crop enum** in `models/schemas.py`:
   ```python
   class CropType(str, Enum):
       OIL_PALM = "oil_palm"
       RUBBER = "rubber"  # New crop
   ```

2. **Add configuration** in `models/crop_configs.py`:
   ```python
   rubber_stages = [
       StageConfig(name="young", color_code="#90EE90", ...),
       # ... other stages
   ]
   self.configs["rubber"] = CropConfig(...)
   ```

3. **Create prompt template** in `prompts/` directory

4. **Update analyzer** in `services/crop_analyzer.py` to use the new prompt

## Configuration

Key settings in `config/settings.py`:

- `BEDROCK_MODEL_ID`: The Bedrock model to use
- `BEDROCK_TEMPERATURE`: Model temperature (0.1 for consistent analysis)
- `MAX_IMAGE_SIZE_MB`: Maximum image file size (10MB)
- `MAX_IMAGE_DIMENSION`: Maximum image width/height (4096px)

## Architecture Highlights

### Extensible Design
- **Crop Configurations**: Easily add new crops without changing core logic
- **Stage Definitions**: Flexible stage definitions per crop type
- **Prompt Templates**: Separate prompt engineering from business logic

### Robust Processing
- **Image Validation**: Validates format, size, and content
- **Automatic Resizing**: Handles large images efficiently
- **Error Handling**: Comprehensive error handling throughout the pipeline

### AI-Powered Analysis
- **Advanced Prompting**: Detailed prompts for accurate detection
- **Structured Output**: Enforces JSON schema for consistent parsing
- **Confidence Scoring**: Filters low-confidence detections

## Performance

- Typical processing time: 2-4 seconds per image
- Supports images up to 10MB
- Automatically resizes large images while preserving quality

## Troubleshooting

### AWS Credentials Error
Ensure your `.env` file has valid AWS credentials with Bedrock access.

### Model Not Found
Verify that the model `meta.llama4-maverick-17b-instruct-v1:0` is available in your AWS region (us-east-1).

### Image Processing Errors
- Check image format (JPEG/PNG only)
- Ensure image is not corrupted
- Verify image size is under 10MB

## Future Enhancements

- [ ] Support for additional crop types (rubber, coffee, etc.)
- [ ] Batch processing of multiple images
- [ ] Disease detection capabilities
- [ ] Historical analysis tracking
- [ ] Integration with IoT devices
- [ ] Mobile app support

## License

Proprietary - AgriAI Project

## Support

For issues or questions, please contact the development team.
