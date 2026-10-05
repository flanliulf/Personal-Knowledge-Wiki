"""真实临时 Git 仓库测试；不依赖 pytest，不证明真实语义审查。"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "closeout_check.py"


class CloseoutCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.package = self.root / "skill"
        (self.package / "scripts").mkdir(parents=True)
        self.script = self.package / "scripts" / "closeout_check.py"
        shutil.copyfile(SOURCE, self.script)
        (self.package / "SKILL.md").write_text("检查入口\n", encoding="utf-8")
        (self.package / "references").mkdir()
        (self.package / "references" / "contract.md").write_text("检查契约\n", encoding="utf-8")
        self.env = os.environ.copy()
        for key in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
            self.env.pop(key, None)
        self.git("init", "-q")
        self.git("config", "user.name", "Closeout Test")
        self.git("config", "user.email", "closeout@example.invalid")
        self.write("AGENTS.md", "现行规约\n")
        self.write("README.md", "现有导航\n")
        self.write("data.md", "初始内容\n")
        self.git("add", "AGENTS.md", "README.md", "data.md")
        self.git("commit", "-qm", "initial")
        self.context_path = self.runtime / "context.json"
        self.report_path = self.runtime / "report.json"
        self.request_path = self.runtime / "request.json"
        self.context = {
            "task": "检查本次授权文档修改",
            "authorization_evidence": "用户在可信测试输入中确认检查 data.md 的候选修改",
            "authorized_scope": ["data.md"], "policy_paths": ["AGENTS.md"],
            "baseline": {"status": "known", "head": self.git("rev-parse", "HEAD").strip(),
                         "status_porcelain_v2": ""},
        }
        self.request = {"active": True, "request_id": "closeout-1",
                        "repo_root": str(self.repo), "context_path": str(self.context_path),
                        "report_path": str(self.report_path)}
        self.save_context()
        self.save_request()
        self.write("data.md", "拟提交内容\n")
        self.git("add", "data.md")

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def git(self, *args, check=True):
        result = subprocess.run(["git", "-C", str(self.repo), *args], env=self.env,
                                capture_output=True, text=True)
        if check and result.returncode:
            self.fail(result.stderr)
        return result.stdout

    def save_context(self):
        self.context_path.write_text(json.dumps(self.context, ensure_ascii=False), encoding="utf-8")

    def save_request(self):
        self.request_path.write_text(json.dumps(self.request, ensure_ascii=False), encoding="utf-8")

    def run_cli(self, command, *, event=None, host=None, env=None, request_path=None):
        args = [sys.executable, str(self.script), command, "--request",
                str(request_path or self.request_path)]
        if host:
            args += ["--host", host]
        result = subprocess.run(args, input=json.dumps(event) if event is not None else "",
                                env=env or self.env, cwd=self.repo, capture_output=True, text=True)
        try:
            value = json.loads(result.stdout)
        except ValueError:
            self.fail(f"stdout 不是 JSON: {result.stdout!r}, stderr={result.stderr!r}")
        return result.returncode, value

    def get_snapshot(self, **kwargs):
        code, value = self.run_cli("snapshot", **kwargs)
        self.assertEqual(code, 0, value)
        return value

    def report(self, *, snapshot=None, **overrides):
        snapshot = snapshot or self.get_snapshot()
        value = {"schema_version": 1, "snapshot_id": snapshot["snapshot_id"],
                 "scope_basis": "start_snapshot", "policy_discovery_complete": True,
                 "commit_check": "PASS", "policy_update": "NONE", "findings": [],
                 "checks": [{"name": "规约审查", "required": True, "status": "PASS",
                             "evidence": "本用例由测试作者提供合法报告；不证明真实语义审查"}],
                 "policy_changes": [], "limitations": []}
        value.update(overrides)
        self.report_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return value

    def stop(self, host="codex", **overrides):
        event = {"hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(self.repo),
                 "session_id": "ignored", "transcript_path": "/must/not/be/read.jsonl"}
        event.update(overrides)
        code, value = self.run_cli("hook", event=event, host=host)
        self.assertEqual(code, 0)
        return value

    def load_module(self):
        spec = importlib.util.spec_from_file_location("closeout_check_test_module", self.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_snapshot_binds_index_instead_of_unstaged_worktree(self):
        first = self.get_snapshot()
        self.write("data.md", "未暂存的另一内容\n")
        self.write("README.md", "未暂存的新导航\n")
        self.assertEqual(first["snapshot_id"], self.get_snapshot()["snapshot_id"])
        self.assertEqual(first["snapshot_target"], "index")
        self.assertEqual(first["index"]["staged_changes"], [{"status": "M", "paths": ["data.md"]}])
        self.git("add", "data.md")
        self.assertNotEqual(first["snapshot_id"], self.get_snapshot()["snapshot_id"])

    def test_unstaged_policy_is_not_used(self):
        first = self.get_snapshot()
        self.write("AGENTS.md", "工作区候选规约\n")
        after = self.get_snapshot()
        self.assertEqual(first["snapshot_id"], after["snapshot_id"])
        fingerprint = after["policies"][0]["index"]["content_sha256"]
        self.assertEqual(fingerprint, hashlib.sha256("现行规约\n".encode()).hexdigest())

    def test_add_delete_rename_changes_are_recorded(self):
        self.git("mv", "README.md", "导航.md")
        self.git("rm", "-f", "data.md")
        self.write("new.md", "新增\n")
        self.git("add", "new.md")
        changes = self.get_snapshot()["index"]["staged_changes"]
        self.assertIn({"status": "R100", "paths": ["README.md", "导航.md"]}, changes)
        self.assertIn({"status": "D", "paths": ["data.md"]}, changes)
        self.assertIn({"status": "A", "paths": ["new.md"]}, changes)

    def test_custom_git_index_is_respected(self):
        normal = self.get_snapshot()
        alternate = self.runtime / "alternate-index"
        shutil.copyfile(self.repo / ".git" / "index", alternate)
        alternate_env = {**self.env, "GIT_INDEX_FILE": str(alternate)}
        subprocess.run(["git", "-C", str(self.repo), "reset", "--quiet", "HEAD"],
                       env=alternate_env, check=True, capture_output=True)
        selected = self.get_snapshot(env=alternate_env)
        self.assertEqual(selected["repo"]["index_file"], str(alternate.resolve()))
        self.assertEqual(selected["index"]["staged_changes"], [])
        self.assertNotEqual(normal["index"]["entries_sha256"], selected["index"]["entries_sha256"])

    def test_missing_report_and_fail_report_do_not_pass(self):
        self.assertEqual(self.run_cli("verify")[0], 1)
        self.report(commit_check="FAIL")
        self.assertEqual(self.run_cli("verify")[0], 1)
        self.report()
        code, result = self.run_cli("verify")
        self.assertEqual(code, 0)
        self.assertTrue(result["verified"])
        self.assertFalse(self.request_path.with_name(self.request_path.name + ".closeout-state.json").exists())

    def test_context_or_index_policy_changes_expire_report(self):
        self.report()
        self.context["task"] = "用户修订后的任务"
        self.save_context()
        self.assertEqual(self.run_cli("verify")[0], 1)
        self.report()
        self.write("AGENTS.md", "本次修改后的规约\n")
        self.git("add", "AGENTS.md")
        self.assertEqual(self.run_cli("verify")[0], 1)

    def test_checker_change_expires_report(self):
        self.report()
        (self.package / "references" / "contract.md").write_text("修订的契约\n", encoding="utf-8")
        self.assertEqual(self.run_cli("verify")[0], 1)

    def test_pycache_is_excluded_from_checker_fingerprint(self):
        first = self.get_snapshot()
        (self.package / "scripts" / "__pycache__").mkdir()
        (self.package / "scripts" / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
        self.assertEqual(first["snapshot_id"], self.get_snapshot()["snapshot_id"])

    def test_policy_symlink_resolves_only_inside_same_tree(self):
        (self.repo / "CLAUDE.md").symlink_to("AGENTS.md")
        self.git("add", "CLAUDE.md")
        self.context["policy_paths"] = ["CLAUDE.md"]
        self.save_context()
        fingerprint = self.get_snapshot()["policies"][0]["index"]
        self.assertEqual(fingerprint["resolved_path"], "AGENTS.md")
        self.assertEqual([item["mode"] for item in fingerprint["chain"]], ["120000", "100644"])

    def test_broken_external_and_looping_policy_symlinks_fail(self):
        for target in ("missing.md", "../outside.md", "/outside.md", "CLAUDE.md"):
            with self.subTest(target=target):
                link = self.repo / "CLAUDE.md"
                if link.is_symlink():
                    link.unlink()
                link.symlink_to(target)
                self.git("add", "CLAUDE.md")
                self.context["policy_paths"] = ["CLAUDE.md"]
                self.save_context()
                self.assertEqual(self.run_cli("snapshot")[0], 2)

    def test_untracked_policy_cannot_be_borrowed_from_worktree(self):
        self.write("new-policy.md", "未暂存规约\n")
        self.context["policy_paths"] = ["new-policy.md"]
        self.save_context()
        self.assertEqual(self.run_cli("snapshot")[0], 2)

    def test_unmerged_index_is_rejected(self):
        old_blob = self.git("rev-parse", "HEAD:data.md").strip()
        new_blob = self.git("rev-parse", ":data.md").strip()
        self.git("update-index", "--force-remove", "data.md")
        rows = f"100644 {old_blob} 1\tdata.md\n100644 {new_blob} 2\tdata.md\n"
        result = subprocess.run(["git", "-C", str(self.repo), "update-index", "--index-info"],
                                env=self.env, input=rows, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_cli("snapshot")[0], 2)
        self.assertEqual(self.run_cli("verify")[0], 2)

    def test_path_traversal_absolute_and_empty_scope_are_rejected(self):
        for field, value in (("policy_paths", ["../AGENTS.md"]),
                             ("policy_paths", ["/AGENTS.md"]),
                             ("authorized_scope", []),
                             ("policy_paths", []),
                             ("authorized_scope", ["a/../data.md"])):
            with self.subTest(field=field, value=value):
                old = self.context[field]
                self.context[field] = value
                self.save_context()
                self.assertEqual(self.run_cli("snapshot")[0], 2)
                self.context[field] = old
                self.save_context()

    def test_invalid_request_and_package_runtime_path_are_rejected(self):
        self.request["report_path"] = str(self.package / "report.json")
        self.save_request()
        self.assertEqual(self.run_cli("verify")[0], 2)
        self.assertEqual(self.stop(), {})
        self.request["report_path"] = str(self.report_path)
        self.request["request_id"] = ""
        self.save_request()
        self.assertEqual(self.run_cli("snapshot")[0], 2)

    def test_runtime_paths_must_be_distinct_after_resolution(self):
        self.request["report_path"] = str(self.context_path)
        self.save_request()
        self.assertEqual(self.run_cli("snapshot")[0], 2)
        self.request["report_path"] = str(self.report_path)
        alias = self.runtime / "request-alias.json"
        alias.symlink_to(self.request_path)
        self.request["context_path"] = str(alias)
        self.save_request()
        self.assertEqual(self.run_cli("verify")[0], 2)

    def test_external_policy_only_is_bound_without_reading_source(self):
        self.context["policy_paths"] = []
        self.context["external_policies"] = [{
            "source": "/not/read/global-policy.md", "applicability": "本项目所有修改",
            "content": "用户提供的必要规则：只修改授权内容。",
        }]
        self.save_context()
        first = self.get_snapshot()
        self.assertEqual(first["policies"], [])
        self.assertEqual(first["context"]["external_policy_count"], 1)
        self.report(snapshot=first)
        self.assertEqual(self.run_cli("verify")[0], 0)
        self.context["external_policies"][0]["content"] = "用户更新的必要规则内容。"
        self.save_context()
        self.assertEqual(self.run_cli("verify")[0], 1)

    def test_no_policy_or_empty_external_policy_content_is_rejected(self):
        self.context["policy_paths"] = []
        self.context["external_policies"] = []
        self.save_context()
        self.assertEqual(self.run_cli("snapshot")[0], 2)
        self.context["external_policies"] = [{"source": "全局规则", "applicability": "本项目", "content": ""}]
        self.save_context()
        self.assertEqual(self.run_cli("snapshot")[0], 2)

    def test_unknown_baseline_requires_confirmed_candidate_scope_basis(self):
        self.context["baseline"] = {"status": "unknown", "reason": "未保存起始状态"}
        self.save_context()
        self.report()
        self.assertEqual(self.run_cli("verify")[0], 1)
        self.report(scope_basis="user_confirmed_candidate")
        self.assertEqual(self.run_cli("verify")[0], 0)

    def test_report_required_evidence_is_checked(self):
        cases = (
            {"policy_discovery_complete": False},
            {"policy_update": "DECISION_REQUIRED"},
            {"findings": [{"blocking": True, "type": "VIOLATION", "rule": "现行规则",
                           "change_evidence": "候选中的违规内容", "minimal_action": "先修正问题"}]},
            {"findings": [{}]},
            {"checks": []},
            {"checks": [{"required": True, "status": "NOT_CHECKED"}]},
            {"checks": [{"required": True, "status": "N/A"}]},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                self.report(**changes)
                self.assertEqual(self.run_cli("verify")[0], 1)
        self.report(policy_update="RECOMMENDED", findings=[{
            "blocking": False, "type": "POLICY_GAP", "rule": "无覆盖条款",
            "change_evidence": "本测试模拟新增资产", "minimal_action": "由用户评估是否补充规则",
        }], checks=[
            {"name": "范围与现行规则", "required": True, "status": "PASS", "evidence": "测试报告证据"},
            {"name": "运行检查", "required": True, "status": "N/A", "reason": "项目不适用此检查"},
        ])
        self.assertEqual(self.run_cli("verify")[0], 0)

    def test_authorization_evidence_must_be_recorded(self):
        self.context.pop("authorization_evidence")
        self.save_context()
        self.assertEqual(self.run_cli("snapshot")[0], 2)
        self.context["authorization_evidence"] = "  "
        self.save_context()
        self.assertEqual(self.run_cli("verify")[0], 2)

    def test_empty_check_evidence_cannot_pass(self):
        cases = (
            [{"name": "检查", "required": True, "status": "PASS"}],
            [{"name": " ", "required": True, "status": "PASS", "evidence": "记录"}],
            [{"name": "检查", "required": True, "status": "PASS", "evidence": "  "}],
            [{"name": "检查", "required": False, "status": "NOT_CHECKED", "reason": "未执行"}],
            [{"name": "检查", "required": True, "status": "N/A", "reason": "不适用"}],
            [{"name": "检查", "required": False, "status": "FAIL"}],
        )
        for checks in cases:
            with self.subTest(checks=checks):
                self.report(checks=checks)
                self.assertEqual(self.run_cli("verify")[0], 1)

    def test_findings_and_report_evidence_have_minimum_structure(self):
        for changes in (
            {"findings": [{"blocking": False}]},
            {"findings": [{"blocking": False, "type": "OTHER", "rule": "规则",
                           "change_evidence": "变更", "minimal_action": "建议"}]},
            {"policy_changes": None}, {"policy_changes": ["不是对象"]},
            {"limitations": None}, {"limitations": [False]}, {"limitations": ["  "]},
        ):
            with self.subTest(changes=changes):
                self.report(**changes)
                self.assertEqual(self.run_cli("verify")[0], 1)

    def test_required_unverified_check_blocks_despite_valid_core_pass(self):
        checks = [
            {"name": "范围与规约", "required": True, "status": "PASS", "evidence": "有效测试记录"},
            {"name": "项目必需检查", "required": True, "status": "NOT_CHECKED", "reason": "尚未执行"},
        ]
        self.report(checks=checks)
        code, result = self.run_cli("verify")
        self.assertEqual(code, 1)
        self.assertIn("必要检查未通过", result["reason"])
        checks[1]["required"] = False
        self.report(checks=checks)
        self.assertEqual(self.run_cli("verify")[0], 0)

    def test_skipped_requires_no_staged_changes(self):
        self.report(commit_check="SKIPPED", checks=[])
        self.assertEqual(self.run_cli("verify")[0], 1)
        self.git("reset", "--quiet", "HEAD")
        self.report(commit_check="SKIPPED", checks=[])
        self.assertEqual(self.run_cli("verify")[0], 0)

    def test_both_hosts_remind_once_per_request_id(self):
        for host in ("codex", "claude-code"):
            with self.subTest(host=host):
                self.request["request_id"] = host + "-1"
                self.save_request()
                self.assertEqual(self.stop(host)["decision"], "block")
                self.assertEqual(self.stop(host), {})
                self.write("data.md", host + "变化内容\n")
                self.git("add", "data.md")
                self.assertEqual(self.stop(host), {})
                self.assertEqual(self.run_cli("verify")[0], 1)
                self.request["request_id"] = host + "-2"
                self.save_request()
                self.assertEqual(self.stop(host)["decision"], "block")

    def test_hook_ignores_non_stop_active_recursion_and_other_repo(self):
        self.assertEqual(self.stop(hook_event_name="SessionEnd"), {})
        self.assertEqual(self.stop(stop_hook_active=True), {})
        self.assertEqual(self.stop(cwd=str(self.runtime)), {})
        self.request["active"] = False
        self.save_request()
        self.assertEqual(self.stop(), {})
        self.request["active"] = True
        self.save_request()
        self.assertEqual(self.stop()["decision"], "block")

    def test_hook_pass_consumes_request_and_cannot_late_remind(self):
        self.report()
        self.assertEqual(self.stop(), {})
        self.assertTrue(self.request_path.with_name(self.request_path.name + ".closeout-state.json").exists())
        self.write("data.md", "审查后下一回合的修改\n")
        self.git("add", "data.md")
        self.assertEqual(self.stop(), {})
        self.assertEqual(self.run_cli("verify")[0], 1)

    def test_hook_without_staged_changes_does_not_request_audit(self):
        self.git("reset", "--quiet", "HEAD")
        self.assertEqual(self.stop(), {})
        self.write("data.md", "后续回合的修改\n")
        self.git("add", "data.md")
        self.assertEqual(self.stop(), {})

    def test_snapshot_rejects_concurrent_index_change(self):
        module = self.load_module()
        request = module.load_request(self.request_path)
        original = module.index_entries
        count = 0

        def read_index(root):
            nonlocal count
            count += 1
            if count == 2:
                self.write("data.md", "采集中并发修改\n")
                self.git("add", "data.md")
            return original(root)

        with mock.patch.object(module, "index_entries", side_effect=read_index):
            with self.assertRaises(module.CheckError):
                module.snapshot(request)

    def test_verify_rejects_candidate_change_between_snapshots(self):
        self.report()
        module = self.load_module()
        request = module.load_request(self.request_path)
        original = module.snapshot
        count = 0

        def collect_snapshot(value):
            nonlocal count
            count += 1
            if count == 2:
                self.write("data.md", "核验期间并发修改\n")
                self.git("add", "data.md")
            return original(value)

        with mock.patch.object(module, "snapshot", side_effect=collect_snapshot):
            valid, reason, _ = module.report_result(request)
        self.assertFalse(valid)
        self.assertIn("失效", reason)

    def test_verify_rejects_report_change_between_snapshots(self):
        value = self.report()
        module = self.load_module()
        request = module.load_request(self.request_path)
        original = module.snapshot
        count = 0

        def collect_snapshot(request_value):
            nonlocal count
            count += 1
            if count == 2:
                value["commit_check"] = "FAIL"
                self.report_path.write_text(json.dumps(value), encoding="utf-8")
            return original(request_value)

        with mock.patch.object(module, "snapshot", side_effect=collect_snapshot):
            valid, reason, _ = module.report_result(request)
        self.assertFalse(valid)
        self.assertIn("失效", reason)

    def test_invalid_hook_input_still_outputs_json(self):
        result = subprocess.run([sys.executable, str(self.script), "hook", "--host", "codex",
                                 "--request", str(self.request_path)], env=self.env,
                                input="not JSON", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual(self.stop()["decision"], "block")

    def test_initial_repository_has_absent_head_policy_record(self):
        fresh = self.root / "fresh"
        fresh.mkdir()
        subprocess.run(["git", "-C", str(fresh), "init", "-q"], env=self.env, check=True)
        (fresh / "AGENTS.md").write_text("初始规约\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(fresh), "add", "AGENTS.md"], env=self.env, check=True)
        self.request["repo_root"] = str(fresh)
        self.save_request()
        value = self.get_snapshot()
        self.assertIsNone(value["repo"]["head"])
        self.assertEqual(value["policies"][0]["head"]["status"], "absent")


if __name__ == "__main__":
    unittest.main()
