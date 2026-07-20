#!/usr/bin/env python3
"""根据回合 CSV 从原视频生成独立片段。"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="切分羽毛球回合视频")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--rallies-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--time-offset", type=float, default=0.0)
    parser.add_argument("--pre-roll", type=float, default=0.35)
    parser.add_argument("--post-roll", type=float, default=0.45)
    parser.add_argument(
        "--include-unconfirmed",
        action="store_true",
        help="调试时允许导出待确认候选；正式严格目录不要使用",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rallies = pd.read_csv(args.rallies_csv)
    if not args.include_unconfirmed:
        rallies = rallies[rallies["is_complete_rally"].astype(str).str.lower().eq("true")]
    for row in rallies.itertuples(index=False):
        serve_value = getattr(row, "serve_time", row.start)
        landing_value = getattr(row, "landing_time", row.end)
        if args.include_unconfirmed and pd.isna(landing_value):
            # 待确认候选没有死球时间，只按候选审核窗口导出，不能称为正式回合。
            serve_value = row.start
            landing_value = row.end
        serve_time = float(serve_value)
        landing_time = float(landing_value)
        start = max(0.0, serve_time + args.time_offset - args.pre_roll)
        end = landing_time + args.time_offset + args.post_roll
        shot_status = str(getattr(row, "shot_count_status", "无法计拍"))
        stroke_value = getattr(row, "stroke_estimate", "unknown")
        stroke_label = (
            f"{int(stroke_value)}strokes"
            if pd.notna(stroke_value) and shot_status != "无法计拍"
            else "shots-unconfirmed"
        )
        complete = str(getattr(row, "is_complete_rally", False)).lower() == "true"
        completeness_label = "confirmed" if complete else "pending-review"
        output = args.output_dir / (
            f"candidate_{int(row.rally_id):03d}_{completeness_label}_"
            f"{start:.2f}_{end:.2f}_{stroke_label}.mp4"
        )
        command = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start:.3f}",
            "-to",
            f"{end:.3f}",
            "-i",
            str(args.video),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            str(args.crf),
            "-c:a",
            "aac",
            str(output),
        ]
        subprocess.run(command, check=True)
        print(output)


if __name__ == "__main__":
    main()
