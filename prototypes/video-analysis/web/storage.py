"""本地项目目录与 JSON 持久化。"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(
    os.environ.get("YUJI_WEB_PROJECT_ROOT", "outputs/video-web/projects")
).resolve()
_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_dir(project_id: str) -> Path:
    if not project_id or any(char not in "0123456789abcdef-" for char in project_id):
        raise ValueError("项目 ID 非法")
    path = (PROJECT_ROOT / project_id).resolve()
    if PROJECT_ROOT not in path.parents:
        raise ValueError("项目路径非法")
    return path


def create_project(filename: str, content_type: str | None) -> dict[str, Any]:
    project_id = str(uuid.uuid4())
    root = project_dir(project_id)
    for name in (
        "source",
        "work",
        "candidates",
        "rallies/marked",
        "rallies/original",
        "logs",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)
    project = {
        "id": project_id,
        "filename": filename,
        "content_type": content_type or "application/octet-stream",
        "status": "queued",
        "stage": "等待处理",
        "progress": 0,
        "error": None,
        "warnings": [],
        "media": {},
        "source_file": None,
        "marked_video": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    save_project(project)
    save_candidates(project_id, [])
    save_rallies(project_id, [])
    return project


def _atomic_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def save_project(project: dict[str, Any]) -> None:
    with _LOCK:
        project["updated_at"] = utc_now()
        _atomic_write(project_dir(project["id"]) / "project.json", project)


def load_project(project_id: str) -> dict[str, Any]:
    path = project_dir(project_id) / "project.json"
    if not path.exists():
        raise FileNotFoundError(project_id)
    with _LOCK:
        return json.loads(path.read_text(encoding="utf-8"))


def update_project(project_id: str, **changes: Any) -> dict[str, Any]:
    project = load_project(project_id)
    project.update(changes)
    save_project(project)
    return project


def list_projects() -> list[dict[str, Any]]:
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    projects = []
    for path in PROJECT_ROOT.glob("*/project.json"):
        try:
            projects.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(projects, key=lambda item: item.get("created_at", ""), reverse=True)


def _collection_path(project_id: str, name: str) -> Path:
    return project_dir(project_id) / f"{name}.json"


def load_candidates(project_id: str) -> list[dict[str, Any]]:
    return json.loads(_collection_path(project_id, "candidates").read_text(encoding="utf-8"))


def save_candidates(project_id: str, candidates: list[dict[str, Any]]) -> None:
    with _LOCK:
        _atomic_write(_collection_path(project_id, "candidates"), candidates)


def load_rallies(project_id: str) -> list[dict[str, Any]]:
    return json.loads(_collection_path(project_id, "rallies").read_text(encoding="utf-8"))


def save_rallies(project_id: str, rallies: list[dict[str, Any]]) -> None:
    with _LOCK:
        _atomic_write(_collection_path(project_id, "rallies"), rallies)


def safe_project_file(project_id: str, relative_path: str) -> Path:
    root = project_dir(project_id)
    path = (root / relative_path).resolve()
    if root not in path.parents or not path.is_file():
        raise FileNotFoundError(relative_path)
    return path
