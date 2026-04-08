# Floor Plan Editor -- Roadmap

## Current State
A mature PyQt6 desktop application with clean three-layer architecture: `core/` (geometry.py, level.py -- pure data models), `gui/` (canvas, main_window, object_selection, properties_panel, object_library, floor_selector, viewer_3d), `utils/` (undo/redo commands, export, roomplan_importer, measurements, transforms, annotations, clipboard). Has tests, example data, an iOS companion app (RoomScanner), and comprehensive documentation including `ARCHITECTURE.md`. The most well-organized project in this collection.

## Short-term Improvements
- [x] Expand test coverage -- added pytest unit tests for `core/geometry.py` (Point, Wall, Opening, FloorPlan, Building) with 24 test cases
- [ ] Add integration tests for save/load round-trips (`.floorplan` JSON format)
- [ ] Add CI configuration (GitHub Actions) to run tests and linting on each push
- [ ] Add type checking with mypy -- the core layer should be fully typed
- [x] Move `tests/analyze_corners.py`, `tests/visualize_wall_order.py`, and `tests/debug_rotation.py` to `scripts/debug/` directory -- they are not tests

## Feature Enhancements
- [ ] Implement DXF/DWG import/export for CAD interoperability
- [ ] Add dimension auto-calculation and display for walls (length annotations)
- [ ] Implement room area auto-calculation displayed inside room labels
- [ ] Add a material/finish library (flooring, wall colors, textures)
- [ ] Improve `gui/viewer_3d.py` -- add textured walls, lighting, and walkthrough mode
- [ ] Add collaborative editing via file-based sync or real-time protocol

## Long-term Vision
- [ ] Implement a web-based version (Three.js frontend) sharing `core/` data models
- [ ] Add AR mode -- overlay floor plan on camera feed using ARKit/ARCore
- [ ] Integrate with smart home APIs (HomeKit, SmartThings) for device placement
- [ ] Add energy modeling (window/wall insulation, HVAC layout suggestions)
- [ ] Publish to PyPI and create a Homebrew formula for easy installation

## Technical Debt
- [x] `gui/canvas.py` split into canvas.py (425 lines), canvas_drawing.py (420 lines), canvas_events.py (375 lines) -- drawing logic separated from event handling
- [ ] `utils/undo_stack.py` and `utils/undo_commands.py` could benefit from better documentation of the command pattern
- [ ] `data/examples/` has both `.floorplan` files and Python creation scripts -- clarify which is source of truth
- [ ] `scripts/generate_screenshots.py` depends on GUI state -- make it headless-capable
- [x] Added `pyproject.toml` -- project is now configurable for pytest, mypy, and ruff
- [x] Added `.gitignore`
- [x] Fixed hardcoded path in `scripts/debug/debug_rotation.py`
