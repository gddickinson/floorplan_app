# Floor Plan Editor - Enhanced Version

**Version 2.0** - January 2026

This is the enhanced version of the Floor Plan Editor with two major feature additions:

## 🆕 What's New in Version 2.0

### 1. Fixed RoomPlan Import (Wall Ordering Fix)
✅ **Fixed**: Walls from iPhone LiDAR scans now import in correct sequential order  
✅ **Fixed**: Walls form proper closed loops  
✅ **Removed**: Duplicate `iphone_importer.py` (consolidated into `roomplan_importer.py`)

**See**: `docs/roomplan_fix/` for details

### 2. Interactive Object Manipulation
✅ **New**: Select furniture, fixtures, and stairs by clicking  
✅ **New**: Move objects by dragging  
✅ **New**: Resize objects using corner handles  
✅ **New**: Rotate objects using rotation handle  
✅ **New**: Edit object properties in dedicated panel  
✅ **New**: Delete objects with Delete key  
✅ **New**: Full undo/redo support for all transformations

**See**: `docs/interactive_objects/` for details

## 🚀 Quick Start

### Installation

```bash
# Extract the tar file
tar -xzf floorplan_app_complete.tar.gz
cd floorplan_app

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Using Interactive Objects

1. **Press 'S'** to enter SELECT mode
2. **Click** on any furniture, fixture, or stairs to select
3. **Drag** to move, **drag corners** to resize, **drag green handle** to rotate
4. **Edit properties** in the Properties Panel
5. **Press Delete** to remove objects
6. **Press Ctrl+Z** to undo

## 📁 Project Structure

```
floorplan_app/
├── core/                      # Core data structures
│   ├── geometry.py           # Point, Wall, Opening, Room, FloorPlan
│   └── level.py              # Building, multi-floor support
├── gui/                       # User interface
│   ├── canvas.py             # Interactive drawing canvas (UPDATED ✨)
│   ├── main_window.py        # Main application window (UPDATED ✨)
│   ├── properties_panel.py   # Properties editor (UPDATED ✨)
│   ├── object_selection.py   # Object selection system (NEW 🆕)
│   ├── floor_selector.py     # Floor level selector
│   ├── object_library.py     # Object library panel
│   └── viewer_3d.py          # 3D visualization
├── utils/                     # Utilities
│   ├── logging_config.py     # Logging and app config
│   ├── undo_stack.py         # Undo/redo system (UPDATED ✨)
│   ├── undo_commands.py      # Object transformation undo (NEW 🆕)
│   ├── roomplan_importer.py  # RoomPlan JSON importer (FIXED ✅)
│   ├── measurements.py       # Measurement tools
│   ├── transforms.py         # Advanced transformations
│   ├── annotations.py        # Text and dimension annotations
│   ├── clipboard.py          # Copy/paste support
│   └── export.py             # Export to various formats
├── data/                      # Data and examples
│   ├── examples/             # Example floor plans and scripts
│   └── iphone_scans/         # Sample iPhone scans
├── tests/                     # Test scripts
├── docs/                      # Documentation (NEW 🆕)
│   ├── roomplan_fix/         # RoomPlan import fix docs
│   └── interactive_objects/  # Interactive objects docs
└── main.py                    # Application entry point
```

## 🎯 Key Features

### Floor Plan Drawing
- ✅ Interactive wall drawing with snap-to-grid
- ✅ Door and window placement
- ✅ Room creation and labeling
- ✅ Multi-floor support
- ✅ 3D visualization

### Object Manipulation (NEW in v2.0)
- ✅ Click to select objects
- ✅ Drag to move
- ✅ Corner handles for resizing
- ✅ Rotation handle for any angle
- ✅ Properties panel for precise editing
- ✅ Full undo/redo support

### Import/Export
- ✅ Import from iPhone LiDAR scans (RoomPlan) - FIXED
- ✅ Save/load native .floorplan format
- ✅ Export to PDF, PNG, SVG (via export module)

### Advanced Features
- ✅ Furniture and fixture library
- ✅ Measurement tools
- ✅ Annotations and labels
- ✅ Copy/paste objects
- ✅ Grid and dimension display
- ✅ Zoom and pan

## 📚 Documentation

### For Users
- **Quick Start**: See section above
- **Interactive Objects Guide**: `docs/interactive_objects/QUICK_START.md`
- **RoomPlan Import**: `docs/roomplan_fix/QUICK_START.md`

### For Developers
- **Architecture**: `ARCHITECTURE.md`
- **Project Structure**: `PROJECT_STRUCTURE.txt`
- **Interactive Objects Integration**: `docs/interactive_objects/INSTALLATION.md`
- **RoomPlan Fix Details**: `docs/roomplan_fix/README_FIX.md`

## 🎮 Keyboard Shortcuts

### General
- **Ctrl+N** - New floor plan
- **Ctrl+O** - Open file
- **Ctrl+S** - Save
- **Ctrl+Z** - Undo
- **Ctrl+Shift+Z** - Redo

### Tools
- **S** - Select tool
- **W** - Draw wall
- **D** - Add door
- **N** - Add window
- **G** - Toggle grid
- **Ctrl+D** - Toggle dimensions

### Object Manipulation (NEW)
- **Delete** - Delete selected object
- **Escape** - Deselect
- **Arrow keys** - Nudge selected object (if implemented)

## 🔧 What's Changed

### Modified Files

#### gui/canvas.py
- ✅ Added object selection system
- ✅ Added transformation handlers
- ✅ Modified mouse event handlers
- ✅ Added keyboard shortcuts (Delete, Escape)
- ✅ Added selection handle rendering

#### gui/properties_panel.py
- ✅ Added object properties widgets
- ✅ Added property editing handlers
- ✅ Connected to object selection signal

#### gui/main_window.py
- ✅ Connected object_selected signal
- ✅ Linked properties panel to canvas

#### utils/undo_stack.py
- ✅ Added transformation undo commands
- ✅ Exported new command classes

#### utils/roomplan_importer.py
- ✅ Fixed wall ordering algorithm
- ✅ Proper sequential wall tracing
- ✅ Loop closure verification

### New Files

- `gui/object_selection.py` - Object selection and transformation engine
- `utils/undo_commands.py` - Undo/redo for object operations
- `docs/` - Complete documentation for both features

### Removed Files

- `utils/iphone_importer.py` - Duplicate of roomplan_importer (consolidated)

## 🐛 Bug Fixes

### RoomPlan Import
- **Fixed**: Walls now import in correct sequential order
- **Fixed**: Wall endpoints connect properly at corners
- **Fixed**: Closed loop formation verified
- **Improved**: Better logging and error messages

### General
- **Improved**: Memory management for large floor plans
- **Improved**: Performance for object rendering

## 📋 Upgrade Notes

### From v1.0 to v2.0

**Breaking Changes**: None - fully backward compatible

**New Dependencies**: None - uses existing PyQt6

**Data Format**: Unchanged - existing .floorplan files work as-is

**What You Get**:
1. Fixed RoomPlan imports
2. Interactive object manipulation
3. Enhanced properties panel
4. Full undo/redo for objects

## 🎉 Examples

### Import iPhone Scan
```python
# File → Import iPhone Scan → select office2.json
# Walls now import in correct order forming a closed loop
```

### Edit Furniture
```python
# 1. Press 'S' for select mode
# 2. Click on furniture
# 3. Drag to move or drag handles to resize
# 4. Edit exact values in Properties Panel
# 5. Press Delete to remove
```

### Rotate Objects
```python
# 1. Select object
# 2. Drag green circle above object
# 3. Or enter exact angle in Properties Panel
```

## 🚀 Performance

- Handles floor plans with hundreds of objects
- Real-time transformation feedback
- Efficient rendering pipeline
- Minimal memory footprint

## 🔮 Future Enhancements

Planned for future versions:
- Multi-select objects
- Group operations
- Alignment tools
- Snap to walls/objects
- Copy/paste improvements
- Cloud storage integration

## 📞 Support

For issues or questions:
1. Check documentation in `docs/`
2. Review example files in `data/examples/`
3. Check logs in `~/.floorplan_app/logs/`

## 📄 License

[Your license here]

## 👨‍💻 Credits

- **Original Author**: [Your name]
- **RoomPlan Fix**: January 2026
- **Interactive Objects**: January 2026

---

**Version 2.0** | Enhanced with Interactive Objects & Fixed RoomPlan Import
