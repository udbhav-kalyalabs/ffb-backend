"""
Extensible crop configuration system for different agricultural products
"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class StageConfig:
    """Configuration for a fruit/crop stage"""
    name: str
    color_code: str  # Hex color for visualization
    description: str
    keywords: List[str]  # Keywords to help AI identify this stage

@dataclass
class CropConfig:
    """Configuration for a specific crop type"""
    crop_name: str
    scientific_name: str
    stages: List[StageConfig]
    detection_hints: List[str]  # Hints to help AI detect this crop
    min_confidence: float = 0.5
    
class CropConfigManager:
    """Manages configurations for different crop types"""
    
    def __init__(self):
        self.configs: Dict[str, CropConfig] = {}
        self._initialize_configs()
    
    def _initialize_configs(self):
        """Initialize crop configurations"""
        
        # Oil Palm Configuration
        oil_palm_stages = [
            StageConfig(
                name="young",
                color_code="#90EE90",  # Light green
                description="Unripe bunches with green color, hard texture",
                keywords=["green", "unripe", "immature", "hard", "small"]
            ),
            StageConfig(
                name="mature",
                color_code="#FFA500",  # Orange
                description="Maturing bunches with orange-yellow color, approaching harvest",
                keywords=["orange", "yellow", "maturing", "medium", "transitioning"]
            ),
            StageConfig(
                name="ripe",
                color_code="#FF0000",  # Red
                description="Ripe bunches ready for harvest, red-orange color",
                keywords=["red", "ripe", "ready", "harvest", "bright", "full"]
            ),
            StageConfig(
                name="overripe",
                color_code="#8B0000",  # Dark red
                description="Overripe bunches past optimal harvest time",
                keywords=["dark red", "overripe", "past", "late", "deteriorating"]
            )
        ]
        
        self.configs["oil_palm"] = CropConfig(
            crop_name="Oil Palm",
            scientific_name="Elaeis guineensis",
            stages=oil_palm_stages,
            detection_hints=[
                "Look for clustered fruit bunches on palm fronds",
                "Bunches are spherical/oval shaped with multiple fruits",
                "Color ranges from green (young) to red-orange (ripe)",
                "Each tree typically has multiple bunches at different stages",
                "Focus on the size, color, and texture of each bunch"
            ],
            min_confidence=0.6
        )
        
        # Future crops can be added here
        # Example: Rubber tree, Coffee plants, etc.
    
    def get_config(self, crop_type: str) -> CropConfig:
        """Get configuration for a specific crop"""
        if crop_type not in self.configs:
            raise ValueError(f"Crop type '{crop_type}' not configured")
        return self.configs[crop_type]
    
    def get_stage_color(self, crop_type: str, stage: str) -> str:
        """Get color code for a specific stage"""
        config = self.get_config(crop_type)
        for stage_config in config.stages:
            if stage_config.name == stage:
                return stage_config.color_code
        return "#808080"  # Default gray
    
    def list_available_crops(self) -> List[str]:
        """List all configured crop types"""
        return list(self.configs.keys())

# Global instance
crop_config_manager = CropConfigManager()
