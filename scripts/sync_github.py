#!/usr/bin/env python3
"""YUJI 本地仓库到 GitHub 的每日同步脚本。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
REMOTE_NAME = "origin"
REMOTE_URL = "https://github.com/xiaoruDoctor/YUJI.git"
DEFAULT_BRANCH = "main"
TIMEZONE = ZoneInfo("Asia/Shanghai")


def now_local() -> datetime:
    return datetime.now(TIMEZONE)


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        raise RuntimeError(output or f"git {' '.join(args)} 执行失败")
    return completed


def git_output(args: list[str], *, check: bool = True) -> str:
    completed = run_git(args, check=check)
    return completed.stdout.strip()


def ensure_repository() -> None:
    if run_git(["rev-parse", "--is-inside-work-tree"], check=False).returncode != 0:
        run_git(["init", "-b", DEFAULT_BRANCH])

    branch = git_output(["branch", "--show-current"], check=False)
    if not branch:
        run_git(["checkout", "-B", DEFAULT_BRANCH])
    elif branch != DEFAULT_BRANCH:
        run_git(["branch", "-M", DEFAULT_BRANCH])


def ensure_remote() -> None:
    remote_url = git_output(["remote", "get-url", REMOTE_NAME], check=False)
    if not remote_url:
        run_git(["remote", "add", REMOTE_NAME, REMOTE_URL])
        return

    if remote_url != REMOTE_URL:
        raise RuntimeError(f"远端 {REMOTE_NAME} 当前指向 {remote_url}，不是预期的 {REMOTE_URL}")


def remote_branch_exists(branch: str) -> bool:
    completed = run_git(["ls-remote", "--exit-code", "--heads", REMOTE_NAME, branch], check=False)
    return completed.returncode == 0


def has_head() -> bool:
    return run_git(["rev-parse", "--verify", "HEAD"], check=False).returncode == 0


def has_staged_changes() -> bool:
    return run_git(["diff", "--cached", "--quiet"], check=False).returncode != 0


def has_local_changes() -> bool:
    return bool(git_output(["status", "--short"]))


def sync(dry_run: bool) -> int:
    synced_at = now_local().isoformat(timespec="seconds")
    ensure_repository()
    ensure_remote()

    branch = git_output(["branch", "--show-current"]) or DEFAULT_BRANCH

    if remote_branch_exists(branch):
        if dry_run:
            print(f"[dry-run] 将执行：git pull --rebase --autostash {REMOTE_NAME} {branch}")
        else:
            run_git(["pull", "--rebase", "--autostash", REMOTE_NAME, branch])

    if dry_run:
        print("[dry-run] 将执行：git add --all")
        print(f"[dry-run] 当前变动：\n{git_output(['status', '--short']) or '无本地变动'}")
        print(f"[dry-run] 将在有变动时提交并推送到 {REMOTE_URL} 的 {branch} 分支")
        return 0

    run_git(["add", "--all"])

    commit_created = False
    if has_staged_changes():
        message = f"chore: 同步 YUJI 本地文档 {synced_at}"
        run_git(["commit", "-m", message])
        commit_created = True

    if not has_head():
        print("GitHub 同步失败：当前仓库没有任何可提交内容。", file=sys.stderr)
        return 1

    run_git(["push", "-u", REMOTE_NAME, branch])

    if commit_created:
        print(f"GitHub 同步完成：已提交并推送到 {REMOTE_URL} 的 {branch} 分支。")
    elif has_local_changes():
        print(f"GitHub 同步完成：无新增提交，已确认推送到 {REMOTE_URL} 的 {branch} 分支。")
    else:
        print(f"GitHub 同步完成：没有本地变动，已确认远端 {branch} 分支是最新。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 YUJI 本地仓库到 GitHub。")
    parser.add_argument("--dry-run", action="store_true", help="只预览 GitHub 同步动作，不提交或推送。")
    args = parser.parse_args()

    try:
        return sync(dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 - 自动化需要把失败原因直接打印出来
        print(f"GitHub 同步失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
