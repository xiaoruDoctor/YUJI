import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def load_sync_daily_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "sync_daily.py"
    spec = importlib.util.spec_from_file_location("sync_daily", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncDailyTests(unittest.TestCase):
    def test_only_runs_github_sync(self):
        module = load_sync_daily_module()
        calls = []

        def fake_run(args, cwd, text, check):
            calls.append(args)
            return SimpleNamespace(returncode=0)

        with patch.object(module.subprocess, "run", side_effect=fake_run):
            with patch.object(sys, "argv", ["sync_daily.py"]):
                exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [[sys.executable, "scripts/sync_github.py"]])


if __name__ == "__main__":
    unittest.main()
