"""format_dimension: feet-inches labels used for wall lengths, measurements and the cursor position."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.units import format_dimension  # noqa: E402


@pytest.mark.parametrize("inches,unit,text", [
    (120, "ft", "10'"), (126, "ft", "10' 6.0\""), (0, "ft", "0'"), (5.5, "auto", '5.5"'),
    (126.25, "in", '126.2"'), (30, "auto", "2' 6.0\""),
    # rounding must carry into the feet, not print 12.0 inches
    (23.97, "ft", "2'"), (11.96, "ft", "1'"), (35.95, "ft", "3'"),
    # negative positions (left of / above the origin) keep their size
    (-6, "ft", "-0' 6.0\""), (-126, "ft", "-10' 6.0\""), (-24, "ft", "-2'"), (-30, "auto", "-2' 6.0\""),
    (-5.5, "auto", '-5.5"'), (-0.04, "ft", "0'"),
])
def test_format_dimension(inches, unit, text):
    assert format_dimension(inches, unit) == text
