#!/usr/bin/env python3
"""YUJI 每日远端同步总控：仅同步 GitHub。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, args: list[str]) -> int:
    print(f"\n===== {name} 开始 =====")
    completed = subprocess.run(args, cwd=ROOT, text=True, check=False)
    print(f"===== {name} 结束，退出码：{completed.returncode} =====\n")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="执行 YUJI 每日 GitHub 同步。")
    parser.add_argument("--dry-run", action="store_true", help="只预览 GitHub 同步动作。")
    args = parser.parse_args()

    suffix = ["--dry-run"] if args.dry_run else []
    github_code = run_step("GitHub 同步", [sys.executable, "scripts/sync_github.py", *suffix])

    if github_code != 0:
        print("每日同步结果：GitHub 同步失败，需要优先处理。", file=sys.stderr)
        return github_code

    print("每日同步结果：GitHub 已同步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
