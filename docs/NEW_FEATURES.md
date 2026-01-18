# Floor Plan Editor - Version 1.1 New Features

## Overview of New Features

Version 1.1 adds powerful editing and analysis capabilities:

1. **Properties Panel** - Edit wall thickness, door/window sizes, room names, and colors
2. **Undo/Redo** - Full history with unlimited undo
3. **Measurement Tool** - Measure distances and angles
4. **Room Creation** - Create named rooms with area calculation
5. **Statistics** - Comprehensive floor plan analysis
6. **Enhanced Selection** - Select walls, openings, and rooms
7. **Property Editing** - Modify all object properties in real-time

## 1. Properties Panel

### What It Does
The properties panel appears on the right side and shows editable properties for the selected object.

### How to Use
1. Click **Select tool** (S key)
2. Click on any wall, door, window, or room
3. The properties panel updates to show that object's properties
4. Edit any value - changes apply immediately

### Wall Properties
- **Thickness**: Adjust wall thickness (1-24 inches)
- **Type**: Change between exterior, interior, load-bearing
- **Coordinates**: Precise positioning with X/Y coordinates

### Opening Properties  
- **Type**: Switch between door, window, archway
- **Width**: Adjust opening width (6-120 inches)
- **Height**: Set opening height (12-120 inches)
- **Position**: Fine-tune position along wall (0.0-1.0)
- **Sill Height**: For windows, set height from floor

### Room Properties
- **Name**: Give the room a descriptive name
- **Color**: Choose a fill color for visualization
- **Wall Count**: Shows number of walls (read-only)

### Tips
- Changes apply immediately - no need to click "Apply"
- Use coordinate editing for precise wall placement
- Adjust door/window positions numerically for perfect alignment

## 2. Undo/Redo System

### What It Does
Track all changes and reverse them with unlimited undo/redo.

### How to Use
- **Undo**: Press **Ctrl+Z** or Edit → Undo
- **Redo**: Press **Ctrl+Shift+Z** or Edit → Redo
- See action names in the menu ("Undo Add Wall", etc.)

### What's Tracked
- ✓ Adding walls, doors, windows, rooms
- ✓ Deleting any object
- ✓ Property modifications (via properties panel)

### Tips
- Undo stack persists until you close the file
- Maximum 100 undo steps (configurable)
- Property changes update in real-time but can still be undone

## 3. Measurement Tool

### What It Does
Click two points to measure distance and angle between them. Measurements stay visible for reference.

### How to Use
1. Press **M** or click the **Measure** tool
2. Click first point
3. Click second point - measurement is saved
4. Repeat to add more measurements
5. Press **Escape** to cancel current measurement

### Display
- **Distance**: Shown in feet and inches
- **Angle**: Shown in degrees (0-360)
- **Line**: Dashed magenta line with endpoints
- **Labels**: Distance and angle at midpoint

### Managing Measurements
- **Clear all**: Press **C** while in measure mode, or Analysis → Clear Measurements
- **Cancel current**: Press **Escape**
- Measurements persist until cleared

### Use Cases
- Verify wall lengths
- Check angles for diagonal walls
- Plan furniture placement distances
- Measure room diagonals

## 4. Room Creation & Area Calculation

### Creating Rooms

#### Method 1: Using Room Tool
1. Press **R** or select **Create Room** tool
2. Click on walls to select them (they highlight)
3. Click same wall again to deselect
4. Press **Enter** when you have 3+ walls selected
5. Enter room name in dialog
6. Room is created with automatic area calculation

#### Method 2: Programmatically
```python
from core import Room

room = Room(
    name="Living Room",
    wall_ids=[wall1.id, wall2.id, wall3.id, wall4.id],
    color="#FFE4B5"
)
floor_plan.add_room(room)
```

### Room Visualization
- Rooms are filled with semi-transparent color
- Room name appears at center
- Click to select and edit properties
- Color can be changed in properties panel

### Area Calculation
- Automatic calculation using shoelace formula
- Accounts for non-rectangular rooms
- Displayed in properties panel
- Shown in statistics

### Use Cases
- Label different spaces
- Calculate square footage
- Color-code by function (bedrooms, bathrooms, etc.)
- Track total livable area

## 5. Statistics & Analysis

### What It Shows
Comprehensive analysis of your floor plan:
- Wall count and total length
- Breakdown by wall type (exterior/interior)
- Opening count (doors/windows/archways)
- Room count and total area
- Individual room areas and perimeters
- Overall dimensions and bounding box

### How to Use
1. Press **Ctrl+I** or Analysis → Show Statistics
2. View the statistics dialog
3. Copy text if needed

### Example Output
```
=== Walls ===
Total: 10
Total Length: 130.0 ft
  Exterior: 112.0 ft
  Interior: 18.0 ft

=== Openings ===
Total: 5
  Doors: 2
  Windows: 3

=== Rooms ===
Total: 3
Total Area: 516.0 sq ft

Individual Rooms:
  Living Room:
    Area: 300.0 sq ft
    Perimeter: 70.0 ft
  Kitchen:
    Area: 180.0 sq ft
    Perimeter: 57.0 ft
```

