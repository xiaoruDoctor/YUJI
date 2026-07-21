"""羽迹本地视频切球网页 FastAPI 服务。"""

from __future__ import annotations

import shutil
import subprocess
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .pipeline import PROCESSOR
from .storage import (
    PROJECT_ROOT,
    create_project,
    list_projects,
    load_candidates,
    load_project,
    load_rallies,
    project_dir,
    safe_project_file,
    save_candidates,
    save_project,
    save_rallies,
    update_project,
)


STATIC_ROOT = Path(__file__).resolve().parent / "static"
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="yuji-video")
SUBMITTED: set[str] = set()
SUBMITTED_LOCK = threading.Lock()

@asynccontextmanager
async def lifespan(_: FastAPI):
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    for project in list_projects():
        if project.get("status") == "processing":
            update_project(
                project["id"], status="failed", stage="处理被中断",
                error="服务上次退出时任务仍在运行，请点击重新处理。",
            )
    yield


app = FastAPI(title="羽迹本地视频切球", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


class CandidateUpdate(BaseModel):
    serve_time: float = Field(ge=0)
    landing_time: float | None = Field(default=None, ge=0)
    landing_evidence: str = Field(default="", max_length=500)
    shot_count: int | None = Field(default=None, ge=1)
    shot_count_status: str = "无法计拍"


def _get_project(project_id: str) -> dict:
    try:
        return load_project(project_id)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="项目不存在") from None


def _file_url(project_id: str, relative_path: str | None) -> str | None:
    return f"/api/files/{project_id}/{relative_path}" if relative_path else None


def _decorate_project(project: dict) -> dict:
    result = dict(project)
    result["source_url"] = _file_url(project["id"], project.get("source_file"))
    result["marked_video_url"] = _file_url(project["id"], project.get("marked_video"))
    result["log_url"] = _file_url(project["id"], "logs/processing.log")
    return result


def _decorate_item(project_id: str, item: dict) -> dict:
    result = dict(item)
    result["marked_video_url"] = _file_url(project_id, item.get("marked_video"))
    result["original_video_url"] = _file_url(project_id, item.get("original_video"))
    return result


def _run_project(project_id: str) -> None:
    try:
        PROCESSOR(project_id)
    except Exception:
        pass
    finally:
        with SUBMITTED_LOCK:
            SUBMITTED.discard(project_id)


def submit_project(project_id: str) -> None:
    with SUBMITTED_LOCK:
        if project_id in SUBMITTED:
            return
        SUBMITTED.add(project_id)
    EXECUTOR.submit(_run_project, project_id)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/api/projects")
def projects() -> list[dict]:
    return [_decorate_project(project) for project in list_projects()]


@app.post("/api/projects", status_code=202)
def upload_project(video: UploadFile = File(...)) -> dict:
    original_name = Path(video.filename or "video.mp4").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="仅支持 MP4、MOV、M4V、AVI、MKV 视频")
    project = create_project(original_name, video.content_type)
    root = project_dir(project["id"])
    relative = f"source/input{extension}"
    target = root / relative
    try:
        with target.open("wb") as handle:
            shutil.copyfileobj(video.file, handle, length=1024 * 1024)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    project["source_file"] = relative
    project["size"] = target.stat().st_size
    save_project(project)
    submit_project(project["id"])
    return _decorate_project(project)


@app.get("/api/projects/{project_id}")
def project_detail(project_id: str) -> dict:
    return _decorate_project(_get_project(project_id))


@app.post("/api/projects/{project_id}/retry", status_code=202)
def retry_project(project_id: str) -> dict:
    project = _get_project(project_id)
    if project["status"] == "processing":
        raise HTTPException(status_code=409, detail="项目正在处理中")
    project = update_project(
        project_id, status="queued", stage="等待重新处理", progress=0, error=None
    )
    submit_project(project_id)
    return _decorate_project(project)


@app.get("/api/projects/{project_id}/candidates")
def candidates(project_id: str) -> list[dict]:
    _get_project(project_id)
    return [_decorate_item(project_id, item) for item in load_candidates(project_id)]


