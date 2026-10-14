import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingest"))
from parse_splits import clean, normalize_stroke, time_to_seconds  # noqa: E402


@pytest.mark.parametrize("raw, expected", [
    ("38.42", 38.42),
    ("1:12.80", 72.8),
    ("2:41", 161.0),
    (" 0:59.9 ", 59.9),
    ("1:75.00", None),   # seconds past 59 with a minute part
    ("abc", None),
    (None, None),
])
def test_time_to_seconds(raw, expected):
    assert time_to_seconds(raw) == expected


def test_stroke_aliases():
    assert normalize_stroke("Free") == "freestyle"
    assert normalize_stroke("BK") == "backstroke"
    assert normalize_stroke("fly") == "fly"


def test_clean_splits_good_and_bad_rows():
    raw = pd.DataFrame({
        "date": ["2026-05-01", "2026-05-01", "not a date", "2026-05-02"],
        "stroke": ["free", "fly", "back", "free"],
        "distance_m": [50, 25, 25, 50],
        "time": ["52.00", "30.00", "28.00", "5.00"],
    })
    good, rejects = clean(raw)

    assert len(good) == 1
    assert good.iloc[0]["pace_per_100m"] == 104.0
    assert set(rejects["reject_reason"]) == {
        "unknown stroke;", "bad date;", "implausibly fast;"
    }
