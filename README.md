# Floor Plan Editor

A modular, extensible Python application for creating and editing 2D architectural floor plans. Built with PyQt6 and designed with clean separation of concerns for easy expansion to 3D and additional features.

## Features

### Current (v1.0)
- **Interactive Drawing**: Click-to-draw walls with automatic grid snapping
- **Door & Window Placement**: Add openings to walls with visual markers
- **Selection & Editing**: Select and delete walls and openings
- **Visual Feedback**: 
  - Real-time dimension display
  - Grid overlay (toggleable)
  - Snap-to-grid and snap-to-endpoints
- **View Controls**:
  - Zoom in/out with mouse wheel
  - Pan with middle mouse button
  - Fit-to-view
- **File Operations**: Save and load floor plans (JSON format)
- **Comprehensive Logging**: All operations logged for debugging and auditing

### Planned Features
- 3D visualization and modeling
- Room labeling and area calculation
- Export to PDF/PNG
- Measurement tools
- Furniture placement
- Multiple floors/stories

## Installation

### Requirements
- Python 3.8+
- PyQt6

### Setup
```bash
# Clone or download the repository
cd floorplan_app

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Quick Start
1. Launch the application: `python main.py`
2. Press **W** or select "Draw Wall" from the toolbar
3. Click to place wall start point, click again to place end point
4. Press **D** to add doors or **N** to add windows
5. Click on walls to place openings
6. Press **S** to select objects (or Delete to remove them)
7. Save your floor plan with **Ctrl+S**

### Keyboard Shortcuts
- **S**: Select tool
- **W**: Draw wall tool
- **D**: Add door tool
- **N**: Add window tool
- **Delete**: Delete selected object
- **Escape**: Cancel current operation
- **G**: Toggle grid
- **Ctrl+G**: Toggle grid (menu)
- **Ctrl+D**: Toggle dimensions
- **Ctrl+0**: Fit to view
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+N**: New file
- **Ctrl+O**: Open file
- **Ctrl+S**: Save
- **Ctrl+Shift+S**: Save As

### Mouse Controls
- **Left Click**: Place points, select objects
- **Middle Mouse + Drag**: Pan view
- **Mouse Wheel**: Zoom in/out
- **Right Click**: (Reserved for context menus)

## Architecture

The application follows a modular design for easy expansion:

```
floorplan_app/
├── core/                  # Core data structures and geometry
│   ├── __init__.py
│   └── geometry.py       # Point, Wall, Opening, Room, FloorPlan
├── gui/                   # User interface components
│   ├── __init__.py
│   ├── canvas.py         # Interactive drawing canvas
│   └── main_window.py    # Main application window
├── utils/                 # Utilities and configuration
│   ├── __init__.py
│   └── logging_config.py # Logging setup and app config
├── examples/              # Example scripts and floor plans
├── assets/                # Icons and resources
└── main.py               # Application entry point
```

### Core Components

#### `core.geometry`
Defines fundamental building blocks:
- `Point`: 2D coordinates
- `Wall`: Linear wall segments with thickness and type
- `Opening`: Doors, windows, archways
- `Room`: Named spaces defined by walls
- `FloorPlan`: Container for all elements with save/load

#### `gui.canvas`
Interactive drawing surface:
- Handles user input (mouse, keyboard)
- Renders floor plan elements
- Manages view transforms (zoom, pan)
- Grid snapping and visual feedback

#### `gui.main_window`
Main application interface:
- Menu bar and toolbars
- File operations
- Tool selection
- Status updates

#### `utils`
Configuration and utilities:
- Logging setup
- Application settings
- Unit conversions
- Dimension formatting

## File Format

Floor plans are saved as JSON files with `.floorplan` extension:

```json
{
  "name": "My House",
  "scale": 2.0,
  "walls": [
    {
      "id": "uuid-here",
      "start": {"x": 0.0, "y": 0.0},
      "end": {"x": 120.0, "y": 0.0},
      "thickness": 6.0,
      "wall_type": "exterior"
    }
  ],
  "openings": [
    {
      "id": "uuid-here",
      "wall_id": "wall-uuid",
      "position": 0.5,
      "width": 36.0,
      "opening_type": "door",
      "height": 80.0
    }
  ],
  "rooms": [],
  "metadata": {}
}
```

## Extending the Application

### Adding New Tools
1. Add a new mode to `DrawMode` in `gui/canvas.py`
2. Create corresponding action in `gui/main_window.py`
3. Implement handling in `FloorPlanCanvas` event handlers

### Adding New Geometry Types
1. Define new dataclass in `core/geometry.py`
2. Add to `FloorPlan` container with add/remove/get methods
3. Implement rendering in `FloorPlanCanvas`
4. Add serialization (to_dict/from_dict)

### Preparing for 3D
The architecture is designed for 3D expansion:
- All measurements in real-world units (inches)
- Geometry classes can be extended with Z coordinates
- Wall thickness already modeled
- Height properties ready for doors and windows

## Logging

Comprehensive logging is enabled by default:
- Log file location: `~/.floorplan_app/logs/floorplan_YYYYMMDD_HHMMSS.log`
- Console output: INFO level and above
- File output: DEBUG level and above

Configure logging in `utils/logging_config.py`.

## Configuration

Default settings in `utils/logging_config.py` (`AppConfig` class):
- Wall thickness: 6 inches
- Door width: 36 inches (3 feet)
- Window width: 48 inches (4 feet)
- Grid size: 12 inches (1 foot)
- Snap tolerance: 6 inches
- Scale: 2 pixels per inch

## Examples

See the `examples/` directory for:
- Programmatic floor plan creation
- Sample floor plans
- Custom tool implementations

## Development

### Running Tests
```bash
# (Tests to be added)
python -m pytest tests/
```

### Code Style
- Follow PEP 8
- Type hints where appropriate
- Comprehensive docstrings
- Logging for all operations

## Contributing

This is a modular, open architecture. Contributions welcome for:
- 3D visualization
- Additional drawing tools
- Export formats
- UI improvements
- Performance optimizations

## License

[Your license here]

## Author

Created for architectural planning and visualization.

## Changelog

### v1.0 (Current)
- Initial release
- 2D floor plan drawing
- Wall, door, and window support
- Save/load functionality
- Interactive canvas with zoom/pan
- Grid snapping
- Comprehensive logging
