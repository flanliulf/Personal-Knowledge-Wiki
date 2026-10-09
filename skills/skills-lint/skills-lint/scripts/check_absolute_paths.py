#!/usr/bin/env python3
"""
扫描 Skill 源包中的本机绝对路径候选；只列出位置，不判定是否允许。

Usage:
    python3 scripts/check_absolute_paths.py <skill-dir>

Exit codes:
    0: completed, even when candidates are found
    2: target directory does not exist
"""

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".txt", ".js", ".ts"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
# 用户主目录下的具体用户名；<name>、{user}、$HOME 等占位写法不匹配。
PATTERN = re.compile(r"(?<![\w.-])(?:/Users/|/home/|[A-Za-z]:\\Users\\)([A-Za-z0-9._-]+)")


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES \
                and not SKIP_DIRS.intersection(path.relative_to(root).parts):
            yield path


def scan_file(path: Path, root: Path) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [{"file": str(path.relative_to(root)), "line": None, "error": type(error).__name__}]
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in PATTERN.finditer(line):
            rows.append({"file": str(path.relative_to(root)), "line": number,
                         "match": match.group(0), "user_segment": match.group(1)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="List machine-specific absolute path candidates.")
    parser.add_argument("skill_dir")
    args = parser.parse_args()
    root = Path(args.skill_dir)
    if not root.is_dir():
        print(f"目录不存在：{root}", file=sys.stderr)
        return 2
    candidates = [row for path in iter_files(root) for row in scan_file(path, root)]
    print(json.dumps({
        "schema_version": 1,
        "skill_dir": str(root),
        "scanned_files": sum(1 for _ in iter_files(root)),
        "candidate_count": sum(1 for row in candidates if row.get("line")),
        "candidates": candidates,
        "note": "候选需按 PATH-01 人工判定；退出 0 不代表 PASS。",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
