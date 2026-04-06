"""
Validation utilities
"""
from typing import Tuple
import re

def validate_coordinates(
    x_min: int, y_min: int, x_max: int, y_max: int,
    image_width: int, image_height: int
) -> Tuple[bool, str]:
    """
    Validate bounding box coordinates
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if coordinates are within image bounds
    if x_min < 0 or y_min < 0:
        return False, "Minimum coordinates cannot be negative"
    
    if x_max > image_width or y_max > image_height:
        return False, f"Maximum coordinates exceed image dimensions ({image_width}x{image_height})"
    
    # Check if box has positive dimensions
    if x_max <= x_min or y_max <= y_min:
        return False, "Bounding box must have positive dimensions"
    
    return True, ""

def validate_hex_color(color: str) -> bool:
    """Validate hex color code"""
    pattern = r'^#[0-9A-Fa-f]{6}$'
    return bool(re.match(pattern, color))
