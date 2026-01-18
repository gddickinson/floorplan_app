"""
Main application window for the floor plan editor.

Provides the primary interface with menus, toolbars, canvas, and status bar.
"""

import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QVBoxLayout, QWidget, QDockWidget,
    QInputDialog, QDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from core import FloorPlan, Building, WallType
from utils import (
    AppConfig, UndoStack, AddWallCommand, RemoveWallCommand,
    AddOpeningCommand, RemoveOpeningCommand, AddRoomCommand,
    RemoveRoomCommand, get_floor_plan_statistics, format_statistics,
    get_clipboard
)
from .canvas import FloorPlanCanvas, DrawMode
from .properties_panel import PropertiesPanel
from .object_library import ObjectLibrary
from .viewer_3d import Simple3DViewer
from .floor_selector import FloorSelector

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Provides the complete interface for creating and editing floor plans,
    including file operations, drawing tools, and view controls.
    """
    
    def __init__(self):
        super().__init__()
        
        self.current_file: Optional[Path] = None
        self.is_modified = False
        
        # Create the building with a ground floor
        self.building = Building(name="New Building")
        # Get the ground floor that was auto-created
        self.floor_plan = self.building.get_floor(0)
        
        # IMPORTANT: Ensure the floor plan reference is the same object
        # that the building has in its floors dictionary
        if self.floor_plan is None:
            # If somehow no floor 0 exists, create it
            self.floor_plan = FloorPlan(name="Ground Floor", floor_level=0)
            self.building.add_floor(self.floor_plan)
        
        # Create canvas with the floor plan
        self.canvas = FloorPlanCanvas(self.floor_plan)
        
        # Create undo stack
        self.undo_stack = UndoStack()
        
        # Create properties panel
        self.properties_panel = PropertiesPanel()
        self.properties_panel.set_floor_plan(self.floor_plan)
        
        # Create object library
        self.object_library = ObjectLibrary()
        
        # Create 3D viewer
        self.viewer_3d = Simple3DViewer()
        self.viewer_3d.set_building(self.building)
        
        # Create floor selector
        self.floor_selector = FloorSelector()
        self.floor_selector.set_building(self.building)
        
        # Get clipboard
        self.clipboard = get_clipboard()
        
        logger.info(f"Main window initialized with building: {self.building.name}")
        logger.info(f"Floor plan: {self.floor_plan.name}, walls: {len(self.floor_plan.walls)}")
        
        # Setup UI
        self._setup_ui()
        self._create_dock_widgets()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_status_bar()
        self._connect_signals()
        
        # Set initial state
        self.setWindowTitle("Floor Plan Editor - Untitled")
        self.resize(1400, 900)
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Set canvas as central widget
        self.setCentralWidget(self.canvas)
    
    def _create_actions(self):
        """Create all actions for menus and toolbars."""
        # File actions
        self.new_action = QAction("&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.setStatusTip("Create a new floor plan")
        self.new_action.triggered.connect(self.new_file)
        
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setStatusTip("Open an existing floor plan")
        self.open_action.triggered.connect(self.open_file)
        
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setStatusTip("Save the current floor plan")
        self.save_action.triggered.connect(self.save_file)
        
        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.setStatusTip("Save the floor plan with a new name")
        self.save_as_action.triggered.connect(self.save_file_as)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)
        
        # Edit actions
        self.delete_action = QAction("&Delete", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.setStatusTip("Delete selected item")
        self.delete_action.triggered.connect(self.delete_selected)
        
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setStatusTip("Undo last action")
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setStatusTip("Redo last undone action")
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        
        self.copy_action = QAction("&Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.setStatusTip("Copy selected object")
        self.copy_action.triggered.connect(self.copy_selected)
        
        self.paste_action = QAction("&Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.setStatusTip("Paste copied object")
        self.paste_action.triggered.connect(self.paste_object)
        self.paste_action.setEnabled(False)
        
        # View actions
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.setStatusTip("Zoom in")
        self.zoom_in_action.triggered.connect(lambda: self.canvas.zoom(120))
        
        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.setStatusTip("Zoom out")
        self.zoom_out_action.triggered.connect(lambda: self.canvas.zoom(-120))
        
        self.fit_action = QAction("&Fit to View", self)
        self.fit_action.setShortcut(QKeySequence("Ctrl+0"))
        self.fit_action.setStatusTip("Fit entire floor plan in view")
        self.fit_action.triggered.connect(self.canvas.fit_to_view)
        
        self.toggle_grid_action = QAction("Show &Grid", self)
        self.toggle_grid_action.setCheckable(True)
        self.toggle_grid_action.setChecked(True)
        self.toggle_grid_action.setShortcut(QKeySequence("Ctrl+G"))
        self.toggle_grid_action.setStatusTip("Toggle grid display")
        self.toggle_grid_action.triggered.connect(self.toggle_grid)
        
        self.toggle_dimensions_action = QAction("Show &Dimensions", self)
        self.toggle_dimensions_action.setCheckable(True)
        self.toggle_dimensions_action.setChecked(True)
        self.toggle_dimensions_action.setShortcut(QKeySequence("Ctrl+D"))
        self.toggle_dimensions_action.setStatusTip("Toggle dimension display")
        self.toggle_dimensions_action.triggered.connect(self.toggle_dimensions)
        
        # Tool actions
        self.select_action = QAction("&Select", self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)
        self.select_action.setShortcut(QKeySequence("S"))
        self.select_action.setStatusTip("Select and edit objects")
        self.select_action.triggered.connect(lambda: self.set_tool(DrawMode.SELECT))
        
        self.draw_wall_action = QAction("Draw &Wall", self)
        self.draw_wall_action.setCheckable(True)
        self.draw_wall_action.setShortcut(QKeySequence("W"))
        self.draw_wall_action.setStatusTip("Draw walls")
        self.draw_wall_action.triggered.connect(lambda: self.set_tool(DrawMode.DRAW_WALL))
        
        self.add_door_action = QAction("Add &Door", self)
        self.add_door_action.setCheckable(True)
        self.add_door_action.setShortcut(QKeySequence("D"))
        self.add_door_action.setStatusTip("Add doors to walls")
        self.add_door_action.triggered.connect(lambda: self.set_tool(DrawMode.ADD_DOOR))
        
        self.add_window_action = QAction("Add Wi&ndow", self)
        self.add_window_action.setCheckable(True)
        self.add_window_action.setShortcut(QKeySequence("N"))
        self.add_window_action.setStatusTip("Add windows to walls")
        self.add_window_action.triggered.connect(lambda: self.set_tool(DrawMode.ADD_WINDOW))
        
        self.measure_action = QAction("&Measure", self)
        self.measure_action.setCheckable(True)
        self.measure_action.setShortcut(QKeySequence("M"))
        self.measure_action.setStatusTip("Measure distances")
        self.measure_action.triggered.connect(lambda: self.set_tool(DrawMode.MEASURE))
        
        self.create_room_action = QAction("Create &Room", self)
        self.create_room_action.setCheckable(True)
        self.create_room_action.setShortcut(QKeySequence("R"))
        self.create_room_action.setStatusTip("Create room from selected walls")
        self.create_room_action.triggered.connect(lambda: self.set_tool(DrawMode.CREATE_ROOM))
        
        # Group tool actions
        from PyQt6.QtGui import QActionGroup
        self.tool_group = QActionGroup(self)
        self.tool_group.addAction(self.select_action)
        self.tool_group.addAction(self.draw_wall_action)
        self.tool_group.addAction(self.add_door_action)
        self.tool_group.addAction(self.add_window_action)
        self.tool_group.addAction(self.measure_action)
        self.tool_group.addAction(self.create_room_action)
        
        # Analysis actions
        self.statistics_action = QAction("Show &Statistics", self)
        self.statistics_action.setShortcut(QKeySequence("Ctrl+I"))
        self.statistics_action.setStatusTip("Show floor plan statistics")
        self.statistics_action.triggered.connect(self.show_statistics)
        
        self.clear_measurements_action = QAction("Clear Measurements", self)
        self.clear_measurements_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.clear_measurements_action.setStatusTip("Clear all measurements")
        self.clear_measurements_action.triggered.connect(self.clear_measurements)
        
        # Help actions
        self.about_action = QAction("&About", self)
        self.about_action.setStatusTip("About Floor Plan Editor")
        self.about_action.triggered.connect(self.show_about)
    
    def _create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.fit_action)
        view_menu.addSeparator()
        
        # Add dock widget toggles
        self.toggle_properties_action = self.props_dock.toggleViewAction()
        self.toggle_properties_action.setText("Show &Properties Panel")
        view_menu.addAction(self.toggle_properties_action)
        
        self.toggle_library_action = self.library_dock.toggleViewAction()
        self.toggle_library_action.setText("Show &Object Library")
        view_menu.addAction(self.toggle_library_action)
        
        self.toggle_floor_action = self.floor_dock.toggleViewAction()
        self.toggle_floor_action.setText("Show &Floor Selector")
        view_menu.addAction(self.toggle_floor_action)
        
        self.toggle_3d_action = self.viewer_3d_dock.toggleViewAction()
        self.toggle_3d_action.setText("Show &3D View")
        view_menu.addAction(self.toggle_3d_action)
        
        view_menu.addSeparator()
        view_menu.addAction(self.toggle_grid_action)
        view_menu.addAction(self.toggle_dimensions_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.select_action)
        tools_menu.addAction(self.draw_wall_action)
        tools_menu.addAction(self.add_door_action)
        tools_menu.addAction(self.add_window_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.measure_action)
        tools_menu.addAction(self.create_room_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.clear_measurements_action)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        analysis_menu.addAction(self.statistics_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.about_action)
    
    def _create_toolbars(self):
        """Create application toolbars."""
        # Main toolbar
        main_toolbar = QToolBar("Main Toolbar")
        main_toolbar.setMovable(False)
        self.addToolBar(main_toolbar)
        
        main_toolbar.addAction(self.new_action)
        main_toolbar.addAction(self.open_action)
        main_toolbar.addAction(self.save_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.undo_action)
        main_toolbar.addAction(self.redo_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.select_action)
        main_toolbar.addAction(self.draw_wall_action)
        main_toolbar.addAction(self.add_door_action)
        main_toolbar.addAction(self.add_window_action)
        main_toolbar.addAction(self.measure_action)
        main_toolbar.addAction(self.create_room_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.zoom_in_action)
        main_toolbar.addAction(self.zoom_out_action)
        main_toolbar.addAction(self.fit_action)
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _create_dock_widgets(self):
        """Create dock widgets."""
        # Properties panel
        self.props_dock = QDockWidget("Properties", self)
        self.props_dock.setWidget(self.properties_panel)
        self.props_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.props_dock)
        
        # Object library
        self.library_dock = QDockWidget("Object Library", self)
        self.library_dock.setWidget(self.object_library)
        self.library_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.library_dock)
        
        # Floor selector
        self.floor_dock = QDockWidget("Floor Selector", self)
        self.floor_dock.setWidget(self.floor_selector)
        self.floor_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.floor_dock)
        
        # 3D viewer (initially hidden, shown when requested)
        self.viewer_3d_dock = QDockWidget("3D View", self)
        self.viewer_3d_dock.setWidget(self.viewer_3d)
        self.viewer_3d_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.viewer_3d_dock)
        self.viewer_3d_dock.hide()  # Hidden by default
        
        # Connect visibility changed signal to refresh 3D view
        self.viewer_3d_dock.visibilityChanged.connect(self._on_3d_view_visibility_changed)
    
    def _connect_signals(self):
        """Connect signals from canvas and other widgets."""
        self.canvas.plan_modified.connect(self.on_plan_modified)
        self.canvas.status_message.connect(self.status_bar.showMessage)
        self.canvas.selection_changed.connect(self.on_selection_changed)
        self.properties_panel.property_changed.connect(self.on_property_changed)
        self.object_library.object_selected.connect(self.on_object_selected)
        self.floor_selector.floor_changed.connect(self.on_floor_changed)
        self.floor_selector.floor_added.connect(self.on_floor_added)
        self.floor_selector.floor_removed.connect(self.on_floor_removed)
    
    def set_tool(self, mode: str):
        """Set the current drawing tool."""
        self.canvas.set_draw_mode(mode)
        logger.debug(f"Tool changed to: {mode}")
        
        # If switching to room creation mode, show instructions
        if mode == DrawMode.CREATE_ROOM:
            self.status_bar.showMessage("Click walls to select them for room. Press Enter to create room.")
    
    def undo(self):
        """Undo the last action."""
        if self.undo_stack.undo(self.floor_plan):
            self.canvas.update()
            self.update_undo_actions()
            self.status_bar.showMessage(f"Undid: {self.undo_stack.commands[self.undo_stack.current_index + 1].description()}", 2000)
    
    def redo(self):
        """Redo the last undone action."""
        if self.undo_stack.redo(self.floor_plan):
            self.canvas.update()
            self.update_undo_actions()
            self.status_bar.showMessage(f"Redid: {self.undo_stack.commands[self.undo_stack.current_index].description()}", 2000)
    
    def update_undo_actions(self):
        """Update undo/redo action states."""
        self.undo_action.setEnabled(self.undo_stack.can_undo())
        self.redo_action.setEnabled(self.undo_stack.can_redo())
        self.undo_action.setText(self.undo_stack.get_undo_text())
        self.redo_action.setText(self.undo_stack.get_redo_text())
    
    def on_property_changed(self, obj):
        """Handle property changes from the properties panel."""
        self.on_plan_modified()
        self.canvas.update()
    
    def toggle_grid(self):
        """Toggle grid visibility."""
        self.canvas.show_grid = self.toggle_grid_action.isChecked()
        self.canvas.update()
    
    def toggle_dimensions(self):
        """Toggle dimension display."""
        self.canvas.show_dimensions = self.toggle_dimensions_action.isChecked()
        self.canvas.update()
    
    def delete_selected(self):
        """Delete the currently selected item."""
        if self.canvas.selected_wall:
            self.canvas.floor_plan.remove_wall(self.canvas.selected_wall)
            self.canvas.selected_wall = None
            self.on_plan_modified()
            self.canvas.update()
        elif self.canvas.selected_opening:
            self.canvas.floor_plan.remove_opening(self.canvas.selected_opening)
            self.canvas.selected_opening = None
            self.on_plan_modified()
            self.canvas.update()
    
    def on_plan_modified(self):
        """Handle floor plan modifications."""
        self.is_modified = True
        self.update_title()
        # Update 3D view
        if hasattr(self, 'viewer_3d'):
            self.viewer_3d.refresh()
    
    def on_selection_changed(self, obj):
        """Handle selection changes."""
        if obj:
            self.status_bar.showMessage(f"Selected: {obj}")
            self.properties_panel.show_properties(obj)
        else:
            self.status_bar.showMessage("Ready")
            self.properties_panel.show_properties(None)
    
    def show_statistics(self):
        """Show floor plan statistics dialog."""
        stats = get_floor_plan_statistics(self.floor_plan)
        stats_text = format_statistics(stats)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Floor Plan Statistics")
        dialog.resize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(stats_text)
        text_edit.setFontFamily("Courier")
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
    
    def clear_measurements(self):
        """Clear all measurements from the canvas."""
        self.canvas.measurement_tool.clear_measurements()
        self.canvas.update()
        self.status_bar.showMessage("Cleared all measurements", 2000)
    
    def copy_selected(self):
        """Copy the currently selected object to clipboard."""
        # Determine what is selected
        selected = None
        if self.canvas.selected_wall:
            selected = self.floor_plan.get_wall(self.canvas.selected_wall)
        elif self.canvas.selected_opening:
            for opening in self.floor_plan.openings:
                if opening.id == self.canvas.selected_opening:
                    selected = opening
                    break
        elif self.canvas.selected_room:
            for room in self.floor_plan.rooms:
                if room.id == self.canvas.selected_room:
                    selected = room
                    break
        elif self.canvas.selected_furniture:
            selected = self.floor_plan.get_furniture(self.canvas.selected_furniture)
        elif self.canvas.selected_fixture:
            selected = self.floor_plan.get_fixture(self.canvas.selected_fixture)
        elif self.canvas.selected_stair:
            selected = self.floor_plan.get_stair(self.canvas.selected_stair)
        
        if selected:
            self.clipboard.copy(selected)
            self.paste_action.setEnabled(True)
            self.status_bar.showMessage(f"Copied to clipboard: {self.clipboard.get_description()}", 2000)
        else:
            self.status_bar.showMessage("Nothing selected to copy", 2000)
    
    def paste_object(self):
        """Paste object from clipboard."""
        if not self.clipboard.has_content():
            self.status_bar.showMessage("Nothing to paste", 2000)
            return
        
        # Paste with offset so user can see the new object
        from core import Point
        offset = Point(24, 24)  # 2 feet offset
        new_objects = self.clipboard.paste(offset)
        
        # Add to floor plan
        for obj in new_objects:
            from core import Wall, Furniture, Fixture, Stair
            if isinstance(obj, Wall):
                self.floor_plan.add_wall(obj)
            elif isinstance(obj, Furniture):
                self.floor_plan.add_furniture(obj)
            elif isinstance(obj, Fixture):
                self.floor_plan.add_fixture(obj)
            elif isinstance(obj, Stair):
                self.floor_plan.add_stair(obj)
        
        self.on_plan_modified()
        self.canvas.update()
        self.status_bar.showMessage(f"Pasted: {self.clipboard.get_description()}", 2000)
    
    def on_object_selected(self, object_type: str, object_data: dict):
        """Handle object selection from library."""
        self.canvas.set_pending_object(object_type, object_data)
        self.status_bar.showMessage(f"Click to place {object_type}. Press Escape to cancel.")
    
    def on_floor_changed(self, level: int):
        """Handle floor change from floor selector."""
        if not self.building:
            return
        
        new_floor = self.building.get_floor(level)
        if new_floor:
            self.floor_plan = new_floor
            self.canvas.set_floor_plan(new_floor)
            self.properties_panel.set_floor_plan(new_floor)
            self.viewer_3d.set_building(self.building)
            self.viewer_3d.canvas.set_current_floor(new_floor)
            self.viewer_3d.canvas.update()
            
            self.status_bar.showMessage(f"Switched to {new_floor.name}", 2000)
            logger.info(f"Changed to floor level {level}: {new_floor.name}")
    
    def on_floor_added(self, level: int):
        """Handle floor added event."""
        self.on_plan_modified()
        self.viewer_3d.set_building(self.building)
        self.status_bar.showMessage(f"Added floor level {level}", 2000)
    
    def on_floor_removed(self, level: int):
        """Handle floor removed event."""
        self.on_plan_modified()
        self.viewer_3d.set_building(self.building)
        self.status_bar.showMessage(f"Removed floor level {level}", 2000)
    
    def _on_3d_view_visibility_changed(self, visible):
        """Handle 3D view visibility change."""
        if visible:
            # When 3D view becomes visible, refresh it with current building state
            # Use QTimer to defer the update slightly to ensure widget is fully initialized
            logger.info("3D view became visible, scheduling refresh...")
            QTimer.singleShot(100, self._delayed_3d_refresh)
    
    def _delayed_3d_refresh(self):
        """Delayed refresh of 3D view (called via QTimer)."""
        logger.info("Performing delayed 3D refresh")
        self.viewer_3d.set_building(self.building)
        self.viewer_3d.refresh()
    
    def update_title(self):
        """Update window title."""
        title = "Floor Plan Editor - "
        if self.current_file:
            title += self.current_file.name
        else:
            title += "Untitled"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)
    
    def new_file(self):
        """Create a new floor plan."""
        if not self.check_save_changes():
            return
        
        # Create a new building with a fresh ground floor
        self.building = Building(name="New Building")
        self.floor_plan = self.building.get_floor(0)  # Get the auto-created ground floor
        
        # Update all components
        self.canvas.set_floor_plan(self.floor_plan)
        self.properties_panel.set_floor_plan(self.floor_plan)
        
        # Update 3D viewer
        self.viewer_3d.set_building(self.building)
        
        # Update floor selector
        self.floor_selector.set_building(self.building)
        
        # Reset file tracking
        self.current_file = None
        self.is_modified = False
        self.update_title()
        
        logger.info("New floor plan created")
        logger.info(f"  Building: {self.building.name}")
        logger.info(f"  Floor: {self.floor_plan.name} (Level {self.floor_plan.floor_level})")
        
        self.status_bar.showMessage("New floor plan created", 2000)
    
    def open_file(self):
        """Open an existing floor plan."""
        if not self.check_save_changes():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Floor Plan",
            str(Path.home()),
            AppConfig.FILE_FILTER
        )
        
        if file_path:
            try:
                # Load the floor plan from file
                loaded_floor_plan = FloorPlan.load_from_file(file_path)
                
                # Update the building with the loaded floor plan
                # Replace the ground floor with the loaded plan
                self.building.floors[loaded_floor_plan.floor_level] = loaded_floor_plan
                
                # Update our reference to point to the loaded floor plan
                self.floor_plan = loaded_floor_plan
                
                # Update all components
                self.canvas.set_floor_plan(self.floor_plan)
                self.properties_panel.set_floor_plan(self.floor_plan)
                
                # Update 3D viewer with the building
                self.viewer_3d.set_building(self.building)
                
                # Update floor selector
                self.floor_selector.set_building(self.building)
                self.floor_selector.set_current_floor(loaded_floor_plan.floor_level)
                
                # Update file tracking
                self.current_file = Path(file_path)
                self.is_modified = False
                self.update_title()
                
                logger.info(f"Opened floor plan: {file_path}")
                logger.info(f"  Loaded: {loaded_floor_plan.name} (Level {loaded_floor_plan.floor_level})")
                logger.info(f"  Walls: {len(loaded_floor_plan.walls)}, Rooms: {len(loaded_floor_plan.rooms)}")
                logger.info(f"  Building now has {len(self.building.floors)} floor(s)")
                
                self.status_bar.showMessage(f"Opened: {Path(file_path).name}", 3000)
                
            except Exception as e:
                logger.error(f"Failed to open file: {e}")
                QMessageBox.critical(
                    self,
                    "Error Opening File",
                    f"Could not open file:\n{str(e)}"
                )
    
    def save_file(self):
        """Save the current floor plan."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save the floor plan with a new name."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Floor Plan As",
            str(Path.home() / "untitled.floorplan"),
            AppConfig.FILE_FILTER
        )
        
        if file_path:
            # Ensure correct extension
            file_path = Path(file_path)
            if file_path.suffix != AppConfig.FILE_EXTENSION:
                file_path = file_path.with_suffix(AppConfig.FILE_EXTENSION)
            
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: Path):
        """Save floor plan to specified file."""
        try:
            self.floor_plan.save_to_file(str(file_path))
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            self.status_bar.showMessage(f"Saved to {file_path.name}", 3000)
            logger.info(f"Saved floor plan: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            QMessageBox.critical(
                self,
                "Error Saving File",
                f"Could not save file:\n{str(e)}"
            )
    
    def check_save_changes(self) -> bool:
        """
        Check if there are unsaved changes and prompt user.
        
        Returns:
            True if it's safe to proceed (saved or discarded), False otherwise
        """
        if not self.is_modified:
            return True
        
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "Do you want to save your changes?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Save:
            self.save_file()
            return not self.is_modified  # Return False if save was cancelled
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.check_save_changes():
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Floor Plan Editor",
            "<h2>Floor Plan Editor</h2>"
            "<p>A modular, extensible application for creating architectural floor plans.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Interactive 2D wall drawing</li>"
            "<li>Door and window placement (22+ types)</li>"
            "<li>Room creation and area calculation</li>"
            "<li>Complete furniture library (18 types)</li>"
            "<li>Kitchen & bathroom fixtures (15 types)</li>"
            "<li>Stairs and multi-level buildings</li>"
            "<li><b>3D Visualization</b> with isometric view</li>"
            "<li><b>Multi-Floor Buildings</b> with floor navigation</li>"
            "<li>Measurement tools</li>"
            "<li>Grid snapping</li>"
            "<li>Undo/Redo support</li>"
            "<li>Property editing</li>"
            "<li>Statistics and analysis</li>"
            "<li>Zoom, pan, and fit-to-view</li>"
            "<li>Save/load floor plans</li>"
            "<li>Copy/paste objects</li>"
            "</ul>"
            "<p>Version 1.3 - Now with 3D and Multi-Level Support!</p>"
            "<p>Built with PyQt6 and Python</p>"
        )
    
    def keyPressEvent(self, event):
        """Handle key press events in main window."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.canvas.draw_mode == DrawMode.CREATE_ROOM and self.canvas.room_walls_selection:
                # Prompt for room name
                name, ok = QInputDialog.getText(
                    self, "Create Room", "Enter room name:",
                    text=f"Room {len(self.floor_plan.rooms) + 1}"
                )
                if ok and name:
                    room = self.canvas.create_room_from_selection(name)
                    if room:
                        self.on_plan_modified()
                return
        
        super().keyPressEvent(event)
