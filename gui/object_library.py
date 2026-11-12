"""
Object library panel for browsing and placing architectural objects.

Provides a catalog of furniture, fixtures, stairs, and other objects
that can be added to the floor plan.
"""

import logging
from typing import Dict, List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox,
    QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt

from core import (
    Point, Furniture, FurnitureType, Fixture, FixtureType,
    Stair, StairType
)

logger = logging.getLogger(__name__)


from core.catalog import FURNITURE_CATALOG, FIXTURE_CATALOG, STAIR_CATALOG  # noqa: E402


class ObjectLibrary(QWidget):
    """
    Object library panel for browsing and selecting objects to place.
    
    Signals:
        object_selected: Emitted when user wants to place an object
    """
    
    object_selected = pyqtSignal(str, object)  # (type, object_data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        logger.info("Object library initialized")
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Set maximum width to prevent panel from being too wide
        self.setMaximumWidth(300)
        
        # Title
        title = QLabel("<b>Object Library</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget for categories
        self.tabs = QTabWidget()
        
        # Furniture tab
        self.furniture_tab = self._create_furniture_tab()
        self.tabs.addTab(self.furniture_tab, "Furniture")
        
        # Fixtures tab
        self.fixtures_tab = self._create_fixtures_tab()
        self.tabs.addTab(self.fixtures_tab, "Fixtures")
        
        # Stairs tab
        self.stairs_tab = self._create_stairs_tab()
        self.tabs.addTab(self.stairs_tab, "Stairs")
        
        layout.addWidget(self.tabs)
        
        # Instructions
        instructions = QLabel(
            "<i>Select an object and click on the canvas to place it.</i>"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 5px; color: gray;")
        layout.addWidget(instructions)
    
    def _create_furniture_tab(self) -> QWidget:
        """Create the furniture tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Category groups
        categories = {
            "Beds": [
                FurnitureType.BED_SINGLE, FurnitureType.BED_DOUBLE,
                FurnitureType.BED_QUEEN, FurnitureType.BED_KING
            ],
            "Seating": [
                FurnitureType.SOFA, FurnitureType.LOVESEAT,
                FurnitureType.CHAIR, FurnitureType.ARMCHAIR
            ],
            "Tables": [
                FurnitureType.TABLE_DINING, FurnitureType.TABLE_COFFEE,
                FurnitureType.TABLE_SIDE, FurnitureType.DESK
            ],
            "Storage": [
                FurnitureType.DRESSER, FurnitureType.NIGHTSTAND,
                FurnitureType.BOOKSHELF, FurnitureType.CABINET,
                FurnitureType.WARDROBE, FurnitureType.TV_STAND
            ]
        }
        
        for category_name, items in categories.items():
            group = self._create_item_group(category_name, items, FURNITURE_CATALOG, "furniture")
            layout.addWidget(group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_fixtures_tab(self) -> QWidget:
        """Create the fixtures tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Category groups
        categories = {
            "Bathroom": [
                FixtureType.TOILET, FixtureType.SINK, FixtureType.SINK_DOUBLE,
                FixtureType.BATHTUB, FixtureType.SHOWER, FixtureType.SHOWER_CORNER,
                FixtureType.VANITY
            ],
            "Kitchen": [
                FixtureType.REFRIGERATOR, FixtureType.STOVE, FixtureType.OVEN,
                FixtureType.DISHWASHER, FixtureType.MICROWAVE, FixtureType.SINK_KITCHEN
            ],
            "Laundry": [
                FixtureType.WASHER, FixtureType.DRYER
            ],
            "HVAC": [
                FixtureType.WATER_HEATER, FixtureType.FURNACE, FixtureType.AC_UNIT
            ]
        }
        
        for category_name, items in categories.items():
            group = self._create_item_group(category_name, items, FIXTURE_CATALOG, "fixture")
            layout.addWidget(group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_stairs_tab(self) -> QWidget:
        """Create the stairs tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        items = list(StairType)
        group = self._create_item_group("Stair Types", items, STAIR_CATALOG, "stair")
        layout.addWidget(group)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_item_group(self, title: str, items: List, catalog: Dict, 
                          object_type: str) -> QGroupBox:
        """Create a group box with items."""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        for item in items:
            if item in catalog:
                name, width, depth = catalog[item]
                
                item_layout = QHBoxLayout()
                
                # Button
                btn = QPushButton(name)
                btn.setToolTip(f"{width}\" × {depth}\"")
                btn.clicked.connect(
                    lambda checked, i=item, w=width, d=depth, t=object_type: 
                    self._place_object(t, i, w, d)
                )
                item_layout.addWidget(btn)
                
                # Dimensions label
                dims_label = QLabel(f"{width}×{depth}\"")
                dims_label.setStyleSheet("color: gray; font-size: 10px;")
                dims_label.setMaximumWidth(60)
                item_layout.addWidget(dims_label)
                
                layout.addLayout(item_layout)
        
        group.setLayout(layout)
        return group
    
    def _place_object(self, object_type: str, item_type, width: float, depth: float):
        """Signal that user wants to place an object."""
        object_data = {
            'type': item_type,
            'width': width,
            'depth': depth
        }
        
        self.object_selected.emit(object_type, object_data)
        logger.info(f"Selected {object_type}: {item_type.value}")

