# Floor Plan Editor - Quick Start Guide

## Installation

1. **Install Dependencies**
   ```bash
   cd floorplan_app
   pip install -r requirements.txt
   ```

2. **Test Installation**
   ```bash
   python test_installation.py
   ```
   
   You should see "ALL TESTS PASSED ✓"

## Running the Application

### Launch the GUI
```bash
python main.py
```

### Open an Example Floor Plan
```bash
python main.py examples/simple_house.floorplan
```

## Creating Your First Floor Plan

### Step 1: Draw Walls
1. Click the **"Draw Wall"** button in the toolbar (or press **W**)
2. Click on the canvas to place the first point
3. Click again to place the second point
4. The wall is created!
5. Repeat to add more walls

**Tips:**
- Walls automatically snap to the grid (12-inch intervals)
- Walls also snap to endpoints of existing walls
- Press **Escape** to cancel wall drawing

### Step 2: Add Doors
1. Click the **"Add Door"** button (or press **D**)
2. Click on any wall where you want the door
3. The door is placed!

**Tips:**
- Default door width is 36 inches (3 feet)
- Doors are positioned where you click along the wall
- You can add multiple doors to the same wall

### Step 3: Add Windows
1. Click the **"Add Window"** button (or press **N**)
2. Click on any wall where you want the window
3. The window is placed!

**Tips:**
- Default window width is 48 inches (4 feet)
- Windows have a default sill height of 36 inches from the floor

### Step 4: Select and Edit
1. Click the **"Select"** button (or press **S**)
2. Click on any wall or opening to select it
3. Press **Delete** to remove selected items
4. Selected items are highlighted in red

### Step 5: Navigate the View
- **Zoom**: Use mouse wheel or **Ctrl++** / **Ctrl+-**
- **Pan**: Middle-click and drag
- **Fit to View**: Press **Ctrl+0** or use View → Fit to View

### Step 6: Save Your Work
1. Press **Ctrl+S** or File → Save
2. Choose a location and filename
3. Files are saved with `.floorplan` extension

## Example Workflow: Drawing a Simple Room

Let's draw a 12' × 10' room with a door and window:

1. **Start the app**: `python main.py`

2. **Draw the first wall (bottom)**:
   - Press **W** for wall tool
   - Click at approximately (0, 0)
   - Click at approximately (144, 0)  ← 12 feet = 144 inches

3. **Draw the right wall**:
   - Click at (144, 0)
   - Click at (144, 120)  ← 10 feet = 120 inches

4. **Draw the top wall**:
   - Click at (144, 120)
   - Click at (0, 120)

5. **Draw the left wall**:
   - Click at (0, 120)
   - Click at (0, 0)  ← Completes the rectangle!

6. **Add a door**:
   - Press **D** for door tool
   - Click on the bottom wall (around the middle)

7. **Add a window**:
   - Press **N** for window tool
   - Click on the right wall

8. **View your creation**:
   - Press **Ctrl+0** to fit to view
   - Press **G** to toggle grid if needed

9. **Save**:
   - Press **Ctrl+S**
   - Name it "my_first_room.floorplan"

## Keyboard Shortcuts Reference

### Tools
- **S** - Select tool
- **W** - Draw wall tool  
- **D** - Add door tool
- **N** - Add window tool
- **Escape** - Cancel current operation
- **Delete** - Delete selected item

### View
- **Ctrl+0** - Fit to view
- **Ctrl++** - Zoom in
- **Ctrl+-** - Zoom out
- **G** - Toggle grid
- **Ctrl+G** - Toggle grid (alternative)
- **Ctrl+D** - Toggle dimensions

### File Operations
- **Ctrl+N** - New file
- **Ctrl+O** - Open file
- **Ctrl+S** - Save
- **Ctrl+Shift+S** - Save As
- **Ctrl+Q** - Quit

## Tips & Tricks

### Grid Snapping
- Walls automatically snap to 12-inch (1 foot) grid intersections
- To disable: Press **G** to hide the grid (snapping still works)
- Grid size is configurable in `utils/logging_config.py`

### Wall Endpoints
- When drawing a new wall, it will snap to endpoints of existing walls
- This makes it easy to create connected rooms
- Endpoint snapping takes priority over grid snapping

### Dimensions
- Wall lengths are automatically calculated and displayed
- Measurements are shown in feet and inches (e.g., "12' 6\"")
- Toggle dimension display with **Ctrl+D**

### Selection
- Click on walls or openings to select them
- Selected items turn red
- Press **Delete** to remove selected items
- Press **Escape** to deselect

### Pan and Zoom
- Middle mouse button + drag to pan
- Mouse wheel to zoom in/out
- Zoom centers on your mouse cursor position
- Fit to view with **Ctrl+0** to see everything

## Programmatic Usage

You can also create floor plans programmatically! See `examples/create_example_plans.py` for examples:

```python
from core import Point, Wall, FloorPlan

# Create a floor plan
plan = FloorPlan(name="My House")

# Add a wall from (0, 0) to (144, 0) - 12 feet
wall = Wall(Point(0, 0), Point(144, 0))
plan.add_wall(wall)

# Save to file
plan.save_to_file("my_house.floorplan")
```

## Common Units

Remember: All measurements are in **inches** internally

- 1 foot = 12 inches
- Standard door: 36 inches (3 feet) wide
- Standard window: 48 inches (4 feet) wide
- Typical interior wall: 4-6 inches thick
- Typical exterior wall: 6-8 inches thick
- Grid spacing: 12 inches (1 foot)

## Troubleshooting

### "PyQt6 not found"
```bash
pip install PyQt6
```

### Walls won't snap
- Make sure grid is enabled (press **G** to toggle)
- Check that you're close enough to snap points
- Snap tolerance is 6 inches by default

### Can't see my floor plan
- Press **Ctrl+0** to fit to view
- Check that you've actually created walls (check the console logs)
- Make sure walls have reasonable coordinates

### Lost changes
- Floor plans auto-save to `.floorplan` files
- Check `~/.floorplan_app/logs/` for activity logs
- The app will prompt you to save on exit

## Next Steps

1. ✓ Create a simple room (follow example above)
2. ✓ Add doors and windows
3. ✓ Save your floor plan
4. ✓ Open the example files to see complex layouts
5. ✓ Explore the programmatic API in `examples/`
6. ✓ Start planning your house!

## Getting Help

- Check the main README.md for architecture details
- Look at example floor plans in `examples/`
- Review the code in `core/geometry.py` for data structures
- All operations are logged to `~/.floorplan_app/logs/`

## Future Features (Roadmap)

Coming soon:
- 3D visualization
- Room area calculations
- Export to PDF/PNG
- Furniture placement
- Measurement tools
- Multi-story buildings

Happy floor planning! 🏠
