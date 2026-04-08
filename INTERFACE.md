# Floor Plan Editor -- Interface Map

## Project Structure

### Entry Point
- **main.py** -- Application entry, creates QApplication and MainWindow

### Core Layer (`core/`)
Pure data models with no GUI dependencies.
- **geometry.py** -- Point, Wall, WallType, WallStyle, WallMaterial, Opening, OpeningType, Room, Furniture, FurnitureType, Fixture, FixtureType, Stair, StairType, FloorPlan, Building
- **level.py** -- Level class for multi-story building support
- **__init__.py** -- Re-exports core types

### GUI Layer (`gui/`)
PyQt6 widgets for the desktop application.
- **main_window.py** -- MainWindow (QMainWindow), toolbar, menus, status bar
- **canvas.py** -- FloorPlanCanvas (QWidget), DrawMode; delegates drawing and event handling to mixins
- **canvas_drawing.py** -- CanvasDrawingMixin: all `_draw_*` methods (walls, rooms, openings, furniture, fixtures, stairs, measurements, grid)
- **canvas_events.py** -- CanvasEventsMixin: all `_handle_*` click methods, selection, room creation, object placement, deletion
- **properties_panel.py** -- Properties panel for selected objects
- **object_selection.py** -- SelectableObject, ObjectTransformHandler, TransformMode
- **object_library.py** -- Furniture/fixture/stair catalog browser
- **floor_selector.py** -- Multi-floor navigation widget
- **viewer_3d.py** -- 3D visualization widget
- **__init__.py** -- GUI package init

### Utils Layer (`utils/`)
- **undo_commands.py** -- Command pattern: ObjectState, TransformObjectCommand, RemoveObjectCommand
- **undo_stack.py** -- UndoStack for undo/redo
- **export.py** -- File export utilities
- **roomplan_importer.py** -- Import from Apple RoomPlan JSON
- **measurements.py** -- MeasurementTool and Measurement classes
- **transforms.py** -- Geometric transform helpers
- **annotations.py** -- Annotation support
- **clipboard.py** -- Copy/paste support
- **logging_config.py** -- Logging setup
- **__init__.py** -- Re-exports AppConfig, format_dimension

### Tests (`tests/`)
- **test_geometry.py** -- pytest unit tests for core/geometry.py (Point, Wall, Opening, FloorPlan, Building)
- **test_file_load.py** -- File loading tests
- **test_roomplan_import.py** -- RoomPlan import tests
- **test_installation.py** -- Installation verification
- **test_references.py** -- Cross-reference tests

### Scripts (`scripts/`)
- **generate_screenshots.py** -- Screenshot generation
- **debug/analyze_corners.py** -- Corner gap analysis for iPhone scans
- **debug/visualize_wall_order.py** -- Wall connectivity visualization
- **debug/debug_rotation.py** -- Rotation extraction debugging

### Data (`data/`)
- **examples/** -- Example .floorplan files and creation scripts
