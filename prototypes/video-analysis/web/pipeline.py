"""把现有视频算法脚本编排成本地单任务处理管线。"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

from .storage import project_dir, update_project


REPO_ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_ROOT = REPO_ROOT / "prototypes/video-analysis"
SCRIPTS = PROTOTYPE_ROOT / "scripts"
PYTHON = Path(os.environ.get("YUJI_VIDEO_PYTHON", REPO_ROOT / ".venv-video/bin/python"))
RESEARCH_ROOT = REPO_ROOT / ".video-research/badminton-pipeline-repro"
TRACKNET_SCRIPT = Path(os.environ.get(
    "YUJI_TRACKNET_SCRIPT", RESEARCH_ROOT / "scripts/tracknet_runtime/predict.py"
))
TRACKNET_WEIGHT = Path(os.environ.get(
    "YUJI_TRACKNET_WEIGHT", RESEARCH_ROOT / "weights/TrackNet_best.pt"
))
YOLO_WEIGHT = Path(os.environ.get(
    "YUJI_YOLO_WEIGHT", RESEARCH_ROOT / "weights/yolov8s-pose.pt"
))


def _run(command: list[str], log: Path, cwd: Path | None = None) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write("\n$ " + " ".join(command) + "\n")
        handle.flush()
        subprocess.run(
            command,
            cwd=str(cwd or REPO_ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=True,
            text=True,
            env={**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "1"},
        )


def _ffprobe(video: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate",
            "-of", "json", str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _extract_audio(video: Path, output: Path, media: dict, log: Path) -> None:
    has_audio = any(item.get("codec_type") == "audio" for item in media.get("streams", []))
    if has_audio:
        command = [
            "ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn",
            "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output),
        ]
    else:
        duration = float(media["format"]["duration"])
        command = [
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
            "anullsrc=r=16000:cl=mono", "-t", f"{duration:.3f}",
            "-c:a", "pcm_s16le", str(output),
        ]
    _run(command, log)


def _missing_ball_csv(video: Path, output: Path) -> None:
    media = _ffprobe(video)
    duration = float(media["format"]["duration"])
    video_stream = next(item for item in media["streams"] if item["codec_type"] == "video")
    numerator, denominator = video_stream["avg_frame_rate"].split("/")
    fps = float(numerator) / float(denominator)
    frames = round(duration * fps)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Frame", "Visibility", "X", "Y"])
        for frame in range(frames):
            writer.writerow([frame, 0, 0, 0])


def _candidate_records(csv_path: Path) -> list[dict]:
    frame = pd.read_csv(csv_path)
    records = []
    for row in frame.to_dict("records"):
        candidate_id = int(row["rally_id"])
        records.append({
            "id": candidate_id,
            "candidate_start": round(float(row["start"]), 3),
            "candidate_end": round(float(row["end"]), 3),
            "serve_time": round(float(row["serve_time"]), 3),
            "landing_time": None,
            "landing_evidence": "",
            "is_complete_rally": False,
            "shot_count": None,
            "shot_count_status": "无法计拍",
            "status": "pending_confirmation",
            "marked_video": None,
            "original_video": None,
        })
    return records


def process_project(project_id: str) -> None:
    root = project_dir(project_id)
    log = root / "logs/processing.log"
    project = update_project(project_id, status="processing", stage="读取视频", progress=3, error=None)
    source = root / project["source_file"]
    work = root / "work"
    work.mkdir(exist_ok=True)
    people_csv = work / "people.csv"
    ball_raw = work / "ball_raw.csv"
    ball_fused = work / "ball_fused.csv"
    ball_summary = work / "ball_summary.json"
    audio = work / "audio.wav"
    hits = work / "hits.csv"
    candidates_csv = work / "candidates.csv"
    marked = root / "marked_full.mp4"

    try:
        media = _ffprobe(source)
        update_project(project_id, media=media, stage="人物跟踪", progress=8)
        _run([
            str(PYTHON), str(SCRIPTS / "detect_people.py"),
            "--video", str(source), "--model", str(YOLO_WEIGHT),
            "--output", str(people_csv), "--device", "auto",
        ], log)

        update_project(project_id, stage="羽毛球轨迹", progress=38)
        if TRACKNET_SCRIPT.exists() and TRACKNET_WEIGHT.exists() and TRACKNET_WEIGHT.stat().st_size > 1_000_000:
            tracknet_dir = work / "tracknet"
            _run([
                str(PYTHON), str(TRACKNET_SCRIPT), "--video_file", str(source),
                "--tracknet_file", str(TRACKNET_WEIGHT), "--save_dir", str(tracknet_dir),
                "--device", "mps", "--eval_mode", "nonoverlap", "--batch_size", "8",
                "--large_video",
            ], log)
            generated = next(tracknet_dir.glob("*_ball.csv"))
            shutil.copy2(generated, ball_raw)
        else:
            _missing_ball_csv(source, ball_raw)
            project = update_project(project_id)
            warnings = project.get("warnings", [])
            warnings.append("未找到 TrackNet 权重，本次只运行人物与音频候选。")
            update_project(project_id, warnings=warnings)

        _run([
            str(PYTHON), str(SCRIPTS / "fuse_signals.py"),
            "--ball-csv", str(ball_raw), "--output-csv", str(ball_fused),
            "--summary-json", str(ball_summary),
        ], log)
        update_project(project_id, stage="击球与候选分析", progress=68)
        _extract_audio(source, audio, media, log)
        _run([
            str(PYTHON), str(SCRIPTS / "estimate_rallies.py"),
            "--people-csv", str(people_csv), "--audio-wav", str(audio),
            "--ball-csv", str(ball_fused), "--hits-output", str(hits),
            "--rallies-output", str(candidates_csv),
        ], log)

        from .storage import save_candidates
        save_candidates(project_id, _candidate_records(candidates_csv))
        update_project(project_id, stage="生成完整标记视频", progress=78)
        _run([
            str(PYTHON), str(SCRIPTS / "render_debug_video.py"),
            "--video", str(source), "--people-csv", str(people_csv),
            "--ball-csv", str(ball_fused), "--hits-csv", str(hits),
            "--rallies-csv", str(candidates_csv), "--output", str(marked),
        ], log)
        update_project(
            project_id,
            status="review",
            stage="等待人工确认",
            progress=100,
            marked_video="marked_full.mp4",
        )
    except Exception as exc:
        update_project(
            project_id,
            status="failed",
            stage="处理失败",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


def fake_process_project(project_id: str) -> None:
    """测试模式：不运行模型，只创建一个待确认候选。"""
    from .storage import load_project, save_candidates
    root = project_dir(project_id)
    project = load_project(project_id)
    source = root / project["source_file"]
    media = _ffprobe(source)
    duration = float(media["format"]["duration"])
    marked = root / "marked_full.mp4"
    shutil.copy2(source, marked)
    save_candidates(project_id, [{
        "id": 1,
        "candidate_start": 0.0,
        "candidate_end": round(duration, 3),
        "serve_time": 0.0,
        "landing_time": None,
        "landing_evidence": "",
        "is_complete_rally": False,
        "shot_count": None,
        "shot_count_status": "无法计拍",
        "status": "pending_confirmation",
        "marked_video": None,
        "original_video": None,
    }])
    update_project(
        project_id, status="review", stage="等待人工确认", progress=100,
        media=media, marked_video="marked_full.mp4",
    )


PROCESSOR: Callable[[str], None] = (
    fake_process_project if os.environ.get("YUJI_WEB_FAKE_PROCESSING") == "1" else process_project
)
