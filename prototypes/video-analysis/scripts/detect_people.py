#!/usr/bin/env python3
"""使用 YOLO Pose 输出逐帧人物框、跟踪 ID 和人体关键点。"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import torch
from ultralytics import YOLO


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(description="检测羽毛球视频中的人物和姿态")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--confidence", type=float, default=0.25)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(args.model))
    device = choose_device(args.device)
    results = model.track(
        source=str(args.video),
        classes=[0],
        conf=args.confidence,
        device=device,
        persist=True,
        stream=True,
        verbose=False,
    )

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frame",
                "track_id",
                "confidence",
                "x1",
                "y1",
                "x2",
                "y2",
                "keypoints_json",
            ],
        )
        writer.writeheader()
        for frame_index, result in enumerate(results):
            if result.boxes is None:
                continue
            boxes = result.boxes.xyxy.detach().cpu().numpy()
            confidences = result.boxes.conf.detach().cpu().numpy()
            track_ids = (
                result.boxes.id.detach().cpu().numpy().astype(int)
                if result.boxes.id is not None
                else [-1] * len(boxes)
            )
            keypoints = (
                result.keypoints.xy.detach().cpu().numpy()
                if result.keypoints is not None
                else [None] * len(boxes)
            )
            for box, confidence, track_id, points in zip(
                boxes, confidences, track_ids, keypoints
            ):
                writer.writerow(
                    {
                        "frame": frame_index,
                        "track_id": int(track_id),
                        "confidence": float(confidence),
                        "x1": float(box[0]),
                        "y1": float(box[1]),
                        "x2": float(box[2]),
                        "y2": float(box[3]),
                        "keypoints_json": ""
                        if points is None
                        else json.dumps(points.tolist()),
                    }
                )


if __name__ == "__main__":
    main()
