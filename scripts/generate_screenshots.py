#!/usr/bin/env python3
"""
Generate screenshots of the Floor Plan Editor for documentation.

Creates PNG images showing the GUI and rendered floor plans.

Usage:
    python scripts/generate_screenshots.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

from core import (
    Point, Wall, WallType, WallStyle, Opening, OpeningType,
    Room, FloorPlan, Furniture, FurnitureType, Fixture, FixtureType,
    Stair, StairType
)
from gui import MainWindow
from gui.canvas import FloorPlanCanvas, DrawMode

OUTPUT_DIR = project_root / "docs" / "images"


def ft(feet):
    """Convert feet to inches."""
    return feet * 12


def create_demo_house():
    """Create a demo house floor plan for screenshots."""
    plan = FloorPlan(name="Demo House")

    # Living Room (20' x 15')
    w1 = Wall(Point(0, 0), Point(ft(20), 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w2 = Wall(Point(ft(20), 0), Point(ft(20), ft(15)), 6, WallType.INTERIOR)
    w3 = Wall(Point(ft(20), ft(15)), Point(0, ft(15)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w4 = Wall(Point(0, ft(15)), Point(0, 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    for w in [w1, w2, w3, w4]:
        plan.add_wall(w)

    plan.add_opening(Opening(w1.id, 0.5, 72, OpeningType.DOOR_FRENCH, height=84))
    plan.add_opening(Opening(w3.id, 0.5, 72, OpeningType.WINDOW_BAY, sill_height=36))
    plan.add_opening(Opening(w4.id, 0.4, 48, OpeningType.WINDOW_CASEMENT, sill_height=36))

    living = Room(
        name="Living Room", wall_ids=[w1.id, w2.id, w3.id, w4.id], color="#FFE4B5"
    )
    plan.add_room(living)

    plan.add_furniture(Furniture(Point(ft(10), ft(8)), 84, 36, FurnitureType.SOFA, rotation=90))
    plan.add_furniture(Furniture(Point(ft(14), ft(5)), 36, 36, FurnitureType.ARMCHAIR))
    plan.add_furniture(Furniture(Point(ft(10), ft(5)), 48, 24, FurnitureType.TABLE_COFFEE))
    plan.add_furniture(Furniture(Point(ft(16), ft(13)), 60, 18, FurnitureType.TV_STAND, rotation=270))

    # Kitchen (15' x 12')
    w5 = Wall(Point(ft(20), 0), Point(ft(35), 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w6 = Wall(Point(ft(35), 0), Point(ft(35), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w7 = Wall(Point(ft(35), ft(12)), Point(ft(20), ft(12)), 6, WallType.INTERIOR)
    for w in [w5, w6, w7]:
        plan.add_wall(w)

    plan.add_opening(Opening(w5.id, 0.5, 60, OpeningType.WINDOW_DOUBLE, sill_height=36))
    plan.add_opening(Opening(w7.id, 0.3, 36, OpeningType.DOOR_SINGLE))

    kitchen = Room(name="Kitchen", wall_ids=[w5.id, w6.id, w7.id, w2.id], color="#F0E68C")
    plan.add_room(kitchen)

    plan.add_fixture(Fixture(Point(ft(22), ft(2)), 36, 30, FixtureType.REFRIGERATOR))
    plan.add_fixture(Fixture(Point(ft(27), ft(2)), 30, 24, FixtureType.STOVE))
    plan.add_fixture(Fixture(Point(ft(31), ft(2)), 24, 24, FixtureType.DISHWASHER))
    plan.add_fixture(Fixture(Point(ft(29), ft(2)), 33, 22, FixtureType.SINK_KITCHEN, rotation=270))

    # Bedroom (15' x 12')
    w8 = Wall(Point(ft(20), ft(12)), Point(ft(20), ft(15)), 6, WallType.INTERIOR)
    w9 = Wall(Point(ft(20), ft(15)), Point(ft(35), ft(15)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w10 = Wall(Point(ft(35), ft(15)), Point(ft(35), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    for w in [w8, w9, w10]:
        plan.add_wall(w)

    plan.add_opening(Opening(w9.id, 0.5, 48, OpeningType.WINDOW_DOUBLE, sill_height=36))

    bedroom = Room(name="Bedroom", wall_ids=[w7.id, w8.id, w9.id, w10.id], color="#FFB6C1")
    plan.add_room(bedroom)

    plan.add_furniture(Furniture(Point(ft(27), ft(13.5)), 60, 80, FurnitureType.BED_QUEEN))
    plan.add_furniture(Furniture(Point(ft(23), ft(13)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(32), ft(13)), 24, 18, FurnitureType.NIGHTSTAND))

    # Bathroom (8' x 7')
    w11 = Wall(Point(ft(35), ft(12)), Point(ft(43), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w12 = Wall(Point(ft(43), ft(12)), Point(ft(43), ft(5)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w13 = Wall(Point(ft(43), ft(5)), Point(ft(35), ft(5)), 6, WallType.INTERIOR)
    for w in [w11, w12, w13]:
        plan.add_wall(w)

    plan.add_opening(Opening(w13.id, 0.5, 30, OpeningType.DOOR_POCKET))
    plan.add_opening(Opening(w12.id, 0.5, 36, OpeningType.WINDOW_AWNING, sill_height=60))

    bathroom = Room(
        name="Bathroom", wall_ids=[w6.id, w11.id, w12.id, w13.id], color="#B0E0E6"
    )
    plan.add_room(bathroom)

    plan.add_fixture(Fixture(Point(ft(37), ft(7)), 20, 30, FixtureType.TOILET, rotation=90))
    plan.add_fixture(Fixture(Point(ft(41), ft(7)), 36, 22, FixtureType.SINK, rotation=270))
    plan.add_fixture(Fixture(Point(ft(39), ft(11)), 60, 32, FixtureType.BATHTUB))

    return plan


def grab_canvas_to_file(canvas, filepath):
    """Grab a canvas widget and save as PNG."""
    pixmap = canvas.grab()
    pixmap.save(str(filepath), "PNG")
    size_kb = filepath.stat().st_size / 1024
    print(f"  Saved: {filepath.name} ({size_kb:.0f} KB)")


def generate_all_screenshots():
    """Generate all screenshots for documentation."""
    print("Generating screenshots for README...")
    print(f"Output directory: {OUTPUT_DIR}\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    plan = create_demo_house()

    # --- Screenshot 1: Main GUI overview ---
    window = MainWindow()
    window.canvas.set_floor_plan(plan)
    window.floor_plan = plan
    window.setWindowTitle("Floor Plan Editor - Demo House")
    window.resize(1400, 900)
    window.show()

    step_index = [0]

    def next_step():
        steps = [
            capture_gui_overview,
            capture_clean_render,
            capture_with_selection,
            capture_iphone_import,
            finish,
        ]
        if step_index[0] < len(steps):
            fn = steps[step_index[0]]
            step_index[0] += 1
            fn()

    def capture_gui_overview():
        print("1. Capturing GUI overview...")
        pixmap = window.grab()
        path = OUTPUT_DIR / "gui_overview.png"
        pixmap.save(str(path), "PNG")
        size_kb = path.stat().st_size / 1024
        print(f"  Saved: {path.name} ({size_kb:.0f} KB)")
        QTimer.singleShot(200, next_step)

    def capture_clean_render():
        print("2. Capturing clean floor plan render...")
        # Use a standalone canvas at higher resolution for a clean render
        clean_canvas = FloorPlanCanvas(plan)
        clean_canvas.resize(1200, 800)
        clean_canvas.show_grid = False
        clean_canvas.show()
        QTimer.singleShot(200, lambda: _do_clean_render(clean_canvas))

    def _do_clean_render(clean_canvas):
        clean_canvas.fit_to_view()
        clean_canvas.update()
        QTimer.singleShot(200, lambda: _save_clean_render(clean_canvas))

    def _save_clean_render(clean_canvas):
        path = OUTPUT_DIR / "floor_plan_render.png"
        grab_canvas_to_file(clean_canvas, path)
        clean_canvas.close()

        # Also save with grid
        grid_canvas = FloorPlanCanvas(plan)
        grid_canvas.resize(1200, 800)
        grid_canvas.show_grid = True
        grid_canvas.show()
        QTimer.singleShot(200, lambda: _do_grid_render(grid_canvas))

    def _do_grid_render(grid_canvas):
        grid_canvas.fit_to_view()
        grid_canvas.update()
        QTimer.singleShot(200, lambda: _save_grid_render(grid_canvas))

    def _save_grid_render(grid_canvas):
        path = OUTPUT_DIR / "floor_plan_with_grid.png"
        grab_canvas_to_file(grid_canvas, path)
        grid_canvas.close()
        QTimer.singleShot(200, next_step)

    def capture_with_selection():
        print("3. Capturing with object selected...")
        window.canvas.set_draw_mode(DrawMode.SELECT)
        if plan.furniture:
            first_furniture = plan.furniture[0]
            window.canvas.selected_furniture = first_furniture.id
            window.canvas.object_selected.emit(first_furniture)
            window.canvas.update()
        QTimer.singleShot(300, _save_selection)

    def _save_selection():
        pixmap = window.grab()
        path = OUTPUT_DIR / "gui_with_selection.png"
        pixmap.save(str(path), "PNG")
        size_kb = path.stat().st_size / 1024
        print(f"  Saved: {path.name} ({size_kb:.0f} KB)")
        QTimer.singleShot(200, next_step)

    def capture_iphone_import():
        print("4. Rendering iPhone scan import...")
        scan_dir = project_root / "data" / "iphone_scans"
        scan_files = list(scan_dir.glob("*.json"))

        if not scan_files:
            print("  Skipped: no scan files found")
            QTimer.singleShot(100, next_step)
            return

        try:
            from utils.roomplan_importer import import_roomplan_json
            imported_plan = import_roomplan_json(str(scan_files[0]))
            if not imported_plan:
                print("  Skipped: import returned None")
                QTimer.singleShot(100, next_step)
                return

            scan_canvas = FloorPlanCanvas(imported_plan)
            scan_canvas.resize(1200, 800)
            scan_canvas.show_grid = True
            scan_canvas.show()
            QTimer.singleShot(200, lambda: _do_scan_render(scan_canvas))

        except Exception as e:
            print(f"  Skipped: {e}")
            QTimer.singleShot(100, next_step)

    def _do_scan_render(scan_canvas):
        scan_canvas.fit_to_view()
        scan_canvas.update()
        QTimer.singleShot(200, lambda: _save_scan_render(scan_canvas))

    def _save_scan_render(scan_canvas):
        path = OUTPUT_DIR / "iphone_scan_import.png"
        grab_canvas_to_file(scan_canvas, path)
        scan_canvas.close()
        QTimer.singleShot(200, next_step)

    def finish():
        print(f"\nDone! Screenshots saved to {OUTPUT_DIR}/")
        print("Files generated:")
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.0f} KB)")
        app.quit()

    # Start capture chain after window is fully rendered
    QTimer.singleShot(600, next_step)


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Floor Plan Editor")

    generate_all_screenshots()

    sys.exit(app.exec())
