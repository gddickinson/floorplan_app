# Floor Plan Editor - Architecture & Extensibility Guide

## Overview

This document provides a technical overview of the floor plan editor's architecture, design patterns, and extension points. Use this as a reference when extending the application or adding new features.

## Design Philosophy

The application follows these core principles:

1. **Separation of Concerns**: Clean boundaries between data (core), presentation (gui), and utilities
2. **Modularity**: Each component has a single, well-defined responsibility
3. **Extensibility**: Easy to add new geometry types, tools, and features
4. **Type Safety**: Dataclasses and type hints throughout
5. **Logging**: Comprehensive activity tracking for debugging
6. **Serialization**: All data structures support JSON serialization

## Architecture Layers

```
┌─────────────────────────────────────────┐
│          main.py (Entry Point)          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│   GUI Layer    │    │   Utils Layer    │
│  (PyQt6 UI)    │    │  (Config/Log)    │
└───────┬────────┘    └──────────────────┘
        │
        │ Uses
        │
┌───────▼────────┐
│   Core Layer   │
│  (Data Model)  │
└────────────────┘
```

### Layer Details

#### Core Layer (`core/`)
**Purpose**: Pure data structures and geometry, no UI dependencies

**Components**:
- `geometry.py`: All geometry classes and floor plan container
  - `Point`: 2D coordinates with distance calculation
  - `Wall`: Line segments with thickness and type
  - `Opening`: Doors, windows, archways on walls
  - `Room`: Named spaces defined by wall sets
  - `FloorPlan`: Container managing all elements

**Key Features**:
- Immutable where possible (dataclasses)
- Complete serialization (to_dict/from_dict)
- UUID-based IDs for all elements
- Unit conversions and measurements
- No external dependencies (pure Python)

**Extension Points**:
- Add new geometry types (e.g., `Furniture`, `Fixture`, `Stair`)
- Add new wall types or opening types (Enums)
- Add 3D coordinates (extend `Point` to `Point3D`)
- Add measurement methods (area, volume, etc.)

#### GUI Layer (`gui/`)
**Purpose**: Interactive interface using PyQt6

**Components**:
- `canvas.py`: Interactive drawing surface
  - Coordinate transformations (world ↔ screen)
  - Event handling (mouse, keyboard)
  - Rendering with QPainter
  - Selection and manipulation
  - Grid snapping logic

- `main_window.py`: Main application window
  - Menus and toolbars
  - File operations
  - Tool management
  - Status updates

**Key Features**:
- Model-View separation (FloorPlan is the model)
- Signal-based communication (Qt signals/slots)
- Modular drawing modes
- Pluggable tools

**Extension Points**:
- Add new drawing modes (e.g., `DrawMode.DRAW_FURNITURE`)
- Add new tools (measurement, annotation, etc.)
- Add property panels (dock widgets)
- Add export dialogs (PDF, PNG, etc.)
- Add 3D view widget

#### Utils Layer (`utils/`)
**Purpose**: Cross-cutting concerns and configuration

**Components**:
- `logging_config.py`: Logging setup and app configuration
  - Centralized logging
  - Application constants
  - Unit conversion helpers
  - Path management

**Extension Points**:
- Add new configuration settings
- Add new utility functions
- Add theme/styling support
- Add user preferences

## Data Flow

### Creating a Wall (User Interaction)
```
User clicks canvas
      ↓
MouseEvent → canvas.mousePressEvent()
      ↓
screen_to_world() converts coordinates
      ↓
find_snap_point() applies snapping
      ↓
Wall created in FloorPlan
      ↓
plan_modified signal emitted
      ↓
Canvas repaints → _draw_wall()
```

### Saving a Floor Plan
```
User clicks Save
      ↓
MainWindow.save_file()
      ↓
FloorPlan.to_dict() serializes all elements
      ↓
json.dump() writes to file
      ↓
Status message and logging
```

### Loading a Floor Plan
```
User clicks Open
      ↓
QFileDialog selects file
      ↓
FloorPlan.load_from_file()
      ↓
FloorPlan.from_dict() deserializes
      ↓
Canvas.set_floor_plan() updates view
      ↓
fit_to_view() and repaint
```

## Key Design Patterns

### 1. Data Class Pattern
All geometry types are dataclasses for clean serialization:

```python
@dataclass
class Wall:
    start: Point
    end: Point
    thickness: float = 6.0
    wall_type: WallType = WallType.INTERIOR
    id: Optional[str] = None
```

Benefits:
- Automatic `__init__`, `__repr__`
- Type hints built-in
- Easy to serialize
- Immutable options

