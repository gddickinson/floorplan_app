# Session log

## 2026-11-11 — web interface + GitHub Pages editor (branch `web-interface`)
- Added `web/`: FastAPI app (port 8217) and a browser floor plan editor that runs entirely client-side (static site):
  SVG 2D editor with grid and desktop snapping, walls/doors/windows/rooms/furniture/fixtures/stairs, properties,
  statistics, measure tool, undo, autosave, raw-WebGL 3D preview, .floorplan open/save, SVG/PNG export.
- Factored Qt-free logic into `core/` (config, units, catalog, snapping, plan_stats, demo_plans, room_geometry); the
  desktop GUI imports it back. JS port checked by `web/static/geometry.test.mjs` on `tests/fixtures/geometry_fixture.json`
  (3 plans, 3160 comparisons, max diff 1.4e-14). `tests/test_web.py` opens web-saved files in the Python loader.
- Bugs fixed (separate commits, regression tests): room outline/area wrong when walls are not listed in drawing order
  (+ follow-up for shared walls overshooting both corners); room perimeter counted shared wall overshoots; door/window
  counts and styling ignored the specific types (door_french, window_bay, ...); format_dimension for negative values
  and values rounding to 12"; corner-handle resize moved the corner twice as far as the cursor.
- README: the PNG/PDF export claim corrected (exporter exists in utils/export.py but is not on the desktop menus).
- Open: stairs' `rotation` field is ignored by drawing but used by desktop selection (selection box is wrong for stairs
  not running vertically); `Building.create_new_floor` uses 96" per level regardless of ceiling height.
