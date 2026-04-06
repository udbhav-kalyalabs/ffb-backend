"""
Object detection service for precise bounding box localization
Supports multiple backends: Ultralytics YOLO, Roboflow, Custom endpoints
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)


class Detection:
    """Represents a detected object with bounding box and optional segmentation mask"""
    def __init__(self, bbox: List[float], confidence: float, class_id: int = 0, class_name: str = "bunch", 
                 segmentation: Optional[List[List[float]]] = None, area: Optional[float] = None):
        self.bbox = bbox  # [x_min, y_min, x_max, y_max]
        self.confidence = confidence
        self.class_id = class_id
        self.class_name = class_name
        self.segmentation = segmentation  # List of [x, y] points forming the contour
        self.area = area  # Actual area in pixels (for segmentation masks)
        
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "bbox": self.bbox,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name
        }
        if self.segmentation:
            result["segmentation"] = self.segmentation
        if self.area:
            result["area"] = self.area
        return result


class ObjectDetector(ABC):
    """Base class for object detection backends"""
    
    @abstractmethod
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """
        Detect objects in image
        
        Args:
            image_bytes: Raw image bytes
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of Detection objects
        """
        pass


class UltralyticsYOLODetector(ObjectDetector):
    """
    Ultralytics YOLO detector (local or API)
    Can use pre-trained models or custom trained models
    """
    
    def __init__(self, model_path: str = "yolov8n.pt", use_api: bool = False, api_key: Optional[str] = None):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model weights or model name
            use_api: Whether to use Ultralytics HUB API
            api_key: API key for Ultralytics HUB
        """
        self.model_path = model_path
        self.use_api = use_api
        self.api_key = api_key
        self.model = None
        
        if not use_api:
            try:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
                logger.info(f"Loaded YOLO model: {model_path}")
            except ImportError:
                logger.error("Ultralytics not installed. Install with: pip install ultralytics")
                raise
    
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """Detect objects using YOLO"""
        if self.use_api:
            return self._detect_api(image_bytes, confidence_threshold)
        else:
            return self._detect_local(image_bytes, confidence_threshold)
    
    def _detect_local(self, image_bytes: bytes, confidence_threshold: float) -> List[Detection]:
        """Run local YOLO inference"""
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run inference
        results = self.model(image, conf=confidence_threshold, verbose=False)
        
        # Parse results
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()  # [x_min, y_min, x_max, y_max]
                conf = float(boxes.conf[i].cpu().numpy())
                cls = int(boxes.cls[i].cpu().numpy())
                
                # Get class name if available
                class_name = result.names[cls] if result.names else "object"
                
                detections.append(Detection(
                    bbox=box.tolist(),
                    confidence=conf,
                    class_id=cls,
                    class_name=class_name
                ))
        
        logger.info(f"YOLO detected {len(detections)} objects")
        return detections
    
    def _detect_api(self, image_bytes: bytes, confidence_threshold: float) -> List[Detection]:
        """Run YOLO inference via Ultralytics API"""
        # TODO: Implement API call to Ultralytics HUB
        raise NotImplementedError("Ultralytics API integration not yet implemented")


