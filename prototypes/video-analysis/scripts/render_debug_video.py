#!/usr/bin/env python3
"""渲染人物、羽毛球轨迹、击球候选和回合状态调试视频。"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections import deque
from math import hypot
from pathlib import Path

import cv2
import pandas as pd


def is_plausible_shuttle(point: tuple[int, int], people_frame: pd.DataFrame) -> bool:
    """抑制落在人物身体内部、且远离双手腕的明显球体误检。"""
    x, y = point
    for person in people_frame.itertuples(index=False):
        if not (person.x1 <= x <= person.x2 and person.y1 <= y <= person.y2):
            continue
        try:
            keypoints = json.loads(person.keypoints_json)
            wrists = (keypoints[9], keypoints[10])
            near_wrist = any(hypot(x - wrist[0], y - wrist[1]) <= 90 for wrist in wrists)
        except (IndexError, TypeError, ValueError, json.JSONDecodeError):
            near_wrist = False
        if not near_wrist:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="生成羽迹算法调试视频")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--people-csv", required=True, type=Path)
    parser.add_argument("--ball-csv", required=True, type=Path)
    parser.add_argument("--hits-csv", required=True, type=Path)
    parser.add_argument("--rallies-csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--trail-frames", type=int, default=18)
    args = parser.parse_args()

    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temporary_file:
        temporary = Path(temporary_file.name)
    writer = cv2.VideoWriter(
        str(temporary), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    people = pd.read_csv(args.people_csv)
    people_by_frame = {
        int(frame_id): frame_rows
        for frame_id, frame_rows in people.groupby("frame", sort=False)
    }
    ball = pd.read_csv(args.ball_csv).set_index("Frame")
    hits = pd.read_csv(args.hits_csv)
    rallies = pd.read_csv(args.rallies_csv)
    hit_frames = {int(round(value * fps)): index + 1 for index, value in enumerate(hits.time)}
    trail: deque[tuple[int, int, str]] = deque(maxlen=args.trail_frames)

    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        time_seconds = frame_index / fps

        current_rally = rallies[
            (rallies["start"] <= time_seconds) & (rallies["end"] >= time_seconds)
        ]
        if len(current_rally):
            rally = current_rally.iloc[0]
            is_complete = str(rally.is_complete_rally).lower() == "true"
            color = (0, 220, 0) if is_complete else (0, 165, 255)
            cv2.putText(
                frame,
                f"CANDIDATE {int(rally.rally_id):02d}  {getattr(rally, 'status', 'candidate')}",
                (30, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
                cv2.LINE_AA,
            )
        else:
            cv2.putText(
                frame,
                "BETWEEN RALLIES",
                (30, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (180, 180, 180),
                2,
                cv2.LINE_AA,
            )

        nearby_hits = [
            number
            for hit_frame, number in hit_frames.items()
            if abs(hit_frame - frame_index) <= max(1, int(fps * 0.08))
        ]

        people_frame = people_by_frame.get(frame_index, people.iloc[0:0])
        for person in people_frame.itertuples(index=False):
            cv2.rectangle(
                frame,
                (int(person.x1), int(person.y1)),
                (int(person.x2), int(person.y2)),
                (255, 180, 0),
                2,
            )
            cv2.putText(
                frame,
                f"P{int(person.track_id)}",
                (int(person.x1), max(20, int(person.y1) - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 180, 0),
                2,
                cv2.LINE_AA,
            )

        shuttle_point = None
        shuttle_status = "missing"
        if frame_index in ball.index:
            shuttle = ball.loc[frame_index]
            if shuttle.track_status in {"detected", "interpolated"}:
                shuttle_point = (int(shuttle.X_fused), int(shuttle.Y_fused))
                shuttle_status = str(shuttle.track_status)
                if not is_plausible_shuttle(shuttle_point, people_frame):
                    shuttle_point = None
                    shuttle_status = "body_false_positive"
                    trail.clear()
                    continue_drawing = False
                else:
                    continue_drawing = True
            else:
                continue_drawing = False
            if continue_drawing:
                shuttle_color = (
                    (0, 255, 255)
                    if shuttle.track_status == "detected"
                    else (255, 80, 255)
                )
                trail.append((*shuttle_point, shuttle_status))
                # 使用克制的小光圈；击球瞬间只做轻微放大，避免遮挡人物和球路。
                overlay = frame.copy()
                glow_radius = 23 if nearby_hits else 16
                cv2.circle(overlay, shuttle_point, glow_radius + 5, shuttle_color, 2)
                cv2.circle(overlay, shuttle_point, glow_radius, shuttle_color, 4)
                cv2.circle(overlay, shuttle_point, 8, (255, 255, 255), 2)
                cv2.circle(overlay, shuttle_point, 3, shuttle_color, -1)
                frame = cv2.addWeighted(
                    overlay, 0.62 if nearby_hits else 0.52, frame, 0.38 if nearby_hits else 0.48, 0
                )
                cv2.putText(
                    frame, "SHUTTLE", (shuttle_point[0] + 20, shuttle_point[1] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, shuttle_color, 1, cv2.LINE_AA,
                )

        # 连续拖尾与方向线；丢失后不外推、不继续画假点。
        points = list(trail)
        if shuttle_point is not None:
            for index in range(1, len(points)):
                previous = points[index - 1][:2]
                current = points[index][:2]
                step_distance = ((current[0] - previous[0]) ** 2 + (current[1] - previous[1]) ** 2) ** 0.5
                if step_distance > 220:
                    continue
                alpha = index / max(1, len(points) - 1)
                color = (0, int(100 + 155 * alpha), 255)
                thickness = max(1, int(3 * alpha))
                cv2.line(
                    frame,
                    previous,
                    current,
                    (20, 20, 20),
                    thickness + 2,
                    cv2.LINE_AA,
                )
                cv2.line(
                    frame,
                    previous,
                    current,
                    color,
                    thickness,
                    cv2.LINE_AA,
                )
            if len(points) >= 2:
                previous = points[-2][:2]
                current = points[-1][:2]
                step_distance = ((current[0] - previous[0]) ** 2 + (current[1] - previous[1]) ** 2) ** 0.5
                if step_distance <= 220:
                    cv2.arrowedLine(
                        frame, previous, current, (255, 255, 255), 1, cv2.LINE_AA, tipLength=0.25
                    )
        else:
            trail.clear()
        if nearby_hits:
            cv2.putText(
                frame,
                f"HIT {nearby_hits[-1]}",
                (width - 180, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            f"t={time_seconds:06.2f}s",
            (30, height - 24),
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
    print(args.output)


if __name__ == "__main__":
    main()
