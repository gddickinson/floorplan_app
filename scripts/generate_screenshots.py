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

from core.demo_plans import create_demo_house
from gui import MainWindow
from gui.canvas import FloorPlanCanvas, DrawMode

OUTPUT_DIR = project_root / "docs" / "images"


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