class RoboflowDetector(ObjectDetector):
    """
    Roboflow object detection API
    Supports pre-trained and custom models
    """
    
    def __init__(self, api_key: str, model_id: str, version: int = 1):
        """
        Initialize Roboflow detector
        
        Args:
            api_key: Roboflow API key
            model_id: Model ID (workspace/project format)
            version: Model version number
        """
        self.api_key = api_key
        self.model_id = model_id
        self.version = version
        
        logger.info(f"Initializing RoboflowDetector with model_id={model_id}, version={version}")
        
        try:
            from roboflow import Roboflow
            rf = Roboflow(api_key=api_key)
            
            # Try to load the model - handle both private and Universe (public) models
            try:
                if '/' in model_id:
                    workspace_id, project_id = model_id.split('/', 1)
                    logger.info(f"Loading Roboflow model: workspace={workspace_id}, project={project_id}, version={version}")
                    project = rf.workspace(workspace_id).project(project_id)
                else:
                    logger.info(f"Loading Roboflow project: {model_id}, version={version}")
                    project = rf.workspace().project(model_id)
                
                self.model = project.version(version).model
                logger.info(f"Successfully loaded Roboflow model: {model_id} v{version}")
            except Exception as workspace_error:
                # For Universe models, try alternative API format
                logger.warning(f"Standard workspace access failed: {workspace_error}")
                logger.info("Attempting to use Inference API for Universe model...")
                # We'll use the predict API directly instead
                self.model = None  # Will use API calls directly
                self.use_api = True
                logger.info(f"Using Roboflow Inference API for model_id={self.model_id}, version={self.version}")
                
        except ImportError:
            logger.error("Roboflow not installed. Install with: pip install roboflow")
            raise
    
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """Detect objects using Roboflow (supports both detection and segmentation)"""
        
        # If using API mode (for Universe models), use HTTP API
        if hasattr(self, 'use_api') and self.use_api:
            return self._detect_via_api(image_bytes, confidence_threshold)
        
        # Otherwise use Python library
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            # Run inference
            predictions = self.model.predict(tmp_path, confidence=int(confidence_threshold * 100)).json()
            
            # Parse predictions
            detections = self._parse_roboflow_predictions(predictions, confidence_threshold)
            
            logger.info(f"Roboflow detected {len(detections)} objects" + 
                       (f" with segmentation masks" if any(d.segmentation for d in detections) else ""))
            return detections
            
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
    
    def _detect_via_api(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """Use Roboflow Inference API for Universe models"""
        import requests
        import base64
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build API URL for Universe model
        # Format: https://detect.roboflow.com/project-id/version
        # Extract just the project name from model_id (which is "workspace/project")
        project_name = self.model_id.split('/')[-1] if '/' in self.model_id else self.model_id
        url = f"https://detect.roboflow.com/{project_name}/{self.version}"
            
        params = {
            "api_key": self.api_key,
            "confidence": int(confidence_threshold * 100)
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        logger.info(f"Calling Roboflow API: {url}")
        
        try:
            response = requests.post(url, params=params, headers=headers, data=image_b64, timeout=30)
            response.raise_for_status()
            predictions = response.json()
            
            detections = self._parse_roboflow_predictions(predictions, confidence_threshold)
            
            logger.info(f"Roboflow API detected {len(detections)} objects" +
                       (f" with segmentation masks" if any(d.segmentation for d in detections) else ""))
            return detections
            
        except Exception as e:
            logger.error(f"Roboflow API error: {str(e)}")
            raise
    
    def _parse_roboflow_predictions(self, predictions: dict, confidence_threshold: float) -> List[Detection]:
        """Parse Roboflow prediction response (works for both detection and segmentation)"""
        detections = []
        
        for pred in predictions.get('predictions', []):
            # Roboflow format: {x: center_x, y: center_y, width, height}
            x = pred['x']
            y = pred['y']
            w = pred['width']
            h = pred['height']
            
            # Convert to [x_min, y_min, x_max, y_max]
            x_min = x - w / 2
            y_min = y - h / 2
            x_max = x + w / 2
            y_max = y + h / 2
            
            # Extract segmentation mask if available (for segmentation models)
            segmentation = None
            area = None
            if 'points' in pred:
                # Segmentation model - extract contour points
                points = pred['points']
                # Convert to list of [x, y] coordinates
                segmentation = [[p['x'], p['y']] for p in points]
                
                # Calculate actual area from polygon
                if len(segmentation) > 2:
                    import numpy as np
                    pts = np.array(segmentation)
                    # Shoelace formula for polygon area
                    x_coords = pts[:, 0]
                    y_coords = pts[:, 1]
                    area = 0.5 * abs(sum(x_coords[i] * y_coords[i+1] - x_coords[i+1] * y_coords[i] 
                                        for i in range(-1, len(pts)-1)))
                    logger.debug(f"Calculated segmentation area: {area:.0f} pixels")
            
            detections.append(Detection(
                bbox=[x_min, y_min, x_max, y_max],
                confidence=pred['confidence'],
                class_id=pred.get('class_id', 0),
                class_name=pred.get('class', 'bunch'),
                segmentation=segmentation,
                area=area
            ))
        
        return detections


class CustomAPIDetector(ObjectDetector):
    """
    Custom object detection API endpoint
    For pre-existing detection services
    """
    
    def __init__(self, endpoint_url: str, api_key: Optional[str] = None):
        """
        Initialize custom API detector
        
        Args:
            endpoint_url: API endpoint URL
            api_key: Optional API key for authentication
        """
        self.endpoint_url = endpoint_url
        self.api_key = api_key
    
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """Detect objects using custom API"""
        import requests
        
        # Prepare request
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        params = {'confidence': confidence_threshold}
        
        # Make request
        response = requests.post(
            self.endpoint_url,
            files=files,
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse response (expecting format like the example you showed)
        data = response.json()
        
        detections = []
        for det in data.get('detections', []):
            bbox = det.get('bbox', [])
            # Assume [x_min, y_min, width, height] or [x_min, y_min, x_max, y_max]
            if len(bbox) == 4:
                detections.append(Detection(
                    bbox=bbox,
                    confidence=det.get('confidence', 0.5),
                    class_id=det.get('class_id', 0),
                    class_name=det.get('class_name', 'bunch')
                ))
        
        logger.info(f"Custom API detected {len(detections)} objects")
        return detections


class MockDetector(ObjectDetector):
    """
    Mock detector for testing without actual detection model
    Returns dummy boxes based on simple heuristics
    """
    
    def detect(self, image_bytes: bytes, confidence_threshold: float = 0.25) -> List[Detection]:
        """Return mock detections"""
        # Load image to get dimensions
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        # Create realistic detections in the CENTER area where bunches actually are
        # Based on typical oil palm images, bunches are around 35-55% from top
        detections = [
            Detection(
                bbox=[width * 0.35, height * 0.40, width * 0.55, height * 0.60],
                confidence=0.85,
                class_name="bunch"
            ),
            Detection(
                bbox=[width * 0.55, height * 0.38, width * 0.72, height * 0.55],
                confidence=0.78,
                class_name="bunch"
            ),
            Detection(
                bbox=[width * 0.25, height * 0.42, width * 0.42, height * 0.58],
                confidence=0.72,
                class_name="bunch"
            ),
        ]
        
        logger.info(f"Mock detector returned {len(detections)} dummy detections in realistic positions")
        return detections


# Factory function to create detector based on config
def create_detector(detector_type: str = "mock", **kwargs) -> ObjectDetector:
    """
    Create object detector based on type
    
    Args:
        detector_type: Type of detector ("yolo", "roboflow", "custom", "mock")
        **kwargs: Additional arguments for specific detector
        
    Returns:
        ObjectDetector instance
    """
    if detector_type == "yolo":
        return UltralyticsYOLODetector(**kwargs)
    elif detector_type == "roboflow":
        return RoboflowDetector(**kwargs)
    elif detector_type == "custom":
        return CustomAPIDetector(**kwargs)
    elif detector_type == "mock":
        return MockDetector()
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")
