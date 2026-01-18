"""
Advanced transformation tools for floor plan objects.

Provides interactive move, rotate, and array/pattern tools.
"""

import logging
import math
from typing import List, Optional, Tuple
from copy import deepcopy

from core import Point, Furniture, Fixture, Stair

logger = logging.getLogger(__name__)


class MoveTransform:
    """
    Interactive move tool for objects.
    
    Allows dragging objects to new positions with real-time preview.
    """
    
    def __init__(self):
        self.active = False
        self.object = None
        self.original_position = None
        self.start_mouse = None
        
        logger.info("MoveTransform initialized")
    
    def start(self, obj, mouse_pos: Point):
        """Start moving an object."""
        self.active = True
        self.object = obj
        self.start_mouse = mouse_pos
        
        # Store original position based on object type
        if hasattr(obj, 'position'):
            self.original_position = Point(obj.position.x, obj.position.y)
        elif hasattr(obj, 'start'):
            self.original_position = Point(obj.start.x, obj.start.y)
        
        logger.info(f"Started moving {type(obj).__name__}")
    
    def update(self, mouse_pos: Point):
        """Update object position during drag."""
        if not self.active or not self.object:
            return
        
        # Calculate delta
        dx = mouse_pos.x - self.start_mouse.x
        dy = mouse_pos.y - self.start_mouse.y
        
        # Apply to object
        if hasattr(self.object, 'position'):
            self.object.position.x = self.original_position.x + dx
            self.object.position.y = self.original_position.y + dy
        elif hasattr(self.object, 'start') and hasattr(self.object, 'end'):
            # For objects with start/end (walls, stairs)
            width = self.object.end.x - self.object.start.x
            height = self.object.end.y - self.object.start.y
            self.object.start.x = self.original_position.x + dx
            self.object.start.y = self.original_position.y + dy
            self.object.end.x = self.object.start.x + width
            self.object.end.y = self.object.start.y + height
    
    def finish(self):
        """Finish the move operation."""
        self.active = False
        moved_obj = self.object
        self.object = None
        self.original_position = None
        self.start_mouse = None
        
        logger.info("Finished move operation")
        return moved_obj
    
    def cancel(self):
        """Cancel the move and restore original position."""
        if self.active and self.object:
            if hasattr(self.object, 'position'):
                self.object.position.x = self.original_position.x
                self.object.position.y = self.original_position.y
            elif hasattr(self.object, 'start'):
                width = self.object.end.x - self.object.start.x
                height = self.object.end.y - self.object.start.y
                self.object.start.x = self.original_position.x
                self.object.start.y = self.original_position.y
                self.object.end.x = self.object.start.x + width
                self.object.end.y = self.object.start.y + height
        
        self.active = False
        self.object = None
        logger.info("Cancelled move operation")


class RotateTransform:
    """
    Interactive rotate tool for objects.
    
    Allows rotating objects around their center point.
    """
    
    def __init__(self):
        self.active = False
        self.object = None
        self.original_rotation = 0
        self.center = None
        self.start_angle = 0
        
        logger.info("RotateTransform initialized")
    
    def start(self, obj, mouse_pos: Point):
        """Start rotating an object."""
        if not hasattr(obj, 'rotation'):
            logger.warning(f"Object {type(obj).__name__} cannot be rotated")
            return False
        
        self.active = True
        self.object = obj
        self.original_rotation = obj.rotation
        
        # Calculate center point
        if hasattr(obj, 'position'):
            self.center = Point(obj.position.x, obj.position.y)
        
        # Calculate initial angle
        self.start_angle = math.degrees(
            math.atan2(mouse_pos.y - self.center.y, mouse_pos.x - self.center.x)
        )
        
        logger.info(f"Started rotating {type(obj).__name__}")
        return True
    
    def update(self, mouse_pos: Point):
        """Update rotation during drag."""
        if not self.active or not self.object or not self.center:
            return
        
        # Calculate current angle
        current_angle = math.degrees(
            math.atan2(mouse_pos.y - self.center.y, mouse_pos.x - self.center.x)
        )
        
        # Calculate delta angle
        delta_angle = current_angle - self.start_angle
        
        # Apply rotation
        self.object.rotation = (self.original_rotation + delta_angle) % 360
    
    def snap_to_increment(self, increment: float = 15.0):
        """Snap rotation to nearest increment (e.g., 15 degrees)."""
        if self.object and hasattr(self.object, 'rotation'):
            self.object.rotation = round(self.object.rotation / increment) * increment
    
    def finish(self):
        """Finish the rotation."""
        self.active = False
        rotated_obj = self.object
        self.object = None
        self.original_rotation = 0
        self.center = None
        
        logger.info(f"Finished rotation: {rotated_obj.rotation:.1f}°")
        return rotated_obj
    
    def cancel(self):
        """Cancel rotation and restore original angle."""
        if self.active and self.object:
            self.object.rotation = self.original_rotation
        
        self.active = False
        self.object = None
        logger.info("Cancelled rotation")


