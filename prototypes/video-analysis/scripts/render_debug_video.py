#!/usr/bin/env python3
"""渲染人物、羽毛球轨迹、击球候选和回合状态调试视频。"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="生成羽迹算法调试视频")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--people-csv", required=True, type=Path)
    parser.add_argument("--ball-csv", required=True, type=Path)
    parser.add_argument("--hits-csv", required=True, type=Path)
    parser.add_argument("--rallies-csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    people = pd.read_csv(args.people_csv)
    ball = pd.read_csv(args.ball_csv).set_index("Frame")
    hits = pd.read_csv(args.hits_csv)
    rallies = pd.read_csv(args.rallies_csv)
    target_track_ids = {1, 3, 12, 30}
    hit_frames = {int(round(value * fps)): index + 1 for index, value in enumerate(hits.time)}

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
            color = (0, 220, 0) if bool(rally.is_complete_rally) else (0, 165, 255)
            cv2.putText(
                frame,
                f"RALLY {int(rally.rally_id):02d}  strokes~{int(rally.stroke_estimate)}  conf={rally.confidence:.2f}",
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

        people_frame = people[
            (people["frame"] == frame_index)
            & (people["track_id"].isin(target_track_ids))
        ]
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

        if frame_index in ball.index:
            shuttle = ball.loc[frame_index]
            if shuttle.track_status in {"detected", "interpolated"}:
                shuttle_color = (
                    (0, 255, 255)
                    if shuttle.track_status == "detected"
                    else (0, 140, 255)
                )
                cv2.circle(
                    frame,
                    (int(shuttle.X_fused), int(shuttle.Y_fused)),
                    7,
                    shuttle_color,
                    -1,
                )

        nearby_hits = [
            number
            for hit_frame, number in hit_frames.items()
            if abs(hit_frame - frame_index) <= max(1, int(fps * 0.08))
        ]
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
    print(args.output)


if __name__ == "__main__":
    main()

