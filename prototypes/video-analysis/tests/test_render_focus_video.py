from pathlib import Path
import sys

import pandas as pd
import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from render_focus_video import read_ball_point, select_target_track


def test_select_target_track_uses_clicked_box() -> None:
    people = pd.DataFrame([
        {"frame": 0, "track_id": 3, "confidence": 0.9, "x1": 0, "y1": 0, "x2": 100, "y2": 100},
        {"frame": 0, "track_id": 8, "confidence": 0.8, "x1": 200, "y1": 0, "x2": 300, "y2": 100},
    ])

    assert select_target_track(people, 0, 250, 50) == 8


def test_select_target_track_uses_nearest_available_frame() -> None:
    people = pd.DataFrame([
        {"frame": 2, "track_id": 4, "confidence": 0.9, "x1": 10, "y1": 10, "x2": 80, "y2": 100},
    ])

    assert select_target_track(people, 0, 20, 20) == 4


def test_select_target_track_rejects_missing_tracking_id() -> None:
    people = pd.DataFrame([
        {"frame": 0, "track_id": -1, "confidence": 0.9, "x1": 0, "y1": 0, "x2": 100, "y2": 100},
    ])

    with pytest.raises(ValueError, match="有效跟踪 ID"):
        select_target_track(people, 0, 50, 50)


def test_read_ball_point_supports_fused_rows() -> None:
    row = pd.Series({"track_status": "interpolated", "X_fused": 12.4, "Y_fused": 20.6})

    assert read_ball_point(row) == (12, 21, "interpolated")


def test_read_ball_point_ignores_missing_rows() -> None:
    row = pd.Series({"track_status": "missing", "X_fused": 12, "Y_fused": 21})

    assert read_ball_point(row) is None
