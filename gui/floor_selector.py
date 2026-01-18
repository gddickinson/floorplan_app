"""
Floor selector widget for multi-level buildings.

Provides controls for navigating between different floors in a building,
adding/removing floors, and managing floor properties.
"""

import logging
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from core import Building, FloorPlan

logger = logging.getLogger(__name__)


class FloorSelector(QWidget):
    """
    Floor selector widget for navigating between building levels.
    
    Signals:
        floor_changed: Emitted when user selects a different floor
        floor_added: Emitted when a new floor is added
        floor_removed: Emitted when a floor is removed
    """
    
    floor_changed = pyqtSignal(int)  # floor_level
    floor_added = pyqtSignal(int)  # floor_level
    floor_removed = pyqtSignal(int)  # floor_level
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.building: Optional[Building] = None
        self.current_level = 0
        
        self._setup_ui()
        logger.info("Floor selector initialized")
    
    def _setup_ui(self):
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Set maximum width
        self.setMaximumWidth(250)
        
        # Title
        title = QLabel("<b>Floor Selector</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current floor info
        info_group = QGroupBox("Current Floor")
        info_layout = QVBoxLayout()
        
        self.floor_label = QLabel("Ground Floor (Level 0)")
        self.floor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.floor_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        info_layout.addWidget(self.floor_label)
        
        self.elevation_label = QLabel("Elevation: 0'")
        self.elevation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.elevation_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.up_btn = QPushButton("↑ Up")
        self.up_btn.clicked.connect(self.go_up)
        nav_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton("↓ Down")
        self.down_btn.clicked.connect(self.go_down)
        nav_layout.addWidget(self.down_btn)
        
        layout.addLayout(nav_layout)
        
        # Floor dropdown
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Go to:"))
        
        self.floor_combo = QComboBox()
        self.floor_combo.currentIndexChanged.connect(self._on_floor_selected)
        dropdown_layout.addWidget(self.floor_combo)
        
        layout.addLayout(dropdown_layout)
        
        # Floor management buttons
        mgmt_group = QGroupBox("Floor Management")
        mgmt_layout = QVBoxLayout()
        
        self.add_floor_btn = QPushButton("Add New Floor")
        self.add_floor_btn.clicked.connect(self.add_floor_dialog)
        mgmt_layout.addWidget(self.add_floor_btn)
        
        self.remove_floor_btn = QPushButton("Remove Current Floor")
        self.remove_floor_btn.clicked.connect(self.remove_current_floor)
        mgmt_layout.addWidget(self.remove_floor_btn)
        
        mgmt_group.setLayout(mgmt_layout)
        layout.addWidget(mgmt_group)
        
        layout.addStretch()
        
        # Initially disabled until building is set
        self._update_ui_state()
    
    def set_building(self, building: Building):
        """Set the building to navigate."""
        self.building = building
        
        if building:
            levels = building.get_floor_levels()
            if levels:
                self.current_level = 0 if 0 in levels else levels[0]
        
        self._update_floor_list()
        self._update_ui_state()
        logger.info(f"Set building: {building.name if building else 'None'}")
    
    def _update_floor_list(self):
        """Update the floor dropdown list."""
        self.floor_combo.blockSignals(True)
        self.floor_combo.clear()
        
        if not self.building:
            self.floor_combo.blockSignals(False)
            return
        
        levels = self.building.get_floor_levels()
        for level in levels:
            floor = self.building.get_floor(level)
            if floor:
                self.floor_combo.addItem(f"{floor.name} (Level {level})", level)
        
        # Set current floor in combo
        idx = self.floor_combo.findData(self.current_level)
        if idx >= 0:
            self.floor_combo.setCurrentIndex(idx)
        
        self.floor_combo.blockSignals(False)
        
        self._update_current_floor_info()
    
    def _update_current_floor_info(self):
        """Update the current floor information display."""
        if not self.building:
            self.floor_label.setText("No Building")
            self.elevation_label.setText("")
            return
        
        floor = self.building.get_floor(self.current_level)
        if floor:
            self.floor_label.setText(f"{floor.name}")
            elevation_ft = floor.elevation / 12.0
            self.elevation_label.setText(f"Level {self.current_level} | Elevation: {elevation_ft:.1f}'")
        else:
            self.floor_label.setText(f"Level {self.current_level}")
            self.elevation_label.setText("")
    
    def _update_ui_state(self):
        """Update button enabled states."""
        has_building = self.building is not None
        
        self.up_btn.setEnabled(has_building and self.can_go_up())
        self.down_btn.setEnabled(has_building and self.can_go_down())
        self.floor_combo.setEnabled(has_building)
        self.add_floor_btn.setEnabled(has_building)
        
        # Can't remove if only one floor
        can_remove = has_building and self.building.get_floor_count() > 1
        self.remove_floor_btn.setEnabled(can_remove)
    
    def can_go_up(self) -> bool:
        """Check if can go up a floor."""
        if not self.building:
            return False
        
        levels = self.building.get_floor_levels()
        return self.current_level < max(levels)
    
    def can_go_down(self) -> bool:
        """Check if can go down a floor."""
        if not self.building:
            return False
        
        levels = self.building.get_floor_levels()
        return self.current_level > min(levels)
    
    def go_up(self):
        """Navigate to floor above."""
        if not self.can_go_up():
            return
        
        levels = sorted(self.building.get_floor_levels())
        current_idx = levels.index(self.current_level)
        if current_idx < len(levels) - 1:
            self.set_current_floor(levels[current_idx + 1])
    
    def go_down(self):
        """Navigate to floor below."""
        if not self.can_go_down():
            return
        
        levels = sorted(self.building.get_floor_levels())
        current_idx = levels.index(self.current_level)
        if current_idx > 0:
            self.set_current_floor(levels[current_idx - 1])
    
    def set_current_floor(self, level: int):
        """Set the current floor level."""
        if self.building and level in self.building.floors:
            self.current_level = level
            self._update_floor_list()
            self._update_ui_state()
            self.floor_changed.emit(level)
            logger.info(f"Changed to floor level {level}")
    
    def _on_floor_selected(self, index):
        """Handle floor selection from dropdown."""
        if index < 0:
            return
        
        level = self.floor_combo.currentData()
        if level is not None:
            self.set_current_floor(level)
    
    def add_floor_dialog(self):
        """Show dialog to add a new floor."""
        if not self.building:
            return
        
        dialog = AddFloorDialog(self.building, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            level = dialog.get_floor_level()
            name = dialog.get_floor_name()
            copy_from = dialog.get_copy_from()
            
            # Create the floor
            floor = self.building.create_new_floor(level, name, copy_from)
            
            self._update_floor_list()
            self._update_ui_state()
            self.floor_added.emit(level)
            
            # Switch to new floor
            self.set_current_floor(level)
            
            logger.info(f"Added new floor: {name} (Level {level})")
    
    def remove_current_floor(self):
        """Remove the current floor."""
        if not self.building or self.building.get_floor_count() <= 1:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        
        floor = self.building.get_floor(self.current_level)
        reply = QMessageBox.question(
            self,
            "Remove Floor",
            f"Are you sure you want to remove {floor.name}?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            level_to_remove = self.current_level
            
            # Switch to different floor first
            levels = self.building.get_floor_levels()
            levels.remove(level_to_remove)
            self.set_current_floor(levels[0] if levels else 0)
            
            # Remove the floor
            self.building.remove_floor(level_to_remove)
            
            self._update_floor_list()
            self._update_ui_state()
            self.floor_removed.emit(level_to_remove)
            
            logger.info(f"Removed floor level {level_to_remove}")


class AddFloorDialog(QDialog):
    """Dialog for adding a new floor."""
    
    def __init__(self, building: Building, parent=None):
        super().__init__(parent)
        
        self.building = building
        
        self.setWindowTitle("Add New Floor")
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        # Floor level
        self.level_spin = QSpinBox()
        self.level_spin.setRange(-10, 50)
        
        # Suggest next level
        levels = self.building.get_floor_levels()
        suggested_level = max(levels) + 1 if levels else 1
        self.level_spin.setValue(suggested_level)
        
        form.addRow("Floor Level:", self.level_spin)
        
        # Floor name
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.building._generate_floor_name(suggested_level))
        form.addRow("Floor Name:", self.name_edit)
        
        # Update name when level changes
        self.level_spin.valueChanged.connect(
            lambda v: self.name_edit.setText(self.building._generate_floor_name(v))
        )
        
        # Copy from existing floor
        self.copy_check = QCheckBox("Copy layout from floor:")
        form.addRow(self.copy_check)
        
        self.copy_combo = QComboBox()
        self.copy_combo.setEnabled(False)
        
        for level in sorted(levels):
            floor = self.building.get_floor(level)
            if floor:
                self.copy_combo.addItem(f"{floor.name} (Level {level})", level)
        
        self.copy_check.toggled.connect(self.copy_combo.setEnabled)
        form.addRow("", self.copy_combo)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_floor_level(self) -> int:
        """Get the floor level."""
        return self.level_spin.value()
    
    def get_floor_name(self) -> str:
        """Get the floor name."""
        return self.name_edit.text()
    
    def get_copy_from(self) -> Optional[int]:
        """Get the floor to copy from, or None."""
        if self.copy_check.isChecked():
            return self.copy_combo.currentData()
        return None
