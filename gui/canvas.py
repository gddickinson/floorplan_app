"""
Interactive canvas widget for drawing and editing floor plans.

The canvas handles:
- Wall drawing and editing
- Opening (door/window) placement
- Selection and manipulation
- Grid display and snapping
- Zoom and pan
"""

import logging
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QWheelEvent,
    QMouseEvent, QPaintEvent, QFont
)

from core import (
    Point, Wall, Opening, OpeningType, Room, FloorPlan,
    Furniture, FurnitureType, Fixture, FixtureType, Stair, StairType
)
from utils import AppConfig, format_dimension
from utils.measurements import MeasurementTool
from .object_selection import (
    SelectableObject, ObjectTransformHandler, TransformMode
)
from utils.undo_commands import ObjectState, TransformObjectCommand, RemoveObjectCommand


logger = logging.getLogger(__name__)


class DrawMode:
    """Drawing modes for the canvas."""
    SELECT = "select"
    DRAW_WALL = "draw_wall"
    ADD_DOOR = "add_door"
    ADD_WINDOW = "add_window"
    MEASURE = "measure"
    CREATE_ROOM = "create_room"
    MOVE = "move"
    PLACE_FURNITURE = "place_furniture"
    PLACE_FIXTURE = "place_fixture"
    PLACE_STAIR = "place_stair"
    ROTATE = "rotate"


