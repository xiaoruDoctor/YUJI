#!/usr/bin/env python3
"""渲染指定球员与羽毛球短轨迹，供首版视觉能力验收。"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from collections import deque
from pathlib import Path

import cv2
import pandas as pd


def select_target_track(
    people: pd.DataFrame,
    selection_frame: int,
    selection_x: float,
    selection_y: float,
) -> int:
    """根据指定帧上的点击位置选择目标人物跟踪 ID。"""
    frame_rows = people[people["frame"] == selection_frame]
    if frame_rows.empty:
        available = sorted(int(value) for value in people["frame"].unique())
        if not available:
            raise ValueError("人物检测结果为空")
        nearest = min(available, key=lambda value: abs(value - selection_frame))
        frame_rows = people[people["frame"] == nearest]

    containing = frame_rows[
        (frame_rows["x1"] <= selection_x)
        & (frame_rows["x2"] >= selection_x)
        & (frame_rows["y1"] <= selection_y)
        & (frame_rows["y2"] >= selection_y)
    ]
    candidates = containing if not containing.empty else frame_rows.copy()
    candidates = candidates.assign(
        distance=(
            ((candidates["x1"] + candidates["x2"]) / 2 - selection_x) ** 2
            + ((candidates["y1"] + candidates["y2"]) / 2 - selection_y) ** 2
        )
    )
    target_id = int(candidates.sort_values(["distance", "confidence"], ascending=[True, False]).iloc[0]["track_id"])
    if target_id < 0:
        raise ValueError("目标人物没有有效跟踪 ID，请提高人物检测置信度后重试")
    return target_id


def read_ball_point(row: pd.Series) -> tuple[int, int, str] | None:
    """兼容原始与融合后的 TrackNet CSV 格式。"""
    status = str(row.get("track_status", "detected" if int(row.get("Visibility", 0)) else "missing"))
    if status not in {"detected", "interpolated"}:
        return None
    x = row.get("X_fused", row.get("X"))
    y = row.get("Y_fused", row.get("Y"))
    if pd.isna(x) or pd.isna(y):
        return None
    return int(round(float(x))), int(round(float(y))), status


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染指定球员和羽毛球短轨迹")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--people-csv", required=True, type=Path)
    parser.add_argument("--ball-csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--selection-frame", type=int, default=0)
    parser.add_argument("--selection-x", required=True, type=float)
    parser.add_argument("--selection-y", required=True, type=float)
    parser.add_argument("--trail-frames", type=int, default=12)
    args = parser.parse_args()

    people = pd.read_csv(args.people_csv)
    target_id = select_target_track(
        people, args.selection_frame, args.selection_x, args.selection_y
    )
    target = people[people["track_id"] == target_id]
    target_by_frame = {int(row.frame): row for row in target.itertuples(index=False)}

    ball = pd.read_csv(args.ball_csv)
    ball_frame_column = "Frame" if "Frame" in ball.columns else "frame"
    ball_by_frame = {
        int(row[ball_frame_column]): row for _, row in ball.iterrows()
    }

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise ValueError(f"无法打开视频：{args.video}")
    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as handle:
        temporary = Path(handle.name)
    writer = cv2.VideoWriter(
        str(temporary), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    trail: deque[tuple[int, int]] = deque(maxlen=max(1, args.trail_frames))

    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break

        person = target_by_frame.get(frame_index)
        if person is not None:
            first = (int(person.x1), int(person.y1))
            second = (int(person.x2), int(person.y2))
            cv2.rectangle(frame, first, second, (255, 180, 0), 3)
            cv2.putText(
                frame,
                "TARGET PLAYER",
                (first[0], max(28, first[1] - 9)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 180, 0),
                2,
                cv2.LINE_AA,
            )

        shuttle = None
        ball_row = ball_by_frame.get(frame_index)
        if ball_row is not None:
            shuttle = read_ball_point(ball_row)
        if shuttle is None:
            trail.clear()
        else:
            x, y, status = shuttle
            point = (x, y)
            trail.append(point)
            points = list(trail)
            for index in range(1, len(points)):
                previous, current = points[index - 1], points[index]
                distance = ((current[0] - previous[0]) ** 2 + (current[1] - previous[1]) ** 2) ** 0.5
                if distance <= 220:
                    cv2.line(frame, previous, current, (0, 210, 255), 3, cv2.LINE_AA)
            color = (0, 255, 255) if status == "detected" else (255, 80, 255)
            cv2.circle(frame, point, 16, color, 3, cv2.LINE_AA)
            cv2.circle(frame, point, 4, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.putText(
                frame,
                "SHUTTLE",
                (x + 18, max(24, y - 12)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            f"t={frame_index / fps:06.2f}s",
            (24, height - 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)
        frame_index += 1

    capture.release()
    writer.release()
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(temporary), "-i", str(args.video),
            "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "libx264", "-preset", "fast",
            "-crf", "18", "-c:a", "aac", "-shortest", str(args.output),
        ],
        check=True,
    )
    temporary.unlink(missing_ok=True)
    print(f"目标人物 Track ID：{target_id}")
    print(args.output)


if __name__ == "__main__":
    main()
