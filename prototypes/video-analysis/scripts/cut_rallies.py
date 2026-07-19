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
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rallies = pd.read_csv(args.rallies_csv)
    for row in rallies.itertuples(index=False):
        output = args.output_dir / (
            f"rally_{int(row.rally_id):03d}_{row.start:.2f}_{row.end:.2f}_"
            f"{int(row.stroke_estimate)}strokes.mp4"
        )
        command = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{row.start:.3f}",
            "-to",
            f"{row.end:.3f}",
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

