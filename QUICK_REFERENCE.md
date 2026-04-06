# AgriAI - Quick Reference Card

## 🚀 Quick Commands

```bash
# Install
pip install -r requirements.txt

# Test configuration
python -c "from config.settings import settings; settings.validate(); print('✓ OK')"

# Test single sample
python tests/test_with_samples.py 1

# Test all samples
python tests/test_with_samples.py all

# Start API server
python main.py
```

## 📡 API Endpoints

```bash
# Analyze image
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "image=@path/to/image.jpg" \
  -F "crop_type=oil_palm" \
  -F "min_confidence=0.6"

# Health check
curl http://localhost:8000/api/v1/health

# Supported crops
curl http://localhost:8000/api/v1/supported-crops
```

## 🎨 Color Codes

| Stage | Color | Hex |
|-------|-------|-----|
| Young | 🟢 Light Green | `#90EE90` |
| Mature | 🟠 Orange | `#FFA500` |
| Ripe | 🔴 Red | `#FF0000` |
| Overripe | 🔴 Dark Red | `#8B0000` |

## 📊 Response Structure

```json
{
  "success": true,
  "analysis": {
    "total_bunches": 3,
    "bunches": [{
      "id": 1,
      "stage": "ripe",
      "confidence": 0.95,
      "bounding_box": {
        "x_min": 520, "y_min": 650,
        "x_max": 780, "y_max": 850,
        "center_x": 650, "center_y": 750
      },
      "color_code": "#FF0000"
    }],
    "stage_summary": {"young": 0, "mature": 1, "ripe": 2},
    "health_score": 85.0,
    "recommendations": [...]
  }
}
```

## 🎯 Frontend Integration

```javascript
// Upload and draw
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST', body: formData
})
.then(r => r.json())
.then(data => {
  data.analysis.bunches.forEach(b => {
    ctx.strokeStyle = b.color_code;
    ctx.strokeRect(
      b.bounding_box.x_min,
      b.bounding_box.y_min,
      b.bounding_box.x_max - b.bounding_box.x_min,
      b.bounding_box.y_max - b.bounding_box.y_min
    );
  });
});
```

## ⚙️ Configuration

**Model**: Claude 3.5 Sonnet  
**Region**: ap-south-1  
**Max Size**: 2048x2048px  
**Processing**: ~9-10 seconds  
**Confidence**: 85-95%

## 📁 Key Files

- `main.py` - API server
- `config/settings.py` - Configuration
- `services/bedrock_service.py` - AI model
- `tests/test_with_samples.py` - Testing
- `.env` - AWS credentials

## 🔧 Troubleshooting

```bash
# Check config
python -c "from config.settings import settings; print(settings.BEDROCK_INFERENCE_PROFILE_ARN)"

# Test image processing
python -c "from services.image_processor import image_processor; print('✓ Import OK')"

# View logs
# All output goes to console with INFO level
```

## 📚 Documentation

- `README.md` - Full documentation
- `QUICK_START.md` - Get started guide
- `API_EXAMPLES.md` - Code examples
- `FINAL_STATUS.md` - Project status
- `/docs` - Interactive API docs (when server running)

## ✅ Checklist

- [x] Dependencies installed
- [x] Configuration validated
- [x] Test passes
- [x] API server starts
- [ ] Frontend integrated
- [ ] Production deployment

## 🆘 Quick Help

**Issue**: Image too large  
**Fix**: Already handled, auto-compressed to <5MB

**Issue**: Slow processing  
**Fix**: Normal, AI analysis takes 9-10s

**Issue**: AWS credentials error  
**Fix**: Check `.env` file exists with valid keys

**Issue**: Wrong detections  
**Fix**: Adjust `min_confidence` parameter (0.5-0.8)

---

**Status**: ✅ READY  
**Version**: 1.0.0  
**Model**: Claude 3.5 Sonnet
