# AgriAI API Examples

Complete examples for integrating with the AgriAI API from various platforms.

## Starting the Server

```bash
# Start the API server
python main.py

# Server will run at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Testing Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "AgriAI Analysis API"
}
```

### 2. Get Supported Crops

```bash
curl http://localhost:8000/api/v1/supported-crops
```

Response:
```json
{
  "supported_crops": ["oil_palm"],
  "details": {
    "oil_palm": {
      "name": "Oil Palm",
      "scientific_name": "Elaeis guineensis",
      "stages": ["young", "mature", "ripe", "overripe"],
      "min_confidence": 0.6
    }
  }
}
```

### 3. Analyze Image - Complete Examples

#### Using curl

```bash
# Basic analysis
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "image=@oilpalm_samples/sample1.jpg" \
  -F "crop_type=oil_palm"

# With custom confidence threshold
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "image=@oilpalm_samples/sample2.jpg" \
  -F "crop_type=oil_palm" \
  -F "min_confidence=0.7" \
  -F "include_recommendations=true"
```

#### Using Python requests

```python
import requests
import json

def analyze_crop_image(image_path, crop_type='oil_palm', min_confidence=0.5):
    """Analyze a crop image"""
    url = 'http://localhost:8000/api/v1/analyze'
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'crop_type': crop_type,
            'min_confidence': min_confidence,
            'include_recommendations': True
        }
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        
        return response.json()

# Usage
result = analyze_crop_image('oilpalm_samples/sample1.jpg')

if result['success']:
    print(f"✓ Found {result['analysis']['total_bunches']} bunches")
    print(f"  Young: {result['analysis']['stage_summary']['young']}")
    print(f"  Mature: {result['analysis']['stage_summary']['mature']}")
    print(f"  Ripe: {result['analysis']['stage_summary']['ripe']}")
    
    for bunch in result['analysis']['bunches']:
        print(f"\nBunch #{bunch['id']}:")
        print(f"  Stage: {bunch['stage']}")
        print(f"  Confidence: {bunch['confidence']:.2%}")
        print(f"  Position: [{bunch['bounding_box']['x_min']}, "
              f"{bunch['bounding_box']['y_min']}, "
              f"{bunch['bounding_box']['x_max']}, "
              f"{bunch['bounding_box']['y_max']}]")
else:
    print(f"✗ Error: {result['error']}")
```

#### Using Python httpx (async)

```python
import httpx
import asyncio

async def analyze_image_async(image_path):
    """Async image analysis"""
    url = 'http://localhost:8000/api/v1/analyze'
    
    async with httpx.AsyncClient() as client:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'crop_type': 'oil_palm', 'min_confidence': 0.5}
            
            response = await client.post(url, files=files, data=data)
            response.raise_for_status()
            
            return response.json()

# Usage
result = asyncio.run(analyze_image_async('oilpalm_samples/sample1.jpg'))
print(result)
```

#### Using JavaScript/TypeScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function analyzeCropImage(imagePath, cropType = 'oil_palm') {
  const formData = new FormData();
  formData.append('image', fs.createReadStream(imagePath));
  formData.append('crop_type', cropType);
  formData.append('min_confidence', '0.5');
  formData.append('include_recommendations', 'true');
  
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/analyze',
      formData,
      {
        headers: formData.getHeaders()
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Analysis failed:', error.message);
    throw error;
  }
}

// Usage
analyzeCropImage('oilpalm_samples/sample1.jpg')
  .then(result => {
    if (result.success) {
      console.log(`Found ${result.analysis.total_bunches} bunches`);
      result.analysis.bunches.forEach(bunch => {
        console.log(`  ${bunch.stage}: ${(bunch.confidence * 100).toFixed(0)}%`);
      });
    }
  });
```

#### Using JavaScript (Browser/React)

```javascript
// React component example
import React, { useState } from 'react';

function CropAnalyzer() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);
  
  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Preview image
    setImageUrl(URL.createObjectURL(file));
    
    // Analyze image
    setLoading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('crop_type', 'oil_palm');
    formData.append('min_confidence', '0.5');
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const drawBoundingBoxes = (canvasRef) => {
    if (!canvasRef.current || !result || !result.success) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      
      // Draw bounding boxes
      result.analysis.bunches.forEach(bunch => {
        const box = bunch.bounding_box;
        
        // Draw rectangle
        ctx.strokeStyle = bunch.color_code;
        ctx.lineWidth = 3;
        ctx.strokeRect(
          box.x_min,
          box.y_min,
          box.x_max - box.x_min,
          box.y_max - box.y_min
        );
        
        // Draw label background
        ctx.fillStyle = bunch.color_code;
        ctx.fillRect(box.x_min, box.y_min - 25, 120, 25);
        
        // Draw label text
        ctx.fillStyle = 'white';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(
          `${bunch.stage} ${(bunch.confidence * 100).toFixed(0)}%`,
          box.x_min + 5,
          box.y_min - 8
        );
      });
    };
    
    img.src = imageUrl;
  };
  
  return (
    <div>
      <input type="file" accept="image/*" onChange={handleImageUpload} />
      
      {loading && <p>Analyzing...</p>}
      
      {result && result.success && (
        <div>
          <h3>Analysis Results</h3>
          <p>Total bunches: {result.analysis.total_bunches}</p>
          <ul>
            <li>Young: {result.analysis.stage_summary.young}</li>
            <li>Mature: {result.analysis.stage_summary.mature}</li>
            <li>Ripe: {result.analysis.stage_summary.ripe}</li>
          </ul>
          
          <canvas ref={canvasRef => drawBoundingBoxes({ current: canvasRef })} />
        </div>
      )}
    </div>
  );
}

