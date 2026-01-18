"""
3D Viewer for floor plans.

Provides a simple 3D visualization of the floor plan using basic 3D rendering.
Shows walls, floors, ceilings, stairs, and furniture in 3D perspective.
"""

import logging
import math
from typing import Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon, QTransform

from core import FloorPlan, Building, Wall, Room

logger = logging.getLogger(__name__)


class Simple3DViewer(QWidget):
    """
    Simple 3D viewer using isometric projection.
    
    Displays floor plans in 3D using an isometric view without requiring OpenGL.
    Shows walls with height, floors, ceilings, and objects in 3D.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.building: Optional[Building] = None
        self.current_floor: Optional[FloorPlan] = None
        self.show_all_floors = True
        
        # View parameters
        self.rotation_angle = 45  # Degrees
        self.tilt_angle = 30  # Degrees
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Create the rendering canvas
        self.canvas = Viewer3DCanvas(self)
        
        self._setup_ui()
        
        logger.info("3D Viewer initialized")
    
    def _setup_ui(self):
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Controls
        controls = QHBoxLayout()
        
        # Rotation slider
        controls.addWidget(QLabel("Rotate:"))
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(45)
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)
        controls.addWidget(self.rotation_slider)
        
        # Tilt slider
        controls.addWidget(QLabel("Tilt:"))
        self.tilt_slider = QSlider(Qt.Orientation.Horizontal)
        self.tilt_slider.setRange(0, 90)
        self.tilt_slider.setValue(30)
        self.tilt_slider.valueChanged.connect(self._on_tilt_changed)
        controls.addWidget(self.tilt_slider)
        
        # Reset button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        controls.addWidget(reset_btn)
        
        # Toggle floors button
        self.toggle_floors_btn = QPushButton("Show Current Floor Only")
        self.toggle_floors_btn.clicked.connect(self.toggle_all_floors)
        controls.addWidget(self.toggle_floors_btn)
        
        # Debug button
        debug_btn = QPushButton("Debug Info")
        debug_btn.clicked.connect(self._show_debug_info)
        controls.addWidget(debug_btn)
        
        layout.addLayout(controls)
        
        # Add the 3D canvas
        layout.addWidget(self.canvas, stretch=1)
        
        # Set minimum size
        self.setMinimumSize(600, 400)
    
    def set_building(self, building: Building):
        """Set the building to display."""
        self.building = building
        if building and building.floors:
            # Show ground floor by default
            levels = building.get_floor_levels()
            self.current_floor = building.get_floor(0) if 0 in levels else building.get_floor(levels[0])
        
        # Update canvas
        self.canvas.set_building(building)
        self.canvas.set_current_floor(self.current_floor)
        self.canvas.update()
    
    def set_floor_plan(self, floor_plan: FloorPlan):
        """Set a single floor plan to display."""
        self.current_floor = floor_plan
        # Create a temporary building with just this floor
        self.building = Building(name="Single Floor")
        self.building.add_floor(floor_plan)
        self.show_all_floors = False
        
        # Update canvas
        self.canvas.set_building(self.building)
        self.canvas.set_current_floor(floor_plan)
        self.canvas.update()
    
    def toggle_all_floors(self):
        """Toggle between showing all floors or just current floor."""
        self.show_all_floors = not self.show_all_floors
        if self.show_all_floors:
            self.toggle_floors_btn.setText("Show Current Floor Only")
        else:
            self.toggle_floors_btn.setText("Show All Floors")
        
        self.canvas.set_show_all_floors(self.show_all_floors)
        self.canvas.update()
    
    def _on_rotation_changed(self, value):
        """Handle rotation slider change."""
        self.rotation_angle = value
        self.canvas.set_rotation(value)
        self.canvas.update()
    
    def _on_tilt_changed(self, value):
        """Handle tilt slider change."""
        self.tilt_angle = value
        self.canvas.set_tilt(value)
        self.canvas.update()
    
    def reset_view(self):
        """Reset view to default."""
        self.rotation_angle = 45
        self.tilt_angle = 30
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.rotation_slider.setValue(45)
        self.tilt_slider.setValue(30)
        
        self.canvas.set_rotation(45)
        self.canvas.set_tilt(30)
        self.canvas.set_zoom(1.0)
        self.canvas.set_offset(0, 0)
        self.canvas.update()
    
    def _show_debug_info(self):
        """Show debug information dialog."""
        from PyQt6.QtWidgets import QMessageBox
        
        info = "=== 3D Viewer Debug Info ===\n\n"
        
        if self.building:
            info += f"Building: {self.building.name}\n"
            info += f"Floors: {len(self.building.floors)}\n"
            info += f"Floor levels: {self.building.get_floor_levels()}\n\n"
            
            for level in sorted(self.building.get_floor_levels()):
                floor = self.building.get_floor(level)
                if floor:
                    info += f"Level {level} ({floor.name}):\n"
                    info += f"  Walls: {len(floor.walls)}\n"
                    info += f"  Openings: {len(floor.openings)}\n"
                    info += f"  Rooms: {len(floor.rooms)}\n"
                    info += f"  Furniture: {len(floor.furniture)}\n\n"
        else:
            info += "No building set!\n\n"
        
        if self.current_floor:
            info += f"Current floor: {self.current_floor.name}\n"
            info += f"  Level: {self.current_floor.floor_level}\n"
            info += f"  Walls: {len(self.current_floor.walls)}\n"
        else:
            info += "No current floor!\n"
        
        info += f"\nShow all floors: {self.show_all_floors}\n"
        info += f"Canvas building: {self.canvas.building is not None}\n"
        
        if self.canvas.building:
            info += f"Canvas building floors: {len(self.canvas.building.floors)}\n"
        
        QMessageBox.information(self, "3D Viewer Debug Info", info)
    
    def refresh(self):
        """Force refresh the 3D view."""
        logger.info("Refreshing 3D view")
        # Use QTimer to defer the update slightly to avoid race conditions
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self.canvas.update)


class Viewer3DCanvas(QWidget):
    """Canvas widget for rendering 3D view."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.building: Optional[Building] = None
        self.current_floor: Optional[FloorPlan] = None
        self.show_all_floors = True
        
        # View parameters
        self.rotation_angle = 45
        self.tilt_angle = 30
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.dragging = False
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
    
    def set_building(self, building: Building):
        """Set the building to display."""
        self.building = building
    
    def set_current_floor(self, floor_plan: FloorPlan):
        """Set the current floor."""
        self.current_floor = floor_plan
    
    def set_show_all_floors(self, show_all: bool):
        """Set whether to show all floors or just current."""
        self.show_all_floors = show_all
    
    def set_rotation(self, angle: int):
        """Set rotation angle."""
        self.rotation_angle = angle
    
    def set_tilt(self, angle: int):
        """Set tilt angle."""
        self.tilt_angle = angle
    
    def set_zoom(self, zoom: float):
        """Set zoom level."""
        self.zoom = zoom
    
    def set_offset(self, x: float, y: float):
        """Set pan offset."""
        self.offset_x = x
        self.offset_y = y
    
    def paintEvent(self, event):
        """Paint the 3D view."""
        # Safety check - ensure widget is ready
        if not self.isVisible() or self.width() <= 0 or self.height() <= 0:
            return
        
        painter = QPainter(self)
        
        # Safety check - ensure painter is valid
        if not painter.isActive():
            logger.warning("Painter is not active, skipping paint")
            return
        
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Fill background
            painter.fillRect(self.rect(), QColor("#2C2C2C"))  # Dark gray background
            
            # Debug: Log what we have
            if self.building:
                logger.debug(f"3D Paint: Building has {len(self.building.floors)} floors")
                for level, floor in self.building.floors.items():
                    logger.debug(f"  Level {level}: {len(floor.walls)} walls")
            
            if not self.building or not self.building.floors:
                # Draw "no data" message
                painter.setPen(QColor("#FFFFFF"))
                font = painter.font()
                font.setPointSize(14)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                               "No floor plan loaded\n\nDraw some walls or load a floor plan\nto see the 3D view")
                logger.debug("3D Paint: No building or no floors")
                return
            
            # Check if there's any geometry to render
            has_geometry = False
            for floor_plan in self.building.floors.values():
                if floor_plan.walls:
                    has_geometry = True
                    break
            
            if not has_geometry:
                # Draw "no geometry" message  
                painter.setPen(QColor("#FFFFFF"))
                font = painter.font()
                font.setPointSize(14)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                               f"No walls drawn yet\n\n({len(self.building.floors)} floor(s) in building)\n\nDraw some walls in the 2D view\nto see them in 3D")
                logger.debug(f"3D Paint: Building has {len(self.building.floors)} floors but no walls")
                return
            
            logger.debug(f"3D Paint: Rendering {len(self.building.floors)} floor(s) with geometry")
            
            # Save painter state
            painter.save()
            
            # Center the view
            center_x = self.width() / 2 + self.offset_x
            center_y = self.height() / 2 + self.offset_y
            painter.translate(center_x, center_y)
            
            # Draw floors
            floors_to_draw = []
            if self.show_all_floors:
                levels = sorted(self.building.get_floor_levels())
                for level in levels:
                    floor = self.building.get_floor(level)
                    if floor:
                        floors_to_draw.append(floor)
            else:
                if self.current_floor:
                    floors_to_draw.append(self.current_floor)
            
            # Draw each floor
            for floor_plan in floors_to_draw:
                if floor_plan:
                    self._draw_floor_3d(painter, floor_plan)
            
            # Restore painter state
            painter.restore()
            
            # Draw legend
            self._draw_legend(painter)
            
        except Exception as e:
            logger.error(f"Error in paintEvent: {e}", exc_info=True)
        finally:
            # Ensure painter is properly ended
            if painter.isActive():
                painter.end()
        """Paint the 3D view."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor("#E0E0E0"))
        
        if not self.building or not self.building.floors:
            # Draw "no data" message
            painter.setPen(QColor("#808080"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                           "No floor plan loaded\nOpen a floor plan to see 3D view")
            return
        
        # Save painter state
        painter.save()
        
        # Center the view
        center_x = self.width() / 2 + self.offset_x
        center_y = self.height() / 2 + self.offset_y
        painter.translate(center_x, center_y)
        
        # Draw floors
        floors_to_draw = []
        if self.show_all_floors:
            levels = sorted(self.building.get_floor_levels())
            for level in levels:
                floors_to_draw.append(self.building.get_floor(level))
        else:
            if self.current_floor:
                floors_to_draw.append(self.current_floor)
        
        # Draw each floor
        for floor_plan in floors_to_draw:
            if floor_plan:
                self._draw_floor_3d(painter, floor_plan)
        
        # Restore painter state
        painter.restore()
        
        # Draw legend
        self._draw_legend(painter)
    
    def _draw_floor_3d(self, painter: QPainter, floor_plan: FloorPlan):
        """Draw a single floor in 3D."""
        if not floor_plan.walls:
            return
        
        # Base elevation for this floor
        base_z = floor_plan.elevation
        
        # Draw floor slab
        self._draw_floor_slab(painter, floor_plan, base_z)
        
        # Draw walls
        for wall in floor_plan.walls:
            self._draw_wall_3d(painter, wall, base_z)
        
        # Draw rooms (as floor fill)
        for room in floor_plan.rooms:
            self._draw_room_3d(painter, room, floor_plan, base_z)
    
    def _draw_floor_slab(self, painter: QPainter, floor_plan: FloorPlan, z: float):
        """Draw the floor slab."""
        bounds = floor_plan.get_bounds()
        if not bounds:
            return
        
        min_pt, max_pt = bounds
        
        # Create floor rectangle points
        corners_3d = [
            (min_pt.x, min_pt.y, z),
            (max_pt.x, min_pt.y, z),
            (max_pt.x, max_pt.y, z),
            (min_pt.x, max_pt.y, z)
        ]
        
        # Project to 2D
        corners_2d = [self._project_3d_to_2d(x, y, z) for x, y, z in corners_3d]
        
        # Draw floor
        polygon = QPolygon([QPoint(int(x), int(y)) for x, y in corners_2d])
        painter.setBrush(QBrush(QColor("#F5F5DC")))  # Beige floor
        painter.setPen(QPen(QColor("#8B7355"), 1))
        painter.drawPolygon(polygon)
    
    def _draw_wall_3d(self, painter: QPainter, wall: Wall, base_z: float):
        """Draw a wall in 3D."""
        # Wall bottom and top Z coordinates
        z_bottom = base_z
        z_top = base_z + wall.height
        
        # Calculate wall direction and perpendicular
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 0.1:
            return
        
        # Perpendicular vector for thickness
        perp_x = -dy / length * wall.thickness / 2
        perp_y = dx / length * wall.thickness / 2
        
        # Wall corners (8 points for a box)
        corners_3d = [
            # Bottom face
            (wall.start.x - perp_x, wall.start.y - perp_y, z_bottom),
            (wall.start.x + perp_x, wall.start.y + perp_y, z_bottom),
            (wall.end.x + perp_x, wall.end.y + perp_y, z_bottom),
            (wall.end.x - perp_x, wall.end.y - perp_y, z_bottom),
            # Top face
            (wall.start.x - perp_x, wall.start.y - perp_y, z_top),
            (wall.start.x + perp_x, wall.start.y + perp_y, z_top),
            (wall.end.x + perp_x, wall.end.y + perp_y, z_top),
            (wall.end.x - perp_x, wall.end.y - perp_y, z_top),
        ]
        
        # Project all corners
        corners_2d = [self._project_3d_to_2d(x, y, z) for x, y, z in corners_3d]
        
        # Draw visible faces
        # Front face
        front = QPolygon([
            QPoint(int(corners_2d[0][0]), int(corners_2d[0][1])),
            QPoint(int(corners_2d[3][0]), int(corners_2d[3][1])),
            QPoint(int(corners_2d[7][0]), int(corners_2d[7][1])),
            QPoint(int(corners_2d[4][0]), int(corners_2d[4][1]))
        ])
        
        color = self._get_wall_color(wall)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawPolygon(front)
        
        # Right face
        right = QPolygon([
            QPoint(int(corners_2d[3][0]), int(corners_2d[3][1])),
            QPoint(int(corners_2d[2][0]), int(corners_2d[2][1])),
            QPoint(int(corners_2d[6][0]), int(corners_2d[6][1])),
            QPoint(int(corners_2d[7][0]), int(corners_2d[7][1]))
        ])
        
        painter.setBrush(QBrush(color.darker(110)))
        painter.drawPolygon(right)
        
        # Top face
        top = QPolygon([
            QPoint(int(corners_2d[4][0]), int(corners_2d[4][1])),
            QPoint(int(corners_2d[5][0]), int(corners_2d[5][1])),
            QPoint(int(corners_2d[6][0]), int(corners_2d[6][1])),
            QPoint(int(corners_2d[7][0]), int(corners_2d[7][1]))
        ])
        
        painter.setBrush(QBrush(color.lighter(105)))
        painter.drawPolygon(top)
    
    def _draw_room_3d(self, painter: QPainter, room: Room, floor_plan: FloorPlan, base_z: float):
        """Draw room floor fill in 3D."""
        if not room.wall_ids or not room.color:
            return
        
        # Get room vertices
        vertices = []
        for wall_id in room.wall_ids:
            wall = floor_plan.get_wall(wall_id)
            if wall:
                vertices.append((wall.start.x, wall.start.y))
                vertices.append((wall.end.x, wall.end.y))
        
        if len(vertices) < 3:
            return
        
        # Remove duplicates
        unique_vertices = []
        seen = set()
        for v in vertices:
            key = (round(v[0], 1), round(v[1], 1))
            if key not in seen:
                unique_vertices.append(v)
                seen.add(key)
        
        # Project to 2D
        projected = [self._project_3d_to_2d(x, y, base_z + 0.5) for x, y in unique_vertices]
        
        # Draw filled polygon
        polygon = QPolygon([QPoint(int(x), int(y)) for x, y in projected])
        color = QColor(room.color)
        color.setAlpha(100)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)
    
    def _project_3d_to_2d(self, x: float, y: float, z: float) -> tuple:
        """
        Project 3D coordinates to 2D isometric view.
        
        Uses isometric projection with rotation and tilt.
        """
        # Apply zoom
        x *= self.zoom * 0.5
        y *= self.zoom * 0.5
        z *= self.zoom * 0.5
        
        # Rotation around Z axis
        rot_rad = math.radians(self.rotation_angle)
        cos_rot = math.cos(rot_rad)
        sin_rot = math.sin(rot_rad)
        
        x_rot = x * cos_rot - y * sin_rot
        y_rot = x * sin_rot + y * cos_rot
        
        # Tilt (isometric projection)
        tilt_rad = math.radians(self.tilt_angle)
        cos_tilt = math.cos(tilt_rad)
        sin_tilt = math.sin(tilt_rad)
        
        # Isometric projection
        screen_x = x_rot
        screen_y = y_rot * cos_tilt - z * sin_tilt
        
        return (screen_x, screen_y)
    
    def _get_wall_color(self, wall: Wall) -> QColor:
        """Get color for a wall based on its style."""
        style_colors = {
            "solid": "#D3D3D3",
            "brick": "#B22222",
            "concrete": "#808080",
            "glass": "#87CEEB",
            "curtain": "#B0C4DE",
            "wood_frame": "#DEB887",
            "metal_stud": "#C0C0C0",
            "stone": "#696969"
        }
        
        color_str = style_colors.get(wall.wall_style.value, "#D3D3D3")
        return QColor(color_str)
    
    def _draw_legend(self, painter: QPainter):
        """Draw view legend."""
        painter.save()
        
        # Draw instructions
        text = f"Rotation: {self.rotation_angle}° | Tilt: {self.tilt_angle}° | Zoom: {self.zoom:.2f}x"
        painter.setPen(QColor("#000000"))
        painter.drawText(10, 20, text)
        
        if self.building:
            floor_info = f"Floors: {self.building.get_floor_count()}"
            if self.current_floor:
                floor_info += f" | Current: Level {self.current_floor.floor_level}"
            painter.drawText(10, 40, floor_info)
        
        painter.restore()
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for panning."""
        if self.dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom *= 0.9
        
        # Limit zoom
        self.zoom = max(0.1, min(5.0, self.zoom))
        self.update()
