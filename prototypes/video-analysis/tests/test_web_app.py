"""羽迹本地视频网页接口测试。"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("YUJI_WEB_PROJECT_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("YUJI_WEB_FAKE_PROCESSING", "1")
    prototype = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(prototype))
    for name in ["web.app", "web.pipeline", "web.storage"]:
        sys.modules.pop(name, None)
    app_module = importlib.import_module("web.app")
    with TestClient(app_module.app) as test_client:
        yield test_client
    app_module.EXECUTOR.shutdown(wait=True)


def make_video(path: Path, duration: float = 1.0) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
        f"color=c=black:s=320x180:d={duration}", "-f", "lavfi", "-i",
        f"anullsrc=r=44100:cl=mono:d={duration}", "-c:v", "libx264",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ], check=True)


def create_project(client: TestClient, tmp_path: Path) -> dict:
    video = tmp_path / "sample.mp4"
    make_video(video)
    with video.open("rb") as handle:
        response = client.post("/api/projects", files={"video": (video.name, handle, "video/mp4")})
    assert response.status_code == 202
    project = response.json()
    for _ in range(50):
        project = client.get(f"/api/projects/{project['id']}").json()
        if project["status"] == "review":
            return project
        time.sleep(0.02)
    raise AssertionError("测试项目未完成")


def test_rejects_unsupported_file(client: TestClient) -> None:
    response = client.post("/api/projects", files={"video": ("bad.txt", b"bad", "text/plain")})
    assert response.status_code == 415


def test_project_persists_and_exposes_candidate(client: TestClient, tmp_path: Path) -> None:
    project = create_project(client, tmp_path)
    assert project["source_url"]
    assert project["marked_video_url"]
    candidates = client.get(f"/api/projects/{project['id']}/candidates").json()
    assert len(candidates) == 1
    assert candidates[0]["status"] == "pending_confirmation"
    assert candidates[0]["is_complete_rally"] is False


def test_candidate_requires_valid_dead_ball_evidence(client: TestClient, tmp_path: Path) -> None:
    project = create_project(client, tmp_path)
    project_id = project["id"]
    response = client.post(f"/api/projects/{project_id}/candidates/1/confirm")
    assert response.status_code == 422

    response = client.patch(
        f"/api/projects/{project_id}/candidates/1",
        json={"serve_time": 0.8, "landing_time": 0.2, "landing_evidence": "可见落地"},
    )
    assert response.status_code == 422


def test_confirm_exports_marked_and_original_versions(client: TestClient, tmp_path: Path) -> None:
    project = create_project(client, tmp_path)
    project_id = project["id"]
    response = client.patch(
        f"/api/projects/{project_id}/candidates/1",
        json={
            "serve_time": 0.1,
            "landing_time": 0.8,
            "landing_evidence": "测试画面中可见落地",
            "shot_count": None,
            "shot_count_status": "无法计拍",
        },
    )
    assert response.status_code == 200
    response = client.post(f"/api/projects/{project_id}/candidates/1/confirm")
    assert response.status_code == 200
    rally = response.json()
    assert rally["is_complete_rally"] is True
    assert client.get(rally["marked_video_url"]).status_code == 200
    assert client.get(rally["original_video_url"]).status_code == 200
    rallies = client.get(f"/api/projects/{project_id}/rallies").json()
    assert len(rallies) == 1
