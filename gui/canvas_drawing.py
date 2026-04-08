"""Drawing routines for the floor plan canvas.

Contains all _draw_* methods extracted from FloorPlanCanvas to keep
the main canvas module under 500 lines. These are mixed-in via
CanvasDrawingMixin, which FloorPlanCanvas inherits from.
"""

import logging
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPolygonF

from core import (
    Point, Wall, Opening, OpeningType, Room,
    Furniture, Fixture, FixtureType, Stair,
)
from utils import AppConfig, format_dimension

logger = logging.getLogger(__name__)


class CanvasDrawingMixin:
    """Mixin providing all drawing methods for FloorPlanCanvas.

    Expects the host class to provide:
      - self.floor_plan (FloorPlan)
      - self.scale (float)
      - self.show_grid / self.show_dimensions (bool)
      - self.selected_wall / selected_opening / selected_room / etc.
      - self.measurement_tool, self.hover_point, self.temp_wall_start
      - self.pending_object, self.pending_object_type
      - world_to_screen(Point) -> QPointF
      - screen_to_world(QPointF) -> Point
    """

    # ── grid ────────────────────────────────────────────────────────
    def _draw_grid(self, painter: QPainter):
        """Draw the background grid."""
        pen = QPen(QColor(AppConfig.GRID_COLOR))
        pen.setWidth(1)
        painter.setPen(pen)

        grid_size = AppConfig.GRID_SIZE

        top_left_world = self.screen_to_world(QPointF(0, 0))
        bottom_right_world = self.screen_to_world(
            QPointF(self.width(), self.height())
        )

        start_x = int(top_left_world.x / grid_size) * grid_size
        end_x = int(bottom_right_world.x / grid_size + 1) * grid_size
        start_y = int(top_left_world.y / grid_size) * grid_size
        end_y = int(bottom_right_world.y / grid_size + 1) * grid_size

        x = start_x
        while x <= end_x:
            p1 = self.world_to_screen(Point(x, start_y))
            p2 = self.world_to_screen(Point(x, end_y))
            painter.drawLine(p1, p2)
            x += grid_size

        y = start_y
        while y <= end_y:
            p1 = self.world_to_screen(Point(start_x, y))
            p2 = self.world_to_screen(Point(end_x, y))
            painter.drawLine(p1, p2)
            y += grid_size

    # ── walls ───────────────────────────────────────────────────────
    def _draw_walls(self, painter: QPainter):
        """Draw all walls."""
        for wall in self.floor_plan.walls:
            is_selected = (wall.id == self.selected_wall)
            self._draw_wall(painter, wall, is_selected)

    def _draw_wall(self, painter: QPainter, wall: Wall, selected: bool = False):
        """Draw a single wall."""
        color = AppConfig.SELECTED_COLOR if selected else AppConfig.WALL_COLOR
        pen = QPen(QColor(color))
        pen.setWidth(max(2, int(wall.thickness * self.scale / 6)))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        p1 = self.world_to_screen(wall.start)
        p2 = self.world_to_screen(wall.end)
        painter.drawLine(p1, p2)

        if selected and self.show_dimensions:
            self._draw_wall_dimension(painter, wall)

    def _draw_wall_dimension(self, painter: QPainter, wall: Wall):
        """Draw dimension text for a wall."""
        midpoint = wall.midpoint()
        screen_mid = self.world_to_screen(midpoint)

        dimension_text = format_dimension(wall.length())
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))

        text_rect = painter.fontMetrics().boundingRect(dimension_text)
        text_rect.moveCenter(screen_mid.toPoint())

        painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), QColor("#FFFFFF"))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, dimension_text)

    # ── openings ────────────────────────────────────────────────────
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
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y

        opening_center = Point(
            wall.start.x + dx * opening.position,
            wall.start.y + dy * opening.position,
        )

        if opening.opening_type == OpeningType.DOOR:
            color = AppConfig.DOOR_COLOR
        else:
            color = AppConfig.WINDOW_COLOR
        if selected:
            color = AppConfig.SELECTED_COLOR

        pen = QPen(QColor(color))
        pen.setWidth(3)
        painter.setPen(pen)

        center_screen = self.world_to_screen(opening_center)
        width_pixels = opening.width * self.scale / 2
        painter.drawEllipse(center_screen, width_pixels, width_pixels)

        font = QFont("Arial", 8)
        painter.setFont(font)
        label = "D" if opening.opening_type == OpeningType.DOOR else "W"
        painter.drawText(center_screen.toPoint(), label)

    # ── temp / hover ────────────────────────────────────────────────
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

    # ── rooms ───────────────────────────────────────────────────────
    def _draw_rooms(self, painter: QPainter):
        """Draw all rooms as filled polygons."""
        for room in self.floor_plan.rooms:
            is_selected = (room.id == self.selected_room)
            self._draw_room(painter, room, is_selected)

    def _draw_room(self, painter: QPainter, room: Room, selected: bool = False):
        """Draw a single room as a filled polygon."""
        if not room.wall_ids:
            return

        polygon = QPolygonF()
        points_added = set()
        for wall_id in room.wall_ids:
            wall = self.floor_plan.get_wall(wall_id)
            if wall:
                start_key = (round(wall.start.x, 1), round(wall.start.y, 1))
                if start_key not in points_added:
                    polygon.append(self.world_to_screen(wall.start))
                    points_added.add(start_key)
                end_key = (round(wall.end.x, 1), round(wall.end.y, 1))
                if end_key not in points_added:
                    polygon.append(self.world_to_screen(wall.end))
                    points_added.add(end_key)

        if polygon.size() < 3:
            return

        color = QColor(room.color) if room.color else QColor("#F0F0F0")
        if selected:
            color = color.lighter(120)

        color.setAlpha(100)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)

        if polygon.size() > 0:
            cx = sum(polygon[i].x() for i in range(polygon.size())) / polygon.size()
            cy = sum(polygon[i].y() for i in range(polygon.size())) / polygon.size()

            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("#000000"))
            painter.drawText(
                int(cx) - 50, int(cy) - 10, 100, 20,
                Qt.AlignmentFlag.AlignCenter, room.name,
            )

    # ── measurements ────────────────────────────────────────────────
    def _draw_measurements(self, painter: QPainter):
        """Draw all measurements."""
        pen = QPen(QColor("#FF00FF"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        for measurement in self.measurement_tool.measurements:
            p1 = self.world_to_screen(measurement.start)
            p2 = self.world_to_screen(measurement.end)
            painter.drawLine(p1, p2)
            painter.drawEllipse(p1, 5, 5)
            painter.drawEllipse(p2, 5, 5)

            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2

            distance_text = format_dimension(measurement.distance())
            angle_text = f"{measurement.angle():.1f}\u00b0"

            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.setPen(QColor("#FF00FF"))
            painter.drawText(int(mid_x), int(mid_y) - 10, distance_text)
            painter.drawText(int(mid_x), int(mid_y) + 10, angle_text)

        temp = self.measurement_tool.get_temp_measurement(
            self.hover_point if self.hover_point else Point(0, 0)
        )
        if temp and self.draw_mode == "measure":
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            p1 = self.world_to_screen(temp.start)
            p2 = self.world_to_screen(temp.end)
            painter.drawLine(p1, p2)
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            painter.drawText(int(mid_x), int(mid_y), format_dimension(temp.distance()))

    # ── furniture ───────────────────────────────────────────────────
    def _draw_furniture_items(self, painter: QPainter):
        """Draw all furniture."""
        for furniture in self.floor_plan.furniture:
            is_selected = (furniture.id == self.selected_furniture)
            self._draw_furniture(painter, furniture, is_selected)

    def _draw_furniture(self, painter: QPainter, furniture: Furniture,
                        selected: bool = False):
        """Draw a single furniture item."""
        pos = self.world_to_screen(furniture.position)
        width_screen = furniture.width * self.scale
        depth_screen = furniture.depth * self.scale

        color = QColor(AppConfig.SELECTED_COLOR) if selected else QColor("#8B7355")

        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.save()
        painter.translate(pos)
        painter.rotate(furniture.rotation)

        rect = QRectF(-width_screen / 2, -depth_screen / 2, width_screen, depth_screen)
        painter.drawRect(rect)
        color.setAlpha(50)
        painter.fillRect(rect, color)
        painter.restore()

        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(pos.toPoint(), furniture.name[:3])

    # ── fixtures ────────────────────────────────────────────────────
    def _draw_fixtures(self, painter: QPainter):
        """Draw all fixtures."""
        for fixture in self.floor_plan.fixtures:
            is_selected = (fixture.id == self.selected_fixture)
            self._draw_fixture(painter, fixture, is_selected)

    def _draw_fixture(self, painter: QPainter, fixture: Fixture,
                      selected: bool = False):
        """Draw a single fixture."""
        pos = self.world_to_screen(fixture.position)
        width_screen = fixture.width * self.scale
        depth_screen = fixture.depth * self.scale

        if selected:
            color = QColor(AppConfig.SELECTED_COLOR)
        elif "kitchen" in fixture.fixture_type.value or fixture.fixture_type in [
            FixtureType.REFRIGERATOR, FixtureType.STOVE, FixtureType.OVEN,
            FixtureType.DISHWASHER, FixtureType.MICROWAVE,
        ]:
            color = QColor("#C0C0C0")
        elif fixture.fixture_type in [
            FixtureType.TOILET, FixtureType.SINK, FixtureType.BATHTUB,
            FixtureType.SHOWER, FixtureType.VANITY,
        ]:
            color = QColor("#ADD8E6")
        else:
            color = QColor("#808080")

        pen = QPen(color.darker())
        pen.setWidth(2)
        painter.setPen(pen)

        painter.save()
        painter.translate(pos)
        painter.rotate(fixture.rotation)

        rect = QRectF(-width_screen / 2, -depth_screen / 2, width_screen, depth_screen)
        painter.drawRect(rect)
        color.setAlpha(80)
        painter.fillRect(rect, color)
        painter.restore()

        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(pos.toPoint(), fixture.name[:3])

    # ── stairs ──────────────────────────────────────────────────────
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

        color = QColor(AppConfig.SELECTED_COLOR) if selected else QColor("#A0522D")

        pen = QPen(color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = (dx ** 2 + dy ** 2) ** 0.5

        if length > 0:
            perp_x = -dy / length * width_screen / 2
            perp_y = dx / length * width_screen / 2

            for i in range(stair.num_steps + 1):
                t = i / stair.num_steps
                step_x = p1.x() + dx * t
                step_y = p1.y() + dy * t
                painter.drawLine(
                    int(step_x - perp_x), int(step_y - perp_y),
                    int(step_x + perp_x), int(step_y + perp_y),
                )

        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        painter.drawText(int(mid_x), int(mid_y), stair.stair_type.value.upper())

    # ── pending object preview ──────────────────────────────────────
    def _draw_pending_object(self, painter: QPainter):
        """Draw object being placed (preview)."""
        if not self.pending_object or not self.hover_point:
            return

        pen = QPen(QColor("#0000FF"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        pos = self.world_to_screen(self.hover_point)

        if self.pending_object_type in ("furniture", "fixture"):
            width_screen = self.pending_object["width"] * self.scale
            depth_screen = self.pending_object["depth"] * self.scale
            rect = QRectF(
                pos.x() - width_screen / 2, pos.y() - depth_screen / 2,
                width_screen, depth_screen,
            )
            painter.drawRect(rect)
        elif self.pending_object_type == "stair":
            if self.temp_wall_start:
                p1 = self.world_to_screen(self.temp_wall_start)
                painter.drawLine(p1, pos)
