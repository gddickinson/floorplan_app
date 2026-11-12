"""FastAPI web app for the Floor Plan Editor: serves the browser editor in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8217, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below. The editor
itself runs in the browser (static/model.js, geometry.js, stats.js port core/); POST /api/analyze runs a plan through
the Python core so the local app can show that both agree. Imports only core/ (no PyQt6).
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core import FloorPlan
from core.plan_stats import calculate_perimeter, calculate_room_area, format_statistics, get_floor_plan_statistics
from core.room_geometry import room_polygon
from web.catalog import EXAMPLES, catalog, example_plan, examples

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Floor Plan Editor")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary and counts for the home page."""
    cat = catalog()
    return {"title": "Floor Plan Editor", "examples": len(EXAMPLES),
            "furniture": len(cat["furniture"]), "fixtures": len(cat["fixtures"]), "stairs": len(cat["stairs"]),
            "opening_types": len(cat["enums"]["opening_type"]), "grid_inches": cat["settings"]["grid_size"],
            "description": "A 2D/3D architectural floor plan design application built with Python and PyQt6: "
                           "walls, doors, windows, rooms, furniture, fixtures and stairs, saved as .floorplan JSON."}


@app.get("/api/catalog")
def catalog_route():
    """Object library sizes, enum values and drawing settings (inches)."""
    return catalog()


@app.get("/api/examples")
def example_list():
    return examples()


@app.get("/api/examples/{name}")
def example_file(name: str):
    """One example plan in the .floorplan format (FloorPlan.to_dict; opens in the desktop app with File > Open)."""
    if name not in EXAMPLES:
        raise HTTPException(404, f"unknown example {name}")
    return example_plan(name).to_dict()


@app.post("/api/analyze")
def analyze(plan: dict):
    """Load a .floorplan dict with the Python core and return what it computes (for comparison with the browser)."""
    try:
        fp = FloorPlan.from_dict(plan)
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, f"not a valid floor plan: {exc}") from exc
    stats = get_floor_plan_statistics(fp)
    rooms = [{"id": r.id, "name": r.name, "area_sqft": calculate_room_area(r, fp),
              "perimeter_ft": calculate_perimeter(r, fp),
              "polygon": [[p.x, p.y] for p in room_polygon(r, fp)]} for r in fp.rooms]
    return {"dict": fp.to_dict(), "stats": stats, "stats_text": format_statistics(stats), "rooms": rooms}


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/catalog", "/examples"] + [f"/examples/{n}" for n in EXAMPLES]
