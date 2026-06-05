#!/usr/bin/env python3
"""YUJI 本地 Markdown 到飞书在线文档的增量同步脚本。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
COMPANY_ROOT = DOCS_ROOT / "yuji-company"
INDEX_PATH = COMPANY_ROOT / "feishu-sync-index.md"
STATE_PATH = COMPANY_ROOT / ".feishu-sync-state.json"
REPORT_DIR = COMPANY_ROOT / "sync-reports"
TMP_DIR = ROOT / ".yuji-sync-tmp"

WIKI_SPACE_ID = "7507296694975905820"
WIKI_PARENT_NODE_TOKEN = "GSh5wwHU6iA6YqkbX4IcDATSnbh"
TIMEZONE = ZoneInfo("Asia/Shanghai")

EXCLUDED_RELATIVE_PATHS = {
    "docs/yuji-company/feishu-sync-index.md",
    "docs/yuji-company/.feishu-sync-state.json",
}

EXCLUDED_PREFIXES = (
    "docs/yuji-company/sync-reports/",
)


@dataclass
class SyncResult:
    path: str
    title: str
    action: str
    status: str
    url: str = ""
    error: str = ""


def now_local() -> datetime:
    return datetime.now(TIMEZONE)


def rel_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def should_sync(path: Path) -> bool:
    relative = rel_path(path)
    if relative in EXCLUDED_RELATIVE_PATHS:
        return False
    if any(relative.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if any(part.startswith(".") for part in Path(relative).parts):
        return False
    return path.suffix.lower() == ".md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "version": 1,
            "space_id": WIKI_SPACE_ID,
            "parent_node_token": WIKI_PARENT_NODE_TOKEN,
            "items": {},
        }
    with STATE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)
        file.write("\n")


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n") :]
    return text


def extract_title(path: Path, text: str) -> str:
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter_match:
        title_match = re.search(r"^title:\s*(.+)$", frontmatter_match.group(1), re.MULTILINE)
        if title_match:
            return title_match.group(1).strip().strip('"').strip("'")

    xml_title = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    if xml_title:
        return re.sub(r"\s+", " ", xml_title.group(1)).strip()

    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()

    return path.stem


def prepare_markdown(path: Path, title: str, synced_at: str) -> Path:
    original = path.read_text(encoding="utf-8")
    body = strip_frontmatter(original)
    body = re.sub(r"<title>.*?</title>\s*", "", body, count=1, flags=re.DOTALL).lstrip()
    body = re.sub(r"^# .+?\n+", "", body, count=1)

    relative = rel_path(path)
    safe_name = hashlib.sha1(relative.encode("utf-8")).hexdigest() + ".md"
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = TMP_DIR / safe_name

    content = (
        f"# {title}\n\n"
        f"> 本文档由 Codex 从本地文件 `{relative}` 同步到飞书。\n"
        f"> 最近同步时间：{synced_at}\n\n"
        f"{body.rstrip()}\n"
    )
    temp_path.write_text(content, encoding="utf-8")
    return temp_path


def parse_json_output(output: str) -> dict[str, Any]:
    start = output.find("{")
    if start == -1:
        raise ValueError(output.strip() or "命令没有返回 JSON")
    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(output[start:])
    return data


def run_lark(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise RuntimeError(combined.strip() or f"命令失败：{' '.join(args)}")
    return parse_json_output(combined)


def create_remote_doc(temp_path: Path, dry_run: bool) -> dict[str, Any]:
    relative_temp = rel_path(temp_path)
    args = [
        "lark-cli",
        "docs",
        "+create",
        "--api-version",
        "v2",
        "--as",
        "user",
        "--parent-token",
        WIKI_PARENT_NODE_TOKEN,
        "--doc-format",
        "markdown",
        "--content",
        f"@{relative_temp}",
    ]
    if dry_run:
        args.append("--dry-run")
    return run_lark(args)


def update_remote_doc(doc: str, temp_path: Path, dry_run: bool) -> dict[str, Any]:
    relative_temp = rel_path(temp_path)
    args = [
        "lark-cli",
        "docs",
        "+update",
        "--api-version",
        "v2",
        "--as",
        "user",
        "--doc",
        doc,
        "--command",
        "overwrite",
        "--doc-format",
        "markdown",
        "--content",
        f"@{relative_temp}",
    ]
    if dry_run:
        args.append("--dry-run")
    return run_lark(args)


def remote_doc_from_create(data: dict[str, Any]) -> tuple[str, str]:
    document = data.get("data", {}).get("document", {})
    return document.get("document_id", ""), document.get("url", "")


def write_index(state: dict[str, Any], synced_at: str) -> None:
    rows = []
    for path, item in sorted(state.get("items", {}).items()):
        title = item.get("title", "")
        url = item.get("url", "")
        linked = f"[打开]({url})" if url else ""
        rows.append(
            "| "
            + " | ".join(
                [
                    f"`{path}`",
                    title.replace("|", "\\|"),
                    linked,
                    item.get("last_synced_at", ""),
                    item.get("status", ""),
                ]
            )
            + " |"
        )

    content = (
        "# YUJI 飞书同步映射表\n\n"
        "本文件由 `scripts/sync_feishu.py` 维护，用于记录本地正式文档与飞书在线文档之间的映射关系。\n\n"
        f"- 最近生成时间：{synced_at}\n"
        f"- 目标知识库空间 ID：`{WIKI_SPACE_ID}`\n"
        f"- 目标父节点 token：`{WIKI_PARENT_NODE_TOKEN}`\n\n"
        "| 本地路径 | 飞书标题 | 飞书链接 | 最近同步时间 | 状态 |\n"
        "|-|-|-|-|-|\n"
        + "\n".join(rows)
        + ("\n" if rows else "")
    )
    INDEX_PATH.write_text(content, encoding="utf-8")


def write_report(results: list[SyncResult], synced_at: str, dry_run: bool) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_local().strftime("%Y-%m-%d-%H%M%S")
    suffix = "dry-run" if dry_run else "sync"
    report_path = REPORT_DIR / f"{stamp}-{suffix}.md"

    lines = [
        f"# YUJI 飞书同步报告",
        "",
        f"- 运行时间：{synced_at}",
        f"- 模式：{'dry-run' if dry_run else '正式同步'}",
        f"- 目标知识库空间 ID：`{WIKI_SPACE_ID}`",
        f"- 目标父节点 token：`{WIKI_PARENT_NODE_TOKEN}`",
        "",
        "| 本地路径 | 动作 | 状态 | 飞书链接 | 错误 |",
        "|-|-|-|-|-|",
    ]

    for result in results:
        url = f"[打开]({result.url})" if result.url else ""
        error = result.error.replace("\n", "<br>").replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{result.path}`",
                    result.action,
                    result.status,
                    url,
                    error,
                ]
            )
            + " |"
        )

    if not results:
        lines.append("| - | none | no_changes |  |  |")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def sync(limit: int | None, dry_run: bool) -> int:
    synced_at = now_local().isoformat(timespec="seconds")
    state = load_state()
    items = state.setdefault("items", {})
    markdown_files = [path for path in sorted(DOCS_ROOT.rglob("*.md")) if should_sync(path)]
    agents_path = ROOT / "AGENTS.md"
    if agents_path.exists() and should_sync(agents_path):
        markdown_files.insert(0, agents_path)
    existing_paths = {rel_path(path) for path in markdown_files}
    results: list[SyncResult] = []

    for mapped_path, item in sorted(items.items()):
        if mapped_path not in existing_paths and item.get("status") != "local_missing":
            item["status"] = "local_missing"
            item["last_error"] = "本地文件已不存在；未删除飞书远端文档。"
            results.append(
                SyncResult(
                    path=mapped_path,
                    title=item.get("title", ""),
                    action="mark_missing",
                    status="local_missing",
                    url=item.get("url", ""),
                    error=item["last_error"],
                )
            )

    changed_files: list[Path] = []
    for path in markdown_files:
        relative = rel_path(path)
        current_hash = sha256_file(path)
        if items.get(relative, {}).get("sha256") != current_hash:
            changed_files.append(path)

    if limit is not None:
        changed_files = changed_files[:limit]

    for path in changed_files:
        relative = rel_path(path)
        current_hash = sha256_file(path)
        text = path.read_text(encoding="utf-8")
        title = extract_title(path, text)
        item = items.get(relative, {})
        action = "update" if item.get("doc_token") else "create"
        temp_path = prepare_markdown(path, title, synced_at)

        try:
            if dry_run:
                if action == "create":
                    create_remote_doc(temp_path, dry_run=True)
                else:
                    update_remote_doc(item["doc_token"], temp_path, dry_run=True)
                results.append(SyncResult(relative, title, action, "dry_run", item.get("url", "")))
                continue

            if action == "create":
                data = create_remote_doc(temp_path, dry_run=False)
                doc_token, url = remote_doc_from_create(data)
                if not doc_token:
                    raise RuntimeError(json.dumps(data, ensure_ascii=False))
                item.update({"doc_token": doc_token, "url": url})
            else:
                update_remote_doc(item["doc_token"], temp_path, dry_run=False)

            item.update(
                {
                    "sha256": current_hash,
                    "title": title,
                    "last_synced_at": synced_at,
                    "status": "synced",
                    "last_error": "",
                }
            )
            items[relative] = item
            results.append(SyncResult(relative, title, action, "synced", item.get("url", "")))
        except Exception as exc:  # noqa: BLE001 - 同步报告需要完整记录失败原因
            error = str(exc)
            item.update(
                {
                    "sha256": item.get("sha256", ""),
                    "title": title,
                    "last_synced_at": item.get("last_synced_at", ""),
                    "status": "failed",
                    "last_error": error,
                }
            )
            items[relative] = item
            results.append(SyncResult(relative, title, action, "failed", item.get("url", ""), error))

    if not dry_run:
        save_state(state)
        write_index(state, synced_at)
    report_path = write_report(results, synced_at, dry_run)

    try:
        shutil.rmtree(TMP_DIR)
    except FileNotFoundError:
        pass

    print(f"同步报告：{rel_path(report_path)}")
    failed = [result for result in results if result.status == "failed"]
    missing = [result for result in results if result.status == "local_missing"]
    print(f"变动文件：{len(changed_files)}，失败：{len(failed)}，本地缺失：{len(missing)}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 YUJI 本地 Markdown 到飞书在线文档。")
    parser.add_argument("--dry-run", action="store_true", help="只预览 lark-cli 写入请求，不更新映射状态。")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少个变动文件，用于测试。")
    args = parser.parse_args()

    if not DOCS_ROOT.exists():
        print("未找到 docs 目录，没有可同步文件。", file=sys.stderr)
        return 1

    return sync(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
