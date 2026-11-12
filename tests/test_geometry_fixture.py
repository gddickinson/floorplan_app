"""The committed Python-vs-JS fixture (tests/fixtures/geometry_fixture.json) is what the Python core computes now."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import make_geometry_fixture  # noqa: E402


def _same(a, b, where="fixture"):
    if isinstance(b, bool) or b is None or isinstance(b, str):
        assert a == b, f"{where}: {a!r} != {b!r} (run scripts/make_geometry_fixture.py)"
    elif isinstance(b, (int, float)):
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), f"{where}: {a} != {b}"
    elif isinstance(b, list):
        assert len(a) == len(b), f"{where}: length"
        for i, (x, y) in enumerate(zip(a, b)):
            _same(x, y, f"{where}[{i}]")
    else:
        assert list(a) == list(b), f"{where}: keys"
        for k in b:
            _same(a[k], b[k], f"{where}.{k}")


def test_fixture_is_current():
    committed = json.loads(make_geometry_fixture.OUT.read_text())
    fresh = json.loads(json.dumps(make_geometry_fixture.build()))
    _same(committed, fresh)