### 2. Factory Pattern
`from_dict()` class methods for deserialization:

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'Wall':
    return cls(
        start=Point.from_dict(data["start"]),
        end=Point.from_dict(data["end"]),
        ...
    )
```

### 3. Signal-Slot Pattern (Qt)
Decoupled communication between components:

```python
# Canvas emits signals
self.plan_modified = pyqtSignal()
self.status_message = pyqtSignal(str)

# MainWindow connects to them
self.canvas.plan_modified.connect(self.on_plan_modified)
self.canvas.status_message.connect(self.status_bar.showMessage)
```

### 4. Coordinate Transform Pattern
Separation of world coordinates (inches) and screen coordinates (pixels):

```python
def world_to_screen(self, point: Point) -> QPointF:
    """Convert world coordinates to screen coordinates."""
    x = point.x * self.scale + self.offset_x + self.width() / 2
    y = point.y * self.scale + self.offset_y + self.height() / 2
    return QPointF(x, y)
```

## Extension Guide

### Adding a New Geometry Type (e.g., Furniture)

1. **Define the class in `core/geometry.py`**:
```python
@dataclass
class Furniture:
    position: Point
    width: float
    depth: float
    rotation: float = 0.0
    furniture_type: str = "chair"
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {...}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Furniture':
        return cls(...)
```

2. **Add to FloorPlan container**:
```python
class FloorPlan:
    ...
    furniture: List[Furniture] = field(default_factory=list)
    
    def add_furniture(self, item: Furniture) -> str:
        self.furniture.append(item)
        logger.info(f"Added furniture: {item.id}")
        return item.id
```

3. **Update serialization**:
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        ...
        "furniture": [f.to_dict() for f in self.furniture]
    }
```

4. **Add rendering in `gui/canvas.py`**:
```python
def paintEvent(self, event: QPaintEvent):
    ...
    self._draw_furniture(painter)

def _draw_furniture(self, painter: QPainter):
    for item in self.floor_plan.furniture:
        self._draw_furniture_item(painter, item)
```

5. **Add tool in `gui/main_window.py`**:
```python
self.add_furniture_action = QAction("Add &Furniture", self)
self.add_furniture_action.triggered.connect(
    lambda: self.set_tool(DrawMode.ADD_FURNITURE)
)
```

### Adding a New Drawing Tool

1. **Add mode to `DrawMode` in `gui/canvas.py`**:
```python
class DrawMode:
    ...
    MEASURE_DISTANCE = "measure_distance"
```

2. **Add action in `gui/main_window.py`**:
```python
self.measure_action = QAction("&Measure", self)
self.measure_action.setShortcut(QKeySequence("M"))
self.measure_action.triggered.connect(
    lambda: self.set_tool(DrawMode.MEASURE_DISTANCE)
)
```

3. **Handle clicks in `canvas.py`**:
```python
def mousePressEvent(self, event: QMouseEvent):
    ...
    elif self.draw_mode == DrawMode.MEASURE_DISTANCE:
        self._handle_measure_click(snap_pos)

def _handle_measure_click(self, point: Point):
    if not self.measure_start:
        self.measure_start = point
    else:
        distance = self.measure_start.distance_to(point)
        self.status_message.emit(f"Distance: {format_dimension(distance)}")
        self.measure_start = None
```

### Preparing for 3D

The architecture is ready for 3D expansion:

1. **Extend Point to Point3D**:
```python
@dataclass
class Point3D:
    x: float
    y: float
    z: float = 0.0  # Default to ground level
```

2. **Add height to walls**:
```python
@dataclass
class Wall:
    ...
    height: float = 96.0  # Default 8 feet
```

3. **Create 3D view widget**:
```python
# In gui/view3d.py
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

class FloorPlan3DView(QOpenGLWidget):
    def __init__(self, floor_plan: FloorPlan):
        ...
    
    def initializeGL(self):
        # Setup OpenGL
        
    def paintGL(self):
        # Render 3D scene
```

4. **Add to main window**:
```python
self.view_3d = FloorPlan3DView(self.floor_plan)
dock = QDockWidget("3D View", self)
dock.setWidget(self.view_3d)
self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
```

## Testing Strategy

### Unit Tests (To Be Added)
```python
# tests/test_geometry.py
def test_wall_length():
    wall = Wall(Point(0, 0), Point(3, 4))
    assert abs(wall.length() - 5.0) < 0.01

def test_serialization():
    plan = FloorPlan(name="Test")
    plan.add_wall(Wall(Point(0, 0), Point(10, 0)))
    
    data = plan.to_dict()
    loaded = FloorPlan.from_dict(data)
    
    assert len(loaded.walls) == 1
    assert loaded.name == "Test"
```

