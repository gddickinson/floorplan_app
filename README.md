# Floor Plan Editor

A 2D/3D architectural floor plan design application built with Python and PyQt6.

![Version](https://img.shields.io/badge/version-1.3.4-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

---

## ✨ Features

### 🏗️ **Core Capabilities**

- **Interactive 2D Drawing** - Draw walls, doors, windows with mouse
- **Multi-Level Buildings** - Design buildings with unlimited floors (basements to penthouses)
- **3D Visualization** - Real-time isometric 3D view with rotation, tilt, zoom, and pan
- **Comprehensive Object Library** - 69+ architectural elements:
  - 9 door types (single, double, French, sliding, pocket, bifold, Dutch, garage)
  - 9 window types (single, double, bay, bow, casement, awning, slider, picture, skylight)
  - 18 furniture types (beds, sofas, tables, storage)
  - 15 fixtures (kitchen, bathroom, laundry, HVAC)
  - 6 stair types (straight, L-shaped, U-shaped, winder, spiral, curved)
  - 8 wall styles (solid, brick, concrete, glass, curtain, wood, metal, stone)

### 🎨 **Design Tools**

- **Room Creation** - Auto-calculate room areas
- **Grid Snapping** - Precise alignment
- **Measurement Tools** - Built-in dimension display
- **Undo/Redo** - Full history support
- **Copy/Paste** - Duplicate objects efficiently
- **Properties Panel** - Edit dimensions, styles, names
- **Statistics** - Automatic floor plan analysis

### 🌐 **Views & Navigation**

- **2D Canvas** - Traditional top-down floor plan view
- **3D Viewer** - Interactive isometric 3D visualization
- **Floor Selector** - Navigate multi-story buildings
- **Zoom/Pan** - Smooth navigation
- **Multiple Docks** - Detachable, resizable panels

### 💾 **File Management**

- **Save/Load** - Native `.floorplan` format
- **Multi-Floor Buildings** - `.building` format for complete structures
- **Import/Export** - JSON-based for easy integration

---

## 📸 Screenshots

### 2D Floor Plan Editor
```
┌────────────────────────────────────────────────┐
│  File  Edit  View  Tools  Analysis  Help      │
├──────┬──────────────────────────┬──────────────┤
│Floor │                          │  Properties  │
│      │     2D Canvas            │              │
│Level │   [Floor Plan Drawing]   │  Wall:       │
│  2   │                          │  Length: 15' │
│  1   │   Interactive drawing    │  Thick: 6"   │
│► 0   │   with grid, snapping    │  Type: Ext.  │
│ -1   │   zoom, pan              │  Style: Brick│
│      │                          │              │
│[Add] │                          │  [Delete]    │
│[Del] │                          │              │
├──────┴──────────────────────────┴──────────────┤
│ Ready | 28 walls, 8 rooms | 2,847 sq ft       │
└────────────────────────────────────────────────┘
```

### 3D Visualization
```
┌────────────────────────────────────────────────┐
│  Rotate: ░░▓░░  Tilt: ░▓░░  [Reset] [Toggle]  │
├────────────────────────────────────────────────┤
│                                                │
│              ╱▔▔▔▔▔▔▔▔╲                       │
│             ╱          ╲                       │
│            │  Building  │  ← Isometric 3D     │
│            │  in full   │     visualization   │
│            │  3D view   │                     │
│             ╲          ╱                       │
│              ╲________╱                        │
│                                                │
│  Interactive: Rotate, Zoom, Pan               │
└────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# 1. Extract the archive
tar -xzf floorplan_app_v1.3.4_macOS_fix.tar.gz
cd floorplan_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python main.py
```

### Requirements

- **Python:** 3.9 or higher
- **PyQt6:** 6.4.0 or higher
- **Operating System:** macOS, Linux, or Windows

### First Steps

```bash
# Test installation
python test_installation.py

# Load example house
python main.py examples/comprehensive_house.floorplan

# Start with a blank canvas
python main.py
```

---

## 📖 Usage Guide

### Basic Workflow

**1. Draw Walls**
```
Tools → Draw Wall (or press W)
Click to place wall start point
Click to place wall end point
Press Escape when done
```

**2. Add Doors & Windows**
```
Tools → Add Door (or press D)
Click on a wall to place door
Adjust position with properties panel
```

**3. Create Rooms**
```
Tools → Create Room (or press R)
Click on connected walls to define room
Room area calculated automatically
```

**4. Add Furniture**
```
Object Library panel (left side)
Select furniture from catalog
Click on canvas to place
```

**5. View in 3D**
```
View → Show 3D View
Use sliders to rotate and tilt
Mouse wheel to zoom
Drag to pan
```

**6. Navigate Floors**
```
Floor Selector panel (left side)
Click ↑ Up or ↓ Down to change floors
Add New Floor to create additional levels
```

**7. Save Your Work**
```
File → Save As
Choose location and filename
Saves in .floorplan format
```

---

## 🎯 Key Features Explained

### Multi-Floor Buildings

Design complete buildings with multiple levels:

- **Add Floors:** Floor Selector → Add New Floor
- **Copy Layouts:** Check "Copy from floor" when adding
- **Navigate:** Use ↑↓ buttons or dropdown menu
- **3D View:** Toggle "Show All Floors" to see stacking

**Example:** Create a 3-story house:
```
1. Design ground floor completely
2. Add New Floor (Level 1)
3. Check "Copy layout from: Ground Floor"
4. Modify second floor as needed
5. Repeat for third floor
6. View in 3D to see all floors stacked
```

### 3D Visualization

Interactive isometric 3D view:

- **Rotate:** 0-360° horizontal rotation
- **Tilt:** 0-90° vertical angle
- **Zoom:** Mouse wheel (0.1x - 5.0x)
- **Pan:** Left-click and drag
- **Reset:** Click "Reset View" for defaults

**Controls:**
- Rotate slider: Spin building horizontally
- Tilt slider: Change viewing angle
- Mouse wheel: Zoom in/out
- Left-drag: Pan around
- Reset button: Return to 45°/30° defaults

### Object Library

69+ pre-defined objects with standard dimensions:

**Doors:**
- Single (3'0"), Double (6'0"), French, Sliding
- Pocket, Bifold, Dutch, Garage (16'0")

**Windows:**
- Single (3'0"), Double (6'0"), Bay, Bow
- Casement, Awning, Slider, Picture, Skylight

**Furniture:**
- Beds: Single, Double, Queen, King
- Seating: Sofa, Loveseat, Chairs
- Tables: Dining, Coffee, Side, Desk
- Storage: Dresser, Nightstand, Bookshelf

**Fixtures:**
- Kitchen: Refrigerator, Stove, Dishwasher, Sink
- Bathroom: Toilet, Sink, Bathtub, Shower
- Laundry: Washer, Dryer
- HVAC: Water Heater, Furnace, AC Unit

### Copy/Paste System

Duplicate objects efficiently:

```
Select object → Ctrl+C (copy)
Ctrl+V (paste) → Object appears offset by 2 feet
Paste multiple times for arrays
```

Supports: Walls, Furniture, Fixtures, Stairs

### Properties Panel

Edit selected objects:

- **Walls:** Length, thickness, height, type, style
- **Openings:** Width, height, type, position
- **Rooms:** Name, color, area (calculated)
- **Furniture:** Size, rotation, position
- **Fixtures:** Type, dimensions, location

---

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New File | Ctrl+N |
| Open File | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Undo | Ctrl+Z |
| Redo | Ctrl+Shift+Z |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Delete | Delete/Backspace |
| Draw Wall | W |
| Add Door | D |
| Add Window | N |
| Create Room | R |
| Measure | M |
| Zoom In | Ctrl++ |
| Zoom Out | Ctrl+- |
| Fit to View | Ctrl+0 |
| Cancel | Escape |

---

## 📁 File Formats

### .floorplan (Single Floor)

JSON format containing:
- Walls, openings, rooms
- Furniture, fixtures, stairs
- Floor level, elevation, ceiling height
- Metadata

**Use for:** Single-level designs

### .building (Multi-Floor)

JSON format containing:
- Multiple FloorPlan objects
- Floor hierarchy and relationships
- Building-wide metadata

**Use for:** Complete multi-story buildings

---

## 🔧 Troubleshooting

### 3D View Shows "No walls drawn yet"

**Solution:**
1. Click "Debug Info" button in 3D view
2. Check wall count for current floor
3. If walls = 0, they weren't loaded properly
4. Close and reopen 3D view
5. Or draw one more wall to trigger refresh

See: `3D_TROUBLESHOOTING.md`

### Application Crashes on macOS

**Cause:** Qt widget initialization race condition

**Solution:** Already fixed in v1.3.4! But if issues persist:
1. Update to latest version
2. Check Python version (3.9+ required)
3. Reinstall PyQt6: `pip install --force-reinstall PyQt6`

See: `MACOS_CRASH_FIX.md`

### Walls Not Showing in 3D After Loading File

**Cause:** Building object not synced with loaded FloorPlan

**Solution:** Fixed in v1.3.3+. Update to latest version.

See: `FILE_LOADING_FIX.md`

### Panels Don't Fit on Screen

**Solution:**
1. All panels have scroll bars
2. Dock widgets can be detached (drag title bar)
3. View menu → Hide unnecessary panels
4. Resize docks by dragging edges

See: `UI_IMPROVEMENTS.md`

---

## 📚 Documentation

Comprehensive documentation included:

- **README.md** - This file (overview and quick start)
- **QUICKSTART.md** - Step-by-step tutorial
- **ARCHITECTURE.md** - Code structure and design
- **NEW_FEATURES.md** - Feature descriptions
- **VERSION_1.2_FEATURES.md** - Object library details
- **QUICK_REFERENCE.md** - Object catalog
- **3D_AND_MULTIFLOOR_GUIDE.md** - Multi-level and 3D usage
- **3D_TROUBLESHOOTING.md** - Debugging 3D issues
- **FILE_LOADING_FIX.md** - Technical fix details
- **MACOS_CRASH_FIX.md** - macOS-specific fixes
- **UI_IMPROVEMENTS.md** - Interface enhancements

---

## 🏗️ Architecture

### Project Structure

```
floorplan_app/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── test_installation.py    # Installation verification
├── test_references.py      # Object sync testing
├── test_file_load.py       # File loading testing
│
├── core/                   # Core data structures
│   ├── __init__.py
│   ├── geometry.py         # Point, Wall, Opening, Room, etc.
│   └── level.py            # Multi-level support (legacy)
│
├── gui/                    # User interface
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── canvas.py           # 2D drawing canvas
│   ├── viewer_3d.py        # 3D visualization widget
│   ├── floor_selector.py   # Floor navigation panel
│   ├── properties_panel.py # Object properties editor
│   └── object_library.py   # Object catalog panel
│
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── app_config.py       # Configuration
│   ├── logging_config.py   # Logging setup
│   ├── conversions.py      # Unit conversions
│   ├── undo_stack.py       # Undo/redo system
│   ├── measurements.py     # Statistics
│   └── clipboard.py        # Copy/paste
│
├── examples/               # Example files
│   ├── comprehensive_house.floorplan
│   └── create_comprehensive_house.py
│
└── [Documentation files]
```

### Design Patterns

- **MVC Architecture** - Separation of data, view, logic
- **Observer Pattern** - Signal/slot for event handling
- **Command Pattern** - Undo/redo implementation
- **Factory Pattern** - Object creation
- **Singleton Pattern** - Global configuration

---

## 🧪 Testing

### Automated Tests

```bash
# Core functionality
python test_installation.py

# Object references
python test_references.py

# File loading
python test_file_load.py
```

### Manual Testing

```bash
# Test 3D visualization
python main.py examples/comprehensive_house.floorplan
# View → Show 3D View

# Test multi-floor
python main.py
# Floor Selector → Add New Floor
# View → Show 3D View → Show All Floors

# Test all features
python main.py
# Draw walls, add objects, create rooms
# Save, close, reopen
# Verify everything loads correctly
```

---

## 🐛 Known Issues

### Fixed Issues

- ✅ **v1.3.3** - File loading didn't update 3D view
- ✅ **v1.3.4** - macOS crash on 3D view activation
- ✅ **v1.2.1** - Dock widgets making window too tall
- ✅ **v1.3.1** - 3D canvas not rendering properly

### Current Limitations

- **No HVAC ductwork** - Planned for future release
- **No electrical/plumbing** - Planned for future release
- **No PDF export** - Planned for v1.4
- **No DXF/DWG import** - Under consideration
- **No collaborative editing** - Future enhancement

---

## 🗺️ Roadmap

### Version 1.4 (Planned)

- [ ] PDF/PNG export of 2D and 3D views
- [ ] Print functionality
- [ ] Templates library
- [ ] Grid customization
- [ ] Dimension annotations
- [ ] Area/perimeter measurements on canvas

### Version 1.5 (Planned)

- [ ] OpenGL-accelerated 3D rendering
- [ ] Camera fly-through animations
- [ ] Section views (cut-away)
- [ ] Elevation views (2D side views)
- [ ] Materials and textures

### Version 2.0 (Future)

- [ ] BIM (Building Information Modeling) support
- [ ] IFC import/export
- [ ] Cost estimation
- [ ] Energy analysis integration
- [ ] Collaborative editing
- [ ] Cloud storage integration

---

## 🤝 Contributing

This is currently a personal project, but suggestions are welcome!

**How to contribute:**

1. **Report bugs** - Describe issue, include logs, steps to reproduce
2. **Request features** - Explain use case, provide examples
3. **Share examples** - Create interesting floor plans to showcase
4. **Write documentation** - Tutorials, guides, videos

---

## 📜 Version History

### v1.3.4 (2026-01-18) - Current Release
- **Fixed:** macOS crash on 3D view activation
- **Added:** QTimer-based deferred updates
- **Added:** Comprehensive painter safety checks
- **Improved:** Widget initialization timing
- **Tested:** MacBook Pro M-series compatibility

### v1.3.3 (2026-01-18)
- **Fixed:** File loading not updating Building object
- **Fixed:** 3D view showing empty after file load
- **Added:** Proper Building/FloorPlan synchronization
- **Added:** Comprehensive logging for debugging

### v1.3.2 (2026-01-18)
- **Added:** Debug Info button in 3D viewer
- **Added:** Automatic 3D refresh on changes
- **Added:** Reference synchronization tests
- **Improved:** 3D viewer initialization

### v1.3.1 (2026-01-18)
- **Fixed:** 3D visualization not displaying
- **Added:** Separate Viewer3DCanvas class
- **Improved:** 3D rendering architecture

### v1.3.0 (2026-01-18)
- **Added:** Multi-floor building support
- **Added:** 3D isometric visualization
- **Added:** Floor selector widget
- **Added:** Building class for multi-level management
- **Added:** Wall height properties
- **Added:** Floor elevation system

### v1.2.1 (2026-01-18)
- **Fixed:** Dock widgets making window too tall
- **Added:** Scroll bars in panels
- **Added:** Panel size constraints
- **Added:** Detachable/reattachable docks
- **Added:** View menu toggles

### v1.2.0 (2026-01-18)
- **Added:** Comprehensive object library (69 objects)
- **Added:** 18 furniture types
- **Added:** 15 fixture types
- **Added:** 6 stair types
- **Added:** 22 door/window types
- **Added:** 8 wall styles
- **Added:** Copy/paste system
- **Added:** Object Library panel

### v1.1.0 (2026-01-18)
- **Added:** Properties panel
- **Added:** Undo/redo system
- **Added:** Measurement tool
- **Added:** Room creation with area calculation
- **Added:** Statistics generation
- **Added:** Enhanced selection system

### v1.0.0 (2026-01-18)
- Initial release
- Basic wall drawing
- Door/window placement
- Save/load functionality
- Zoom/pan/grid

---

## 👏 Credits

**Built with:**
- **Python** - Programming language
- **PyQt6** - GUI framework
- **Qt** - Cross-platform UI toolkit

**Inspired by:**
- Professional CAD software
- Architectural design tools
- Home design applications

---

## 📄 License

MIT License

Copyright (c) 2026 George

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 📞 Support

**Issues?** Check the troubleshooting guides:
- `3D_TROUBLESHOOTING.md` - 3D view problems
- `MACOS_CRASH_FIX.md` - macOS crashes
- `FILE_LOADING_FIX.md` - File loading issues

**Questions?** Check the documentation:
- `QUICKSTART.md` - Getting started
- `3D_AND_MULTIFLOOR_GUIDE.md` - Advanced features
- `QUICK_REFERENCE.md` - Object catalog

**Want to learn more?**
- Read `ARCHITECTURE.md` for code structure
- See `examples/` for sample floor plans
- Run `python test_installation.py` to verify setup

---

## 🎉 Thank You!

Thank you for using Floor Plan Editor! 

**Happy designing!** 🏗️✨

---

**Floor Plan Editor v1.3.4** | Built using Python & PyQt6 | 2026
