"""
Properties panel for editing floor plan elements.

Provides an interactive panel for viewing and modifying properties
of selected walls, openings, and rooms.
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDoubleSpinBox, QGroupBox,
    QScrollArea, QColorDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from core import Wall, Opening, Room, WallType, OpeningType, Point
from core import Furniture, Fixture, Stair, FurnitureType, FixtureType
from utils import format_dimension, feet_to_inches, inches_to_feet

logger = logging.getLogger(__name__)


class PropertiesPanel(QWidget):
    """
    Properties panel for editing selected floor plan elements.
    
    Signals:
        property_changed: Emitted when a property is modified
    """
    
    property_changed = pyqtSignal(object)  # The modified object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_object = None
        self.floor_plan = None
        
        self._setup_ui()
        
        # Initialize object properties widgets
        self._init_object_properties()
        
        logger.info("Properties panel initialized")
    
    def _setup_ui(self):
        """Setup the UI layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Set maximum width to prevent panel from being too wide
        self.setMaximumWidth(350)
        
        # Title
        title = QLabel("<b>Properties</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title)
        
        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        
        scroll.setWidget(self.properties_widget)
        self.main_layout.addWidget(scroll)
        
        # Initially show "nothing selected" message
        self._show_no_selection()
    
    def set_floor_plan(self, floor_plan):
        """Set the floor plan reference."""
        self.floor_plan = floor_plan
    
    def show_properties(self, obj):
        """Show properties for the given object."""
        self.current_object = obj
        
        # Clear current layout
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if obj is None:
            self._show_no_selection()
        elif isinstance(obj, Wall):
            self._show_wall_properties(obj)
        elif isinstance(obj, Opening):
            self._show_opening_properties(obj)
        elif isinstance(obj, Room):
            self._show_room_properties(obj)
        else:
            self._show_no_selection()
    
    def _show_no_selection(self):
        """Show message when nothing is selected."""
        label = QLabel("No object selected")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: gray; padding: 20px;")
        self.properties_layout.addWidget(label)
        self.properties_layout.addStretch()
    
    def _show_wall_properties(self, wall: Wall):
        """Show properties for a wall."""
        # Wall Info Group
        info_group = QGroupBox("Wall Information")
        info_layout = QFormLayout()
        
        # ID (read-only)
        id_label = QLabel(wall.id[:8] + "...")
        id_label.setStyleSheet("color: gray;")
        info_layout.addRow("ID:", id_label)
        
        # Length (read-only)
        length_label = QLabel(format_dimension(wall.length()))
        info_layout.addRow("Length:", length_label)
        
        info_group.setLayout(info_layout)
        self.properties_layout.addWidget(info_group)
        
        # Wall Properties Group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()
        
        # Thickness
        thickness_spin = QDoubleSpinBox()
        thickness_spin.setRange(1.0, 24.0)
        thickness_spin.setValue(wall.thickness)
        thickness_spin.setSuffix(' "')
        thickness_spin.setDecimals(1)
        thickness_spin.valueChanged.connect(
            lambda v: self._update_wall_thickness(wall, v)
        )
        props_layout.addRow("Thickness:", thickness_spin)
        
        # Wall Type
        type_combo = QComboBox()
        type_combo.addItems([wt.value for wt in WallType])
        type_combo.setCurrentText(wall.wall_type.value)
        type_combo.currentTextChanged.connect(
            lambda v: self._update_wall_type(wall, v)
        )
        props_layout.addRow("Type:", type_combo)
        
        props_group.setLayout(props_layout)
        self.properties_layout.addWidget(props_group)
        
        # Coordinates Group
        coords_group = QGroupBox("Coordinates")
        coords_layout = QFormLayout()
        
        # Start point
        start_x = QDoubleSpinBox()
        start_x.setRange(-10000, 10000)
        start_x.setValue(wall.start.x)
        start_x.setSuffix(' "')
        start_x.valueChanged.connect(
            lambda v: self._update_wall_start_x(wall, v)
        )
        coords_layout.addRow("Start X:", start_x)
        
        start_y = QDoubleSpinBox()
        start_y.setRange(-10000, 10000)
        start_y.setValue(wall.start.y)
        start_y.setSuffix(' "')
        start_y.valueChanged.connect(
            lambda v: self._update_wall_start_y(wall, v)
        )
        coords_layout.addRow("Start Y:", start_y)
        
        # End point
        end_x = QDoubleSpinBox()
        end_x.setRange(-10000, 10000)
        end_x.setValue(wall.end.x)
        end_x.setSuffix(' "')
        end_x.valueChanged.connect(
            lambda v: self._update_wall_end_x(wall, v)
        )
        coords_layout.addRow("End X:", end_x)
        
        end_y = QDoubleSpinBox()
        end_y.setRange(-10000, 10000)
        end_y.setValue(wall.end.y)
        end_y.setSuffix(' "')
        end_y.valueChanged.connect(
            lambda v: self._update_wall_end_y(wall, v)
        )
        coords_layout.addRow("End Y:", end_y)
        
        coords_group.setLayout(coords_layout)
        self.properties_layout.addWidget(coords_group)
        
        self.properties_layout.addStretch()
    
    def _show_opening_properties(self, opening: Opening):
        """Show properties for an opening (door/window)."""
        # Opening Info Group
        info_group = QGroupBox("Opening Information")
        info_layout = QFormLayout()
        
        # ID (read-only)
        id_label = QLabel(opening.id[:8] + "...")
        id_label.setStyleSheet("color: gray;")
        info_layout.addRow("ID:", id_label)
        
        # Wall reference
        wall_label = QLabel(opening.wall_id[:8] + "...")
        wall_label.setStyleSheet("color: gray;")
        info_layout.addRow("Wall:", wall_label)
        
        info_group.setLayout(info_layout)
        self.properties_layout.addWidget(info_group)
        
        # Opening Properties Group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()
        
        # Opening Type
        type_combo = QComboBox()
        type_combo.addItems([ot.value for ot in OpeningType])
        type_combo.setCurrentText(opening.opening_type.value)
        type_combo.currentTextChanged.connect(
            lambda v: self._update_opening_type(opening, v)
        )
        props_layout.addRow("Type:", type_combo)
        
        # Width
        width_spin = QDoubleSpinBox()
        width_spin.setRange(6.0, 120.0)
        width_spin.setValue(opening.width)
        width_spin.setSuffix(' "')
        width_spin.setDecimals(1)
        width_spin.valueChanged.connect(
            lambda v: self._update_opening_width(opening, v)
        )
        props_layout.addRow("Width:", width_spin)
        
        # Height
        height_spin = QDoubleSpinBox()
        height_spin.setRange(12.0, 120.0)
        height_spin.setValue(opening.height)
        height_spin.setSuffix(' "')
        height_spin.setDecimals(1)
        height_spin.valueChanged.connect(
            lambda v: self._update_opening_height(opening, v)
        )
        props_layout.addRow("Height:", height_spin)
        
        # Position along wall
        pos_spin = QDoubleSpinBox()
        pos_spin.setRange(0.0, 1.0)
        pos_spin.setValue(opening.position)
        pos_spin.setDecimals(3)
        pos_spin.setSingleStep(0.01)
        pos_spin.valueChanged.connect(
            lambda v: self._update_opening_position(opening, v)
        )
        props_layout.addRow("Position:", pos_spin)
        
        # Sill height (for windows)
        if opening.opening_type == OpeningType.WINDOW:
            sill_spin = QDoubleSpinBox()
            sill_spin.setRange(0.0, 96.0)
            sill_spin.setValue(opening.sill_height)
            sill_spin.setSuffix(' "')
            sill_spin.setDecimals(1)
            sill_spin.valueChanged.connect(
                lambda v: self._update_opening_sill_height(opening, v)
            )
            props_layout.addRow("Sill Height:", sill_spin)
        
        props_group.setLayout(props_layout)
        self.properties_layout.addWidget(props_group)
        
        self.properties_layout.addStretch()
    
    def _show_room_properties(self, room: Room):
        """Show properties for a room."""
        # Room Info Group
        info_group = QGroupBox("Room Information")
        info_layout = QFormLayout()
        
        # ID (read-only)
        id_label = QLabel(room.id[:8] + "...")
        id_label.setStyleSheet("color: gray;")
        info_layout.addRow("ID:", id_label)
        
        # Number of walls
        wall_count = QLabel(str(len(room.wall_ids)))
        info_layout.addRow("Walls:", wall_count)
        
        info_group.setLayout(info_layout)
        self.properties_layout.addWidget(info_group)
        
        # Room Properties Group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout()
        
        # Name
        name_edit = QLineEdit(room.name)
        name_edit.textChanged.connect(
            lambda v: self._update_room_name(room, v)
        )
        props_layout.addRow("Name:", name_edit)
        
        # Color
        color_layout = QVBoxLayout()
        color_button = QPushButton("Choose Color")
        if room.color:
            color_button.setStyleSheet(f"background-color: {room.color};")
        color_button.clicked.connect(
            lambda: self._choose_room_color(room, color_button)
        )
        color_layout.addWidget(color_button)
        props_layout.addRow("Color:", color_button)
        
        props_group.setLayout(props_layout)
        self.properties_layout.addWidget(props_group)
        
        self.properties_layout.addStretch()
    
    # Update methods for walls
    def _update_wall_thickness(self, wall: Wall, value: float):
        """Update wall thickness."""
        wall.thickness = value
        self.property_changed.emit(wall)
        logger.info(f"Updated wall {wall.id[:8]} thickness to {value}\"")
    
    def _update_wall_type(self, wall: Wall, value: str):
        """Update wall type."""
        wall.wall_type = WallType(value)
        self.property_changed.emit(wall)
        logger.info(f"Updated wall {wall.id[:8]} type to {value}")
    
    def _update_wall_start_x(self, wall: Wall, value: float):
        """Update wall start X coordinate."""
        wall.start.x = value
        self.property_changed.emit(wall)
    
    def _update_wall_start_y(self, wall: Wall, value: float):
        """Update wall start Y coordinate."""
        wall.start.y = value
        self.property_changed.emit(wall)
    
    def _update_wall_end_x(self, wall: Wall, value: float):
        """Update wall end X coordinate."""
        wall.end.x = value
        self.property_changed.emit(wall)
    
    def _update_wall_end_y(self, wall: Wall, value: float):
        """Update wall end Y coordinate."""
        wall.end.y = value
        self.property_changed.emit(wall)
    
    # Update methods for openings
    def _update_opening_type(self, opening: Opening, value: str):
        """Update opening type."""
        opening.opening_type = OpeningType(value)
        self.property_changed.emit(opening)
        logger.info(f"Updated opening {opening.id[:8]} type to {value}")
    
    def _update_opening_width(self, opening: Opening, value: float):
        """Update opening width."""
        opening.width = value
        self.property_changed.emit(opening)
        logger.info(f"Updated opening {opening.id[:8]} width to {value}\"")
    
    def _update_opening_height(self, opening: Opening, value: float):
        """Update opening height."""
        opening.height = value
        self.property_changed.emit(opening)
    
    def _update_opening_position(self, opening: Opening, value: float):
        """Update opening position along wall."""
        opening.position = value
        self.property_changed.emit(opening)
    
    def _update_opening_sill_height(self, opening: Opening, value: float):
        """Update window sill height."""
        opening.sill_height = value
        self.property_changed.emit(opening)
    
    # Update methods for rooms
    def _update_room_name(self, room: Room, value: str):
        """Update room name."""
        room.name = value
        self.property_changed.emit(room)
        logger.info(f"Updated room {room.id[:8]} name to {value}")
    
    def _choose_room_color(self, room: Room, button: QPushButton):
        """Open color chooser for room."""
        current_color = QColor(room.color) if room.color else QColor(Qt.GlobalColor.white)
        color = QColorDialog.getColor(current_color, self, "Choose Room Color")
        
        if color.isValid():
            room.color = color.name()
            button.setStyleSheet(f"background-color: {room.color};")
            self.property_changed.emit(room)
            logger.info(f"Updated room {room.id[:8]} color to {room.color}")

    def _init_object_properties(self):
        """Initialize object properties widgets."""
        from PyQt6.QtWidgets import (
            QGroupBox, QFormLayout, QHBoxLayout, QLabel,
            QDoubleSpinBox, QComboBox, QLineEdit, QPushButton
        )
        
        # Create object properties group
        self.object_properties_group = QGroupBox("Object Properties")
        self.object_properties_layout = QFormLayout()
        self.object_properties_group.setLayout(self.object_properties_layout)
        
        # Position
        self.obj_x_spin = QDoubleSpinBox()
        self.obj_x_spin.setRange(-10000, 10000)
        self.obj_x_spin.setDecimals(2)
        self.obj_x_spin.setSuffix('"')
        self.obj_x_spin.valueChanged.connect(self._on_object_property_changed)
        
        self.obj_y_spin = QDoubleSpinBox()
        self.obj_y_spin.setRange(-10000, 10000)
        self.obj_y_spin.setDecimals(2)
        self.obj_y_spin.setSuffix('"')
        self.obj_y_spin.valueChanged.connect(self._on_object_property_changed)
        
        # Size
        self.obj_width_spin = QDoubleSpinBox()
        self.obj_width_spin.setRange(6, 10000)
        self.obj_width_spin.setDecimals(2)
        self.obj_width_spin.setSuffix('"')
        self.obj_width_spin.valueChanged.connect(self._on_object_property_changed)
        
        self.obj_depth_spin = QDoubleSpinBox()
        self.obj_depth_spin.setRange(6, 10000)
        self.obj_depth_spin.setDecimals(2)
        self.obj_depth_spin.setSuffix('"')
        self.obj_depth_spin.valueChanged.connect(self._on_object_property_changed)
        
        # Rotation
        self.obj_rotation_spin = QDoubleSpinBox()
        self.obj_rotation_spin.setRange(0, 360)
        self.obj_rotation_spin.setDecimals(1)
        self.obj_rotation_spin.setSuffix('°')
        self.obj_rotation_spin.setWrapping(True)
        self.obj_rotation_spin.valueChanged.connect(self._on_object_property_changed)
        
        # Type
        self.obj_type_combo = QComboBox()
        self.obj_type_combo.currentTextChanged.connect(self._on_object_type_changed)
        
        # Name
        self.obj_name_edit = QLineEdit()
        self.obj_name_edit.textChanged.connect(self._on_object_name_changed)
        
        # Add to layout
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.obj_x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.obj_y_spin)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(self.obj_width_spin)
        size_layout.addWidget(QLabel("D:"))
        size_layout.addWidget(self.obj_depth_spin)
        
        self.object_properties_layout.addRow("Position:", pos_layout)
        self.object_properties_layout.addRow("Size:", size_layout)
        self.object_properties_layout.addRow("Rotation:", self.obj_rotation_spin)
        self.object_properties_layout.addRow("Type:", self.obj_type_combo)
        self.object_properties_layout.addRow("Name:", self.obj_name_edit)
        
        # Delete button
        self.delete_object_btn = QPushButton("Delete Object")
        self.delete_object_btn.clicked.connect(self._on_delete_object)
        self.object_properties_layout.addRow("", self.delete_object_btn)
        
        # Add to main layout
        self.main_layout.addWidget(self.object_properties_group)
        
        # Initially hide
        self.object_properties_group.hide()
        
        # Track current object
        self.current_object = None
        self._updating_from_object = False
    
    def show_object_properties(self, obj):
        """Show properties for the given object."""
        if obj is None:
            self.object_properties_group.hide()
            self.current_object = None
            return
        
        self.current_object = obj
        self._updating_from_object = True
        
        # Update type combo
        self.obj_type_combo.clear()
        if isinstance(obj, Furniture):
            self.object_properties_group.setTitle("Furniture Properties")
            for ftype in FurnitureType:
                self.obj_type_combo.addItem(ftype.value.replace('_', ' ').title())
            current_type = obj.furniture_type.value.replace('_', ' ').title()
            index = self.obj_type_combo.findText(current_type)
            if index >= 0:
                self.obj_type_combo.setCurrentIndex(index)
                
        elif isinstance(obj, Fixture):
            self.object_properties_group.setTitle("Fixture Properties")
            for ftype in FixtureType:
                self.obj_type_combo.addItem(ftype.value.replace('_', ' ').title())
            current_type = obj.fixture_type.value.replace('_', ' ').title()
            index = self.obj_type_combo.findText(current_type)
            if index >= 0:
                self.obj_type_combo.setCurrentIndex(index)
                
        elif isinstance(obj, Stair):
            self.object_properties_group.setTitle("Stair Properties")
            self.obj_type_combo.addItem("Staircase")
            self.obj_type_combo.setEnabled(False)
        
        # Update values
        if isinstance(obj, Stair):
            # For stairs, compute center position from start and end
            cx = (obj.start.x + obj.end.x) / 2
            cy = (obj.start.y + obj.end.y) / 2
            self.obj_x_spin.setValue(cx)
            self.obj_y_spin.setValue(cy)
            self.obj_width_spin.setValue(obj.width)
            self.obj_depth_spin.setValue(obj.length())  # Use length for depth
            self.obj_rotation_spin.setValue(obj.rotation)
        else:
            # For furniture and fixtures
            self.obj_x_spin.setValue(obj.position.x)
            self.obj_y_spin.setValue(obj.position.y)
            self.obj_width_spin.setValue(obj.width)
            self.obj_depth_spin.setValue(obj.depth)
            self.obj_rotation_spin.setValue(obj.rotation)
        
        # Name
        if hasattr(obj, 'name'):
            self.obj_name_edit.setText(obj.name or "")
            self.obj_name_edit.setEnabled(True)
        else:
            self.obj_name_edit.setText("")
            self.obj_name_edit.setEnabled(False)
        
        self.object_properties_group.show()
        self._updating_from_object = False
    
    def _on_object_property_changed(self):
        """Handle changes to object properties."""
        if self._updating_from_object or not self.current_object:
            return
        
        # Update object
        if isinstance(self.current_object, Stair):
            # For stairs, update start and end points to achieve new center position
            old_cx = (self.current_object.start.x + self.current_object.end.x) / 2
            old_cy = (self.current_object.start.y + self.current_object.end.y) / 2
            new_cx = self.obj_x_spin.value()
            new_cy = self.obj_y_spin.value()
            dx = new_cx - old_cx
            dy = new_cy - old_cy
            
            # Move start and end
            self.current_object.start = Point(
                self.current_object.start.x + dx,
                self.current_object.start.y + dy
            )
            self.current_object.end = Point(
                self.current_object.end.x + dx,
                self.current_object.end.y + dy
            )
            
            # Update width and rotation
            self.current_object.width = self.obj_width_spin.value()
            self.current_object.rotation = self.obj_rotation_spin.value()
            
            # For depth changes (length), scale start/end points
            new_length = self.obj_depth_spin.value()
            current_length = self.current_object.length()
            if current_length > 0 and abs(new_length - current_length) > 0.01:
                scale = new_length / current_length
                cx = (self.current_object.start.x + self.current_object.end.x) / 2
                cy = (self.current_object.start.y + self.current_object.end.y) / 2
                self.current_object.start = Point(
                    cx + (self.current_object.start.x - cx) * scale,
                    cy + (self.current_object.start.y - cy) * scale
                )
                self.current_object.end = Point(
                    cx + (self.current_object.end.x - cx) * scale,
                    cy + (self.current_object.end.y - cy) * scale
                )
        else:
            # For furniture and fixtures
            self.current_object.position.x = self.obj_x_spin.value()
            self.current_object.position.y = self.obj_y_spin.value()
            self.current_object.width = self.obj_width_spin.value()
            self.current_object.depth = self.obj_depth_spin.value()
            self.current_object.rotation = self.obj_rotation_spin.value()
        
        # Trigger canvas update
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
    
    def _on_object_type_changed(self, type_text: str):
        """Handle changes to object type."""
        if self._updating_from_object or not self.current_object:
            return
        
        # Convert display text back to enum value
        enum_value = type_text.replace(' ', '_').upper()
        
        if isinstance(self.current_object, Furniture):
            try:
                new_type = FurnitureType(enum_value.lower())
                self.current_object.furniture_type = new_type
            except ValueError:
                pass
        
        elif isinstance(self.current_object, Fixture):
            try:
                new_type = FixtureType(enum_value.lower())
                self.current_object.fixture_type = new_type
            except ValueError:
                pass
        
        # Trigger canvas update
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
    
    def _on_object_name_changed(self, name: str):
        """Handle changes to object name."""
        if self._updating_from_object or not self.current_object:
            return
        
        if hasattr(self.current_object, 'name'):
            self.current_object.name = name
    
    def _on_delete_object(self):
        """Handle delete object button click."""
        if not self.current_object:
            return
        
        # Tell canvas to delete the selected object
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.delete_selected_object()

