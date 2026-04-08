"""Event handling routines for the floor plan canvas.

Contains all _handle_* click methods, object selection, and keyboard
handling extracted from FloorPlanCanvas. Mixed in via CanvasEventsMixin.
"""

import logging
from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core import (
    Point, Wall, Opening, OpeningType, Room,
    Furniture, FurnitureType, Fixture, FixtureType, Stair, StairType,
)
from utils import AppConfig, format_dimension
from .object_selection import SelectableObject, TransformMode
from utils.undo_commands import ObjectState, TransformObjectCommand, RemoveObjectCommand

logger = logging.getLogger(__name__)


class CanvasEventsMixin:
    """Mixin providing event-handling methods for FloorPlanCanvas.

    Expects the host class to provide the same attributes as CanvasDrawingMixin
    plus the Qt signals (plan_modified, selection_changed, status_message,
    object_selected) and transform_handler / undo_stack.
    """

    # ── wall drawing ────────────────────────────────────────────────
    def _handle_wall_click(self, point: Point):
        """Handle click in wall drawing mode."""
        if not self.temp_wall_start:
            self.temp_wall_start = point
            self.status_message.emit("Click to place wall end point")
        else:
            if point.distance_to(self.temp_wall_start) > 1.0:
                wall = Wall(self.temp_wall_start, point)
                self.floor_plan.add_wall(wall)
                self.plan_modified.emit()
                self.status_message.emit(
                    f"Wall added: {format_dimension(wall.length())}"
                )
            self.temp_wall_start = None
            self.update()

    # ── selection ───────────────────────────────────────────────────
    def _handle_select_click(self, point: Point):
        """Handle click in selection mode."""
        tolerance = 10.0 / self.scale

        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                self.selected_wall = wall.id
                self.selected_opening = None
                self.selected_room = None
                self.selection_changed.emit(wall)
                self.update()
                return

        for opening in self.floor_plan.openings:
            wall = self.floor_plan.get_wall(opening.wall_id)
            if wall:
                dx = wall.end.x - wall.start.x
                dy = wall.end.y - wall.start.y
                opening_pos = Point(
                    wall.start.x + dx * opening.position,
                    wall.start.y + dy * opening.position,
                )
                if point.distance_to(opening_pos) < opening.width / 2:
                    self.selected_opening = opening.id
                    self.selected_wall = None
                    self.selected_room = None
                    self.selection_changed.emit(opening)
                    self.update()
                    return

        for room in self.floor_plan.rooms:
            if self._point_in_room(point, room):
                self.selected_room = room.id
                self.selected_wall = None
                self.selected_opening = None
                self.selection_changed.emit(room)
                self.update()
                return

        self.selected_wall = None
        self.selected_opening = None
        self.selected_room = None
        self.selection_changed.emit(None)
        self.update()

    def _point_in_room(self, point: Point, room: Room) -> bool:
        """Check if a point is inside a room (ray casting)."""
        if not room.wall_ids:
            return False

        vertices = []
        for wall_id in room.wall_ids:
            wall = self.floor_plan.get_wall(wall_id)
            if wall:
                vertices.append(wall.start)
                vertices.append(wall.end)

        if len(vertices) < 3:
            return False

        unique_vertices: list = []
        seen: set = set()
        for v in vertices:
            key = (round(v.x, 1), round(v.y, 1))
            if key not in seen:
                unique_vertices.append(v)
                seen.add(key)

        inside = False
        n = len(unique_vertices)
        p1 = unique_vertices[0]
        for i in range(n + 1):
            p2 = unique_vertices[i % n]
            if point.y > min(p1.y, p2.y):
                if point.y <= max(p1.y, p2.y):
                    if point.x <= max(p1.x, p2.x):
                        if p1.y != p2.y:
                            xinters = (
                                (point.y - p1.y) * (p2.x - p1.x)
                                / (p2.y - p1.y)
                                + p1.x
                            )
                        if p1.x == p2.x or point.x <= xinters:
                            inside = not inside
            p1 = p2
        return inside

    # ── opening placement ───────────────────────────────────────────
    def _handle_opening_click(self, point: Point):
        """Handle click in door/window placement mode."""
        tolerance = 10.0 / self.scale

        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                wall_length = wall.length()
                dx = wall.end.x - wall.start.x
                dy = wall.end.y - wall.start.y
                t = (
                    (point.x - wall.start.x) * dx
                    + (point.y - wall.start.y) * dy
                ) / (wall_length ** 2)
                t = max(0.1, min(0.9, t))

                opening_type = (
                    OpeningType.DOOR
                    if self.draw_mode == "add_door"
                    else OpeningType.WINDOW
                )
                width = (
                    AppConfig.DEFAULT_DOOR_WIDTH
                    if opening_type == OpeningType.DOOR
                    else AppConfig.DEFAULT_WINDOW_WIDTH
                )

                opening = Opening(
                    wall_id=wall.id,
                    position=t,
                    width=width,
                    opening_type=opening_type,
                )
                self.floor_plan.add_opening(opening)
                self.plan_modified.emit()
                self.status_message.emit(
                    f"{opening_type.value.title()} added to wall"
                )
                self.update()
                return

    # ── measurement ─────────────────────────────────────────────────
    def _handle_measure_click(self, point: Point):
        """Handle click in measurement mode."""
        if not self.measurement_tool.temp_start:
            self.measurement_tool.start_measurement(point)
            self.status_message.emit("Click to finish measurement")
        else:
            measurement = self.measurement_tool.finish_measurement(point)
            if measurement:
                self.status_message.emit(
                    f"Measured: {format_dimension(measurement.distance())} "
                    f"at {measurement.angle():.1f}\u00b0"
                )
            self.update()

    # ── room creation ───────────────────────────────────────────────
    def _handle_room_click(self, point: Point):
        """Handle click in room creation mode."""
        tolerance = 10.0 / self.scale
        for wall in self.floor_plan.walls:
            if self._point_near_line(point, wall.start, wall.end, tolerance):
                if wall.id in self.room_walls_selection:
                    self.room_walls_selection.remove(wall.id)
                    self.status_message.emit(
                        f"Removed wall from selection "
                        f"({len(self.room_walls_selection)} walls)"
                    )
                else:
                    self.room_walls_selection.append(wall.id)
                    self.status_message.emit(
                        f"Added wall to selection "
                        f"({len(self.room_walls_selection)} walls)"
                    )
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
            color=color,
        )
        self.floor_plan.add_room(room)
        self.room_walls_selection.clear()
        self.plan_modified.emit()
        self.update()
        self.status_message.emit(f"Created room: {name}")
        return room

    # ── furniture / fixture / stair placement ───────────────────────
    def _handle_place_furniture(self, point: Point):
        """Handle placing furniture."""
        if not self.pending_object:
            return
        furniture = Furniture(
            position=point,
            width=self.pending_object["width"],
            depth=self.pending_object["depth"],
            furniture_type=self.pending_object["type"],
        )
        self.floor_plan.add_furniture(furniture)
        self.plan_modified.emit()
        self.update()
        self.status_message.emit(f"Placed {furniture.name}")

    def _handle_place_fixture(self, point: Point):
        """Handle placing fixture."""
        if not self.pending_object:
            return
        fixture = Fixture(
            position=point,
            width=self.pending_object["width"],
            depth=self.pending_object["depth"],
            fixture_type=self.pending_object["type"],
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
            self.temp_wall_start = point
            self.status_message.emit("Click to set stair end point")
        else:
            stair = Stair(
                start=self.temp_wall_start,
                end=point,
                width=self.pending_object["width"],
                stair_type=self.pending_object["type"],
            )
            self.floor_plan.add_stair(stair)
            self.plan_modified.emit()
            self.temp_wall_start = None
            self.update()
            self.status_message.emit(f"Placed {stair.stair_type.value} stair")

    # ── geometry helpers ────────────────────────────────────────────
    def _point_near_line(self, point: Point, line_start: Point,
                         line_end: Point, tolerance: float) -> bool:
        """Check if a point is near a line segment."""
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        line_length = (dx ** 2 + dy ** 2) ** 0.5

        if line_length < 0.1:
            return point.distance_to(line_start) < tolerance

        t = (
            (point.x - line_start.x) * dx + (point.y - line_start.y) * dy
        ) / (line_length ** 2)
        t = max(0, min(1, t))

        nearest = Point(line_start.x + t * dx, line_start.y + t * dy)
        return point.distance_to(nearest) < tolerance

    # ── object selection / transform ────────────────────────────────
    def refresh_selectable_objects(self):
        """Refresh the list of selectable objects from the floor plan."""
        if not self.floor_plan:
            self.selectable_objects = []
            return

        self.selectable_objects = []
        for furniture in self.floor_plan.furniture:
            self.selectable_objects.append(SelectableObject(furniture))
        for fixture in self.floor_plan.fixtures:
            self.selectable_objects.append(SelectableObject(fixture))
        for stair in self.floor_plan.stairs:
            self.selectable_objects.append(SelectableObject(stair))

        logger.debug(f"Refreshed {len(self.selectable_objects)} selectable objects")

    def select_object_at_point(self, point: Point) -> bool:
        """Select an object at the given point."""
        if self.selected_object:
            mode = self.transform_handler.get_handle_at_point(point)
            if mode != TransformMode.NONE:
                return True

        for obj in reversed(self.selectable_objects):
            if obj.contains_point(point):
                self.set_selected_object(obj)
                return True

        self.set_selected_object(None)
        return False

    def set_selected_object(self, obj):
        """Set the currently selected object."""
        self.selected_object = obj
        self.transform_handler.set_selected_object(obj)
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
        command = RemoveObjectCommand(self.floor_plan, obj)
        if hasattr(self, "undo_stack") and self.undo_stack:
            self.undo_stack.push(command)
        else:
            command.execute()

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
        self.setCursor(cursor_map.get(mode, Qt.CursorShape.ArrowCursor))