class FloorPlanCanvas(QWidget):
    """
    Interactive canvas for floor plan drawing and editing.
    
    Signals:
        plan_modified: Emitted when the floor plan is modified
        selection_changed: Emitted when selection changes
        status_message: Emitted to update status bar
    """
    
    plan_modified = pyqtSignal()
    selection_changed = pyqtSignal(object)  # Selected object or None
    object_selected = pyqtSignal(object)  # Emits selected object or None
    status_message = pyqtSignal(str)
    
    def __init__(self, floor_plan: Optional[FloorPlan] = None, parent=None):
        super().__init__(parent)
        
        # Floor plan data
        self.floor_plan = floor_plan or FloorPlan()
        
        # Drawing state
        self.draw_mode = DrawMode.SELECT
        self.temp_wall_start: Optional[Point] = None
        self.selected_wall: Optional[str] = None  # Wall ID
        self.selected_opening: Optional[str] = None  # Opening ID
        self.selected_room: Optional[str] = None  # Room ID
        self.selected_furniture: Optional[str] = None  # Furniture ID
        self.selected_fixture: Optional[str] = None  # Fixture ID
        self.selected_stair: Optional[str] = None  # Stair ID
        self.measurement_tool = MeasurementTool()
        self.room_walls_selection: List[str] = []  # For room creation mode
        self.pending_object = None  # Object being placed
        self.pending_object_type = None  # Type of pending object
        
        # View state
        self.scale = AppConfig.DEFAULT_SCALE  # pixels per inch
        self.offset_x = 0.0  # Pan offset in pixels
        self.offset_y = 0.0
        self.show_grid = True
        self.show_dimensions = True
        
        # Interaction state
        self.is_panning = False
        self.last_mouse_pos: Optional[QPointF] = None
        self.hover_point: Optional[Point] = None
        
        # Configure widget
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        

        # Object selection state
        self.selectable_objects = []
        self.transform_handler = ObjectTransformHandler(self.scale)
        self.selected_object = None
        self.is_transforming = False

        logger.info("Canvas initialized")
    
    def set_floor_plan(self, floor_plan: FloorPlan):
        """Set a new floor plan and refresh the view."""
        self.floor_plan = floor_plan
        self.selected_wall = None
        self.selected_opening = None
        self.temp_wall_start = None
        self.fit_to_view()
        self.update()
        self.refresh_selectable_objects()
        logger.info(f"Loaded floor plan: {floor_plan.name}")
    
    def set_draw_mode(self, mode: str):
        """Change the drawing mode."""
        self.draw_mode = mode
        self.temp_wall_start = None
        self.update()
        logger.debug(f"Draw mode changed to: {mode}")
    
    def world_to_screen(self, point: Point) -> QPointF:
        """Convert world coordinates (inches) to screen coordinates (pixels)."""
        x = point.x * self.scale + self.offset_x + self.width() / 2
        y = point.y * self.scale + self.offset_y + self.height() / 2
        return QPointF(x, y)
    
    def screen_to_world(self, screen_point: QPointF) -> Point:
        """Convert screen coordinates (pixels) to world coordinates (inches)."""
        x = (screen_point.x() - self.width() / 2 - self.offset_x) / self.scale
        y = (screen_point.y() - self.height() / 2 - self.offset_y) / self.scale
        return Point(x, y)
    
    def snap_to_grid(self, point: Point) -> Point:
        """Snap a point to the nearest grid intersection."""
        grid_size = AppConfig.GRID_SIZE
        snapped_x = round(point.x / grid_size) * grid_size
        snapped_y = round(point.y / grid_size) * grid_size
        return Point(snapped_x, snapped_y)
    
    def find_snap_point(self, point: Point) -> Point:
        """
        Find the best snap point considering grid and existing walls.
        
        Priority: wall endpoints > grid intersections
        """
        tolerance = AppConfig.SNAP_TOLERANCE
        
        # Check for nearby wall endpoints
        for wall in self.floor_plan.walls:
            for endpoint in [wall.start, wall.end]:
                if point.distance_to(endpoint) < tolerance:
                    return endpoint
        
        # Otherwise snap to grid
        return self.snap_to_grid(point)
    
    def fit_to_view(self):
        """Adjust zoom and pan to fit the entire floor plan in view."""
        bounds = self.floor_plan.get_bounds()
        if not bounds:
            self.scale = AppConfig.DEFAULT_SCALE
            self.offset_x = 0
            self.offset_y = 0
            return
        
        min_pt, max_pt = bounds
        width_inches = max_pt.x - min_pt.x
        height_inches = max_pt.y - min_pt.y
        
        # Add 20% padding
        width_inches *= 1.2
        height_inches *= 1.2
        
        # Calculate scale to fit
        if width_inches > 0 and height_inches > 0:
            scale_x = (self.width() * 0.9) / width_inches
            scale_y = (self.height() * 0.9) / height_inches
            self.scale = min(scale_x, scale_y)
            self.scale = max(AppConfig.MIN_SCALE, min(self.scale, AppConfig.MAX_SCALE))
        
        # Center the plan
        center_x = (min_pt.x + max_pt.x) / 2
        center_y = (min_pt.y + max_pt.y) / 2
        self.offset_x = -center_x * self.scale
        self.offset_y = -center_y * self.scale
        
        self.update()
        logger.info(f"Fit to view: scale={self.scale:.2f}")
    
    def zoom(self, delta: int, center: Optional[QPointF] = None):
        """
        Zoom in or out.
        
        Args:
            delta: Positive to zoom in, negative to zoom out
            center: Optional zoom center in screen coordinates
        """
        if center is None:
            center = QPointF(self.width() / 2, self.height() / 2)
        
        # Get world point before zoom
        world_pt = self.screen_to_world(center)
        
        # Update scale
        factor = 1.1 if delta > 0 else 0.9
        new_scale = self.scale * factor
        new_scale = max(AppConfig.MIN_SCALE, min(new_scale, AppConfig.MAX_SCALE))
        
        if new_scale != self.scale:
            self.scale = new_scale
            
            # Adjust offset to keep the same world point under cursor
            new_screen = self.world_to_screen(world_pt)
            self.offset_x += center.x() - new_screen.x()
            self.offset_y += center.y() - new_screen.y()
            
            self.update()
            self.status_message.emit(f"Zoom: {int(self.scale / AppConfig.DEFAULT_SCALE * 100)}%")
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the canvas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(AppConfig.CANVAS_BG_COLOR))
        
        # Draw grid
        if self.show_grid:
            self._draw_grid(painter)
        
        # Draw rooms (filled polygons)
        self._draw_rooms(painter)
        
        # Draw walls
        self._draw_walls(painter)
        
        # Draw openings
        self._draw_openings(painter)
        
        # Draw furniture
        self._draw_furniture_items(painter)
        
        # Draw fixtures
        self._draw_fixtures(painter)
        
        # Draw stairs
        self._draw_stairs(painter)
        
        # Draw measurements
        self._draw_measurements(painter)
        
        # Draw pending object being placed
        if self.pending_object and self.hover_point:
            self._draw_pending_object(painter)
        
        # Draw temporary wall being drawn
        if self.temp_wall_start and self.hover_point:
            self._draw_temp_wall(painter)
        
        # Draw hover point
        if self.hover_point and self.draw_mode != DrawMode.SELECT:
            self._draw_hover_point(painter)
    
    def _draw_grid(self, painter: QPainter):
        """Draw the background grid."""
        pen = QPen(QColor(AppConfig.GRID_COLOR))
        pen.setWidth(1)
        painter.setPen(pen)
        
        grid_size = AppConfig.GRID_SIZE
        
        # Calculate visible range in world coordinates
        top_left_world = self.screen_to_world(QPointF(0, 0))
        bottom_right_world = self.screen_to_world(QPointF(self.width(), self.height()))
        
        # Round to grid
        start_x = int(top_left_world.x / grid_size) * grid_size
        end_x = int(bottom_right_world.x / grid_size + 1) * grid_size
        start_y = int(top_left_world.y / grid_size) * grid_size
        end_y = int(bottom_right_world.y / grid_size + 1) * grid_size
        
        # Draw vertical lines
        x = start_x
        while x <= end_x:
            p1 = self.world_to_screen(Point(x, start_y))
            p2 = self.world_to_screen(Point(x, end_y))
            painter.drawLine(p1, p2)
            x += grid_size
        
        # Draw horizontal lines
        y = start_y
        while y <= end_y:
            p1 = self.world_to_screen(Point(start_x, y))
            p2 = self.world_to_screen(Point(end_x, y))
            painter.drawLine(p1, p2)
            y += grid_size
    
    def _draw_walls(self, painter: QPainter):
        """Draw all walls."""
        for wall in self.floor_plan.walls:
            is_selected = (wall.id == self.selected_wall)
            self._draw_wall(painter, wall, is_selected)
    
    def _draw_wall(self, painter: QPainter, wall: Wall, selected: bool = False):
        """Draw a single wall."""
        # Choose color
        color = AppConfig.SELECTED_COLOR if selected else AppConfig.WALL_COLOR
        pen = QPen(QColor(color))
        pen.setWidth(max(2, int(wall.thickness * self.scale / 6)))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw wall line
        p1 = self.world_to_screen(wall.start)
        p2 = self.world_to_screen(wall.end)
        painter.drawLine(p1, p2)
        
        # Draw dimension if selected and option enabled
        if selected and self.show_dimensions:
            self._draw_wall_dimension(painter, wall)
    
    def _draw_wall_dimension(self, painter: QPainter, wall: Wall):
        """Draw dimension text for a wall."""
        midpoint = wall.midpoint()
        screen_mid = self.world_to_screen(midpoint)
        
        dimension_text = format_dimension(wall.length())
        
        # Setup text drawing
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        
        # Draw text with background
        text_rect = painter.fontMetrics().boundingRect(dimension_text)
        text_rect.moveCenter(screen_mid.toPoint())
        
        painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), QColor("#FFFFFF"))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, dimension_text)
    
    def _draw_openings(self, painter: QPainter):
        """Draw all doors and windows."""
        for opening in self.floor_plan.openings:
            wall = self.floor_plan.get_wall(opening.wall_id)
            if wall:
                is_selected = (opening.id == self.selected_opening)
                self._draw_opening(painter, opening, wall, is_selected)
    
    def _draw_opening(self, painter: QPainter, opening: Opening, 
                      wall: Wall, selected: bool = False):
        """Draw a door or window on a wall."""
        # Calculate opening position on wall
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        
        opening_center = Point(
            wall.start.x + dx * opening.position,
            wall.start.y + dy * opening.position
        )
        
        # Choose color
        if opening.opening_type == OpeningType.DOOR:
            color = AppConfig.DOOR_COLOR
        else:
            color = AppConfig.WINDOW_COLOR
        
        if selected:
            color = AppConfig.SELECTED_COLOR
        
        # Draw opening marker
        pen = QPen(QColor(color))
        pen.setWidth(3)
        painter.setPen(pen)
        
        center_screen = self.world_to_screen(opening_center)
        width_pixels = opening.width * self.scale / 2
        
        painter.drawEllipse(center_screen, width_pixels, width_pixels)
        
        # Draw label
        font = QFont("Arial", 8)
        painter.setFont(font)
        label = "D" if opening.opening_type == OpeningType.DOOR else "W"
        painter.drawText(center_screen.toPoint(), label)
    
    def _draw_temp_wall(self, painter: QPainter):
        """Draw the wall currently being drawn."""
        if not self.temp_wall_start or not self.hover_point:
            return
        
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        p1 = self.world_to_screen(self.temp_wall_start)
        p2 = self.world_to_screen(self.hover_point)
        painter.drawLine(p1, p2)
        
        # Draw length
        temp_wall = Wall(self.temp_wall_start, self.hover_point)
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        
        midpoint = temp_wall.midpoint()
        screen_mid = self.world_to_screen(midpoint)
        painter.drawText(screen_mid.toPoint(), format_dimension(temp_wall.length()))
    
    def _draw_hover_point(self, painter: QPainter):
        """Draw a marker at the current hover point."""
        pen = QPen(QColor("#0000FF"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        screen_pt = self.world_to_screen(self.hover_point)
        painter.drawEllipse(screen_pt, 5, 5)
    
    def _draw_rooms(self, painter: QPainter):
        """Draw all rooms as filled polygons."""
        for room in self.floor_plan.rooms:
            is_selected = (room.id == self.selected_room)
            self._draw_room(painter, room, is_selected)
    
    def _draw_room(self, painter: QPainter, room: Room, selected: bool = False):
        """Draw a single room as a filled polygon."""
        if not room.wall_ids:
            return
        
        # Collect all wall endpoints to form polygon
        from PyQt6.QtGui import QPolygonF
        polygon = QPolygonF()
        
        # Get unique points from walls
        points_added = set()
        for wall_id in room.wall_ids:
            wall = self.floor_plan.get_wall(wall_id)
            if wall:
                # Add start point if not already added
                start_key = (round(wall.start.x, 1), round(wall.start.y, 1))
                if start_key not in points_added:
                    polygon.append(self.world_to_screen(wall.start))
                    points_added.add(start_key)
                
                # Add end point if not already added
                end_key = (round(wall.end.x, 1), round(wall.end.y, 1))
                if end_key not in points_added:
                    polygon.append(self.world_to_screen(wall.end))
                    points_added.add(end_key)
        
        if polygon.size() < 3:
            return
        
        # Choose color
        if room.color:
            color = QColor(room.color)
        else:
            color = QColor("#F0F0F0")
        
        if selected:
            color = color.lighter(120)
        
        # Draw filled polygon
        color.setAlpha(100)  # Semi-transparent
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)
        
        # Draw room label at center
        if polygon.size() > 0:
            # Calculate centroid
            cx = sum(polygon[i].x() for i in range(polygon.size())) / polygon.size()
            cy = sum(polygon[i].y() for i in range(polygon.size())) / polygon.size()
            
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("#000000"))
            painter.drawText(int(cx) - 50, int(cy) - 10, 100, 20,
                           Qt.AlignmentFlag.AlignCenter, room.name)
    
    def _draw_measurements(self, painter: QPainter):
        """Draw all measurements."""
        pen = QPen(QColor("#FF00FF"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Draw saved measurements
        for measurement in self.measurement_tool.measurements:
            p1 = self.world_to_screen(measurement.start)
            p2 = self.world_to_screen(measurement.end)
            
            # Draw line
            painter.drawLine(p1, p2)
            
            # Draw endpoints
            painter.drawEllipse(p1, 5, 5)
            painter.drawEllipse(p2, 5, 5)
            
            # Draw distance label
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            
            distance_text = format_dimension(measurement.distance())
            angle_text = f"{measurement.angle():.1f}°"
            
            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.setPen(QColor("#FF00FF"))
            painter.drawText(int(mid_x), int(mid_y) - 10, distance_text)
            painter.drawText(int(mid_x), int(mid_y) + 10, angle_text)
        
        # Draw temporary measurement
        temp = self.measurement_tool.get_temp_measurement(self.hover_point if self.hover_point else Point(0, 0))
        if temp and self.draw_mode == DrawMode.MEASURE:
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            p1 = self.world_to_screen(temp.start)
            p2 = self.world_to_screen(temp.end)
            
            painter.drawLine(p1, p2)
            
            # Draw distance
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            painter.drawText(int(mid_x), int(mid_y), format_dimension(temp.distance()))
    
    def _draw_furniture_items(self, painter: QPainter):
        """Draw all furniture."""
        for furniture in self.floor_plan.furniture:
            is_selected = (furniture.id == self.selected_furniture)
            self._draw_furniture(painter, furniture, is_selected)
    
    def _draw_furniture(self, painter: QPainter, furniture: Furniture, selected: bool = False):
        """Draw a single furniture item."""
        # Convert position to screen coordinates
        pos = self.world_to_screen(furniture.position)
        
        # Calculate dimensions in screen coordinates
        width_screen = furniture.width * self.scale
        depth_screen = furniture.depth * self.scale
        
        # Choose color based on selection
        if selected:
            color = QColor(AppConfig.SELECTED_COLOR)
        else:
            color = QColor("#8B7355")  # Brown for furniture
        
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw as rotated rectangle
        painter.save()
        painter.translate(pos)
        painter.rotate(furniture.rotation)
        
        # Draw furniture rectangle
        rect = QRectF(-width_screen/2, -depth_screen/2, width_screen, depth_screen)
        painter.drawRect(rect)
        
        # Fill with semi-transparent color
        color.setAlpha(50)
        painter.fillRect(rect, color)
        
        painter.restore()
        
        # Draw label
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(pos.toPoint(), furniture.name[:3])
    
    def _draw_fixtures(self, painter: QPainter):
        """Draw all fixtures."""
        for fixture in self.floor_plan.fixtures:
            is_selected = (fixture.id == self.selected_fixture)
            self._draw_fixture(painter, fixture, is_selected)
    
    def _draw_fixture(self, painter: QPainter, fixture: Fixture, selected: bool = False):
        """Draw a single fixture."""
        pos = self.world_to_screen(fixture.position)
        width_screen = fixture.width * self.scale
        depth_screen = fixture.depth * self.scale
        
        if selected:
            color = QColor(AppConfig.SELECTED_COLOR)
        else:
            # Different colors for different fixture types
            if "kitchen" in fixture.fixture_type.value or fixture.fixture_type in [
                FixtureType.REFRIGERATOR, FixtureType.STOVE, FixtureType.OVEN,
                FixtureType.DISHWASHER, FixtureType.MICROWAVE
            ]:
                color = QColor("#C0C0C0")  # Silver for kitchen
            elif fixture.fixture_type in [
                FixtureType.TOILET, FixtureType.SINK, FixtureType.BATHTUB,
                FixtureType.SHOWER, FixtureType.VANITY
            ]:
                color = QColor("#ADD8E6")  # Light blue for bathroom
            else:
                color = QColor("#808080")  # Gray for others
        
        pen = QPen(color.darker())
        pen.setWidth(2)
        painter.setPen(pen)
        
        painter.save()
        painter.translate(pos)
        painter.rotate(fixture.rotation)
        
        rect = QRectF(-width_screen/2, -depth_screen/2, width_screen, depth_screen)
        painter.drawRect(rect)
        
        color.setAlpha(80)
        painter.fillRect(rect, color)
        
        painter.restore()
        
        # Draw icon/label
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(pos.toPoint(), fixture.name[:3])
    
    def _draw_stairs(self, painter: QPainter):
        """Draw all stairs."""
        for stair in self.floor_plan.stairs:
            is_selected = (stair.id == self.selected_stair)
            self._draw_stair(painter, stair, is_selected)
    
    def _draw_stair(self, painter: QPainter, stair: Stair, selected: bool = False):
        """Draw a single staircase."""
        p1 = self.world_to_screen(stair.start)
        p2 = self.world_to_screen(stair.end)
        width_screen = stair.width * self.scale
        
        if selected:
            color = QColor(AppConfig.SELECTED_COLOR)
        else:
            color = QColor("#A0522D")  # Sienna for stairs
        
        pen = QPen(color)
        pen.setWidth(3)
        painter.setPen(pen)
        
        # Draw main line
        painter.drawLine(p1, p2)
        
        # Draw steps as perpendicular lines
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = (dx**2 + dy**2)**0.5
        
        if length > 0:
            # Perpendicular vector
            perp_x = -dy / length * width_screen / 2
            perp_y = dx / length * width_screen / 2
            
            # Draw steps
            for i in range(stair.num_steps + 1):
                t = i / stair.num_steps
                step_x = p1.x() + dx * t
                step_y = p1.y() + dy * t
                
                painter.drawLine(
                    int(step_x - perp_x), int(step_y - perp_y),
                    int(step_x + perp_x), int(step_y + perp_y)
                )
        
        # Draw label
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(int(mid_x), int(mid_y), stair.stair_type.value.upper())
    
    def _draw_pending_object(self, painter: QPainter):
        """Draw object being placed (preview)."""
        if not self.pending_object or not self.hover_point:
            return
        
        pen = QPen(QColor("#0000FF"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        pos = self.world_to_screen(self.hover_point)
        
        if self.pending_object_type == "furniture":
            width_screen = self.pending_object['width'] * self.scale
            depth_screen = self.pending_object['depth'] * self.scale
            
            rect = QRectF(pos.x() - width_screen/2, pos.y() - depth_screen/2,
                         width_screen, depth_screen)
            painter.drawRect(rect)
        
        elif self.pending_object_type == "fixture":
            width_screen = self.pending_object['width'] * self.scale
            depth_screen = self.pending_object['depth'] * self.scale
            
            rect = QRectF(pos.x() - width_screen/2, pos.y() - depth_screen/2,
                         width_screen, depth_screen)
            painter.drawRect(rect)
        
        elif self.pending_object_type == "stair":
            # Draw as line for preview
            if self.temp_wall_start:
                p1 = self.world_to_screen(self.temp_wall_start)
                painter.drawLine(p1, pos)
    
    def set_pending_object(self, object_type: str, object_data: dict):
        """Set an object to be placed on next click."""
        self.pending_object = object_data
        self.pending_object_type = object_type
        
        # Set appropriate draw mode
        if object_type == "furniture":
            self.set_draw_mode(DrawMode.PLACE_FURNITURE)
        elif object_type == "fixture":
            self.set_draw_mode(DrawMode.PLACE_FIXTURE)
        elif object_type == "stair":
            self.set_draw_mode(DrawMode.PLACE_STAIR)
        
        self.update()
        logger.info(f"Set pending object: {object_type}")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        
        # Handle object selection and transformation
        if event.button() == Qt.MouseButton.LeftButton:
            world_point = self.screen_to_world(event.position())
            
            if self.draw_mode == DrawMode.SELECT:
                # Check if clicking on handle of selected object
                if self.selected_object:
                    mode = self.transform_handler.get_handle_at_point(world_point)
                    if mode != TransformMode.NONE:
                        # Store initial state for undo
                        self.transform_start_state = ObjectState.from_object(
                            self.selected_object.obj
                        )
                        self.transform_handler.start_transform(world_point, mode)
                        self.is_transforming = True
                        return
                
                # Try to select an object
                if self.select_object_at_point(world_point):
                    return

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            world_pos = self.screen_to_world(event.position())
            snap_pos = self.find_snap_point(world_pos)
            
            if self.draw_mode == DrawMode.DRAW_WALL:
                self._handle_wall_click(snap_pos)
            elif self.draw_mode == DrawMode.SELECT:
                self._handle_select_click(snap_pos)
            elif self.draw_mode in [DrawMode.ADD_DOOR, DrawMode.ADD_WINDOW]:
                self._handle_opening_click(snap_pos)
            elif self.draw_mode == DrawMode.MEASURE:
                self._handle_measure_click(snap_pos)
            elif self.draw_mode == DrawMode.CREATE_ROOM:
                self._handle_room_click(snap_pos)
            elif self.draw_mode == DrawMode.PLACE_FURNITURE:
                self._handle_place_furniture(snap_pos)
            elif self.draw_mode == DrawMode.PLACE_FIXTURE:
                self._handle_place_fixture(snap_pos)
            elif self.draw_mode == DrawMode.PLACE_STAIR:
                self._handle_place_stair(snap_pos)
    
    def _handle_wall_click(self, point: Point):
        """Handle click in wall drawing mode."""
        if not self.temp_wall_start:
            # Start new wall
            self.temp_wall_start = point
            self.status_message.emit(f"Click to place wall end point")
        else:
            # Finish wall
            if point.distance_to(self.temp_wall_start) > 1.0:  # Minimum wall length
                wall = Wall(self.temp_wall_start, point)
                self.floor_plan.add_wall(wall)
                self.plan_modified.emit()
                self.status_message.emit(f"Wall added: {format_dimension(wall.length())}")
            
            self.temp_wall_start = None
            self.update()
    
    def _handle_select_click(self, point: Point):
        """Handle click in selection mode."""
        # Check for wall selection
        tolerance = 10.0 / self.scale  # 10 pixels in world units
        
        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                self.selected_wall = wall.id
                self.selected_opening = None
                self.selected_room = None
                self.selection_changed.emit(wall)
                self.update()
                return
        
        # Check for opening selection
        for opening in self.floor_plan.openings:
            wall = self.floor_plan.get_wall(opening.wall_id)
            if wall:
                dx = wall.end.x - wall.start.x
                dy = wall.end.y - wall.start.y
                opening_pos = Point(
                    wall.start.x + dx * opening.position,
                    wall.start.y + dy * opening.position
                )
                if point.distance_to(opening_pos) < opening.width / 2:
                    self.selected_opening = opening.id
                    self.selected_wall = None
                    self.selected_room = None
                    self.selection_changed.emit(opening)
                    self.update()
                    return
        
        # Check for room selection (click inside room polygon)
        for room in self.floor_plan.rooms:
            if self._point_in_room(point, room):
                self.selected_room = room.id
                self.selected_wall = None
                self.selected_opening = None
                self.selection_changed.emit(room)
                self.update()
                return
        
        # Nothing selected
        self.selected_wall = None
        self.selected_opening = None
        self.selected_room = None
        self.selection_changed.emit(None)
        self.update()
    
    def _point_in_room(self, point: Point, room: Room) -> bool:
        """Check if a point is inside a room using ray casting algorithm."""
        if not room.wall_ids:
            return False
        
        # Get room vertices
        vertices = []
        for wall_id in room.wall_ids:
            wall = self.floor_plan.get_wall(wall_id)
            if wall:
                vertices.append(wall.start)
                vertices.append(wall.end)
        
        if len(vertices) < 3:
            return False
        
        # Remove duplicates
        unique_vertices = []
        seen = set()
        for v in vertices:
            key = (round(v.x, 1), round(v.y, 1))
            if key not in seen:
                unique_vertices.append(v)
                seen.add(key)
        
        # Ray casting algorithm
        inside = False
        n = len(unique_vertices)
        p1 = unique_vertices[0]
        
        for i in range(n + 1):
            p2 = unique_vertices[i % n]
            if point.y > min(p1.y, p2.y):
                if point.y <= max(p1.y, p2.y):
                    if point.x <= max(p1.x, p2.x):
                        if p1.y != p2.y:
                            xinters = (point.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        if p1.x == p2.x or point.x <= xinters:
                            inside = not inside
            p1 = p2
        
        return inside
    
    def _handle_opening_click(self, point: Point):
        """Handle click in door/window placement mode."""
        # Find which wall was clicked
        tolerance = 10.0 / self.scale
        
        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                # Calculate position along wall (0.0 to 1.0)
                wall_length = wall.length()
                dx = wall.end.x - wall.start.x
                dy = wall.end.y - wall.start.y
                
                # Project point onto wall
                t = ((point.x - wall.start.x) * dx + (point.y - wall.start.y) * dy) / (wall_length ** 2)
                t = max(0.1, min(0.9, t))  # Keep away from ends
                
                # Create opening
                opening_type = (OpeningType.DOOR if self.draw_mode == DrawMode.ADD_DOOR 
                              else OpeningType.WINDOW)
                width = (AppConfig.DEFAULT_DOOR_WIDTH if opening_type == OpeningType.DOOR 
                        else AppConfig.DEFAULT_WINDOW_WIDTH)
                
                opening = Opening(
                    wall_id=wall.id,
                    position=t,
                    width=width,
                    opening_type=opening_type
                )
                
                self.floor_plan.add_opening(opening)
                self.plan_modified.emit()
                self.status_message.emit(f"{opening_type.value.title()} added to wall")
                self.update()
                return
    
    def _handle_measure_click(self, point: Point):
        """Handle click in measurement mode."""
        if not self.measurement_tool.temp_start:
            # Start new measurement
            self.measurement_tool.start_measurement(point)
            self.status_message.emit("Click to finish measurement")
        else:
            # Finish measurement
            measurement = self.measurement_tool.finish_measurement(point)
            if measurement:
                self.status_message.emit(
                    f"Measured: {format_dimension(measurement.distance())} "
                    f"at {measurement.angle():.1f}°"
                )
            self.update()
    
    def _handle_room_click(self, point: Point):
        """Handle click in room creation mode."""
        # Find which wall was clicked
        tolerance = 10.0 / self.scale
        
        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                # Toggle wall selection
                if wall.id in self.room_walls_selection:
                    self.room_walls_selection.remove(wall.id)
                    self.status_message.emit(f"Removed wall from selection ({len(self.room_walls_selection)} walls)")
                else:
                    self.room_walls_selection.append(wall.id)
                    self.status_message.emit(f"Added wall to selection ({len(self.room_walls_selection)} walls)")
                
                self.update()
                return
    
    def create_room_from_selection(self, name: str, color: Optional[str] = None):
        """Create a room from the currently selected walls."""
        if len(self.room_walls_selection) < 3:
            self.status_message.emit("Need at least 3 walls to create a room")
            return None
        
        room = Room(
            name=name,
            wall_ids=self.room_walls_selection.copy(),
            color=color
        )
        
        self.floor_plan.add_room(room)
        self.room_walls_selection.clear()
        self.plan_modified.emit()
        self.update()
        
        self.status_message.emit(f"Created room: {name}")
        return room
    
    def _handle_place_furniture(self, point: Point):
        """Handle placing furniture."""
        if not self.pending_object:
            return
        
        furniture = Furniture(
            position=point,
            width=self.pending_object['width'],
            depth=self.pending_object['depth'],
            furniture_type=self.pending_object['type']
        )
        
        self.floor_plan.add_furniture(furniture)
        self.plan_modified.emit()
        self.update()
        
        self.status_message.emit(f"Placed {furniture.name}")
        
        # Keep in placement mode for multiple placements
        # User can press Escape to exit
    
    def _handle_place_fixture(self, point: Point):
        """Handle placing fixture."""
        if not self.pending_object:
            return
        
        fixture = Fixture(
            position=point,
            width=self.pending_object['width'],
            depth=self.pending_object['depth'],
            fixture_type=self.pending_object['type']
        )
        
        self.floor_plan.add_fixture(fixture)
        self.plan_modified.emit()
        self.update()
        
        self.status_message.emit(f"Placed {fixture.name}")
    
    def _handle_place_stair(self, point: Point):
        """Handle placing stair."""
        if not self.pending_object:
            return
        
        if not self.temp_wall_start:
            # First click - set start point
            self.temp_wall_start = point
            self.status_message.emit("Click to set stair end point")
        else:
            # Second click - create stair
            stair = Stair(
                start=self.temp_wall_start,
                end=point,
                width=self.pending_object['width'],
                stair_type=self.pending_object['type']
            )
            
            self.floor_plan.add_stair(stair)
            self.plan_modified.emit()
            self.temp_wall_start = None
            self.update()
            
            self.status_message.emit(f"Placed {stair.stair_type.value} stair")
    
    def _point_near_line(self, point: Point, line_start: Point, 
                        line_end: Point, tolerance: float) -> bool:
        """Check if a point is near a line segment."""
        # Calculate perpendicular distance from point to line
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        line_length = (dx**2 + dy**2)**0.5
        
        if line_length < 0.1:
            return point.distance_to(line_start) < tolerance
        
        # Calculate projection
        t = ((point.x - line_start.x) * dx + (point.y - line_start.y) * dy) / (line_length**2)
        t = max(0, min(1, t))
        
        # Find nearest point on line
        nearest = Point(
            line_start.x + t * dx,
            line_start.y + t * dy
        )
        
        return point.distance_to(nearest) < tolerance
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        
        world_point = self.screen_to_world(event.position())
        
        # Handle object transformation
        if self.is_transforming:
            self.transform_handler.update_transform(world_point)
            self.update()
            return
        
        # Update cursor based on what's under mouse
        if self.draw_mode == DrawMode.SELECT and self.selected_object:
            mode = self.transform_handler.get_handle_at_point(world_point)
            self._update_cursor_for_mode(mode)

        if self.is_panning and self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.position()
            self.update()
            return
        
        # Update hover point for drawing
        world_pos = self.screen_to_world(event.position())
        self.hover_point = self.find_snap_point(world_pos)
        
        # Update status with current position
        self.status_message.emit(
            f"Position: {format_dimension(self.hover_point.x)} x "
            f"{format_dimension(self.hover_point.y)}"
        )
        
        self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        
        # End object transformation
        if event.button() == Qt.MouseButton.LeftButton and self.is_transforming:
            self.transform_handler.end_transform()
            
            # Create undo command
            if hasattr(self, 'transform_start_state'):
                old_state = self.transform_start_state
                new_state = ObjectState.from_object(self.selected_object.obj)
                
                # Only add if something changed
                if (old_state.position.x != new_state.position.x or
                    old_state.position.y != new_state.position.y or
                    old_state.width != new_state.width or
                    old_state.depth != new_state.depth or
                    old_state.rotation != new_state.rotation):
                    
                    command = TransformObjectCommand(
                        self.selected_object.obj,
                        old_state,
                        new_state,
                        "Transform Object"
                    )
                    if hasattr(self, 'undo_stack') and self.undo_stack:
                        self.undo_stack.push(command)
                
                delattr(self, 'transform_start_state')
            
            self.is_transforming = False
            self.update()
            return

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        self.zoom(delta, event.position())
    
    def keyPressEvent(self, event):
        # Handle Delete key
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_object:
                self.delete_selected_object()
                event.accept()
                return
        
        # Handle Escape key  
        if event.key() == Qt.Key.Key_Escape:
            self.set_selected_object(None)
            event.accept()
            return
        

        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_wall:
                self.floor_plan.remove_wall(self.selected_wall)
                self.selected_wall = None
                self.plan_modified.emit()
                self.update()
            elif self.selected_opening:
                self.floor_plan.remove_opening(self.selected_opening)
                self.selected_opening = None
                self.plan_modified.emit()
                self.update()
            elif self.selected_room:
                self.floor_plan.remove_room(self.selected_room)
                self.selected_room = None
                self.plan_modified.emit()
                self.update()
            elif self.selected_furniture:
                self.floor_plan.remove_furniture(self.selected_furniture)
                self.selected_furniture = None
                self.plan_modified.emit()
                self.update()
            elif self.selected_fixture:
                self.floor_plan.remove_fixture(self.selected_fixture)
                self.selected_fixture = None
                self.plan_modified.emit()
                self.update()
            elif self.selected_stair:
                self.floor_plan.remove_stair(self.selected_stair)
                self.selected_stair = None
                self.plan_modified.emit()
                self.update()
        
        elif event.key() == Qt.Key.Key_Escape:
            self.temp_wall_start = None
            self.selected_wall = None
            self.selected_opening = None
            self.selected_room = None
            self.selected_furniture = None
            self.selected_fixture = None
            self.selected_stair = None
            self.room_walls_selection.clear()
            self.measurement_tool.cancel_measurement()
            self.pending_object = None
            self.pending_object_type = None
            self.update()
        
        elif event.key() == Qt.Key.Key_G:
            self.show_grid = not self.show_grid
            self.update()
        
        elif event.key() == Qt.Key.Key_C and self.draw_mode == DrawMode.MEASURE:
            # Clear measurements with 'C' key in measure mode
            self.measurement_tool.clear_measurements()
            self.update()

    def refresh_selectable_objects(self):
        """Refresh the list of selectable objects from the floor plan."""
        if not self.floor_plan:
            self.selectable_objects = []
            return
        
        self.selectable_objects = []
        
        # Add all furniture
        for furniture in self.floor_plan.furniture:
            self.selectable_objects.append(SelectableObject(furniture))
        
        # Add all fixtures
        for fixture in self.floor_plan.fixtures:
            self.selectable_objects.append(SelectableObject(fixture))
        
        # Add all stairs
        for stair in self.floor_plan.stairs:
            self.selectable_objects.append(SelectableObject(stair))
        
        logger.debug(f"Refreshed {len(self.selectable_objects)} selectable objects")
    
    def select_object_at_point(self, point: Point) -> bool:
        """Select an object at the given point."""
        # Check if clicking on currently selected object's handle
        if self.selected_object:
            mode = self.transform_handler.get_handle_at_point(point)
            if mode != TransformMode.NONE:
                return True
        
        # Find object at point
        for obj in reversed(self.selectable_objects):
            if obj.contains_point(point):
                self.set_selected_object(obj)
                return True
        
        # No object found - deselect
        self.set_selected_object(None)
        return False
    
    def set_selected_object(self, obj):
        """Set the currently selected object."""
        self.selected_object = obj
        self.transform_handler.set_selected_object(obj)
        
        # Emit signal for properties panel
        actual_obj = obj.obj if obj else None
        self.object_selected.emit(actual_obj)
        
        self.update()
    
    def get_selected_object(self):
        """Get the currently selected object."""
        if self.selected_object:
            return self.selected_object.obj
        return None
    
    def delete_selected_object(self):
        """Delete the currently selected object."""
        if not self.selected_object or not self.floor_plan:
            return
        
        obj = self.selected_object.obj
        
        # Create undo command
        command = RemoveObjectCommand(self.floor_plan, obj)
        if hasattr(self, 'undo_stack') and self.undo_stack:
            self.undo_stack.push(command)
        else:
            # Execute directly if no undo stack
            command.execute()
        
        # Deselect and refresh
        self.set_selected_object(None)
        self.refresh_selectable_objects()
        self.update()
    
    def _update_cursor_for_mode(self, mode: TransformMode):
        """Update cursor based on transformation mode."""
        cursor_map = {
            TransformMode.MOVE: Qt.CursorShape.SizeAllCursor,
            TransformMode.RESIZE_TL: Qt.CursorShape.SizeFDiagCursor,
            TransformMode.RESIZE_TR: Qt.CursorShape.SizeBDiagCursor,
            TransformMode.RESIZE_BL: Qt.CursorShape.SizeBDiagCursor,
            TransformMode.RESIZE_BR: Qt.CursorShape.SizeFDiagCursor,
            TransformMode.ROTATE: Qt.CursorShape.CrossCursor,
            TransformMode.NONE: Qt.CursorShape.ArrowCursor,
        }
        
        cursor = cursor_map.get(mode, Qt.CursorShape.ArrowCursor)
        self.setCursor(cursor)