@app.patch("/api/projects/{project_id}/candidates/{candidate_id}")
def update_candidate(project_id: str, candidate_id: int, payload: CandidateUpdate) -> dict:
    _get_project(project_id)
    items = load_candidates(project_id)
    candidate = next((item for item in items if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选不存在")
    if candidate.get("is_complete_rally"):
        raise HTTPException(status_code=409, detail="正式回合不能再修改，请保留原始证据")
    if payload.landing_time is not None and payload.serve_time >= payload.landing_time:
        raise HTTPException(status_code=422, detail="死球时间必须晚于发球时间")
    candidate.update(payload.model_dump())
    candidate["status"] = "pending_confirmation"
    candidate["is_complete_rally"] = False
    save_candidates(project_id, items)
    return _decorate_item(project_id, candidate)


@app.delete("/api/projects/{project_id}/candidates/{candidate_id}", status_code=204)
def delete_candidate(project_id: str, candidate_id: int) -> None:
    _get_project(project_id)
    items = load_candidates(project_id)
    remaining = [item for item in items if item["id"] != candidate_id]
    if len(remaining) == len(items):
        raise HTTPException(status_code=404, detail="候选不存在")
    deleted = next(item for item in items if item["id"] == candidate_id)
    if deleted.get("is_complete_rally"):
        raise HTTPException(status_code=409, detail="正式回合不能作为误识别候选删除")
    save_candidates(project_id, remaining)


def _cut_video(source: Path, start: float, end: float, output: Path, crf: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-i", str(source), "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
        "-c:a", "aac", str(output),
    ], check=True)


@app.post("/api/projects/{project_id}/candidates/{candidate_id}/confirm")
def confirm_candidate(project_id: str, candidate_id: int) -> dict:
    project = _get_project(project_id)
    items = load_candidates(project_id)
    candidate = next((item for item in items if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="候选不存在")
    if candidate.get("is_complete_rally"):
        existing = next(
            (item for item in load_rallies(project_id) if item.get("candidate_id") == candidate_id),
            None,
        )
        if existing:
            return _decorate_item(project_id, existing)
        raise HTTPException(status_code=409, detail="该候选已经确认")
    serve = candidate.get("serve_time")
    landing = candidate.get("landing_time")
    evidence = candidate.get("landing_evidence", "").strip()
    if serve is None or landing is None or not evidence:
        raise HTTPException(status_code=422, detail="必须填写发球时间、死球时间和结束证据")
    if float(serve) >= float(landing):
        raise HTTPException(status_code=422, detail="死球时间必须晚于发球时间")

    root = project_dir(project_id)
    rally_number = len(load_rallies(project_id)) + 1
    marked_relative = f"rallies/marked/rally_{rally_number:03d}.mp4"
    original_relative = f"rallies/original/rally_{rally_number:03d}.mp4"
    try:
        _cut_video(root / project["marked_video"], serve, landing, root / marked_relative, 18)
        _cut_video(root / project["source_file"], serve, landing, root / original_relative, 17)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"回合导出失败：{exc}") from exc

    candidate.update({
        "is_complete_rally": True,
        "status": "complete_dead_ball_confirmed",
        "marked_video": marked_relative,
        "original_video": original_relative,
    })
    save_candidates(project_id, items)
    rallies = load_rallies(project_id)
    rally = {**candidate, "rally_id": rally_number, "candidate_id": candidate_id}
    rallies.append(rally)
    save_rallies(project_id, rallies)
    return _decorate_item(project_id, rally)


@app.get("/api/projects/{project_id}/rallies")
def rallies(project_id: str) -> list[dict]:
    _get_project(project_id)
    return [_decorate_item(project_id, item) for item in load_rallies(project_id)]


@app.get("/api/files/{project_id}/{relative_path:path}")
def project_file(project_id: str, relative_path: str) -> FileResponse:
    try:
        path = safe_project_file(project_id, relative_path)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="文件不存在") from None
    return FileResponse(path, filename=path.name if "rallies/" in relative_path else None)

