"""Corner handles resize furniture so the dragged corner follows the cursor and the opposite corner stays put."""
import math
import sys
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import Furniture, FurnitureType, Point  # noqa: E402
from gui.object_selection import ObjectTransformHandler, SelectableObject, TransformMode  # noqa: E402


@pytest.mark.parametrize("rotation", [0.0, 90.0, 30.0])
@pytest.mark.parametrize("mode,corner,opposite", [
    (TransformMode.RESIZE_TL, 0, 2), (TransformMode.RESIZE_TR, 1, 3),
    (TransformMode.RESIZE_BR, 2, 0), (TransformMode.RESIZE_BL, 3, 1)])
def test_corner_follows_cursor(rotation, mode, corner, opposite):
    f = Furniture(Point(100, 50), 60, 30, FurnitureType.DESK, rotation=rotation)
    obj = SelectableObject(f)
    h = ObjectTransformHandler(scale=2.0)
    h.set_selected_object(obj)
    before = h._get_object_corners(obj)
    start = before[corner]
    h.start_transform(start, mode)
    # drag the corner outwards along the object's diagonal by 5 inches
    c = Point(100, 50)
    d = math.hypot(start.x - c.x, start.y - c.y)
    target = Point(start.x + (start.x - c.x) / d * 5, start.y + (start.y - c.y) / d * 5)
    h.update_transform(target)
    after = h._get_object_corners(obj)
    assert after[corner].x == pytest.approx(target.x) and after[corner].y == pytest.approx(target.y)
    assert after[opposite].x == pytest.approx(before[opposite].x)
    assert after[opposite].y == pytest.approx(before[opposite].y)
