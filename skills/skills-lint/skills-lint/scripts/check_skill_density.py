#!/usr/bin/env python3
"""
统计 Skill 入口正文与 Workflow 密度；不执行 YAML 合规或行为验证。

Usage:
    python3 scripts/check_skill_density.py <skill-dir>

Exit codes:
    0: completed, even when warnings are triggered
    1: missing entry, unreadable file or unterminated frontmatter
    2: target directory does not exist
"""

import argparse
import json
import re
import sys
from pathlib import Path


WORKFLOW_CHARS_LIMIT = 1500
WORKFLOW_RATIO_LIMIT = 0.5
BODY_NEAR_LIMIT = 4500


def split_body(text: str) -> str:
    text = text.lstrip("\ufeff")
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], 1):
            if line.strip() in ("---", "..."):
                return "".join(lines[index + 1:]).lstrip("\r\n")
        raise ValueError("YAML frontmatter 缺少结束分隔符")
    return text


def mask_fences(body: str) -> str:
    """屏蔽 fenced code block 并保留字符偏移，避免把示例当作实际章节。"""
    fence = None
    result = []
    for line in body.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        was_inside = fence is not None
        if marker:
            token, tail = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
        result.append(re.sub(r"[^\r\n]", " ", line) if was_inside or fence else line)
    return "".join(result)


def workflow_sections(body: str) -> list:
    masked = mask_fences(body)
    title = r"Workflow(?:[ \t]*(?:（(?:执行流程|工作流)）|\((?:执行流程|工作流)\)))?"
    pattern = rf"^ {{0,3}}(?:\[{title}\]|(?P<markdown>#{{1,6}})[ \t]+{title}(?:[ \t]+#+)?)[ \t]*$"
    sections = []
    for match in re.finditer(pattern, masked, re.MULTILINE | re.IGNORECASE):
        prefix = match.group("markdown")
        next_pattern = (rf"^ {{0,3}}#{{1,{len(prefix)}}}[ \t]+\S.*$" if prefix
                        else r"^ {0,3}\[[^\n]+\][ \t]*$")
        next_section = re.search(next_pattern, masked[match.end():], re.MULTILINE)
        end = match.end() + next_section.start() if next_section else len(body)
        sections.append(body[match.start():end])
    return sections


def extract_workflow(body: str, filename: str) -> str:
    """兼容旧调用签名；任何入口文件均接受中英文标题。"""
    sections = workflow_sections(body)
    return sections[0] if len(sections) == 1 else ""


def has_workflow_reference(body: str) -> bool:
    reference_patterns = [
        r"`references/[^`]*workflow[^`]*\.md`",
        r"`references/[^`]*流程[^`]*\.md`",
        r"\breferences/[^\s)]*workflow[^\s)]*\.md\b",
    ]
    return any(re.search(pattern, body, re.IGNORECASE) for pattern in reference_patterns)


def inspect_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    body = split_body(text)
    sections = workflow_sections(body)
    workflow_status = "identified" if len(sections) == 1 else "missing" if not sections else "ambiguous"
    body_chars = len(body)
    workflow_chars = len(sections[0]) if len(sections) == 1 else None
    workflow_ratio = workflow_chars / body_chars if workflow_chars is not None and body_chars else None
    workflow_reference = has_workflow_reference(mask_fences(body))
    density_warning = (workflow_chars > WORKFLOW_CHARS_LIMIT and workflow_ratio > WORKFLOW_RATIO_LIMIT
                       if workflow_ratio is not None else None)

    return {
        "file": path.name,
        "body_chars": body_chars,
        "workflow_chars": workflow_chars,
        "workflow_ratio": round(workflow_ratio, 4) if workflow_ratio is not None else None,
        "workflow_status": workflow_status,
        "workflow_section_count": len(sections),
        "near_body_limit": body_chars >= BODY_NEAR_LIMIT,
        "has_workflow_reference": workflow_reference,
        "triggered_density_warning": density_warning,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Skill Workflow density.")
    parser.add_argument("skill_dir", help="Path to a Skill directory")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"error: target directory does not exist: {skill_dir}", file=sys.stderr)
        return 2

    if not (skill_dir / "SKILL.md").is_file():
        print("error: SKILL.md 不存在", file=sys.stderr)
        return 1
    try:
        files = [inspect_file(skill_dir / filename) for filename in ("SKILL.md", "SKILL.en.md")
                 if (skill_dir / filename).exists()]
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    result = {
        "schema_version": 2,
        "skill_dir": str(skill_dir),
        "thresholds": {
            "workflow_chars": WORKFLOW_CHARS_LIMIT,
            "workflow_ratio": WORKFLOW_RATIO_LIMIT,
            "near_body_limit": BODY_NEAR_LIMIT,
        },
        "files": files,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
