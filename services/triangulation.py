"""
3D Triangulation and deduplication for multi-view FFB detection

Uses Direct Linear Transform (DLT) for triangulation and DBSCAN for clustering
to identify unique bunches across multiple views.
"""

import numpy as np
from scipy.linalg import svd
from sklearn.cluster import DBSCAN
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Triangulation:
    """
    Triangulates 3D positions of detected bunches from multiple 2D views
    and clusters them to identify unique bunches.
    """

    def __init__(self, camera_calibration):
        """
        Initialize triangulation engine.

        Args:
            camera_calibration: CameraCalibration instance with projection matrices
        """
        self.calib = camera_calibration
        self.triangulated_points = {}
        self.clusters = None

    def triangulate_point(self, detections_per_view: Dict[str, Dict]) -> Optional[np.ndarray]:
        """
        Triangulate 3D position using Direct Linear Transform (DLT).

        This is the core algorithm for converting 2D image coordinates from multiple
        views into a single 3D world coordinate.

        Mathematical basis:
        For each 2D point (u, v) in image i, we have the constraint:
            λ × [u, v, 1]^T = P_i × [X, Y, Z, 1]^T

        Where P_i is the 3×4 projection matrix and [X, Y, Z, 1] is the homogeneous
        3D point. This gives us 2 linear equations per view:
            u × (P_i[2,:] · P) - P_i[0,:] · P = 0
            v × (P_i[2,:] · P) - P_i[1,:] · P = 0

        With N views, we get 2N equations and solve via least squares using SVD.

        Args:
            detections_per_view: Dictionary mapping image names to detected pixel coordinates
                {
                    '1A': {'u': 520.5, 'v': 650.3, 'confidence': 0.95},
                    '1B': {'u': 485.2, 'v': 620.1, 'confidence': 0.92},
                    '2A': {'u': 612.1, 'v': 700.2, 'confidence': 0.88},
                    ...
                }

        Returns:
            np.ndarray: [X, Y, Z] coordinates in meters, or None if triangulation fails
        """

        # Collect valid detections from multiple views
        valid_views = []
        A_matrix = []

        for view_name, pixel_coords in detections_per_view.items():
            if pixel_coords is None:
                continue

            u = float(pixel_coords['u'])
            v = float(pixel_coords['v'])

            try:
                # Get projection matrix for this view
                P = self.calib.get_projection_matrix(view_name)

                # Build two linear equations from this view
                # Equation 1: u × (P[2,:]) - P[0,:]
                # Equation 2: v × (P[2,:]) - P[1,:]

                eq1 = u * P[2, :] - P[0, :]
                eq2 = v * P[2, :] - P[1, :]

                A_matrix.append(eq1)
                A_matrix.append(eq2)
                valid_views.append(view_name)

            except Exception as e:
                logger.warning(f"Failed to get projection matrix for {view_name}: {e}")
                continue

        # Need at least 2 views for triangulation
        if len(valid_views) < 2:
            logger.debug(f"Insufficient views for triangulation: only {len(valid_views)} view(s)")
            return None

        # Convert to numpy array (4×8 for 2 views, grows with more views)
        A = np.array(A_matrix, dtype=np.float64)

        try:
            # Solve using Singular Value Decomposition (SVD)
            # A × X_homogeneous = 0 is an overdetermined homogeneous system
            # Solution is the right singular vector corresponding to smallest singular value

            U, S, Vt = svd(A, full_matrices=True)

            # The solution is the last row of V (last column of Vt)
            # This corresponds to the smallest singular value
            X_homogeneous = Vt[-1, :]

            # Convert from homogeneous coordinates to 3D
            if abs(X_homogeneous[3]) < 1e-6:
                logger.warning("Homogeneous coordinate w is near zero, triangulation unstable")
                return None

            X = X_homogeneous[0] / X_homogeneous[3]
            Y = X_homogeneous[1] / X_homogeneous[3]
            Z = X_homogeneous[2] / X_homogeneous[3]

            point_3d = np.array([X, Y, Z], dtype=np.float32)

            # Sanity check: point should be near tree (within ~5 meters in any direction)
            distance_from_origin = np.linalg.norm(point_3d)
            if distance_from_origin > 10.0:
                logger.warning(
                    f"Triangulated point too far from tree ({distance_from_origin:.2f}m), "
                    "may be an outlier"
                )

            return point_3d

        except np.linalg.LinAlgError as e:
            logger.error(f"SVD failed during triangulation: {e}")
            return None

    def triangulate_multiple(self, all_detections: Dict) -> Dict[str, np.ndarray]:
        """
        Triangulate all detected bunches across all views.

        Args:
            all_detections: Dictionary structure:
                {
                    'bunch_001': {
                        '1A': {'u': 520.5, 'v': 650.3, 'confidence': 0.95},
                        '1B': {'u': 485.2, 'v': 620.1, 'confidence': 0.92},
                        ...
                    },
                    'bunch_002': {...},
                    ...
                }

        Returns:
            Dictionary mapping bunch IDs to their 3D coordinates:
            {
                'bunch_001': np.array([X, Y, Z]),
                'bunch_002': np.array([X, Y, Z]),
                ...
            }
        """
        self.triangulated_points = {}
        successful = 0
        failed = 0

        for bunch_id, detections_per_view in all_detections.items():
            point_3d = self.triangulate_point(detections_per_view)

            if point_3d is not None:
                self.triangulated_points[bunch_id] = point_3d
                successful += 1
            else:
                failed += 1

        logger.info(
            f"Triangulation complete: {successful} successful, {failed} failed"
        )

        return self.triangulated_points

    def cluster_bunches_3d(
        self,
        point_3d_dict: Dict[str, np.ndarray],
        distance_threshold: float = 0.15,
        min_samples: int = 1
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, List[str]]]:
        """
        Cluster nearby 3D points to identify unique bunches.

        The idea: Each physical bunch should appear at multiple 2D locations across
        views. When triangulated, all these detections converge to approximately the
        same 3D point. Bunches closer than distance_threshold are clustered together,
        representing a single physical bunch.

        Args:
            point_3d_dict: Dictionary of triangulated 3D points per detection
                {
                    'bunch_001': np.array([X, Y, Z]),
                    'bunch_002': np.array([X, Y, Z]),
                    ...
                }
            distance_threshold: Maximum distance (meters) between points to be same cluster
                                Default 0.15m (15cm) is reasonable for FFB spacing
            min_samples: Minimum points to form a cluster (1 allows single-view detections)

        Returns:
            Tuple of:
            - unique_bunches: {cluster_id: average_3d_position}
            - bunch_memberships: {cluster_id: [original_bunch_ids]}

        Algorithm details (DBSCAN):
            - Groups points within distance_threshold into clusters
            - Clusters with ≥min_samples points are kept
            - Isolated points form singleton clusters (min_samples=1)
            - This handles both multi-view confirmations and occluded bunches
        """

        if not point_3d_dict:
            logger.warning("No triangulated points to cluster")
            return {}, {}

        # Extract 3D coordinates and maintain mapping
        bunch_ids = list(point_3d_dict.keys())
        points = np.array([point_3d_dict[bid] for bid in bunch_ids])

        logger.info(f"Clustering {len(points)} points with threshold={distance_threshold}m")

        # Apply DBSCAN clustering
        clustering = DBSCAN(
            eps=distance_threshold,
            min_samples=min_samples,
            metric='euclidean'
        ).fit(points)

        labels = clustering.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)  # Exclude noise label -1
        n_noise = list(labels).count(-1)

        logger.info(f"Clustering result: {n_clusters} clusters, {n_noise} noise points")

        # Aggregate clusters
        unique_bunches = {}
        bunch_memberships = {}

        for cluster_id in np.unique(labels):
            if cluster_id == -1:
                # Noise points (isolated)
                continue

            # Find all bunches in this cluster
            member_mask = labels == cluster_id
            members = [bunch_ids[i] for i in np.where(member_mask)[0]]

            # Calculate cluster statistics
            cluster_points = points[member_mask]
            avg_position = np.mean(cluster_points, axis=0)
            cluster_std = np.std(cluster_points, axis=0)
            cluster_radius = np.max(np.linalg.norm(
                cluster_points - avg_position, axis=1
            ))

            # Assign cluster ID
            cluster_key = f"bunch_{cluster_id:03d}"

            unique_bunches[cluster_key] = {
                'position': avg_position,
                'std_dev': cluster_std,
                'radius': cluster_radius,
                'num_views': len(members)
            }

            bunch_memberships[cluster_key] = members

        logger.info(f"Identified {len(unique_bunches)} unique bunches")

        self.clusters = unique_bunches
        return unique_bunches, bunch_memberships

    def reconstruct_accuracy_metrics(
        self,
        clusters: Dict,
        memberships: Dict
    ) -> Dict:
        """
        Calculate accuracy metrics for triangulation and clustering.

        Returns:
            Dictionary with metrics like:
            - mean_cluster_radius: Average spread within clusters
            - median_points_per_cluster: Median number of confirmations
            - outlier_clusters: Clusters with high std deviation
        """
        if not clusters:
            return {}

        metrics = {}

        # Radius statistics
        radii = [c['radius'] for c in clusters.values()]
        metrics['mean_cluster_radius_m'] = np.mean(radii) if radii else 0
        metrics['max_cluster_radius_m'] = np.max(radii) if radii else 0
        metrics['std_dev_radius_m'] = np.std(radii) if radii else 0

        # Point count statistics
        counts = [c['num_views'] for c in clusters.values()]
        metrics['mean_views_per_bunch'] = np.mean(counts) if counts else 0
        metrics['median_views_per_bunch'] = np.median(counts) if counts else 0
        metrics['min_views'] = np.min(counts) if counts else 0
        metrics['max_views'] = np.max(counts) if counts else 0

        # Distribution: how many bunches seen in 1, 2, 3, 4+ views?
        view_distribution = {}
        for count in counts:
            key = f"{count}_views"
            view_distribution[key] = view_distribution.get(key, 0) + 1

        metrics['view_distribution'] = view_distribution

        # Identify suspicious clusters (very large radius = triangulation error)
        threshold_radius = 0.5  # 50cm is suspiciously large
        suspicious = [
            (k, v['radius']) for k, v in clusters.items()
            if v['radius'] > threshold_radius
        ]
        metrics['suspicious_clusters'] = suspicious

        return metrics

    def print_triangulation_summary(self):
        """Print summary of triangulation results"""
        if not self.triangulated_points:
            print("No triangulated points available")
            return

        print("\n" + "="*70)
        print("Triangulation Summary")
        print("="*70)

        points = np.array(list(self.triangulated_points.values()))
        print(f"\nTotal triangulated detections: {len(self.triangulated_points)}")
        print(f"Mean 3D position (m): X={np.mean(points[:, 0]):.2f}, "
              f"Y={np.mean(points[:, 1]):.2f}, Z={np.mean(points[:, 2]):.2f}")
        print(f"Std deviation: X={np.std(points[:, 0]):.2f}, "
              f"Y={np.std(points[:, 1]):.2f}, Z={np.std(points[:, 2]):.2f}")

        if self.clusters:
            print(f"\nUnique bunches identified: {len(self.clusters)}")
            print("\nCluster details:")
            for cluster_id, cluster_data in self.clusters.items():
                pos = cluster_data['position']
                radius = cluster_data['radius']
                num_views = cluster_data['num_views']
                print(f"  {cluster_id}: pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}m) "
                      f"radius={radius:.3f}m views={num_views}")

        print("="*70 + "\n")


if __name__ == "__main__":
    # Example usage (requires camera calibration)
    from config.camera_calibration import iPhone15Calibration

    calib = iPhone15Calibration()
    tri = Triangulation(calib)

    # Example: Simulated detections of a bunch visible in 4 views
    # (These would normally come from YOLOv8 detection)
    example_detections = {
        'bunch_001': {
            '1A': {'u': 2142, 'v': 2856, 'confidence': 0.95},  # Wide view, position 1
            '1B': {'u': 1512, 'v': 2016, 'confidence': 0.92},  # Zoom view, position 1
            '2A': {'u': 1950, 'v': 3100, 'confidence': 0.88},  # Wide view, position 2
            '2B': {'u': 1680, 'v': 2100, 'confidence': 0.90},  # Zoom view, position 2
        }
    }

    # Triangulate
    triangulated = tri.triangulate_multiple(example_detections)
    print(f"Triangulated points: {triangulated}")

    # Cluster
    clusters, memberships = tri.cluster_bunches_3d(triangulated, distance_threshold=0.15)
    print(f"Unique bunches: {len(clusters)}")
    for cluster_id, members in memberships.items():
        print(f"  {cluster_id}: {members}")
