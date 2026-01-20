"""
Annotation system for text labels and dimension lines.

Provides tools for adding notes, labels, and automatic dimensioning
to floor plans.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass, field
import uuid

from core import Point

logger = logging.getLogger(__name__)


@dataclass
class TextAnnotation:
    """
    Text annotation in the floor plan.
    
    Can be used for notes, labels, room names, etc.
    """
    position: Point
    text: str
    font_size: int = 12
    font_family: str = "Arial"
    color: str = "#000000"
    background_color: Optional[str] = None
    rotation: float = 0.0  # degrees
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "text": self.text,
            "font_size": self.font_size,
            "font_family": self.font_family,
            "color": self.color,
            "background_color": self.background_color,
            "rotation": self.rotation
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TextAnnotation':
        """Deserialize from dictionary."""
        return cls(
            position=Point.from_dict(data["position"]),
            text=data["text"],
            font_size=data.get("font_size", 12),
            font_family=data.get("font_family", "Arial"),
            color=data.get("color", "#000000"),
            background_color=data.get("background_color"),
            rotation=data.get("rotation", 0.0),
            id=data.get("id")
        )


@dataclass
class DimensionLine:
    """
    Dimension line showing measurement between two points.
    
    Automatically calculates and displays distance with leader lines
    and text.
    """
    start: Point
    end: Point
    offset: float = 24.0  # Offset from measured line (inches)
    show_arrows: bool = True
    show_extensions: bool = True
    text_above: bool = True
    precision: int = 1  # Decimal places
    units: str = "feet_inches"  # or "inches", "feet", "mm", "cm", "m"
    color: str = "#FF0000"
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def distance(self) -> float:
        """Get the distance in inches."""
        return self.start.distance_to(self.end)
    
    def format_distance(self) -> str:
        """Format the distance according to units setting."""
        dist_inches = self.distance()
        
        if self.units == "feet_inches":
            feet = int(dist_inches // 12)
            inches = dist_inches % 12
            if inches == 0:
                return f"{feet}'-0\""
            else:
                return f"{feet}'-{inches:.{self.precision}f}\""
        
        elif self.units == "feet":
            feet = dist_inches / 12
            return f"{feet:.{self.precision}f}'"
        
        elif self.units == "inches":
            return f"{dist_inches:.{self.precision}f}\""
        
        elif self.units == "mm":
            mm = dist_inches * 25.4
            return f"{mm:.{self.precision}f} mm"
        
        elif self.units == "cm":
            cm = dist_inches * 2.54
            return f"{cm:.{self.precision}f} cm"
        
        elif self.units == "m":
            m = dist_inches * 0.0254
            return f"{m:.{self.precision}f} m"
        
        return f"{dist_inches:.{self.precision}f}\""
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "offset": self.offset,
            "show_arrows": self.show_arrows,
            "show_extensions": self.show_extensions,
            "text_above": self.text_above,
            "precision": self.precision,
            "units": self.units,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DimensionLine':
        """Deserialize from dictionary."""
        return cls(
            start=Point.from_dict(data["start"]),
            end=Point.from_dict(data["end"]),
            offset=data.get("offset", 24.0),
            show_arrows=data.get("show_arrows", True),
            show_extensions=data.get("show_extensions", True),
            text_above=data.get("text_above", True),
            precision=data.get("precision", 1),
            units=data.get("units", "feet_inches"),
            color=data.get("color", "#FF0000"),
            id=data.get("id")
        )


class AnnotationManager:
    """
    Manages text annotations and dimension lines in a floor plan.
    """
    
    def __init__(self):
        self.text_annotations: List[TextAnnotation] = []
        self.dimension_lines: List[DimensionLine] = []
        
        logger.info("AnnotationManager initialized")
    
    def add_text(self, annotation: TextAnnotation) -> str:
        """Add a text annotation."""
        self.text_annotations.append(annotation)
        logger.info(f"Added text annotation: '{annotation.text[:20]}...'")
        return annotation.id
    
    def remove_text(self, annotation_id: str) -> bool:
        """Remove a text annotation."""
        for i, ann in enumerate(self.text_annotations):
            if ann.id == annotation_id:
                self.text_annotations.pop(i)
                logger.info(f"Removed text annotation: {annotation_id}")
                return True
        return False
    
    def add_dimension(self, dimension: DimensionLine) -> str:
        """Add a dimension line."""
        self.dimension_lines.append(dimension)
        logger.info(f"Added dimension line: {dimension.format_distance()}")
        return dimension.id
    
    def remove_dimension(self, dimension_id: str) -> bool:
        """Remove a dimension line."""
        for i, dim in enumerate(self.dimension_lines):
            if dim.id == dimension_id:
                self.dimension_lines.pop(i)
                logger.info(f"Removed dimension line: {dimension_id}")
                return True
        return False
    
    def clear_all_text(self):
        """Remove all text annotations."""
        count = len(self.text_annotations)
        self.text_annotations.clear()
        logger.info(f"Cleared {count} text annotations")
    
    def clear_all_dimensions(self):
        """Remove all dimension lines."""
        count = len(self.dimension_lines)
        self.dimension_lines.clear()
        logger.info(f"Cleared {count} dimension lines")
    
    def auto_dimension_wall(self, wall, offset: float = 24.0) -> DimensionLine:
        """
        Automatically create a dimension line for a wall.
        
        Args:
            wall: Wall object to dimension
            offset: Distance to offset dimension from wall
            
        Returns:
            DimensionLine object
        """
        import math
        
        # Calculate perpendicular offset
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length > 0:
            # Perpendicular unit vector
            perp_x = -dy / length
            perp_y = dx / length
            
            # Offset points
            start_offset = Point(
                wall.start.x + perp_x * offset,
                wall.start.y + perp_y * offset
            )
            end_offset = Point(
                wall.end.x + perp_x * offset,
                wall.end.y + perp_y * offset
            )
            
            dim = DimensionLine(start_offset, end_offset, offset=0)
            self.add_dimension(dim)
            return dim
        
        return None
    
    def auto_dimension_room(self, room, floor_plan, offset: float = 36.0) -> List[DimensionLine]:
        """
        Automatically dimension all walls of a room.
        
        Args:
            room: Room object
            floor_plan: FloorPlan containing the walls
            offset: Distance to offset dimensions
            
        Returns:
            List of created DimensionLine objects
        """
        dimensions = []
        
        for wall_id in room.wall_ids:
            wall = floor_plan.get_wall(wall_id)
            if wall:
                dim = self.auto_dimension_wall(wall, offset)
                if dim:
                    dimensions.append(dim)
        
        logger.info(f"Auto-dimensioned room '{room.name}': {len(dimensions)} dimensions")
        return dimensions
    
    def to_dict(self) -> dict:
        """Serialize all annotations."""
        return {
            "text_annotations": [a.to_dict() for a in self.text_annotations],
            "dimension_lines": [d.to_dict() for d in self.dimension_lines]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnnotationManager':
        """Deserialize annotations."""
        manager = cls()
        
        for ann_data in data.get("text_annotations", []):
            manager.text_annotations.append(TextAnnotation.from_dict(ann_data))
        
        for dim_data in data.get("dimension_lines", []):
            manager.dimension_lines.append(DimensionLine.from_dict(dim_data))
        
        logger.info(f"Loaded {len(manager.text_annotations)} annotations, "
                   f"{len(manager.dimension_lines)} dimensions")
        return manager

