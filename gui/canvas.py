"""Interactive canvas widget for drawing and editing floor plans.

The canvas handles:
- Wall drawing and editing
- Opening (door/window) placement
- Selection and manipulation
- Grid display and snapping
- Zoom and pan

Drawing methods are in canvas_drawing.py (CanvasDrawingMixin).
Event handling methods are in canvas_events.py (CanvasEventsMixin).
"""

import logging
from typing import Optional, List
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QWheelEvent,
    QMouseEvent, QPaintEvent,
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
from .canvas_drawing import CanvasDrawingMixin
from .canvas_events import CanvasEventsMixin


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


class FloorPlanCanvas(CanvasDrawingMixin, CanvasEventsMixin, QWidget):
    """Interactive canvas for floor plan drawing and editing.

    Signals:
        plan_modified: Emitted when the floor plan is modified
        selection_changed: Emitted when selection changes
        status_message: Emitted to update status bar
    """

    plan_modified = pyqtSignal()
    selection_changed = pyqtSignal(object)
    object_selected = pyqtSignal(object)
    status_message = pyqtSignal(str)

    def __init__(self, floor_plan: Optional[FloorPlan] = None, parent=None):
        super().__init__(parent)

        # Floor plan data
        self.floor_plan = floor_plan or FloorPlan()

        # Drawing state
        self.draw_mode = DrawMode.SELECT
        self.temp_wall_start: Optional[Point] = None
        self.selected_wall: Optional[str] = None
        self.selected_opening: Optional[str] = None
        self.selected_room: Optional[str] = None
        self.selected_furniture: Optional[str] = None
        self.selected_fixture: Optional[str] = None
        self.selected_stair: Optional[str] = None
        self.measurement_tool = MeasurementTool()
        self.room_walls_selection: List[str] = []
        self.pending_object = None
        self.pending_object_type = None

        # View state
        self.scale = AppConfig.DEFAULT_SCALE
        self.offset_x = 0.0
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

    # ── Floor plan management ───────────────────────────────────────

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

    # ── Coordinate transforms ───────────────────────────────────────

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
        """Find the best snap point (wall endpoints > grid)."""
        tolerance = AppConfig.SNAP_TOLERANCE
        for wall in self.floor_plan.walls:
            for endpoint in [wall.start, wall.end]:
                if point.distance_to(endpoint) < tolerance:
                    return endpoint
        return self.snap_to_grid(point)

    # ── View controls ───────────────────────────────────────────────

    def fit_to_view(self):
        """Adjust zoom and pan to fit the entire floor plan in view."""
        bounds = self.floor_plan.get_bounds()
        if not bounds:
            self.scale = AppConfig.DEFAULT_SCALE
            self.offset_x = 0
            self.offset_y = 0
            return

        min_pt, max_pt = bounds
        width_inches = (max_pt.x - min_pt.x) * 1.2
        height_inches = (max_pt.y - min_pt.y) * 1.2

        if width_inches > 0 and height_inches > 0:
            scale_x = (self.width() * 0.9) / width_inches
            scale_y = (self.height() * 0.9) / height_inches
            self.scale = min(scale_x, scale_y)
            self.scale = max(AppConfig.MIN_SCALE, min(self.scale, AppConfig.MAX_SCALE))

        center_x = (min_pt.x + max_pt.x) / 2
        center_y = (min_pt.y + max_pt.y) / 2
        self.offset_x = -center_x * self.scale
        self.offset_y = -center_y * self.scale

        self.update()
        logger.info(f"Fit to view: scale={self.scale:.2f}")

    def zoom(self, delta: int, center: Optional[QPointF] = None):
        """Zoom in or out."""
        if center is None:
            center = QPointF(self.width() / 2, self.height() / 2)

        world_pt = self.screen_to_world(center)
        factor = 1.1 if delta > 0 else 0.9
        new_scale = self.scale * factor
        new_scale = max(AppConfig.MIN_SCALE, min(new_scale, AppConfig.MAX_SCALE))

        if new_scale != self.scale:
            self.scale = new_scale
            new_screen = self.world_to_screen(world_pt)
            self.offset_x += center.x() - new_screen.x()
            self.offset_y += center.y() - new_screen.y()
            self.update()
            self.status_message.emit(
                f"Zoom: {int(self.scale / AppConfig.DEFAULT_SCALE * 100)}%"
            )

    # ── Object placement ────────────────────────────────────────────

    def set_pending_object(self, object_type: str, object_data: dict):
        """Set an object to be placed on next click."""
        self.pending_object = object_data
        self.pending_object_type = object_type
        if object_type == "furniture":
            self.set_draw_mode(DrawMode.PLACE_FURNITURE)
        elif object_type == "fixture":
            self.set_draw_mode(DrawMode.PLACE_FIXTURE)
        elif object_type == "stair":
            self.set_draw_mode(DrawMode.PLACE_STAIR)
        self.update()
        logger.info(f"Set pending object: {object_type}")

    # ── Qt event overrides ──────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        """Paint the canvas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(AppConfig.CANVAS_BG_COLOR))

        if self.show_grid:
            self._draw_grid(painter)
        self._draw_rooms(painter)
        self._draw_walls(painter)
        self._draw_openings(painter)
        self._draw_furniture_items(painter)
        self._draw_fixtures(painter)
        self._draw_stairs(painter)
        self._draw_measurements(painter)

        if self.pending_object and self.hover_point:
            self._draw_pending_object(painter)
        if self.temp_wall_start and self.hover_point:
            self._draw_temp_wall(painter)
        if self.hover_point and self.draw_mode != DrawMode.SELECT:
            self._draw_hover_point(painter)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            world_point = self.screen_to_world(event.position())

            if self.draw_mode == DrawMode.SELECT:
                if self.selected_object:
                    mode = self.transform_handler.get_handle_at_point(world_point)
                    if mode != TransformMode.NONE:
                        self.transform_start_state = ObjectState.from_object(
                            self.selected_object.obj
                        )
                        self.transform_handler.start_transform(world_point, mode)
                        self.is_transforming = True
                        return
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

            mode_handlers = {
                DrawMode.DRAW_WALL: self._handle_wall_click,
                DrawMode.SELECT: self._handle_select_click,
                DrawMode.MEASURE: self._handle_measure_click,
                DrawMode.CREATE_ROOM: self._handle_room_click,
                DrawMode.PLACE_FURNITURE: self._handle_place_furniture,
                DrawMode.PLACE_FIXTURE: self._handle_place_fixture,
                DrawMode.PLACE_STAIR: self._handle_place_stair,
            }

            if self.draw_mode in [DrawMode.ADD_DOOR, DrawMode.ADD_WINDOW]:
                self._handle_opening_click(snap_pos)
            elif self.draw_mode in mode_handlers:
                mode_handlers[self.draw_mode](snap_pos)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        world_point = self.screen_to_world(event.position())

        if self.is_transforming:
            self.transform_handler.update_transform(world_point)
            self.update()
            return

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

        world_pos = self.screen_to_world(event.position())
        self.hover_point = self.find_snap_point(world_pos)

        self.status_message.emit(
            f"Position: {format_dimension(self.hover_point.x)} x "
            f"{format_dimension(self.hover_point.y)}"
        )
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_transforming:
            self.transform_handler.end_transform()

            if hasattr(self, "transform_start_state"):
                old_state = self.transform_start_state
                new_state = ObjectState.from_object(self.selected_object.obj)

                if (old_state.position.x != new_state.position.x
                        or old_state.position.y != new_state.position.y
                        or old_state.width != new_state.width
                        or old_state.depth != new_state.depth
                        or old_state.rotation != new_state.rotation):
                    command = TransformObjectCommand(
                        self.selected_object.obj, old_state, new_state,
                        "Transform Object",
                    )
                    if hasattr(self, "undo_stack") and self.undo_stack:
                        self.undo_stack.push(command)

                delattr(self, "transform_start_state")

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
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Delete:
            if self.selected_object:
                self.delete_selected_object()
                event.accept()
                return
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
            if self.selected_object:
                self.set_selected_object(None)
                event.accept()
                return
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
            self.measurement_tool.clear_measurements()
            self.update()
