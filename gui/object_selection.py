"""
Enhanced Object Selection and Transformation for Floor Plan Canvas

Adds ability to select, move, resize, and rotate furniture, fixtures, and stairs.
"""

import math
import logging
from typing import Optional, Tuple, List, Union
from enum import Enum, auto

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QTransform
from PyQt6.QtWidgets import QGraphicsItem

from core import Point, Furniture, Fixture, Stair

logger = logging.getLogger(__name__)


class TransformMode(Enum):
    """Modes for transforming selected objects."""
    NONE = auto()
    MOVE = auto()
    RESIZE_TL = auto()  # Top-left
    RESIZE_TR = auto()  # Top-right
    RESIZE_BL = auto()  # Bottom-left
    RESIZE_BR = auto()  # Bottom-right
    RESIZE_T = auto()   # Top edge
    RESIZE_B = auto()   # Bottom edge
    RESIZE_L = auto()   # Left edge
    RESIZE_R = auto()   # Right edge
    ROTATE = auto()


class SelectableObject:
    """
    Wrapper for furniture, fixtures, and stairs to add selection/transformation state.
    """
    
    def __init__(self, obj: Union[Furniture, Fixture, Stair]):
        self.obj = obj
        self.is_selected = False
        self.transform_mode = TransformMode.NONE
        
    @property
    def position(self) -> Point:
        if isinstance(self.obj, Stair):
            # For stairs, compute center point from start and end
            cx = (self.obj.start.x + self.obj.end.x) / 2
            cy = (self.obj.start.y + self.obj.end.y) / 2
            return Point(cx, cy)
        else:
            return self.obj.position
    
    @position.setter
    def position(self, value: Point):
        if isinstance(self.obj, Stair):
            # For stairs, move both start and end to maintain length
            # Calculate current center
            old_cx = (self.obj.start.x + self.obj.end.x) / 2
            old_cy = (self.obj.start.y + self.obj.end.y) / 2
            # Calculate offset
            dx = value.x - old_cx
            dy = value.y - old_cy
            # Move both points
            self.obj.start = Point(self.obj.start.x + dx, self.obj.start.y + dy)
            self.obj.end = Point(self.obj.end.x + dx, self.obj.end.y + dy)
        else:
            self.obj.position = value
    
    @property
    def width(self) -> float:
        return self.obj.width
    
    @width.setter
    def width(self, value: float):
        self.obj.width = max(6.0, value)  # Minimum 6 inches
    
    @property
    def depth(self) -> float:
        if isinstance(self.obj, Stair):
            # For stairs, depth is the length (distance from start to end)
            return self.obj.length()
        else:
            return self.obj.depth
    
    @depth.setter
    def depth(self, value: float):
        if isinstance(self.obj, Stair):
            # For stairs, changing depth means changing the length
            # Scale start and end points relative to center
            current_length = self.obj.length()
            if current_length > 0:
                scale = max(6.0, value) / current_length
                cx = (self.obj.start.x + self.obj.end.x) / 2
                cy = (self.obj.start.y + self.obj.end.y) / 2
                # Scale relative to center
                self.obj.start = Point(
                    cx + (self.obj.start.x - cx) * scale,
                    cy + (self.obj.start.y - cy) * scale
                )
                self.obj.end = Point(
                    cx + (self.obj.end.x - cx) * scale,
                    cy + (self.obj.end.y - cy) * scale
                )
        else:
            self.obj.depth = max(6.0, value)  # Minimum 6 inches
    
    @property
    def rotation(self) -> float:
        return self.obj.rotation
    
    @rotation.setter
    def rotation(self, value: float):
        # Normalize to 0-360
        self.obj.rotation = value % 360
    
    def get_bounding_rect(self) -> QRectF:
        """Get bounding rectangle in world coordinates."""
        # Center point
        cx = self.position.x
        cy = self.position.y
        
        # Half dimensions
        hw = self.width / 2
        hd = self.depth / 2
        
        # Create rect centered at origin
        rect = QRectF(-hw, -hd, self.width, self.depth)
        
        # Apply rotation
        transform = QTransform()
        transform.translate(cx, cy)
        transform.rotate(self.rotation)
        
        # Get rotated bounding rect
        rotated_rect = transform.mapRect(rect)
        
        return rotated_rect
    
    def contains_point(self, point: Point) -> bool:
        """Check if point is inside the object."""
        # Transform point to object's local coordinate system
        cx = self.position.x
        cy = self.position.y
        
        # Translate to origin
        px = point.x - cx
        py = point.y - cy
        
        # Rotate by negative rotation
        angle = -math.radians(self.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        local_x = px * cos_a - py * sin_a
        local_y = px * sin_a + py * cos_a
        
        # Check if in bounds
        hw = self.width / 2
        hd = self.depth / 2
        
        return -hw <= local_x <= hw and -hd <= local_y <= hd


class ObjectTransformHandler:
    """
    Handles mouse interaction for transforming selected objects.
    """
    
    HANDLE_SIZE = 8  # Handle size in screen pixels
    ROTATION_HANDLE_OFFSET = 30  # Distance from top edge in screen pixels
    
    def __init__(self, scale: float):
        """
        Initialize handler.
        
        Args:
            scale: Current canvas scale (pixels per inch)
        """
        self.scale = scale
        self.selected_object: Optional[SelectableObject] = None
        self.transform_mode = TransformMode.NONE
        self.drag_start_pos: Optional[Point] = None
        self.original_position: Optional[Point] = None
        self.original_width: float = 0
        self.original_depth: float = 0
        self.original_rotation: float = 0
    
    def set_selected_object(self, obj: Optional[SelectableObject]):
        """Set the currently selected object."""
        if self.selected_object:
            self.selected_object.is_selected = False
        
        self.selected_object = obj
        
        if self.selected_object:
            self.selected_object.is_selected = True
            self.transform_mode = TransformMode.NONE
    
    def get_handle_at_point(self, point: Point) -> TransformMode:
        """
        Determine which transformation handle is at the given point.
        
        Args:
            point: World coordinates
            
        Returns:
            TransformMode indicating which handle was clicked
        """
        if not self.selected_object:
            return TransformMode.NONE
        
        obj = self.selected_object
        
        # Convert handle size from screen pixels to world units
        handle_size_world = self.HANDLE_SIZE / self.scale
        
        # Get object corners in world coordinates
        corners = self._get_object_corners(obj)
        
        # Check corner handles (for resizing)
        corner_handles = [
            (TransformMode.RESIZE_TL, corners[0]),
            (TransformMode.RESIZE_TR, corners[1]),
            (TransformMode.RESIZE_BR, corners[2]),
            (TransformMode.RESIZE_BL, corners[3]),
        ]
        
        for mode, corner in corner_handles:
            if self._point_near(point, corner, handle_size_world):
                return mode
        
        # Check rotation handle (above top edge)
        rotation_offset_world = self.ROTATION_HANDLE_OFFSET / self.scale
        rot_handle_pos = self._get_rotation_handle_pos(obj, rotation_offset_world)
        
        if self._point_near(point, rot_handle_pos, handle_size_world):
            return TransformMode.ROTATE
        
        # Check if inside object bounds (for moving)
        if obj.contains_point(point):
            return TransformMode.MOVE
        
        return TransformMode.NONE
    
    def start_transform(self, point: Point, mode: TransformMode):
        """Start a transformation operation."""
        if not self.selected_object:
            return
        
        self.transform_mode = mode
        self.drag_start_pos = point
        self.original_position = Point(
            self.selected_object.position.x,
            self.selected_object.position.y
        )
        self.original_width = self.selected_object.width
        self.original_depth = self.selected_object.depth
        self.original_rotation = self.selected_object.rotation
    
    def update_transform(self, point: Point):
        """Update the transformation based on current mouse position."""
        if not self.selected_object or not self.drag_start_pos:
            return
        
        dx = point.x - self.drag_start_pos.x
        dy = point.y - self.drag_start_pos.y
        
        if self.transform_mode == TransformMode.MOVE:
            self._update_move(dx, dy)
        elif self.transform_mode == TransformMode.ROTATE:
            self._update_rotate(point)
        elif self.transform_mode.name.startswith('RESIZE'):
            self._update_resize(dx, dy)
    
    def end_transform(self):
        """End the current transformation."""
        self.transform_mode = TransformMode.NONE
        self.drag_start_pos = None
    
    def _update_move(self, dx: float, dy: float):
        """Update object position during move."""
        self.selected_object.position = Point(
            self.original_position.x + dx,
            self.original_position.y + dy
        )
    
    def _update_rotate(self, point: Point):
        """Update object rotation."""
        obj = self.selected_object
        
        # Calculate angle from object center to mouse
        dx = point.x - obj.position.x
        dy = point.y - obj.position.y
        
        angle = math.degrees(math.atan2(dy, dx))
        
        # Adjust so rotation handle starts at top (0 degrees = up)
        angle += 90
        
        obj.rotation = angle
    
    def _update_resize(self, dx: float, dy: float):
        """Update object size during resize."""
        obj = self.selected_object
        mode = self.transform_mode
        
        # Rotate delta by inverse object rotation to get local coordinates
        angle = -math.radians(obj.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        local_dx = dx * cos_a - dy * sin_a
        local_dy = dx * sin_a + dy * cos_a
        
        # Apply resize based on which handle
        if mode == TransformMode.RESIZE_TL:
            # Top-left: decrease width and depth, move position
            new_width = self.original_width - 2 * local_dx
            new_depth = self.original_depth - 2 * local_dy
            self._apply_resize(new_width, new_depth, local_dx, local_dy)
            
        elif mode == TransformMode.RESIZE_TR:
            # Top-right: increase width, decrease depth
            new_width = self.original_width + 2 * local_dx
            new_depth = self.original_depth - 2 * local_dy
            self._apply_resize(new_width, new_depth, -local_dx, local_dy)
            
        elif mode == TransformMode.RESIZE_BR:
            # Bottom-right: increase both
            new_width = self.original_width + 2 * local_dx
            new_depth = self.original_depth + 2 * local_dy
            self._apply_resize(new_width, new_depth, -local_dx, -local_dy)
            
        elif mode == TransformMode.RESIZE_BL:
            # Bottom-left: decrease width, increase depth
            new_width = self.original_width - 2 * local_dx
            new_depth = self.original_depth + 2 * local_dy
            self._apply_resize(new_width, new_depth, local_dx, -local_dy)
    
    def _apply_resize(self, new_width: float, new_depth: float, 
                      offset_x: float, offset_y: float):
        """Apply resize with minimum size constraints and position adjustment."""
        obj = self.selected_object
        
        # Enforce minimum sizes
        new_width = max(6.0, new_width)
        new_depth = max(6.0, new_depth)
        
        # Update size
        obj.width = new_width
        obj.depth = new_depth
        
        # Adjust position (in world coordinates)
        # Rotate offset by object rotation
        angle = math.radians(obj.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        world_dx = offset_x * cos_a - offset_y * sin_a
        world_dy = offset_x * sin_a + offset_y * cos_a
        
        obj.position = Point(
            self.original_position.x + world_dx,
            self.original_position.y + world_dy
        )
    
    def _get_object_corners(self, obj: SelectableObject) -> List[Point]:
        """Get the four corners of the object in world coordinates."""
        cx = obj.position.x
        cy = obj.position.y
        hw = obj.width / 2
        hd = obj.depth / 2
        
        # Local corners (before rotation)
        local_corners = [
            (-hw, -hd),  # Top-left
            (hw, -hd),   # Top-right
            (hw, hd),    # Bottom-right
            (-hw, hd),   # Bottom-left
        ]
        
        # Rotate and translate
        angle = math.radians(obj.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        world_corners = []
        for lx, ly in local_corners:
            wx = cx + (lx * cos_a - ly * sin_a)
            wy = cy + (lx * sin_a + ly * cos_a)
            world_corners.append(Point(wx, wy))
        
        return world_corners
    
    def _get_rotation_handle_pos(self, obj: SelectableObject, offset: float) -> Point:
        """Get position of rotation handle."""
        cx = obj.position.x
        cy = obj.position.y
        hd = obj.depth / 2
        
        # Position above top edge
        local_x = 0
        local_y = -(hd + offset)
        
        # Rotate
        angle = math.radians(obj.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        wx = cx + (local_x * cos_a - local_y * sin_a)
        wy = cy + (local_x * sin_a + local_y * cos_a)
        
        return Point(wx, wy)
    
    def _point_near(self, p1: Point, p2: Point, threshold: float) -> bool:
        """Check if two points are within threshold distance."""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        dist_sq = dx * dx + dy * dy
        return dist_sq <= threshold * threshold
    
    def draw_selection_handles(self, painter: QPainter, scale: float):
        """
        Draw selection handles and bounding box for selected object.
        
        Args:
            painter: QPainter to draw with
            scale: Canvas scale (pixels per inch)
        """
        if not self.selected_object:
            return
        
        obj = self.selected_object
        
        # Update scale
        self.scale = scale
        
        # Draw bounding box
        self._draw_bounding_box(painter, obj)
        
        # Draw corner handles
        self._draw_corner_handles(painter, obj)
        
        # Draw rotation handle
        self._draw_rotation_handle(painter, obj)
    
    def _draw_bounding_box(self, painter: QPainter, obj: SelectableObject):
        """Draw bounding box around selected object."""
        corners = self._get_object_corners(obj)
        
        # Draw box
        pen = QPen(QColor(0, 120, 215), 2)  # Blue selection color
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw lines between corners
        for i in range(4):
            c1 = corners[i]
            c2 = corners[(i + 1) % 4]
            painter.drawLine(
                QPointF(c1.x * self.scale, c1.y * self.scale),
                QPointF(c2.x * self.scale, c2.y * self.scale)
            )
    
    def _draw_corner_handles(self, painter: QPainter, obj: SelectableObject):
        """Draw resize handles at corners."""
        corners = self._get_object_corners(obj)
        
        pen = QPen(QColor(0, 120, 215), 1)
        brush = QBrush(QColor(255, 255, 255))
        painter.setPen(pen)
        painter.setBrush(brush)
        
        for corner in corners:
            cx = corner.x * self.scale
            cy = corner.y * self.scale
            painter.drawRect(
                int(cx - self.HANDLE_SIZE / 2),
                int(cy - self.HANDLE_SIZE / 2),
                self.HANDLE_SIZE,
                self.HANDLE_SIZE
            )
    
    def _draw_rotation_handle(self, painter: QPainter, obj: SelectableObject):
        """Draw rotation handle above object."""
        rotation_offset_world = self.ROTATION_HANDLE_OFFSET / self.scale
        handle_pos = self._get_rotation_handle_pos(obj, rotation_offset_world)
        
        # Draw line from top center to handle
        cx = obj.position.x
        cy = obj.position.y
        hd = obj.depth / 2
        
        # Top center in world coords
        angle = math.radians(obj.rotation)
        top_x = cx - hd * math.sin(angle)
        top_y = cy - hd * math.cos(angle)
        
        # Draw line
        pen = QPen(QColor(0, 120, 215), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(top_x * self.scale, top_y * self.scale),
            QPointF(handle_pos.x * self.scale, handle_pos.y * self.scale)
        )
        
        # Draw handle (circle)
        brush = QBrush(QColor(100, 200, 100))  # Green for rotation
        painter.setBrush(brush)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        cx = handle_pos.x * self.scale
        cy = handle_pos.y * self.scale
        painter.drawEllipse(
            QPointF(cx, cy),
            self.HANDLE_SIZE / 2,
            self.HANDLE_SIZE / 2
        )
