"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific API tests ---------------------------------------------------------------------------------
import json  # noqa: E402

from core import FloorPlan  # noqa: E402
from web.catalog import EXAMPLES  # noqa: E402


@pytest.mark.parametrize("name", list(EXAMPLES))
def test_example_files_load_in_python(name):
    d = client.get(f"/api/examples/{name}").json()
    assert FloorPlan.from_dict(d).to_dict() == d


def test_examples_are_stable():
    a = client.get("/api/examples/demo_house").json()
    b = client.get("/api/examples/demo_house").json()
    assert a == b and a["walls"][0]["id"] == "wall_1"


def test_analyze_demo_house():
    d = client.get("/api/examples/demo_house").json()
    r = client.post("/api/analyze", json=d).json()
    areas = {x["name"]: round(x["area_sqft"], 6) for x in r["rooms"]}
    assert areas == {"Living Room": 300.0, "Kitchen": 180.0, "Bedroom": 45.0, "Bathroom": 56.0}
    assert r["stats"]["openings"]["doors"] == 3 and r["stats"]["openings"]["windows"] == 5


def test_analyze_rejects_bad_plan():
    r = client.post("/api/analyze", json={"walls": [{"start": {"x": 0, "y": 0}}]})
    assert r.status_code == 422


def test_catalog_matches_desktop_library():
    from core.catalog import FURNITURE_CATALOG
    cat = client.get("/api/catalog").json()
    assert len(cat["furniture"]) == len(FURNITURE_CATALOG) == 18
    assert cat["settings"]["grid_size"] == 12.0


ROUNDTRIP_JS = """
import { fromDict, toFileText, makeWall, makeOpening, makeFurniture, makeStair, roomFromDict } from './model.js';
const d = JSON.parse(process.argv[2]);
const plan = fromDict(d);
const w = makeWall({x: 600, y: 0}, {x: 600, y: 120}, {wall_type: 'exterior', wall_style: 'brick'});
plan.walls.push(w);
plan.openings.push(makeOpening(w.id, 0.25, 30, 'window_casement', {sill_height: 40}));
plan.furniture.push(makeFurniture({x: 610, y: 60}, 24, 24, 'chair', {rotation: 45}));
plan.stairs.push(makeStair({x: 0, y: 300}, {x: 120, y: 300}, 36, 'l_shaped'));
plan.rooms.push(roomFromDict({name: 'Web room', wall_ids: [w.id], color: null}));
process.stdout.write(toFileText(plan));
"""


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
@pytest.mark.parametrize("name", list(EXAMPLES))
def test_web_saved_file_opens_in_python(name, tmp_path):
    """Desktop -> web -> desktop: a plan loaded, edited and saved by the JS model is read back by FloorPlan."""
    d = client.get(f"/api/examples/{name}").json()
    script = tmp_path / "rt.mjs"
    script.write_text(ROUNDTRIP_JS.replace("./model.js", (STATIC / "model.js").as_uri()))
    r = subprocess.run(["node", str(script), json.dumps(d)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    path = tmp_path / "web.floorplan"
    path.write_text(r.stdout)
    plan = FloorPlan.load_from_file(str(path))
    saved = json.loads(r.stdout)
    assert plan.to_dict() == saved
    assert {k: saved[k] for k in d if k not in ("walls", "openings", "furniture", "stairs", "rooms")} == \
        {k: d[k] for k in d if k not in ("walls", "openings", "furniture", "stairs", "rooms")}
    assert saved["walls"][:len(d["walls"])] == d["walls"] and len(saved["walls"]) == len(d["walls"]) + 1
    assert saved["furniture"][-1]["name"] == "Chair" and saved["openings"][-1]["opening_type"] == "window_casement"
