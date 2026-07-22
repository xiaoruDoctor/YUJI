# 雅思组合混双双人标记案例 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为首个雅思组合公开赛视频产出靠近镜头两名球员与羽毛球短轨迹的可追溯标记案例。

**Architecture:** 复用现有 YOLO Pose 与 TrackNet 产出的逐帧 CSV，并把单目标渲染器扩展为双目标渲染器。新增案例运行脚本负责创建不可变的输入清单、调用现有检测脚本、生成标记视频和抽检素材；所有本例产物隔离在 `data/video-cases/yasi-mixed-doubles-2026-07-21/`。

**Tech Stack:** Python 3.11、pandas、OpenCV、Ultralytics YOLO Pose、TrackNetV3、ffmpeg、pytest。

---

## 文件结构

- 修改：`prototypes/video-analysis/scripts/render_focus_video.py`：选择两个不重复人物轨迹并渲染双人框。
- 修改：`prototypes/video-analysis/tests/test_render_focus_video.py`：覆盖双人选择和渲染参数行为。
- 新增：`prototypes/video-analysis/scripts/run_dual_player_case.py`：建立案例目录、生成清单、编排检测、渲染和抽检。
- 新增：`prototypes/video-analysis/tests/test_run_dual_player_case.py`：覆盖清单和抽检时间点的确定性行为。
- 新增：`data/video-cases/yasi-mixed-doubles-2026-07-21/` 下的 `source/`、`detections/`、`outputs/`、`review/` 产物。
- 新增：`data/video-cases/yasi-mixed-doubles-2026-07-21/README.md`：记录实际选择帧、两名球员轨迹 ID、测量结果和版权边界。

### Task 1: 双目标轨迹选择

**Files:**
- Modify: `prototypes/video-analysis/scripts/render_focus_video.py`
- Test: `prototypes/video-analysis/tests/test_render_focus_video.py`

- [ ] **Step 1: 写出双目标选择的失败测试**

```python
from render_focus_video import select_target_tracks

def test_select_target_tracks_returns_two_clicked_boxes() -> None:
    people = pd.DataFrame([
        {"frame": 24, "track_id": 3, "confidence": 0.9, "x1": 40, "y1": 500, "x2": 180, "y2": 800},
        {"frame": 24, "track_id": 8, "confidence": 0.8, "x1": 400, "y1": 480, "x2": 540, "y2": 790},
    ])
    assert select_target_tracks(people, 24, [(100, 650), (470, 620)]) == [3, 8]

def test_select_target_tracks_rejects_duplicate_track() -> None:
    people = pd.DataFrame([
        {"frame": 24, "track_id": 3, "confidence": 0.9, "x1": 40, "y1": 500, "x2": 180, "y2": 800},
    ])
    with pytest.raises(ValueError, match="两个不同"):
        select_target_tracks(people, 24, [(100, 650), (110, 660)])
```

- [ ] **Step 2: 验证测试按预期失败**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_render_focus_video.py -q`

Expected: `ImportError`，因为 `select_target_tracks` 尚未定义。

- [ ] **Step 3: 实现最小双目标选择函数**

```python
def select_target_tracks(
    people: pd.DataFrame, selection_frame: int, selections: list[tuple[float, float]]
) -> list[int]:
    if len(selections) != 2:
        raise ValueError("必须提供两个近场球员选择坐标")
    selected: list[int] = []
    for x, y in selections:
        candidate = select_target_track(
            people[~people["track_id"].isin(selected)], selection_frame, x, y
        )
        if candidate in selected:
            raise ValueError("无法选出两个不同的有效跟踪 ID")
        selected.append(candidate)
    return selected
```

- [ ] **Step 4: 验证选择测试通过**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_render_focus_video.py -q`

Expected: 所有现有与新增选择测试通过。

- [ ] **Step 5: 提交双目标选择实现**

```bash
git add prototypes/video-analysis/scripts/render_focus_video.py prototypes/video-analysis/tests/test_render_focus_video.py
git commit -m "feat: support selecting two target players"
```