class ArrayTool:
    """
    Create arrays/patterns of objects.
    
    Supports linear arrays (rows/columns) and circular/radial arrays.
    """
    
    @staticmethod
    def linear_array(obj, count: int, offset: Point, include_original: bool = True) -> List:
        """
        Create a linear array of objects.
        
        Args:
            obj: Object to array
            count: Number of copies
            offset: Offset between each copy
            include_original: Whether to include the original object
            
        Returns:
            List of objects (including or excluding original)
        """
        import uuid
        
        objects = []
        
        if include_original:
            objects.append(obj)
        
        for i in range(1, count + (0 if include_original else 1)):
            # Deep copy the object
            new_obj = deepcopy(obj)
            
            # Generate new ID
            new_obj.id = str(uuid.uuid4())
            
            # Apply offset
            if hasattr(new_obj, 'position'):
                new_obj.position.x += offset.x * i
                new_obj.position.y += offset.y * i
            elif hasattr(new_obj, 'start') and hasattr(new_obj, 'end'):
                new_obj.start.x += offset.x * i
                new_obj.start.y += offset.y * i
                new_obj.end.x += offset.x * i
                new_obj.end.y += offset.y * i
            
            objects.append(new_obj)
        
        logger.info(f"Created linear array of {len(objects)} objects")
        return objects
    
    @staticmethod
    def rectangular_array(obj, rows: int, cols: int, row_spacing: float, 
                         col_spacing: float, include_original: bool = True) -> List:
        """
        Create a rectangular array (grid) of objects.
        
        Args:
            obj: Object to array
            rows: Number of rows
            cols: Number of columns
            row_spacing: Spacing between rows (inches)
            col_spacing: Spacing between columns (inches)
            include_original: Whether to include original
            
        Returns:
            List of objects in grid pattern
        """
        import uuid
        
        objects = []
        
        for row in range(rows):
            for col in range(cols):
                if row == 0 and col == 0 and include_original:
                    objects.append(obj)
                    continue
                
                # Deep copy
                new_obj = deepcopy(obj)
                new_obj.id = str(uuid.uuid4())
                
                # Apply offsets
                if hasattr(new_obj, 'position'):
                    new_obj.position.x += col * col_spacing
                    new_obj.position.y += row * row_spacing
                elif hasattr(new_obj, 'start') and hasattr(new_obj, 'end'):
                    new_obj.start.x += col * col_spacing
                    new_obj.start.y += row * row_spacing
                    new_obj.end.x += col * col_spacing
                    new_obj.end.y += row * row_spacing
                
                objects.append(new_obj)
        
        logger.info(f"Created {rows}×{cols} rectangular array ({len(objects)} objects)")
        return objects
    
    @staticmethod
    def circular_array(obj, count: int, radius: float, start_angle: float = 0,
                      rotate_objects: bool = True) -> List:
        """
        Create a circular/radial array of objects.
        
        Args:
            obj: Object to array
            count: Number of objects in circle
            radius: Radius of circle (inches)
            start_angle: Starting angle (degrees)
            rotate_objects: Whether to rotate objects to face center
            
        Returns:
            List of objects arranged in circle
        """
        import uuid
        
        objects = []
        
        # Get center point
        if hasattr(obj, 'position'):
            center = Point(obj.position.x, obj.position.y)
        else:
            center = Point(0, 0)
        
        angle_step = 360.0 / count
        
        for i in range(count):
            angle = math.radians(start_angle + i * angle_step)
            
            # Calculate position on circle
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            
            # Create copy
            if i == 0:
                new_obj = obj
            else:
                new_obj = deepcopy(obj)
                new_obj.id = str(uuid.uuid4())
            
            # Set position
            if hasattr(new_obj, 'position'):
                new_obj.position.x = x
                new_obj.position.y = y
                
                # Rotate to face center
                if rotate_objects and hasattr(new_obj, 'rotation'):
                    new_obj.rotation = (math.degrees(angle) + 90) % 360
            
            objects.append(new_obj)
        
        logger.info(f"Created circular array of {count} objects (radius: {radius}\")")
        return objects
