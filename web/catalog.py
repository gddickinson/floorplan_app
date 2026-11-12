"""Data the browser editor needs from the Python core: example plans, the object library, enums and settings.

Example plans are built by the repo's own code (core/demo_plans.py); their uuid ids are replaced by stable readable
ids (wall_1, room_1, ...) so the served files, the fixture and the static site do not change from build to build.
"""
from core import FurnitureType, FixtureType, OpeningType, StairType, WallStyle, WallType
from core.catalog import FIXTURE_CATALOG, FURNITURE_CATALOG, STAIR_CATALOG
from core.config import AppConfig
from core.demo_plans import create_demo_house, create_test_floor
from core.geometry import FloorPlan, WallMaterial
from core.room_geometry import JOIN_TOLERANCE
from core.snapping import OPENING_MAX_T, OPENING_MIN_T

EXAMPLES = {
    "demo_house": ("Demo House", create_demo_house,
                   "The plan drawn for the README screenshots (scripts/generate_screenshots.py): living room, "
                   "kitchen, bedroom and bathroom with doors, windows, furniture and fixtures."),
    "test_floor": ("Test Floor", create_test_floor,
                   "The four-wall 10 ft x 10 ft plan used by tests/test_file_load.py: a starting point for "
                   "drawing (no room defined yet)."),
}


def stable_ids(plan: FloorPlan) -> FloorPlan:
    """Replace uuid ids by kind_n ids, keeping every cross-reference (openings and rooms refer to wall ids)."""
    wall_map = {}
    for i, w in enumerate(plan.walls, 1):
        wall_map[w.id] = w.id = f"wall_{i}"
    for i, o in enumerate(plan.openings, 1):
        o.id, o.wall_id = f"opening_{i}", wall_map.get(o.wall_id, o.wall_id)
    for i, r in enumerate(plan.rooms, 1):
        r.id, r.wall_ids = f"room_{i}", [wall_map.get(w, w) for w in r.wall_ids]
    for kind, items in (("furniture", plan.furniture), ("fixture", plan.fixtures), ("stair", plan.stairs)):
        for i, obj in enumerate(items, 1):
            obj.id = f"{kind}_{i}"
    return plan


def example_plan(name: str) -> FloorPlan:
    return stable_ids(EXAMPLES[name][1]())


def examples():
    out = []
    for key, (title, _, note) in EXAMPLES.items():
        p = example_plan(key)
        out.append({"name": key, "title": title, "note": note, "walls": len(p.walls), "rooms": len(p.rooms),
                    "openings": len(p.openings), "objects": len(p.furniture) + len(p.fixtures) + len(p.stairs)})
    return out


def _lib(catalog):
    return [{"type": t.value, "name": name, "width": w, "depth": d} for t, (name, w, d) in catalog.items()]


def catalog():
    """Object library, enum values and drawing settings (all lengths in inches)."""
    return {
        "furniture": _lib(FURNITURE_CATALOG),
        "fixtures": _lib(FIXTURE_CATALOG),
        "stairs": _lib(STAIR_CATALOG),
        "enums": {
            "wall_type": [e.value for e in WallType], "wall_style": [e.value for e in WallStyle],
            "wall_material": [e.value for e in WallMaterial], "opening_type": [e.value for e in OpeningType],
            "furniture_type": [e.value for e in FurnitureType], "fixture_type": [e.value for e in FixtureType],
            "stair_type": [e.value for e in StairType],
        },
        "settings": {
            "grid_size": AppConfig.GRID_SIZE, "snap_tolerance": AppConfig.SNAP_TOLERANCE,
            "wall_thickness": AppConfig.DEFAULT_WALL_THICKNESS, "door_width": AppConfig.DEFAULT_DOOR_WIDTH,
            "window_width": AppConfig.DEFAULT_WINDOW_WIDTH, "default_scale": AppConfig.DEFAULT_SCALE,
            "min_scale": AppConfig.MIN_SCALE, "max_scale": AppConfig.MAX_SCALE,
            "file_extension": AppConfig.FILE_EXTENSION, "join_tolerance": JOIN_TOLERANCE,
            "opening_min_t": OPENING_MIN_T, "opening_max_t": OPENING_MAX_T,
            "colors": {"wall": AppConfig.WALL_COLOR, "selected": AppConfig.SELECTED_COLOR,
                       "door": AppConfig.DOOR_COLOR, "window": AppConfig.WINDOW_COLOR, "grid": AppConfig.GRID_COLOR},
        },
    }
