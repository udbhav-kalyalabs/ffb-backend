"""
Multi-view FFB detection and deduplication pipeline orchestrator

Coordinates YOLOv8 detection, correspondence matching, 3D triangulation,
and DBSCAN clustering to produce unique FFB counts.
"""

import numpy as np
import cv2
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

from ultralytics import YOLO
from config.camera_calibration import iPhone15Calibration
from services.triangulation import Triangulation

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Single detection in an image"""
    image_name: str
    bunch_id: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    u_center: float  # Pixel center X
    v_center: float  # Pixel center Y
    confidence: float
    class_name: str = "bunch"


@dataclass
class UniqueBunch:
    """Identified unique bunch after deduplication"""
    bunch_id: str
    position_3d: np.ndarray  # [X, Y, Z] in meters
    num_views: int
    detection_ids: List[str]
    confidence: float  # Average of contributing detections
    triangulation_error: float  # Cluster radius


class MultiViewProcessor:
    """
    Main orchestrator for multi-view FFB counting pipeline.

    Pipeline:
    1. Load 8 images per tree (4 positions × 2 zoom levels)
    2. Run YOLOv8 detection on all images
    3. Establish correspondences between same bunch in different images
    4. Triangulate 3D positions using camera calibration
    5. Cluster nearby points to identify unique bunches
    6. Return unique bunch count with detailed metadata
    """

    def __init__(self, model_path: str, tree_distance_meters: float = 2.0):
        """
        Initialize multi-view processor.

        Args:
            model_path: Path to trained YOLOv8 model (.pt file)
            tree_distance_meters: Assumed distance from camera to tree center
        """
        logger.info(f"Loading YOLOv8 model from {model_path}")
        self.model = YOLO(model_path)

        logger.info("Initializing camera calibration")
        self.camera_calib = iPhone15Calibration(
            tree_distance_meters=tree_distance_meters
        )

        logger.info("Initializing triangulation engine")
        self.triangulator = Triangulation(self.camera_calib)

        # Results storage
        self.all_detections: Dict[str, List[DetectionResult]] = {}
        self.correspondences: Dict[str, Dict] = {}
        self.triangulated_points: Dict[str, np.ndarray] = {}
        self.unique_bunches: Dict[str, UniqueBunch] = {}

        logger.info("MultiViewProcessor initialized")

    def process_tree(
        self,
        tree_images: Dict[str, np.ndarray],
        tree_id: str = "tree_001",
        confidence_threshold: float = 0.25
    ) -> Dict:
        """
        Process all 8 images of a tree and return unique bunch count.

        Args:
            tree_images: Dictionary mapping image names to image arrays
                {
                    '1A': np.ndarray (RGB),
                    '1B': np.ndarray (RGB),
                    '2A': np.ndarray (RGB),
                    '2B': np.ndarray (RGB),
                    ...
                }
            tree_id: Identifier for this tree
            confidence_threshold: Minimum detection confidence (0.0-1.0)

        Returns:
            Dictionary with:
            {
                'tree_id': str,
                'unique_bunch_count': int,
                'bunches': [UniqueBunch objects],
                'accuracy_metrics': {...},
                'processing_stages': {...},
                'error': Optional[str]
            }
        """

        logger.info(f"Processing tree {tree_id} with {len(tree_images)} images")

        start_time = time.time()
        processing_times = {}

        try:
            # Stage 1: Detection
            logger.info("Stage 1/5: Running YOLOv8 detection on all images")
            stage_start = time.time()

            self.all_detections = self._detect_bunches_all_views(
                tree_images,
                confidence_threshold
            )

            total_detections = sum(
                len(dets) for dets in self.all_detections.values()
            )
            processing_times['detection'] = time.time() - stage_start
            logger.info(
                f"  ✓ Detected {total_detections} bunches across "
                f"{len(self.all_detections)} images "
                f"({processing_times['detection']:.2f}s)"
            )

            # Stage 2: Correspondence matching
            logger.info("Stage 2/5: Matching same bunches across views")
            stage_start = time.time()

            self.correspondences = self._establish_correspondences()

            num_correspondences = len(self.correspondences)
            processing_times['correspondence'] = time.time() - stage_start
            logger.info(
                f"  ✓ Established {num_correspondences} correspondences "
                f"({processing_times['correspondence']:.2f}s)"
            )

            # Stage 3: Triangulation
            logger.info("Stage 3/5: Triangulating 3D positions")
            stage_start = time.time()

            self.triangulated_points = self.triangulator.triangulate_multiple(
                self.correspondences
            )

            num_triangulated = len(self.triangulated_points)
            processing_times['triangulation'] = time.time() - stage_start
            logger.info(
                f"  ✓ Triangulated {num_triangulated} points "
                f"({processing_times['triangulation']:.2f}s)"
            )

            # Stage 4: Clustering/Deduplication
            logger.info("Stage 4/5: Clustering to identify unique bunches")
            stage_start = time.time()

            clusters, memberships = self.triangulator.cluster_bunches_3d(
                self.triangulated_points,
                distance_threshold=0.15,
                min_samples=1
            )

            num_unique = len(clusters)
            processing_times['clustering'] = time.time() - stage_start
            logger.info(
                f"  ✓ Identified {num_unique} unique bunches "
                f"({processing_times['clustering']:.2f}s)"
            )

            # Stage 5: Format results
            logger.info("Stage 5/5: Formatting results")
            stage_start = time.time()

            self.unique_bunches = self._format_results(
                clusters,
                memberships,
                self.correspondences
            )

            processing_times['formatting'] = time.time() - stage_start

            total_time = time.time() - start_time

            # Compute accuracy metrics
            accuracy_metrics = self._compute_accuracy_metrics()

            result = {
                'success': True,
                'tree_id': tree_id,
                'unique_bunch_count': num_unique,
                'bunches': list(self.unique_bunches.values()),
                'total_detections': total_detections,
                'num_correspondences': num_correspondences,
                'num_triangulated': num_triangulated,
                'accuracy_metrics': accuracy_metrics,
                'processing_stages': {
                    'detection_ms': processing_times['detection'] * 1000,
                    'correspondence_ms': processing_times['correspondence'] * 1000,
                    'triangulation_ms': processing_times['triangulation'] * 1000,
                    'clustering_ms': processing_times['clustering'] * 1000,
                    'formatting_ms': processing_times['formatting'] * 1000,
                    'total_ms': total_time * 1000
                },
                'error': None
            }

            logger.info(
                f"✓ Tree {tree_id} processed successfully in {total_time:.2f}s "
                f"→ {num_unique} unique bunches"
            )

            return result

        except Exception as e:
            logger.error(f"✗ Error processing tree {tree_id}: {str(e)}")
            return {
                'success': False,
                'tree_id': tree_id,
                'unique_bunch_count': 0,
                'bunches': [],
                'error': str(e),
                'processing_stages': processing_times
            }

    def _detect_bunches_all_views(
        self,
        tree_images: Dict[str, np.ndarray],
        confidence_threshold: float
    ) -> Dict[str, List[DetectionResult]]:
        """
        Run YOLOv8 detection on all images.

        Args:
            tree_images: {image_name: np.ndarray}
            confidence_threshold: Min confidence (0.0-1.0)

        Returns:
            {image_name: [DetectionResult]}
        """

        all_detections = {}

        for image_name, image_array in tree_images.items():
            logger.debug(f"  Detecting in {image_name}")

            # Convert BGR to RGB if needed (OpenCV uses BGR)
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image_array

            # Run YOLOv8
            results = self.model.predict(
                image_rgb,
                conf=confidence_threshold,
                verbose=False
            )

            detections = []
            if results and len(results) > 0:
                for box in results[0].boxes:
                    x_min, y_min, x_max, y_max = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])

                    u_center = (x_min + x_max) / 2.0
                    v_center = (y_min + y_max) / 2.0

                    detection = DetectionResult(
                        image_name=image_name,
                        bunch_id=f"{image_name}_det_{len(detections)}",
                        x_min=float(x_min),
                        y_min=float(y_min),
                        x_max=float(x_max),
                        y_max=float(y_max),
                        u_center=u_center,
                        v_center=v_center,
                        confidence=confidence
                    )
                    detections.append(detection)

            all_detections[image_name] = detections
            logger.debug(f"    Found {len(detections)} bunches")

        return all_detections

    def _establish_correspondences(self) -> Dict[str, Dict]:
        """
        Match same physical bunch across different images.

        Uses spatial proximity: detections at nearby pixel coordinates in images
        from same position (e.g., 1A and 1B) are likely the same bunch.

        Returns:
            {correspondence_id: {image_name: {'u': x, 'v': y, 'confidence': c}}}
        """

        correspondences = {}
        correspondence_counter = 0

        # Process each position (1, 2, 3, 4)
        for position in ['1', '2', '3', '4']:
            # Get A and B images for this position
            image_a = f"{position}A"
            image_b = f"{position}B"

            detections_a = self.all_detections.get(image_a, [])
            detections_b = self.all_detections.get(image_b, [])

            logger.debug(
                f"  Matching position {position}: "
                f"{len(detections_a)} in {image_a}, "
                f"{len(detections_b)} in {image_b}"
            )

            # Match A detections to B detections
            matched_b_indices = set()

            for det_a in detections_a:
                # Find nearest detection in B image
                best_match_idx = None
                best_distance = float('inf')

                for idx_b, det_b in enumerate(detections_b):
                    if idx_b in matched_b_indices:
                        continue

                    # Euclidean distance in pixel space
                    distance = np.sqrt(
                        (det_a.u_center - det_b.u_center)**2 +
                        (det_a.v_center - det_b.v_center)**2
                    )

                    # Spatial proximity threshold (~5% of image width)
                    # For 4284×5712, that's ~214 pixels
                    if distance < 300 and distance < best_distance:
                        best_match_idx = idx_b
                        best_distance = distance

                # Create correspondence
                corr_id = f"bunch_{correspondence_counter:04d}"
                correspondence_counter += 1

                correspondence = {
                    image_a: {
                        'u': det_a.u_center,
                        'v': det_a.v_center,
                        'confidence': det_a.confidence
                    }
                }

                if best_match_idx is not None:
                    det_b = detections_b[best_match_idx]
                    correspondence[image_b] = {
                        'u': det_b.u_center,
                        'v': det_b.v_center,
                        'confidence': det_b.confidence
                    }
                    matched_b_indices.add(best_match_idx)

                correspondences[corr_id] = correspondence

            # Add unmatched B detections as single-view detections
            for idx_b, det_b in enumerate(detections_b):
                if idx_b not in matched_b_indices:
                    corr_id = f"bunch_{correspondence_counter:04d}"
                    correspondence_counter += 1

                    correspondences[corr_id] = {
                        image_b: {
                            'u': det_b.u_center,
                            'v': det_b.v_center,
                            'confidence': det_b.confidence
                        }
                    }

        return correspondences

    def _format_results(
        self,
        clusters: Dict,
        memberships: Dict,
        correspondences: Dict
    ) -> Dict[str, UniqueBunch]:
        """
        Convert clustering results to UniqueBunch objects.

        Args:
            clusters: {cluster_id: {position, std_dev, radius, num_views}}
            memberships: {cluster_id: [member_ids]}
            correspondences: Original correspondences dict

        Returns:
            {bunch_id: UniqueBunch}
        """

        unique_bunches = {}

        for cluster_id, cluster_data in clusters.items():
            # Get all members and extract confidence
            member_ids = memberships.get(cluster_id, [])

            confidences = []
            for member_id in member_ids:
                corr = correspondences.get(member_id, {})
                for view_data in corr.values():
                    confidences.append(view_data.get('confidence', 0.5))

            avg_confidence = np.mean(confidences) if confidences else 0.5

            bunch = UniqueBunch(
                bunch_id=cluster_id,
                position_3d=cluster_data['position'],
                num_views=cluster_data['num_views'],
                detection_ids=member_ids,
                confidence=float(avg_confidence),
                triangulation_error=float(cluster_data['radius'])
            )

            unique_bunches[cluster_id] = bunch

        return unique_bunches

    def _compute_accuracy_metrics(self) -> Dict:
        """Compute metrics about triangulation quality"""

        if not self.unique_bunches:
            return {}

        metrics = self.triangulator.reconstruct_accuracy_metrics(
            {b.bunch_id: {
                'position': b.position_3d,
                'std_dev': np.array([0, 0, 0]),  # Not available
                'radius': b.triangulation_error,
                'num_views': b.num_views
            } for b in self.unique_bunches.values()},
            {b.bunch_id: b.detection_ids for b in self.unique_bunches.values()}
        )

        return metrics

    def get_results_summary(self) -> str:
        """Get human-readable summary of results"""

        if not self.unique_bunches:
            return "No bunches detected"

        summary = f"\nMulti-View Analysis Results\n"
        summary += f"{'='*50}\n"
        summary += f"Total unique bunches: {len(self.unique_bunches)}\n"
        summary += f"\nDetailed per-bunch breakdown:\n"

        for bunch_id, bunch in self.unique_bunches.items():
            summary += (
                f"  {bunch_id}: "
                f"pos=({bunch.position_3d[0]:.2f}m, "
                f"{bunch.position_3d[1]:.2f}m, "
                f"{bunch.position_3d[2]:.2f}m) "
                f"views={bunch.num_views} "
                f"conf={bunch.confidence:.2f} "
                f"err={bunch.triangulation_error:.3f}m\n"
            )

        return summary


if __name__ == "__main__":
    # Example usage (requires trained model and images)

    # Initialize processor
    processor = MultiViewProcessor(
        model_path="weights/yolov8_large_ffb_v1.pt",
        tree_distance_meters=2.0
    )

    # Load example images (placeholder - you'd load real images)
    # tree_images = {
    #     '1A': cv2.imread('path/to/1A.jpg'),
    #     '1B': cv2.imread('path/to/1B.jpg'),
    #     ...
    # }

    # Process tree
    # result = processor.process_tree(tree_images, tree_id='T1')
    # print(processor.get_results_summary())
