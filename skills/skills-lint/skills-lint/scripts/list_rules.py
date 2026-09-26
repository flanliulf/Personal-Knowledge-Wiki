#!/usr/bin/env python3
"""读取共享规则表并生成待检查清单；不宣称执行了 lint。

用法：python3 list_rules.py <skill-dir> --profile tooling --host codex
退出码：0 清单生成成功；1 规则表或目标无效；2 参数错误。
仅使用 Python 标准库，无写入操作。
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


REGISTRY = Path(__file__).resolve().parent.parent / "references" / "rule-registry.json"


def load_registry(path=REGISTRY):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("contract_version") != "1.0.0":
        raise ValueError("不支持的规则表版本")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("rules 必须是非空列表")
    seen = set()
    for rule in rules:
        for key in ("id", "title", "scope", "source", "severity", "method", "criteria"):
            if not isinstance(rule.get(key), str) or not rule[key]:
                raise ValueError(f"规则缺少有效字段: {key}")
        if rule["id"] in seen:
            raise ValueError(f"重复 rule id: {rule['id']}")
        seen.add(rule["id"])
        if rule["scope"] not in data["scopes"] or rule["source"] not in data["sources"]:
            raise ValueError(f"未知 scope/source: {rule['id']}")
        if rule["severity"] not in ("Error", "Warning"):
            raise ValueError(f"未知 severity: {rule['id']}")
    return data


def build_plan(target, profile, host, registry):
    scopes = {"base"}
    if profile == "tooling":
        scopes.add("tooling")
    if host == "codex":
        scopes.add("codex")
    rows = []
    for rule in registry["rules"]:
        applicable = rule["scope"] in scopes
        rows.append({**rule, "status": "NOT_CHECKED" if applicable else "N/A",
                     "reason": "等待按 criteria 检查" if applicable else "不属于所选 scope"})
    return {"contract_version": registry["contract_version"], "target": str(target.resolve()),
            "profile": profile, "host": host, "scopes": sorted(scopes),
            "registered_count": len(rows), "candidate_count": sum(r["status"] == "NOT_CHECKED" for r in rows),
            "executed_count": 0, "rules": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir")
    parser.add_argument("--profile", choices=("base", "tooling"), default="base")
    parser.add_argument("--host", choices=("unspecified", "codex"), default="unspecified")
    args = parser.parse_args()
    target = Path(args.skill_dir)
    try:
        if not target.is_dir():
            raise ValueError("目标目录不存在")
        registry = load_registry()
        result = build_plan(target, args.profile, args.host, registry)
        result["registry_path"] = str(REGISTRY)
        result["registry_sha256"] = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
