#!/usr/bin/env python3
"""对 TrackNet 轨迹做固定亮点过滤、短缺口插值和可信度分层。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def remove_static_false_positives(
    frame: pd.DataFrame, radius: float, minimum_repeats: int
) -> pd.DataFrame:
    """删除在近似固定位置长期重复出现的亮点误检。"""
    result = frame.copy()
    visible = result[result["Visibility"].eq(1)]
    if visible.empty:
        return result

    bucket_x = (visible["X"] / radius).round().astype(int)
    bucket_y = (visible["Y"] / radius).round().astype(int)
    counts = visible.assign(bucket_x=bucket_x, bucket_y=bucket_y).groupby(
        ["bucket_x", "bucket_y"]
    )["Frame"].count()
    static_buckets = set(counts[counts >= minimum_repeats].index)
    is_static = [
        (round(x / radius), round(y / radius)) in static_buckets
        for x, y in zip(result["X"], result["Y"])
    ]
    result.loc[is_static, ["Visibility", "X", "Y"]] = [0, 0, 0]
    return result


def interpolate_short_gaps(frame: pd.DataFrame, max_gap_frames: int) -> pd.DataFrame:
    """只连接两端均可见且长度较短的轨迹缺口。"""
    result = frame.copy()
    visible = result["Visibility"].eq(1)
    result["X_fused"] = result["X"].where(visible).interpolate(
        limit=max_gap_frames, limit_area="inside"
    )
    result["Y_fused"] = result["Y"].where(visible).interpolate(
        limit=max_gap_frames, limit_area="inside"
    )
    result["is_interpolated"] = (
        ~visible & result["X_fused"].notna() & result["Y_fused"].notna()
    )
    result["track_status"] = np.select(
        [visible, result["is_interpolated"]],
        ["detected", "interpolated"],
        default="missing",
    )
    return result


def summarize(frame: pd.DataFrame) -> dict:
    detected = int(frame["track_status"].eq("detected").sum())
    interpolated = int(frame["track_status"].eq("interpolated").sum())
    total = len(frame)
    return {
        "frames": total,
        "detected_frames": detected,
        "interpolated_frames": interpolated,
        "trajectory_coverage": (detected + interpolated) / total if total else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="融合羽毛球轨迹检测结果")
    parser.add_argument("--ball-csv", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument("--static-radius", type=float, default=8.0)
    parser.add_argument("--static-repeats", type=int, default=12)
    parser.add_argument("--max-gap-frames", type=int, default=8)
    args = parser.parse_args()

    frame = pd.read_csv(args.ball_csv)
    frame = remove_static_false_positives(
        frame, args.static_radius, args.static_repeats
    )
    frame = interpolate_short_gaps(frame, args.max_gap_frames)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.summary_json.write_text(
        json.dumps(summarize(frame), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

