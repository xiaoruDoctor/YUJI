#!/usr/bin/env python3
"""融合人物挥拍和击球声音，生成击球候选与回合候选。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import butter, find_peaks, sosfilt


WRIST_INDICES = (9, 10)


def parse_wrist_center(value: str) -> tuple[float, float]:
    points = np.asarray(json.loads(value), dtype=float)
    wrists = points[list(WRIST_INDICES)]
    return float(np.nanmean(wrists[:, 0])), float(np.nanmean(wrists[:, 1]))


def select_target_players(
    people: pd.DataFrame, frame_width: int
) -> tuple[int, set[int]]:
    """选择持续出现的近场主球员和右侧远场主球员轨迹。"""
    frame = people.copy()
    frame["area"] = (frame["x2"] - frame["x1"]) * (
        frame["y2"] - frame["y1"]
    )
    frame["cx"] = (frame["x1"] + frame["x2"]) / 2
    summary = frame.groupby("track_id").agg(
        frames=("frame", "nunique"),
        median_area=("area", "median"),
        median_cx=("cx", "median"),
    )

    persistent = summary[summary["frames"] >= max(30, people["frame"].nunique() * 0.3)]
    if persistent.empty:
        persistent = summary
    near_track = int(
        persistent.sort_values(["frames", "median_area"], ascending=False).index[0]
    )
    near_area = float(summary.loc[near_track, "median_area"])

    far = summary[
        (summary["median_cx"] >= frame_width * 0.68)
        & (summary["median_area"] <= near_area * 0.9)
        & (summary["frames"] >= 15)
    ]
    return near_track, {int(value) for value in far.index}


def build_motion_signal(
    people: pd.DataFrame,
    frame_count: int,
    near_track: int,
    far_tracks: set[int],
) -> np.ndarray:
    selected = people[
        people["track_id"].eq(near_track) | people["track_id"].isin(far_tracks)
    ].copy()
    wrist_coordinates = np.asarray(
        [parse_wrist_center(value) for value in selected["keypoints_json"]]
    )
    selected["wrist_x"] = wrist_coordinates[:, 0]
    selected["wrist_y"] = wrist_coordinates[:, 1]
    selected = selected.sort_values(["track_id", "frame"])
    selected["wrist_speed"] = np.hypot(
        selected.groupby("track_id")["wrist_x"].diff(),
        selected.groupby("track_id")["wrist_y"].diff(),
    ).clip(0, 120)
    signal = (
        selected.groupby("frame")["wrist_speed"]
        .max()
        .reindex(range(frame_count), fill_value=0)
        .rolling(3, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )
    return signal


def audio_transients(audio_path: Path) -> tuple[int, np.ndarray, np.ndarray]:
    sample_rate, audio = wavfile.read(audio_path)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if np.issubdtype(audio.dtype, np.integer):
        maximum = np.iinfo(audio.dtype).max
        audio = audio.astype(float) / maximum
    else:
        audio = audio.astype(float)

    upper = min(7500, sample_rate / 2 - 100)
    sos = butter(4, [1500, upper], btype="bandpass", fs=sample_rate, output="sos")
    filtered = sosfilt(sos, audio)
    window = max(1, int(sample_rate * 0.008))
    energy = np.sqrt(
        np.convolve(filtered * filtered, np.ones(window) / window, mode="same")
    )
    peaks, _ = find_peaks(
        energy,
        distance=int(sample_rate * 0.16),
        prominence=np.quantile(energy, 0.85),
    )
    return sample_rate, energy, peaks


def detect_hits(
    motion: np.ndarray,
    fps: float,
    sample_rate: int,
    audio_score: np.ndarray,
    audio_peaks: np.ndarray,
    ball_tracks: pd.DataFrame | None = None,
) -> pd.DataFrame:
    motion_positive = motion[motion > 0]
    motion_threshold = (
        float(np.quantile(motion_positive, 0.65)) if len(motion_positive) else 0
    )
    peak_scores = audio_score[audio_peaks]
    audio_soft = float(np.quantile(peak_scores, 0.35))
    audio_strong = float(np.quantile(peak_scores, 0.95))

    candidates = []
    for peak in audio_peaks:
        time_seconds = peak / sample_rate
        frame_index = int(time_seconds * fps)
        start = max(0, frame_index - round(fps * 0.18))
        end = min(len(motion), frame_index + round(fps * 0.18) + 1)
        motion_value = float(motion[start:end].max()) if start < end else 0
        audio_value = float(audio_score[peak])
        has_motion = motion_value >= motion_threshold
        has_audio = audio_value >= audio_soft
        is_strong_audio = audio_value >= audio_strong
        if (has_motion and has_audio) or is_strong_audio:
            has_ball_support = False
            if ball_tracks is not None:
                ball_start = max(0, frame_index - round(fps * 0.15))
                ball_end = frame_index + round(fps * 0.15)
                nearby = ball_tracks[
                    ball_tracks["Frame"].between(ball_start, ball_end)
                ]
                has_ball_support = bool(
                    len(nearby)
                    and nearby["track_status"].isin(["detected", "interpolated"]).any()
                )
            candidates.append(
                {
                    "time": time_seconds,
                    "audio_score": audio_value,
                    "motion_score": motion_value,
                    "has_motion_support": has_motion,
                    "strong_audio_only": is_strong_audio and not has_motion,
                    "has_ball_support": has_ball_support,
                }
            )
    return pd.DataFrame(candidates)


def group_rallies(
    hits: pd.DataFrame,
    motion: np.ndarray,
    fps: float,
    maximum_hit_gap: float,
    active_bridge_gap: float,
    active_motion_ratio: float,
    minimum_hits: int,
    boundary_padding: float,
) -> pd.DataFrame:
    if hits.empty:
        return pd.DataFrame(
            columns=["rally_id", "start", "end", "duration", "stroke_estimate"]
        )

    groups: list[list[dict]] = []
    current: list[dict] = []
    for record in hits.sort_values("time").to_dict("records"):
        if current:
            gap = record["time"] - current[-1]["time"]
            gap_start = max(0, int(current[-1]["time"] * fps))
            gap_end = min(len(motion), int(record["time"] * fps) + 1)
            gap_motion = motion[gap_start:gap_end]
            active_ratio = (
                float(np.mean(gap_motion >= np.quantile(motion[motion > 0], 0.65)))
                if len(gap_motion) and np.any(motion > 0)
                else 0
            )
            should_split = gap > maximum_hit_gap and not (
                gap <= active_bridge_gap and active_ratio >= active_motion_ratio
            )
            if should_split:
                groups.append(current)
                current = []
        current.append(record)
    if current:
        groups.append(current)

    rows = []
    positive_motion = motion[motion > 0]
    active_threshold = (
        float(np.quantile(positive_motion, 0.65)) if len(positive_motion) else 0
    )
    quiet_threshold = active_threshold * 0.5

    def adaptive_start(first_hit: float) -> float:
        first_frame = int(first_hit * fps)
        search_start = max(0, first_frame - int(fps * 2.5))
        quiet_run = max(1, int(fps * 0.35))
        candidate = max(0.0, first_hit - boundary_padding)
        for index in range(first_frame - quiet_run, search_start - 1, -1):
            window = motion[index : index + quiet_run]
            if len(window) == quiet_run and np.all(window <= quiet_threshold):
                candidate = (index + quiet_run) / fps
                break
        return max(0.0, candidate)

    def adaptive_end(last_hit: float) -> float:
        last_frame = int(last_hit * fps)
        search_end = min(len(motion), last_frame + int(fps * 3.0))
        quiet_run = max(1, int(fps * 0.5))
        candidate = min(len(motion) / fps, last_hit + max(1.5, boundary_padding))
        for index in range(last_frame, max(last_frame, search_end - quiet_run)):
            window = motion[index : index + quiet_run]
            if len(window) == quiet_run and np.all(window <= quiet_threshold):
                candidate = index / fps
                break
        return max(last_hit, candidate)

    for group in groups:
        if len(group) < minimum_hits:
            continue
        first = group[0]["time"]
        last = group[-1]["time"]
        start = adaptive_start(first)
        end = adaptive_end(last)
        supported = sum(bool(item["has_motion_support"]) for item in group)
        ball_supported = sum(bool(item.get("has_ball_support")) for item in group)
        evidence_confidence = (supported + ball_supported) / (2 * len(group))
        # 安静窗口只能生成候选边界，不能证明羽毛球已经落地或成为死球。
        # 在接入可靠的落点/下网证据前，自动结果一律保守标为待确认。
        window_not_truncated = start > 0.2 and end < len(motion) / fps - 0.2
        rows.append(
            {
                "rally_id": len(rows) + 1,
                "start": start,
                "end": end,
                "duration": end - start,
                "stroke_estimate": len(group),
                "motion_supported_hits": supported,
                "ball_supported_hits": ball_supported,
                "confidence": evidence_confidence,
                "serve_time": first,
                "landing_time": np.nan,
                "landing_evidence": "未检测到可确认的落地、下网或死球证据",
                "is_complete_rally": False,
                "shot_count_status": "无法计拍",
                "status": (
                    "pending_confirmation"
                    if window_not_truncated
                    else "incomplete_video_window"
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="估算羽毛球击球事件和回合")
    parser.add_argument("--people-csv", required=True, type=Path)
    parser.add_argument("--audio-wav", required=True, type=Path)
    parser.add_argument("--ball-csv", type=Path)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--frame-width", type=int, default=1280)
    parser.add_argument("--hits-output", required=True, type=Path)
    parser.add_argument("--rallies-output", required=True, type=Path)
    parser.add_argument("--maximum-hit-gap", type=float, default=2.2)
    parser.add_argument("--active-bridge-gap", type=float, default=3.5)
    parser.add_argument("--active-motion-ratio", type=float, default=0.3)
    parser.add_argument("--minimum-hits", type=int, default=2)
    parser.add_argument("--boundary-padding", type=float, default=0.8)
    args = parser.parse_args()

    people = pd.read_csv(args.people_csv)
    frame_count = int(people["frame"].max()) + 1
    near_track, far_tracks = select_target_players(people, args.frame_width)
    motion = build_motion_signal(people, frame_count, near_track, far_tracks)
    sample_rate, audio_score, audio_peaks = audio_transients(args.audio_wav)
    ball_tracks = pd.read_csv(args.ball_csv) if args.ball_csv else None
    hits = detect_hits(
        motion,
        args.fps,
        sample_rate,
        audio_score,
        audio_peaks,
        ball_tracks,
    )
    rallies = group_rallies(
        hits,
        motion,
        args.fps,
        args.maximum_hit_gap,
        args.active_bridge_gap,
        args.active_motion_ratio,
        args.minimum_hits,
        args.boundary_padding,
    )

    args.hits_output.parent.mkdir(parents=True, exist_ok=True)
    args.rallies_output.parent.mkdir(parents=True, exist_ok=True)
    hits.to_csv(args.hits_output, index=False)
    rallies.to_csv(args.rallies_output, index=False)
    print(
        json.dumps(
            {
                "near_track": near_track,
                "far_tracks": sorted(far_tracks),
                "hit_candidates": len(hits),
                "rally_candidates": len(rallies),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