export default CropAnalyzer;
```

## Response Format

Complete response structure:

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
      },
      {
        "id": 2,
        "stage": "mature",
        "confidence": 0.87,
        "bounding_box": {
          "x_min": 300,
          "y_min": 150,
          "x_max": 420,
          "y_max": 280,
          "center_x": 360,
          "center_y": 215
        },
        "color_code": "#FFA500",
        "description": "Maturing bunch approaching harvest"
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
      "Monitor 2 mature bunches for optimal harvest timing within 1-2 weeks",
      "Tree shows good health with diverse bunch stages"
    ]
  },
  "image_metadata": {
    "width": 1920,
    "height": 1080,
    "analyzed_at": "2026-01-29T03:50:00.123456",
    "file_size_kb": 3102.5
  },
  "processing_time_ms": 2450.5,
  "error": null
}
```

## Error Handling

Error response format:

```json
{
  "success": false,
  "crop_type": "oil_palm",
  "analysis": null,
  "image_metadata": {
    "width": 0,
    "height": 0,
    "analyzed_at": "2026-01-29T03:50:00",
    "file_size_kb": null
  },
  "processing_time_ms": 150.0,
  "error": "Invalid image file: cannot identify image file"
}
```

Common error scenarios:

```python
# Handle errors properly
try:
    result = analyze_crop_image('invalid.jpg')
    if not result['success']:
        print(f"Analysis failed: {result['error']}")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Drawing Bounding Boxes - Complete Example

```javascript
function drawAnalysisResults(imageElement, analysisResult, canvasElement) {
  const canvas = canvasElement;
  const ctx = canvas.getContext('2d');
  
  // Set canvas size to match image
  canvas.width = analysisResult.image_metadata.width;
  canvas.height = analysisResult.image_metadata.height;
  
  // Draw image
  ctx.drawImage(imageElement, 0, 0);
  
  // Draw each bunch
  analysisResult.analysis.bunches.forEach((bunch, index) => {
    const box = bunch.bounding_box;
    const width = box.x_max - box.x_min;
    const height = box.y_max - box.y_min;
    
    // Draw bounding box
    ctx.strokeStyle = bunch.color_code;
    ctx.lineWidth = 4;
    ctx.strokeRect(box.x_min, box.y_min, width, height);
    
    // Draw semi-transparent fill
    ctx.fillStyle = bunch.color_code + '20'; // Add alpha
    ctx.fillRect(box.x_min, box.y_min, width, height);
    
    // Draw label background
    const label = `${bunch.stage.toUpperCase()} (${(bunch.confidence * 100).toFixed(0)}%)`;
    ctx.font = 'bold 16px Arial';
    const textWidth = ctx.measureText(label).width;
    
    ctx.fillStyle = bunch.color_code;
    ctx.fillRect(box.x_min, box.y_min - 30, textWidth + 20, 30);
    
    // Draw label text
    ctx.fillStyle = 'white';
    ctx.fillText(label, box.x_min + 10, box.y_min - 10);
    
    // Draw center point
    ctx.fillStyle = bunch.color_code;
    ctx.beginPath();
    ctx.arc(box.center_x, box.center_y, 5, 0, 2 * Math.PI);
    ctx.fill();
  });
  
  // Draw summary
  ctx.font = 'bold 20px Arial';
  ctx.fillStyle = 'white';
  ctx.strokeStyle = 'black';
  ctx.lineWidth = 3;
  const summary = `Total: ${analysisResult.analysis.total_bunches} bunches`;
  ctx.strokeText(summary, 10, 30);
  ctx.fillText(summary, 10, 30);
}
```

## Batch Processing Example

```python
import os
from pathlib import Path
import requests
import json

def batch_analyze_directory(directory_path, output_file='results.json'):
    """Analyze all images in a directory"""
    results = []
    image_files = list(Path(directory_path).glob('*.jpg'))
    
    print(f"Found {len(image_files)} images to analyze")
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Analyzing {image_path.name}...")
        
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    'http://localhost:8000/api/v1/analyze',
                    files={'image': f},
                    data={'crop_type': 'oil_palm', 'min_confidence': 0.5}
                )
                
                result = response.json()
                results.append({
                    'filename': image_path.name,
                    'result': result
                })
                
                if result['success']:
                    bunches = result['analysis']['total_bunches']
                    print(f"  ✓ Found {bunches} bunches")
                else:
                    print(f"  ✗ Failed: {result['error']}")
                    
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'filename': image_path.name,
                'error': str(e)
            })
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    return results

# Usage
batch_analyze_directory('oilpalm_samples', 'batch_results.json')
```

## Performance Tips

1. **Image Size**: Resize large images before uploading for faster processing
2. **Confidence Threshold**: Use 0.6-0.7 for production, 0.5 for testing
3. **Batch Processing**: Add delays between requests to avoid overload
4. **Error Handling**: Always check `success` field before accessing `analysis`
5. **Timeouts**: Set appropriate timeouts (30-60 seconds recommended)

```python
# Example with timeout and retries
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

response = session.post(
    url,
    files=files,
    data=data,
    timeout=60  # 60 seconds timeout
)
```