### Task 2: 双人框渲染接口

**Files:**
- Modify: `prototypes/video-analysis/scripts/render_focus_video.py`
- Test: `prototypes/video-analysis/tests/test_render_focus_video.py`

- [ ] **Step 1: 写出渲染参数的失败测试**

```python
from render_focus_video import target_styles

def test_target_styles_assigns_stable_distinct_labels() -> None:
    assert target_styles([3, 8]) == {
        3: {"label": "NEAR PLAYER L", "color": (255, 180, 0)},
        8: {"label": "NEAR PLAYER R", "color": (80, 220, 80)},
    }
```

- [ ] **Step 2: 验证失败原因是函数缺失**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_render_focus_video.py::test_target_styles_assigns_stable_distinct_labels -q`

Expected: `ImportError`，因为 `target_styles` 尚未定义。

- [ ] **Step 3: 实现样式映射与 CLI 双坐标参数**

```python
def target_styles(track_ids: list[int]) -> dict[int, dict[str, object]]:
    if len(track_ids) != 2:
        raise ValueError("双人渲染必须包含两个轨迹 ID")
    return {
        track_ids[0]: {"label": "NEAR PLAYER L", "color": (255, 180, 0)},
        track_ids[1]: {"label": "NEAR PLAYER R", "color": (80, 220, 80)},
    }

parser.add_argument("--selection-x2", required=True, type=float)
parser.add_argument("--selection-y2", required=True, type=float)
```

在主循环中，以 `track_id` 为键建立 `target_by_frame`，用 `target_styles()` 的色彩与标签逐个绘制；球点和短轨迹逻辑保持不变。

- [ ] **Step 4: 验证全部渲染单元测试通过**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_render_focus_video.py -q`

Expected: 所有测试通过。

- [ ] **Step 5: 提交双人渲染实现**

```bash
git add prototypes/video-analysis/scripts/render_focus_video.py prototypes/video-analysis/tests/test_render_focus_video.py
git commit -m "feat: render two near-court players"
```

### Task 3: 案例目录与可重现清单

**Files:**
- Create: `prototypes/video-analysis/scripts/run_dual_player_case.py`
- Create: `prototypes/video-analysis/tests/test_run_dual_player_case.py`

- [ ] **Step 1: 写出清单的失败测试**

```python
from run_dual_player_case import write_manifest

def test_write_manifest_records_source_hash_and_media(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_bytes(b"video")
    output = tmp_path / "manifest.json"
    write_manifest(source, output, {"format": {"duration": "3.0"}})
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["source_sha256"] == hashlib.sha256(b"video").hexdigest()
    assert manifest["source_path"] == str(source)
```

- [ ] **Step 2: 验证测试失败**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_run_dual_player_case.py -q`

Expected: `ModuleNotFoundError`，因为案例脚本尚未创建。

- [ ] **Step 3: 实现清单函数与目录初始化**

```python
def write_manifest(source: Path, output: Path, media: dict) -> None:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "source_path": str(source.resolve()),
        "source_sha256": digest,
        "media": media,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def case_paths(case_root: Path) -> dict[str, Path]:
    return {name: case_root / name for name in ("source", "detections", "outputs", "review")}
```

- [ ] **Step 4: 验证清单测试通过**

Run: `.venv-video/bin/python -m pytest prototypes/video-analysis/tests/test_run_dual_player_case.py -q`

Expected: 所有案例脚本测试通过。

- [ ] **Step 5: 提交案例目录基础能力**

```bash
git add prototypes/video-analysis/scripts/run_dual_player_case.py prototypes/video-analysis/tests/test_run_dual_player_case.py
git commit -m "feat: add reproducible video case manifest"
```

### Task 4: 运行首个真实案例与验收产物

**Files:**
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/source/manifest.json`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/detections/people.csv`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_raw.csv`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_fused.csv`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/outputs/near-court-dual-player-shuttle.mp4`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/review/check-*.jpg`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/review/report.json`
- Create: `data/video-cases/yasi-mixed-doubles-2026-07-21/README.md`