### Use Cases
- Calculate material quantities
- Estimate construction costs
- Verify building codes (square footage requirements)
- Compare design alternatives

## 6. Enhanced Selection System

### Selecting Objects

**Walls**
- Click near any wall to select
- Selected wall turns red
- Properties show in panel

**Doors/Windows**
- Click on the opening marker
- Selected opening highlighted
- Edit size and position in panel

**Rooms**
- Click inside any room polygon
- Room highlights (lighter color)
- Edit name and color in panel

### Multi-Step Editing Workflow
1. Select object (click it)
2. View/edit properties in panel
3. See changes immediately
4. Undo if needed (Ctrl+Z)

## 7. Keyboard Shortcuts (New & Updated)

### Tools
- **S**: Select
- **W**: Draw Wall
- **D**: Add Door
- **N**: Add Window
- **M**: Measure
- **R**: Create Room

### Edit Commands
- **Ctrl+Z**: Undo
- **Ctrl+Shift+Z**: Redo
- **Delete**: Delete selected object
- **Escape**: Cancel/deselect

### View Controls
- **Ctrl+0**: Fit to view
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **G**: Toggle grid

### Analysis
- **Ctrl+I**: Show statistics
- **C** (in measure mode): Clear measurements
- **Enter** (in room mode): Create room from selection

### File Operations
- **Ctrl+N**: New
- **Ctrl+O**: Open
- **Ctrl+S**: Save
- **Ctrl+Shift+S**: Save As

## Advanced Usage Examples

### Example 1: Creating a Multi-Room House
```python
# Create kitchen
kitchen_walls = [w1, w2, w3, w4]
kitchen = Room(
    name="Kitchen",
    wall_ids=[w.id for w in kitchen_walls],
    color="#B0E0E6"  # Light blue
)
plan.add_room(kitchen)

# Calculate area
from utils import calculate_room_area
area = calculate_room_area(kitchen, plan)
print(f"Kitchen: {area:.1f} sq ft")
```

### Example 2: Modifying Properties
```python
# Get wall by ID
wall = floor_plan.get_wall(wall_id)

# Modify properties
wall.thickness = 8.0
wall.wall_type = WallType.LOAD_BEARING

# Changes persist when saved
floor_plan.save_to_file("plan.floorplan")
```

### Example 3: Batch Statistics
```python
from utils import get_floor_plan_statistics

stats = get_floor_plan_statistics(floor_plan)

# Access specific values
total_area = stats['rooms']['total_area_sqft']
wall_count = stats['walls']['count']
door_count = stats['openings']['doors']

# Get individual room data
for name, data in stats['rooms']['individual'].items():
    print(f"{name}: {data['area_sqft']:.1f} sq ft")
```

## Tips & Best Practices

### Property Editing
- Use the properties panel for fine-tuning
- Adjust coordinates for pixel-perfect alignment
- Set wall thickness by function (exterior=6-8", interior=4-6")

### Room Creation
- Create rooms after all walls are in place
- Use consistent wall selection (clockwise or counter-clockwise)
- Name rooms descriptively for better organization

### Measurements
- Use measurements for verification, not construction
- Keep important measurements visible
- Clear measurements when changing design significantly

### Undo/Redo
- Don't be afraid to experiment - you can always undo
- Use undo to compare alternatives
- Save before making major changes

### Performance
- For large plans (100+ walls), property updates are instant
- Room area calculation is fast even for complex polygons
- Statistics generation takes <1 second for typical houses

## What's Next (Future Features)

Planned for future versions:
- **Copy/Paste**: Duplicate walls and room layouts
- **Export to PDF**: Print floor plans with measurements
- **Export to PNG**: Generate images for presentations
- **Move Tool**: Drag objects to new positions
- **Furniture Library**: Add and place furniture
- **Multi-Story**: Support for multiple floors
- **3D View**: Visualize in 3D

## Troubleshooting

**Properties panel is empty**
- Make sure something is selected
- Click on object again to reselect

**Room area shows as 0 or None**
- Ensure room has at least 3 walls
- Check that walls form a closed polygon
- Verify wall endpoints connect properly

**Measurements not appearing**
- Make sure you're in Measure mode (M key)
- Click two different points
- Check that points aren't too close

**Undo not working**
- Some operations may not be tracked yet
- Property changes via panel ARE tracked
- Direct modifications in code are NOT tracked

## Summary of Capabilities

You can now:
- ✓ Edit any property of walls, doors, windows, rooms
- ✓ Undo and redo all changes
- ✓ Measure distances and angles precisely
- ✓ Create and label rooms
- ✓ Calculate room areas automatically
- ✓ Generate comprehensive statistics
- ✓ Fine-tune designs with real-time feedback

These tools make the Floor Plan Editor a professional-grade tool for architectural planning and visualization!
