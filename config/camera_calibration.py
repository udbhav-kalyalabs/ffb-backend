"""
Camera calibration for iPhone 15 with variable zoom levels
Handles both wide-angle (26mm) and 3x zoom (52mm) focal lengths
"""

import numpy as np
from scipy.spatial.transform import Rotation
from typing import Dict, Tuple
import math


class iPhone15Calibration:
    """
    iPhone 15 camera calibration with support for dual zoom levels.

    Reference specs:
    - Main camera: f/1.6 aperture
    - Wide (1x): 26mm equivalent focal length
    - Zoom (3x): 52mm equivalent focal length
    - Sensor: ~1/1.28" (8.75mm diagonal)
    """

    # iPhone 15 sensor specifications
    SENSOR_WIDTH_MM = 6.86  # Actual sensor width in mm
    SENSOR_HEIGHT_MM = 5.15  # Actual sensor height in mm
    SENSOR_DIAGONAL_MM = math.sqrt(SENSOR_WIDTH_MM**2 + SENSOR_HEIGHT_MM**2)

    # 35mm equivalent focal lengths (from EXIF)
    FOCAL_LENGTH_WIDE_35MM = 26.0  # mm (1x, A images)
    FOCAL_LENGTH_ZOOM_35MM = 52.0  # mm (3x, B images)

    # Relationship: equivalent_focal_length = actual_focal_length * crop_factor
    # For iPhone 15: crop_factor ≈ 1/0.8 ≈ 1.24 (typical for smartphone)
    # So actual focal lengths:
    CROP_FACTOR = 1.24
    FOCAL_LENGTH_WIDE_ACTUAL = FOCAL_LENGTH_WIDE_35MM / CROP_FACTOR  # ~21mm actual
    FOCAL_LENGTH_ZOOM_ACTUAL = FOCAL_LENGTH_ZOOM_35MM / CROP_FACTOR  # ~42mm actual

    def __init__(self, tree_distance_meters: float = 2.0):
        """
        Initialize camera calibration.

        Args:
            tree_distance_meters: Approximate distance from camera to tree center (2.0m default)
                                 This varies per position but we use average for initial setup
        """
        self.tree_distance = tree_distance_meters

        # Generate intrinsic matrices for each zoom level
        self.K_wide = self._compute_intrinsic_wide()
        self.K_zoom = self._compute_intrinsic_zoom()

        # Generate extrinsic matrices for each position
        self.extrinsics = self._setup_extrinsics()

    def _compute_intrinsic_wide(self) -> np.ndarray:
        """
        Compute intrinsic matrix K for wide-angle (A) images
        Resolution: 4284 × 5712 pixels
        Focal length: 26mm (35mm equivalent)
        """
        image_width = 4284
        image_height = 5712

        # Calculate pixel focal length
        # For wider FOV, we use the horizontal field of view
        focal_length_pixels = self._mm_to_pixels(
            focal_length_mm=self.FOCAL_LENGTH_WIDE_ACTUAL,
            image_width=image_width
        )

        # Principal point (image center)
        cx = image_width / 2.0
        cy = image_height / 2.0

        # Intrinsic matrix K (assume square pixels)
        K = np.array([
            [focal_length_pixels, 0, cx],
            [0, focal_length_pixels, cy],
            [0, 0, 1]
        ], dtype=np.float32)

        return K

    def _compute_intrinsic_zoom(self) -> np.ndarray:
        """
        Compute intrinsic matrix K for 3x zoom (B) images
        Resolution: 3024 × 4032 pixels
        Focal length: 52mm (35mm equivalent)
        """
        image_width = 3024
        image_height = 4032

        focal_length_pixels = self._mm_to_pixels(
            focal_length_mm=self.FOCAL_LENGTH_ZOOM_ACTUAL,
            image_width=image_width
        )

        cx = image_width / 2.0
        cy = image_height / 2.0

        K = np.array([
            [focal_length_pixels, 0, cx],
            [0, focal_length_pixels, cy],
            [0, 0, 1]
        ], dtype=np.float32)

        return K

    def _mm_to_pixels(self, focal_length_mm: float, image_width: int) -> float:
        """
        Convert focal length from mm to pixels using sensor width

        Formula: f_pixels = (image_width_pixels * f_mm) / sensor_width_mm
        """
        return (image_width * focal_length_mm) / self.SENSOR_WIDTH_MM

    def _setup_extrinsics(self) -> Dict[str, Dict]:
        """
        Setup extrinsic matrices [R|t] for each of the 4 capture positions.

        Positions are arranged around the tree:
        - Position 1 (North): Camera at North, looking South toward tree
        - Position 2 (East): Camera at East, looking West toward tree
        - Position 3 (South): Camera at South, looking North toward tree
        - Position 4 (West): Camera at West, looking East toward tree

        Assumption: Camera height is approximately 1.5 meters (phone held level at ~chest/head height)

        Returns:
            {position_name: {'R': rotation_matrix, 't': translation_vector, 'angle': yaw_degrees}}
        """

        # Camera height above ground (meters)
        camera_height = 1.5

        # Tree height (center of bunch concentration, meters)
        tree_center_height = 1.5

        # Vertical offset (should be ~0 if both at same height)
        z_offset = tree_center_height - camera_height  # ~0 meters

        extrinsics = {}

        # Define 4 positions around tree (North, East, South, West)
        positions = [
            {'name': '1A/1B', 'angle': 0, 'description': 'North facing tree'},
            {'name': '2A/2B', 'angle': 90, 'description': 'East facing tree'},
            {'name': '3A/3B', 'angle': 180, 'description': 'South facing tree'},
            {'name': '4A/4B', 'angle': 270, 'description': 'West facing tree'}
        ]

        for pos in positions:
            angle_deg = pos['angle']
            angle_rad = np.radians(angle_deg)

            # Camera position in world coordinates
            # Tree center is at origin [0, 0, 1.5] (height adjustment)
            camera_x = self.tree_distance * np.cos(angle_rad)
            camera_y = self.tree_distance * np.sin(angle_rad)
            camera_z = z_offset

            # Translation vector (camera position relative to tree center)
            t = np.array([
                [camera_x],
                [camera_y],
                [camera_z]
            ], dtype=np.float32)

            # Rotation matrix: Camera looking toward tree center
            # Yaw: rotate around Z-axis to face tree
            # Pitch: slight downward tilt if capturing lower bunches

            # Simple approach: Pure yaw rotation (camera always at tree height, looking straight ahead)
            R_yaw = Rotation.from_euler('z', angle_rad).as_matrix()

            # If capturing bunches lower on tree, add slight pitch (downward tilt ~-10 degrees)
            R_pitch = Rotation.from_euler('x', np.radians(-10)).as_matrix()

            # Combined rotation
            R = R_pitch @ R_yaw

            extrinsics[pos['name']] = {
                'R': R.astype(np.float32),
                't': t,
                'angle': angle_deg,
                'description': pos['description'],
                'world_position': np.array([camera_x, camera_y, camera_z])
            }

        return extrinsics

    def get_projection_matrix(self, image_name: str) -> np.ndarray:
        """
        Get 3×4 projection matrix P = K × [R|t] for a specific image.

        Args:
            image_name: Image identifier (e.g., '1A', '1B', '2A', '2B', ...)

        Returns:
            3×4 projection matrix
        """
        # Determine if this is a wide (A) or zoom (B) image
        if image_name.endswith('A'):
            K = self.K_wide
            position_key = image_name  # '1A', '2A', etc.
        elif image_name.endswith('B'):
            K = self.K_zoom
            position_key = image_name.replace('B', 'A')  # Convert '1B' to '1A' for extrinsics
        else:
            raise ValueError(f"Unknown image name: {image_name}. Must end with 'A' or 'B'")

        # Get extrinsic for this position (same extrinsic for both A and B at same position)
        ext = self.extrinsics[position_key]

        R = ext['R']
        t = ext['t']

        # Combine into 3×4 matrix [R|t]
        Rt = np.hstack([R, t])

        # Projection matrix P = K × [R|t]
        P = K @ Rt

        return P

    def get_intrinsic(self, image_name: str) -> np.ndarray:
        """Get intrinsic matrix K for an image"""
        if image_name.endswith('A'):
            return self.K_wide
        elif image_name.endswith('B'):
            return self.K_zoom
        else:
            raise ValueError(f"Unknown image name: {image_name}")

    def get_extrinsic(self, image_name: str) -> Tuple[np.ndarray, np.ndarray]:
        """Get extrinsic matrices [R, t] for an image"""
        position_key = image_name[:-1]  # Remove 'A' or 'B' suffix

        if position_key not in self.extrinsics:
            raise ValueError(f"Unknown position: {position_key}")

        ext = self.extrinsics[position_key]
        return ext['R'], ext['t']

    def print_calibration_summary(self):
        """Print calibration parameters for verification"""
        print("\n" + "="*70)
        print("iPhone 15 Camera Calibration Summary")
        print("="*70)

        print("\n[INTRINSIC MATRICES]")
        print(f"\nWide-angle (A images) - 26mm equivalent, 4284×5712 pixels:")
        print(self.K_wide)

        print(f"\n3x Zoom (B images) - 52mm equivalent, 3024×4032 pixels:")
        print(self.K_zoom)

        print("\n[EXTRINSIC MATRICES]")
        for pos_name, ext in self.extrinsics.items():
            print(f"\n{pos_name} - {ext['description']}")
            print(f"  Angle: {ext['angle']}°")
            print(f"  World position (m): {ext['world_position']}")
            print(f"  Rotation matrix R:\n{ext['R']}")
            print(f"  Translation vector t:\n{ext['t'].flatten()}")

        print("\n" + "="*70)
        print(f"Tree distance (assumed): {self.tree_distance}m")
        print(f"Camera height: 1.5m")
        print("="*70 + "\n")

    def validate_geometry(self):
        """
        Validate that camera geometry makes sense

        Returns:
            Dictionary of validation checks
        """
        checks = {}

        # Check 1: Positions are roughly equidistant from tree
        distances = []
        for ext in self.extrinsics.values():
            dist = np.linalg.norm(ext['world_position'])
            distances.append(dist)

        avg_dist = np.mean(distances)
        max_deviation = np.max([abs(d - avg_dist) for d in distances])
        checks['position_consistency'] = {
            'average_distance': avg_dist,
            'max_deviation': max_deviation,
            'pass': max_deviation < 0.1  # Within 10cm
        }

        # Check 2: Focal lengths are reasonable
        checks['focal_lengths'] = {
            'wide_mm': self.FOCAL_LENGTH_WIDE_35MM,
            'zoom_mm': self.FOCAL_LENGTH_ZOOM_35MM,
            'zoom_ratio': self.FOCAL_LENGTH_ZOOM_35MM / self.FOCAL_LENGTH_WIDE_35MM
        }

        # Check 3: Intrinsic matrices have reasonable values
        fx_wide = self.K_wide[0, 0]
        fy_wide = self.K_wide[1, 1]
        fx_zoom = self.K_zoom[0, 0]
        fy_zoom = self.K_zoom[1, 1]

        checks['intrinsic_parameters'] = {
            'wide_fx': fx_wide,
            'wide_fy': fy_wide,
            'zoom_fx': fx_zoom,
            'zoom_fy': fy_zoom,
            'fx_zoom_ratio': fx_zoom / fx_wide,
            'pass': abs((fx_zoom / fx_wide) - 2.0) < 0.1  # Should be ~2x zoom
        }

        return checks


# Singleton instance for global use
camera_calibration = iPhone15Calibration(tree_distance_meters=2.0)


if __name__ == "__main__":
    # Print calibration details
    camera_calibration.print_calibration_summary()

    # Validate geometry
    validation = camera_calibration.validate_geometry()
    print("\n[VALIDATION CHECKS]")
    import json
    print(json.dumps(validation, indent=2, default=str))

    # Example: Get projection matrix for image 1A
    print("\n[EXAMPLE: Projection Matrix for image 1A]")
    P_1A = camera_calibration.get_projection_matrix('1A')
    print(f"P_1A (3×4):\n{P_1A}")

    print("\n[EXAMPLE: Projection Matrix for image 1B]")
    P_1B = camera_calibration.get_projection_matrix('1B')
    print(f"P_1B (3×4):\n{P_1B}")