### Integration Tests
```python
# tests/test_gui.py
def test_wall_drawing(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    # Simulate wall drawing
    window.canvas.set_draw_mode(DrawMode.DRAW_WALL)
    # ... simulate clicks
    
    assert len(window.floor_plan.walls) == 1
```

## Performance Considerations

### Current Performance
- Suitable for typical residential floor plans (50-200 walls)
- Real-time rendering on modern hardware
- JSON serialization is fast enough (<1ms for typical plans)

### Optimization Opportunities
1. **Spatial Indexing**: Add R-tree for large plans
2. **Caching**: Cache transformed coordinates
3. **Level of Detail**: Simplify rendering when zoomed out
4. **Batching**: Batch similar drawing operations

### Memory Usage
- Typical residential plan: <1 MB in memory
- File size: <100 KB for typical plans (JSON is verbose but compressible)

## Logging Strategy

### Log Levels
- **DEBUG**: Detailed flow, coordinates, calculations
- **INFO**: User actions, file operations, major events
- **WARNING**: Unexpected but recoverable situations
- **ERROR**: Failures, exceptions

### Log Categories
```python
logger = logging.getLogger(__name__)

# Use module-specific loggers
logger = logging.getLogger('core.geometry')
logger = logging.getLogger('gui.canvas')
logger = logging.getLogger('gui.main_window')
```

### Example Log Output
```
2025-01-17 14:30:15 - gui.canvas - INFO - Canvas initialized
2025-01-17 14:30:20 - core.geometry - INFO - Added wall: abc-123 (120.0 inches)
2025-01-17 14:30:25 - core.geometry - INFO - Added door: def-456
2025-01-17 14:30:30 - gui.main_window - INFO - Saved floor plan: my_house.floorplan
```

## Configuration Management

### Current Approach
Static configuration in `utils/logging_config.py`:

```python
class AppConfig:
    DEFAULT_WALL_THICKNESS = 6.0
    DEFAULT_DOOR_WIDTH = 36.0
    GRID_SIZE = 12.0
    ...
```

### Future: User Preferences
```python
# Add to utils/preferences.py
class UserPreferences:
    @staticmethod
    def load() -> Dict[str, Any]:
        config_file = AppConfig.get_config_dir() / "preferences.json"
        if config_file.exists():
            return json.load(open(config_file))
        return {}
    
    @staticmethod
    def save(prefs: Dict[str, Any]):
        config_file = AppConfig.get_config_dir() / "preferences.json"
        json.dump(prefs, open(config_file, 'w'), indent=2)
```

## Best Practices for Extension

1. **Follow Existing Patterns**: Match the style of existing code
2. **Add Logging**: Log all significant operations
3. **Type Hints**: Use type hints consistently
4. **Docstrings**: Document classes and non-trivial methods
5. **Serialization**: Support to_dict/from_dict for new types
6. **Signals**: Use Qt signals for UI updates
7. **Unit Tests**: Add tests for new functionality
8. **Incremental**: Build features incrementally

## Common Gotchas

1. **Coordinate Systems**: Remember to convert between world and screen coordinates
2. **Qt Event Loop**: Long operations should be threaded or use QTimer
3. **Signal Loops**: Be careful of signal loops (A emits → B updates → A emits)
4. **Float Precision**: Use tolerances when comparing floating-point coordinates
5. **File Paths**: Use `pathlib.Path` for cross-platform compatibility

## Future Development Roadmap

### Phase 2: Enhanced 2D
- [ ] Room area calculations
- [ ] Furniture library
- [ ] Dimensioning tools
- [ ] Text annotations
- [ ] Print/export to PDF

### Phase 3: 3D Visualization
- [ ] 3D view window
- [ ] Wall extrusion
- [ ] Basic rendering
- [ ] Camera controls

### Phase 4: Advanced Features
- [ ] Multi-story buildings
- [ ] Electrical/plumbing layers
- [ ] Material assignments
- [ ] Cost estimation
- [ ] Building code validation

## Resources

- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Python Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Logging Best Practices: https://docs.python.org/3/howto/logging.html

## Summary

This architecture provides:
✓ Clean separation of concerns
✓ Easy to understand and modify
✓ Extensible for new features
✓ Ready for 3D expansion
✓ Production-ready logging
✓ Robust serialization

The modular design means you can:
- Add new geometry types without touching the GUI
- Add new tools without modifying core classes
- Switch rendering backends if needed
- Add export formats easily
- Scale to larger, more complex plans

Happy extending! 🚀
