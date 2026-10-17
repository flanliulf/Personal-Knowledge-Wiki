import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from check_absolute_paths import scan_file

# 运行时拼接虚构路径，避免本测试文件自身成为扫描候选。
USERS, HOME = "/" + "Users/", "/" + "home/"


class ScanFileTests(unittest.TestCase):
    def scan(self, text, name="SKILL.md"):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            path = root / name
            path.write_text(text, encoding="utf-8")
            return scan_file(path, root)

    def test_reports_machine_paths_with_line_numbers(self) -> None:
        rows = self.scan(f"ok\nroot='{USERS}alice/project'\nsee {HOME}bob/x and C:\\Users\\carol\\y\n")
        self.assertEqual([(r["line"], r["user_segment"]) for r in rows],
                         [(2, "alice"), (3, "bob"), (3, "carol")])

    def test_placeholders_and_relative_paths_are_not_candidates(self) -> None:
        text = f"{USERS}<name>/x\n{HOME}{{user}}/x\n$HOME/x\n~/x\nreferences/workflow.md\nfoo{USERS}alice\n"
        self.assertEqual(self.scan(text), [])

    def test_unreadable_text_is_reported_as_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            (root / "bad.md").write_bytes(b"\xff")
            rows = scan_file(root / "bad.md", root)
        self.assertEqual(rows[0]["error"], "UnicodeDecodeError")


class CliTests(unittest.TestCase):
    def run_cli(self, target):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS_DIR / "check_absolute_paths.py"), target],
                              capture_output=True, text=True)

    def test_cli_lists_candidates_and_skips_cache_and_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            (root / "references").mkdir()
            (root / "references" / "guide.md").write_text(f"cd {USERS}alice/repo\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "x.py").write_text(f"'{USERS}alice'\n", encoding="utf-8")
            (root / "image.png").write_bytes((USERS + "alice").encode())
            completed = self.run_cli(str(root))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["file"], "references/guide.md")

    def test_cli_missing_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            self.assertEqual(self.run_cli(str(Path(temporary_dir) / "missing")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
