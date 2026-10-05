#!/usr/bin/env python3
"""绑定 index 检查快照；不执行语义审查、修改仓库或读取会话正文。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import stat
import subprocess
import sys
import tempfile
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GIT_ENV = os.environ.copy()
if GIT_ENV.get("GIT_INDEX_FILE"):
    GIT_ENV["GIT_INDEX_FILE"] = str(Path(GIT_ENV["GIT_INDEX_FILE"]).absolute())


class CheckError(Exception):
    """输入、Git 状态或采集一致性错误。"""


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise CheckError(f"无法读取 {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise CheckError(f"{label} 必须是 JSON object")
    return value, raw


def external_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\0" in value or not Path(value).is_absolute():
        raise CheckError(f"{label} 必须是绝对路径")
    try:
        path = Path(value).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise CheckError(f"{label} 路径无法解析: {exc}") from exc
    if path == PACKAGE_ROOT or PACKAGE_ROOT in path.parents:
        raise CheckError(f"{label} 不得保存在检查器源包内")
    return path


def relative_paths(value: Any, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise CheckError(f"{label} 必须是{'非空' if not allow_empty else ''}相对路径数组")
    result = []
    for item in value:
        if not isinstance(item, str) or not item or "\0" in item:
            raise CheckError(f"{label} 含无效路径")
        path = PurePosixPath(item)
        if path.is_absolute() or any(part in ("", ".", "..") for part in item.split("/")):
            raise CheckError(f"{label} 禁止绝对路径、空路径段或路径遍历: {item}")
        if "\\" in item or item.endswith("/"):
            raise CheckError(f"{label} 必须使用仓库相对 POSIX 路径: {item}")
        result.append(item)
    if len(set(result)) != len(result):
        raise CheckError(f"{label} 含重复路径")
    return result


def load_request(request_path: Path) -> dict[str, Any]:
    request_path = external_path(str(request_path), "request")
    request, _ = read_json(request_path, "request")
    if type(request.get("active")) is not bool:
        raise CheckError("request.active 必须是 bool")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise CheckError("request.request_id 必须是非空字符串")
    root_value = request.get("repo_root")
    if not isinstance(root_value, str) or "\0" in root_value or not Path(root_value).is_absolute():
        raise CheckError("request.repo_root 必须是绝对路径")
    try:
        repo_root = Path(root_value).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise CheckError(f"repo_root 路径无法解析: {exc}") from exc
    if not repo_root.is_dir():
        raise CheckError("request.repo_root 不存在或不是目录")
    context_path = external_path(request.get("context_path"), "context_path")
    report_path = external_path(request.get("report_path"), "report_path")
    if len({request_path, context_path, report_path}) != 3:
        raise CheckError("request、context、report 解析后的路径必须互不相同")
    return {
        **request,
        "request_path": request_path,
        "repo_root": repo_root,
        "context_path": context_path,
        "report_path": report_path,
    }


def load_context(request: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    context, raw = read_json(request["context_path"], "context")
    if not nonempty_text(context.get("task")):
        raise CheckError("context.task 必须是非空字符串")
    if not nonempty_text(context.get("authorization_evidence")):
        raise CheckError("context.authorization_evidence 必须记录非空授权依据")
    relative_paths(context.get("authorized_scope"), "authorized_scope")
    policy_paths = relative_paths(context.get("policy_paths"), "policy_paths", allow_empty=True)
    external_policies = context.get("external_policies", [])
    if not isinstance(external_policies, list) or any(
        not isinstance(item, dict) or any(not nonempty_text(item.get(field))
                                        for field in ("source", "applicability", "content"))
        for item in external_policies
    ):
        raise CheckError("external_policies 须逐项记录非空 source、applicability 和 content")
    if not policy_paths and not external_policies:
        raise CheckError("必须提供仓库规约或可信外部规约内容，不能猜测适用规则")
    baseline = context.get("baseline")
    if not isinstance(baseline, dict) or baseline.get("status") not in ("known", "unknown"):
        raise CheckError("context.baseline 必须是 object，status 为 known 或 unknown")
    if baseline["status"] == "known" and len(baseline) < 2:
        raise CheckError("baseline.status=known 时必须附起始状态记录")
    return context, raw


def git(root: Path, *args: str, missing_ok: bool = False, env: dict[str, str] | None = None) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], env=env or GIT_ENV,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError as exc:
        raise CheckError(f"无法执行 Git: {exc}") from exc
    if result.returncode and not missing_ok:
        error = result.stderr.decode("utf-8", "replace").strip()
        raise CheckError(f"Git 检查失败: {error}")
    return result.stdout if not result.returncode else b""


def git_path(root: Path, *args: str) -> str:
    value = git(root, "rev-parse", *args).decode().strip()
    path = Path(value)
    return str((path if path.is_absolute() else root / path).resolve())


def identity(root: Path) -> dict[str, Any]:
    actual_root = git_path(root, "--show-toplevel")
    if actual_root != str(root):
        raise CheckError("repo_root 必须指向实际 Git worktree 根目录")
    return {
        "worktree_root": actual_root,
        "git_dir": git_path(root, "--absolute-git-dir"),
        "common_dir": git_path(root, "--git-common-dir"),
        "index_file": git_path(root, "--git-path", "index"),
        "head": git(root, "rev-parse", "--verify", "HEAD", missing_ok=True).decode().strip() or None,
    }


def index_entries(root: Path) -> list[dict[str, Any]]:
    entries = []
    for row in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, object_id, stage = metadata.decode().split(" ")
        if stage != "0":
            raise CheckError("index 存在未合并条目，不能生成有效检查快照")
        entries.append({"path": path.decode("utf-8", "surrogateescape"),
                        "mode": mode, "object_id": object_id, "stage": int(stage)})
    return sorted(entries, key=lambda item: item["path"])


def head_entries(root: Path, head: str | None) -> dict[str, dict[str, Any]]:
    if head is None:
        return {}
    entries = {}
    for row in git(root, "ls-tree", "-r", "-z", head).split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode().split(" ")
        name = path.decode("utf-8", "surrogateescape")
        entries[name] = {"path": name, "mode": mode, "object_id": object_id,
                         "object_type": object_type}
    return entries


def policy_fingerprint(root: Path, requested: str, entries: dict[str, dict[str, Any]],
                       allow_absent: bool) -> dict[str, Any]:
    if requested not in entries:
        if allow_absent:
            return {"requested_path": requested, "status": "absent"}
        raise CheckError(f"index 中缺少规约文件: {requested}")
    chain, visited, current = [], set(), requested
    while True:
        if current in visited:
            raise CheckError(f"规约软链接循环: {requested}")
        visited.add(current)
        entry = entries.get(current)
        if entry is None:
            raise CheckError(f"规约软链接在同一 tree 内断链: {requested} -> {current}")
        if entry["mode"] not in ("100644", "100755", "120000"):
            raise CheckError(f"规约路径不是普通文件或软链接: {current}")
        content = git(root, "cat-file", "blob", entry["object_id"])
        record = {"path": current, "mode": entry["mode"], "object_id": entry["object_id"],
                  "content_sha256": sha256(content)}
        chain.append(record)
        if entry["mode"] != "120000":
            return {"requested_path": requested, "status": "present", "resolved_path": current,
                    "chain": chain, "content_sha256": sha256(content)}
        try:
            target = content.decode("utf-8")
        except UnicodeError as exc:
            raise CheckError(f"规约软链接目标编码无效: {current}") from exc
        if not target or "\0" in target or PurePosixPath(target).is_absolute():
            raise CheckError(f"规约软链接指向 tree 外部或无效路径: {current}")
        next_path = posixpath.normpath(posixpath.join(posixpath.dirname(current), target))
        if next_path == ".." or next_path.startswith("../") or next_path == ".":
            raise CheckError(f"规约软链接越出 tree: {current}")
        record["target"] = target
        current = next_path


def staged_changes(root: Path, head: str | None) -> list[dict[str, Any]]:
    # 未产生 HEAD 的仓库由 Git 直接将 index 与空 tree 比较。
    args = ["diff", "--cached", "--name-status", "-z", "--find-renames",
            "--no-ext-diff", "--no-textconv", "--no-color"]
    if head:
        args.append(head)
    args.append("--")
    fields = git(root, *args).split(b"\0")
    changes, offset = [], 0
    while offset < len(fields) and fields[offset]:
        status_value = fields[offset].decode()
        count = 2 if status_value.startswith(("R", "C")) else 1
        paths = [item.decode("utf-8", "surrogateescape")
                 for item in fields[offset + 1:offset + 1 + count]]
        if len(paths) != count:
            raise CheckError("Git staged change 输出不完整")
        changes.append({"status": status_value, "paths": paths})
        offset += count + 1
    return changes


def checker_fingerprint() -> dict[str, Any]:
    if not (PACKAGE_ROOT / "SKILL.md").is_file():
        raise CheckError("检查器源包缺少 SKILL.md")
    files = []
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        relative = path.relative_to(PACKAGE_ROOT)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise CheckError(f"检查器源包内不支持软链接: {relative}")
        if path.is_file():
            try:
                files.append({"path": relative.as_posix(),
                              "mode": stat.S_IMODE(path.stat().st_mode),
                              "sha256": sha256(path.read_bytes())})
            except OSError as exc:
                raise CheckError(f"无法读取检查器源文件: {relative}") from exc
    return {"package_root": str(PACKAGE_ROOT), "files_count": len(files),
            "files_sha256": sha256(canonical(files))}


def snapshot(request: dict[str, Any]) -> dict[str, Any]:
    root = request["repo_root"]
    context, context_raw = load_context(request)
    begin_identity = identity(root)
    entries = index_entries(root)
    entries_hash = sha256(canonical(entries))
    checker = checker_fingerprint()
    head_tree = head_entries(root, begin_identity["head"])
    index_tree = {entry["path"]: entry for entry in entries}
    policies = [
        {"path": path,
         "head": policy_fingerprint(root, path, head_tree, allow_absent=True),
         "index": policy_fingerprint(root, path, index_tree, allow_absent=False)}
        for path in context["policy_paths"]
    ]
    value = {
        "schema_version": 1, "snapshot_target": "index",
        "request_id": request["request_id"], "repo": begin_identity,
        "index": {"entries_count": len(entries), "entries_sha256": entries_hash,
                  "staged_changes": staged_changes(root, begin_identity["head"])},
        "context": {"path": str(request["context_path"]), "sha256": sha256(context_raw),
                    "baseline_status": context["baseline"]["status"],
                    "authorized_scope": context["authorized_scope"],
                    "policy_paths": context["policy_paths"],
                    "external_policy_count": len(context.get("external_policies", []))},
        "policies": policies, "checker": checker,
    }
    # 捕获采集中发生的并发变更。仅未暂存正文变化不会影响 index 快照。
    if (identity(root) != begin_identity or
            sha256(canonical(index_entries(root))) != entries_hash or
            sha256(load_context(request)[1]) != value["context"]["sha256"] or
            checker_fingerprint() != checker):
        raise CheckError("采集期间 HEAD、index、context 或检查器发生变化，请重新检查")
    value["snapshot_id"] = sha256(canonical(value))
    return value


def report_result(request: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    before = snapshot(request)
    report_path = request["report_path"]
    if not report_path.is_file():
        return False, "缺少审查报告", before
    report, raw = read_json(report_path, "report")
    reason = "报告与当前 index 快照一致；语义结论来自报告作者"
    valid = True
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        valid, reason = False, "report.schema_version 必须为 1"
    elif report.get("snapshot_id") != before["snapshot_id"]:
        valid, reason = False, "审查报告已过期或对应其他候选快照"
    elif report.get("scope_basis") not in ("start_snapshot", "user_confirmed_candidate"):
        valid, reason = False, "缺少有效范围依据"
    elif (report["scope_basis"] == "start_snapshot" and
          before["context"]["baseline_status"] != "known"):
        valid, reason = False, "start_snapshot 不能使用 unknown 起始状态"
    elif report.get("policy_discovery_complete") is not True:
        valid, reason = False, "适用规约发现未完成"
    elif report.get("commit_check") not in ("PASS", "SKIPPED"):
        valid, reason = False, "报告未给出 PASS 或合法 SKIPPED"
    elif report.get("commit_check") == "SKIPPED" and before["index"]["staged_changes"]:
        valid, reason = False, "index 有修改，不能使用 SKIPPED"
    elif report.get("policy_update") not in ("NONE", "RECOMMENDED"):
        valid, reason = False, "规约演进仍需决策或状态无效"
    else:
        findings = report.get("findings")
        checks = report.get("checks")
        finding_types = {"VIOLATION", "POLICY_GAP", "POLICY_CONFLICT",
                         "INSUFFICIENT_EVIDENCE", "OPTIONAL_IMPROVEMENT"}
        if not isinstance(report.get("policy_changes"), list) or any(
                not isinstance(item, dict) for item in report["policy_changes"]):
            valid, reason = False, "policy_changes 必须是 object 数组"
        elif not isinstance(report.get("limitations"), list) or any(
                not nonempty_text(item) for item in report["limitations"]):
            valid, reason = False, "limitations 必须是非空字符串数组"
        elif not isinstance(findings, list) or any(
            not isinstance(item, dict) or type(item.get("blocking")) is not bool or
            item.get("type") not in finding_types or
            any(not nonempty_text(item.get(field))
                for field in ("rule", "change_evidence", "minimal_action"))
            for item in findings
        ):
            valid, reason = False, "findings 必须逐项声明分类、blocking 与规则/变更/行动证据"
        elif any(item["blocking"] for item in findings):
            valid, reason = False, "报告仍有阻断问题"
        elif not isinstance(checks, list) or (report["commit_check"] == "PASS" and not checks):
            valid, reason = False, "PASS 报告必须列出检查项"
        else:
            for item in checks:
                if (not isinstance(item, dict) or type(item.get("required")) is not bool or
                        not nonempty_text(item.get("name")) or
                        item.get("status") not in ("PASS", "FAIL", "NOT_CHECKED", "N/A")):
                    valid, reason = False, "checks 的 name、required 或 status 无效"
                    break
                evidence_field = "evidence" if item["status"] in ("PASS", "FAIL") else "reason"
                if not nonempty_text(item.get(evidence_field)):
                    valid, reason = False, f"检查 {item['name']} 缺少非空 {evidence_field}"
                    break
                if item["required"] and item["status"] != "PASS":
                    if item["status"] != "N/A":
                        valid, reason = False, "必要检查未通过或未说明不适用原因"
                        break
            if valid and report["commit_check"] == "PASS" and not any(
                    item["status"] == "PASS" for item in checks):
                valid, reason = False, "PASS 报告至少需要一个附证据的 PASS 检查"
    after = snapshot(request)
    try:
        report_unchanged = report_path.read_bytes() == raw
    except OSError:
        report_unchanged = False
    if before["snapshot_id"] != after["snapshot_id"] or not report_unchanged:
        return False, "核验期间候选内容或报告变化，结果已失效", after
    return valid, reason, after


def consume_request(request: dict[str, Any]) -> bool:
    """同一 request_id 只执行一次 Hook 核验；状态位于外部 request 旁。"""
    source = request["request_path"]
    state_path = source.with_name(source.name + ".closeout-state.json")
    lock_path = source.with_name(source.name + ".closeout-state.lock")
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    except OSError as exc:
        raise CheckError(f"无法锁定提醒状态: {exc}") from exc
    try:
        os.close(lock_fd)
        if state_path.exists():
            previous, _ = read_json(state_path, "提醒状态")
            if previous.get("request_id") == request["request_id"]:
                return False
        state = {"schema_version": 1, "request_id": request["request_id"],
                 "consumed": True}
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile("wb", dir=source.parent, prefix=".closeout-",
                                             delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(canonical(state))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, state_path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
        return True
    except OSError as exc:
        raise CheckError(f"无法写入提醒状态: {exc}") from exc
    finally:
        lock_path.unlink(missing_ok=True)


def hook(request: dict[str, Any], host: str, event: Any) -> dict[str, Any]:
    # host 用于显式选择受支持宿主；不会使用 session_id 或 transcript_path。
    if (not isinstance(event, dict) or event.get("hook_event_name") != "Stop" or
            event.get("stop_hook_active") is True or not request["active"]):
        return {}
    cwd = event.get("cwd")
    if (not isinstance(cwd, str) or "\0" in cwd or not Path(cwd).is_absolute()
            or not Path(cwd).is_dir()):
        return {}
    locator_env = {key: value for key, value in GIT_ENV.items()
                   if key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")}
    actual = git(Path(cwd), "rev-parse", "--show-toplevel", missing_ok=True, env=locator_env)
    if not actual or Path(actual.decode().strip()).resolve() != request["repo_root"]:
        return {}
    # 先消费明确请求。PASS 或无改动也不能在后续开发回合迟发提醒。
    if not consume_request(request):
        return {}
    try:
        valid, reason, current = report_result(request)
        if valid:
            return {}
        if not current["index"]["staged_changes"]:
            return {}
    except CheckError as exc:
        reason = str(exc)
    return {"decision": "block", "reason": (
        f"{reason}。读取 {PACKAGE_ROOT / 'SKILL.md'}，针对当前 index 候选执行只读规约检查，"
        f"将报告写入 {request['report_path']}，再运行 verify --request {request['request_path']}。"
        "不要自动修改项目、stage、commit 或 push；本 request_id 只提醒一次。"
    )}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("snapshot", "verify", "hook"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--request", required=True, type=Path)
        if command == "hook":
            command_parser.add_argument("--host", required=True, choices=("codex", "claude-code"))
    args = parser.parse_args(argv)
    try:
        request = load_request(args.request)
        if args.command == "snapshot":
            print(json.dumps(snapshot(request), ensure_ascii=True, sort_keys=True))
            return 0
        if args.command == "verify":
            valid, reason, current = report_result(request)
            print(json.dumps({"verified": valid, "reason": reason,
                              "snapshot_id": current["snapshot_id"]}, ensure_ascii=True))
            return 0 if valid else 1
        try:
            event = json.load(sys.stdin)
        except (ValueError, UnicodeError):
            event = None
        print(json.dumps(hook(request, args.host, event), ensure_ascii=True))
        return 0
    except Exception as exc:
        # CLI 边界保持 JSON 输出；异常绝不转换为检查通过。
        if args.command == "hook":
            # 即使输入损坏，也输出宿主可解析的 JSON；verify 仍拒绝放行。
            print("{}")
            print(f"closeout-check: {exc}；请修正输入后手动执行 verify。", file=sys.stderr)
            return 0
        print(json.dumps({"verified": False, "error": str(exc)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
