"""Web interface for the floor plan editor (FastAPI app + plain ES-module front end, no build step).

Contents:
- app.py: FastAPI app, JSON API under /api, STATIC_ENDPOINTS exported for the GitHub Pages site
- catalog.py: example plans (with stable ids), object catalog, enums and settings sent to the browser
- static/: the browser editor (index.html, core.js router, model.js + geometry.js = JS port of core/, SVG editor,
  WebGL 3D view, save/load/export); see INTERFACE.md for the per-file map
"""