- [ ] **Step 1: 初始化清单并跑人物检测**

Run:

```bash
.venv-video/bin/python prototypes/video-analysis/scripts/run_dual_player_case.py \
  --video data/video-cases/badminton-public-2026-07-21/最强混双组合雅思组合_20260721195610.mp4 \
  --case-root data/video-cases/yasi-mixed-doubles-2026-07-21 \
  --people-model .video-research/badminton-pipeline-repro/weights/yolov8s-pose.pt
```

Expected: 创建 `source/manifest.json` 和 `detections/people.csv`。

- [ ] **Step 2: 跑 TrackNet 并融合球轨迹**

Run:

```bash
.venv-video/bin/python .video-research/badminton-pipeline-repro/scripts/tracknet_runtime/predict.py \
  --video_file data/video-cases/badminton-public-2026-07-21/最强混双组合雅思组合_20260721195610.mp4 \
  --tracknet_file .video-research/badminton-pipeline-repro/weights/TrackNet_best.pt \
  --save_dir data/video-cases/yasi-mixed-doubles-2026-07-21/detections/tracknet \
  --device mps --eval_mode nonoverlap --batch_size 8 --large_video
.venv-video/bin/python prototypes/video-analysis/scripts/fuse_signals.py \
  --ball-csv data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_raw.csv \
  --output-csv data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_fused.csv \
  --summary-json data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_summary.json
```

Expected: 原始与融合 CSV、球轨迹摘要存在。

- [ ] **Step 3: 在稳定比赛帧选定两名近场球员并渲染**

从 1 秒开始每秒抽帧，选择没有片头文字、两名近场红衣球员完整可见的帧；把左球员与右球员身体内的坐标传入渲染器：

```bash
.venv-video/bin/python prototypes/video-analysis/scripts/render_focus_video.py \
  --video data/video-cases/badminton-public-2026-07-21/最强混双组合雅思组合_20260721195610.mp4 \
  --people-csv data/video-cases/yasi-mixed-doubles-2026-07-21/detections/people.csv \
  --ball-csv data/video-cases/yasi-mixed-doubles-2026-07-21/detections/ball_fused.csv \
  --selection-frame 24 --selection-x 205 --selection-y 760 \
  --selection-x2 430 --selection-y2 740 \
  --output data/video-cases/yasi-mixed-doubles-2026-07-21/outputs/near-court-dual-player-shuttle.mp4
```

Expected: 输出保留原音频，且只标记两个近场球员。

- [ ] **Step 4: 写入抽检与统计报告**

在 10%、30%、50%、70%、90% 片段各导出一帧到 `review/check-*.jpg`；报告 JSON 至少包含：两条轨迹 ID、各自有框帧数与覆盖率、球直接检测帧数、插值帧数、球覆盖率，以及四类错误各自初始计数。

- [ ] **Step 5: 用 ffprobe 和 pytest 完成验证**

Run:

```bash
.venv-video/bin/python -m pytest prototypes/video-analysis/tests -q
ffprobe -v error -show_entries stream=codec_type,codec_name -of json \
  data/video-cases/yasi-mixed-doubles-2026-07-21/outputs/near-court-dual-player-shuttle.mp4
```

Expected: pytest 无失败；ffprobe 同时返回 `h264` 视频流与 `aac` 音频流。

- [ ] **Step 6: 提交代码和文本记录，不提交大视频与模型产物**

```bash
git add prototypes/video-analysis/scripts/render_focus_video.py \
  prototypes/video-analysis/scripts/run_dual_player_case.py \
  prototypes/video-analysis/tests/test_render_focus_video.py \
  prototypes/video-analysis/tests/test_run_dual_player_case.py \
  data/video-cases/yasi-mixed-doubles-2026-07-21/README.md
git commit -m "feat: add yasi mixed doubles marking case"
```
