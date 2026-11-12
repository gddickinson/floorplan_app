# Floor Plan Editor -- Interface Map

## Project Structure

### Entry Point
- **main.py** -- Application entry, creates QApplication and MainWindow

### Core Layer (`core/`)
Pure data models with no GUI dependencies.
- **geometry.py** -- Point, Wall, WallType, WallStyle, WallMaterial, Opening, OpeningType, Room, Furniture, FurnitureType, Fixture, FixtureType, Stair, StairType, FloorPlan, Building
- **level.py** -- Level class for multi-story building support
- **room_geometry.py** -- room_outline / room_polygon (walls joined in walking order, corners at centre-line intersections), polygon_area, point_in_polygon, polygon_label_point
- **snapping.py** -- GRID_SIZE, SNAP_TOLERANCE, snap_to_grid, find_snap_point, point_near_line, wall_at_point, opening_position, opening_center (used by gui/canvas*.py)
- **plan_stats.py** -- calculate_room_area, calculate_perimeter, calculate_total_wall_length, calculate_total_area, get_floor_plan_statistics, format_statistics (re-exported by utils/measurements.py)
- **units.py** -- format_dimension, inches_to_feet, feet_to_inches (re-exported by utils/logging_config.py)
- **config.py** -- AppConfig constants (re-exported by utils/logging_config.py)
- **catalog.py** -- FURNITURE_CATALOG, FIXTURE_CATALOG, STAIR_CATALOG (used by gui/object_library.py)
- **demo_plans.py** -- create_demo_house (README screenshots), create_test_floor
- **__init__.py** -- Re-exports core types
- Everything in core/ is Qt-free (the web app imports it without PyQt6).

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
- **measurements.py** -- MeasurementTool and Measurement classes; re-exports the statistics functions of core/plan_stats.py
- **transforms.py** -- Geometric transform helpers
- **annotations.py** -- Annotation support
- **clipboard.py** -- Copy/paste support
- **logging_config.py** -- Logging setup
- **__init__.py** -- Re-exports AppConfig, format_dimension

### Web (`web/`, browser editor; see README "Web version")
- **app.py** -- FastAPI app: GET /api/info, /api/catalog, /api/examples, /api/examples/{name}; POST /api/analyze (Python core on a plan); STATIC_ENDPOINTS
- **catalog.py** -- EXAMPLES (from core/demo_plans.py, stable ids), catalog() (library, enums, settings)
- **static/index.html, core.js, style.css** -- shared web kit (router, api(), theme); style_app.css = project styles
- **static/main.js** -- registers pages; **static_api.js** -- static-site api() from exported JSON
- **static/model.js** -- .floorplan model: fromDict/toDict (FloorPlan.from_dict/to_dict), ENUMS, isDoor/isWindow, make* constructors
- **static/units.js** -- formatDimension, fmt1 (Python .1f), pyRound (Python round)
- **static/geometry.js** -- port of core/snapping.py + core/room_geometry.py; footprint/containsPoint for objects; extent
- **static/stats.js** -- port of core/plan_stats.py (statistics, formatStatistics, roomArea, roomPerimeter)
- **static/geometry.test.mjs** -- node test against tests/fixtures/geometry_fixture.json
- **static/editor.js** -- editor page (#/editor); **editor_state.js** -- state, undo, view transform, autosave
- **static/editor_render.js** -- SVG plan renderer; **editor_symbols.js** -- door/window/object symbols, style colours
- **static/editor_tools.js** -- pointer tools (select/move/resize/rotate, wall, door/window, room, measure, place, pan)
- **static/editor_props.js** -- properties + statistics panels; **editor_io.js** -- open/save .floorplan, SVG/PNG export
- **static/mesh3d.js** -- 3D mesh (walls with openings, floors, objects, stairs); **view3d.js** -- raw WebGL viewer
- **static/home.js, examples.js, about.js, preview.js** -- other pages and plan thumbnails
- **../run_web.py** -- uvicorn on 127.0.0.1:8217

### Tests (`tests/`)
- **test_geometry.py** -- pytest unit tests for core/geometry.py (Point, Wall, Opening, FloorPlan, Building)
- **test_file_load.py** -- File loading tests
- **test_roomplan_import.py** -- RoomPlan import tests
- **test_installation.py** -- Installation verification
- **test_references.py** -- Cross-reference tests
- **test_room_geometry.py** -- room outline/area/perimeter for walls in any order, reversed, T-junctions
- **test_opening_kinds.py** -- OpeningType.is_door / is_window, statistics counts
- **test_format_dimension.py** -- feet-inches labels (negative values, rounding carry)
- **test_object_resize.py** -- corner-handle resize (needs PyQt6)
- **test_geometry_fixture.py** -- the JS fixture is current
- **test_web.py** -- web API, static build, node tests, web <-> desktop file round trip
- **fixtures/geometry_fixture.json** -- Python results for the JS port

### Scripts (`scripts/`)
- **generate_screenshots.py** -- Screenshot generation (desktop GUI)
- **make_geometry_fixture.py** -- writes tests/fixtures/geometry_fixture.json
- **build_static.py** -- exports the GitHub Pages site to site/
- **screenshots.py** -- Playwright smoke test of web routes + docs/img screenshots
- **debug/analyze_corners.py** -- Corner gap analysis for iPhone scans
- **debug/visualize_wall_order.py** -- Wall connectivity visualization
- **debug/debug_rotation.py** -- Rotation extraction debugging

### Data (`data/`)
- **examples/** -- Example .floorplan files and creation scripts
