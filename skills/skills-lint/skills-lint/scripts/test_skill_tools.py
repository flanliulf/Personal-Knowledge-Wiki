#!/usr/bin/env python3
"""验证密度解析边界和规则适用范围；仅使用临时目录，不模拟宿主行为。

用法：python3 -B scripts/test_skill_tools.py
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import check_skill_density as density
import list_rules


class DensityTests(unittest.TestCase):
    def inspect(self, text, filename="SKILL.md"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_text(text, encoding="utf-8")
            return density.inspect_file(path)

    def test_all_heading_languages_in_both_entries(self):
        for filename in ("SKILL.md", "SKILL.en.md"):
            for heading in ("## Workflow", "[Workflow]", "## Workflow（工作流）",
                            "[Workflow（执行流程）]", "## Workflow（执行流程）",
                            "## Workflow (工作流)", "## Workflow ###",
                            "## 执行流程（Workflow）", "[执行流程（Workflow）]",
                            "## 工作流（Workflow）", "## 执行流程 (Workflow)"):
                with self.subTest(filename=filename, heading=heading):
                    row = self.inspect(heading + "\n" + "执行步骤。" * 400, filename)
                    self.assertEqual(row["workflow_status"], "identified")
                    self.assertTrue(row["triggered_density_warning"])

    def test_nested_steps_retained_peer_notes_excluded(self):
        body = "## Workflow\nstart\n### Step 1\n" + "step " * 400 + "\n## Notes\n" + "note " * 500
        workflow = density.extract_workflow(body, "SKILL.md")
        self.assertIn("### Step 1", workflow)
        self.assertNotIn("## Notes", workflow)
        self.assertGreater(len(workflow), 1500)

    def test_fenced_examples_do_not_create_or_end_workflow(self):
        for fence in ("```", "~~~~"):
            text = f"{fence}markdown\n## Workflow\nfake\n{fence}\n## Workflow\nreal\n{fence}\n## Notes\nfake end\n{fence}\nafter\n## Notes\nend"
            row = self.inspect(text)
            self.assertEqual(row["workflow_section_count"], 1)
            self.assertIn("after", density.extract_workflow(text, "SKILL.md"))

    def test_bracket_workflow_retains_markdown_steps(self):
        text = "[Workflow]\nstart\n### Step 1\n" + "step " * 400 + "\n[Notes]\nend"
        workflow = density.extract_workflow(text, "SKILL.md")
        self.assertIn("### Step 1", workflow)
        self.assertNotIn("[Notes]", workflow)
        self.assertGreater(len(workflow), 1500)

    def test_missing_section_is_unknown_not_zero_or_pass(self):
        row = self.inspect("## Steps\n" + "do work " * 1000)
        self.assertEqual(row["workflow_status"], "missing")
        for key in ("workflow_chars", "workflow_ratio", "triggered_density_warning"):
            self.assertIsNone(row[key])

    def test_multiple_sections_are_ambiguous(self):
        row = self.inspect("## Workflow\nfirst\n## Workflow\nsecond")
        self.assertEqual(row["workflow_status"], "ambiguous")
        self.assertIsNone(row["triggered_density_warning"])

    def test_both_title_orders_together_are_ambiguous(self):
        row = self.inspect("## Workflow（执行流程）\nfirst\n## 执行流程（Workflow）\nsecond")
        self.assertEqual(row["workflow_status"], "ambiguous")
        self.assertEqual(row["workflow_section_count"], 2)

    def test_chinese_title_without_english_is_not_workflow(self):
        row = self.inspect("## 执行流程\n" + "执行步骤。" * 400)
        self.assertEqual(row["workflow_status"], "missing")

    def test_frontmatter_delimiters_are_lines(self):
        body = "## Workflow\ntext\n---\nmore"
        text = '\ufeff---\nname: "a---b"\ndescription: >\n  a description\n---\n\n' + body
        self.assertEqual(density.split_body(text), body)
        self.assertEqual(density.split_body(body), body)

    def test_crlf_and_yaml_document_end(self):
        self.assertEqual(density.split_body("---\r\nname: x\r\n...\r\n## Workflow\r\nrun"),
                         "## Workflow\r\nrun")

    def test_unterminated_frontmatter_fails(self):
        with self.assertRaises(ValueError):
            density.split_body("---\nname: x\n## Workflow\nrun")

    def test_cli_missing_entry_and_directory_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            for target, expected in ((tmp, 1), (str(Path(tmp) / "missing"), 2)):
                run = subprocess.run([sys.executable, "-B", density.__file__, target], capture_output=True)
                self.assertEqual(run.returncode, expected)

    def test_cli_utf8_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SKILL.md").write_bytes(b"\xff")
            run = subprocess.run([sys.executable, "-B", density.__file__, tmp], capture_output=True)
            self.assertEqual(run.returncode, 1)

    def test_cli_warns_via_json_with_success_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SKILL.md").write_text("## Workflow\n" + "run " * 1000)
            run = subprocess.run([sys.executable, "-B", density.__file__, tmp], capture_output=True)
            self.assertEqual(run.returncode, 0)
            result = json.loads(run.stdout)
            self.assertEqual(result["schema_version"], 2)
            self.assertTrue(result["files"][0]["triggered_density_warning"])

    def test_reference_in_example_is_not_real_route(self):
        row = self.inspect("## Workflow\nrun\n```\n`references/example-workflow.md`\n```\n")
        self.assertFalse(row["has_workflow_reference"])


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = list_rules.load_registry()

    def plan(self, suffix="plain", profile="base", host="unspecified"):
        return list_rules.build_plan(Path("/tmp") / suffix, profile, host, self.registry)

    def test_external_skill_not_subject_to_project_policy(self):
        plan = self.plan(host="codex")
        selected = {r["id"]: r["status"] for r in plan["rules"]}
        self.assertEqual(selected["YML-01"], "NOT_CHECKED")
        self.assertEqual(selected["CDX-01"], "NOT_CHECKED")
        for rid in ("FILE-02", "FILE-03", "FILE-06", "VER-01", "BODY-01", "MIRROR-01"):
            self.assertEqual(selected[rid], "N/A")
        self.assertEqual(plan["executed_count"], 0)
        self.assertFalse(any(r["status"] == "PASS" for r in plan["rules"]))

    def test_tooling_is_explicit_and_counts_are_dynamic(self):
        plan = self.plan("skills/sample/sample", "tooling")
        rows = {r["id"]: r["status"] for r in plan["rules"]}
        self.assertEqual(rows["FILE-06"], "NOT_CHECKED")
        self.assertEqual(rows["CDX-01"], "N/A")
        self.assertEqual(plan["registered_count"], len(rows))
        self.assertEqual(plan["candidate_count"], sum(r["status"] == "NOT_CHECKED" for r in plan["rules"]))

    def test_directory_does_not_enable_tooling(self):
        plan = self.plan("KnowledgeWiki/skills/example/example")
        self.assertEqual(plan["scopes"], ["base"])

    def test_cli_invalid_target_and_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args, expected in (([tmp + "/missing"], 1), ([tmp, "--profile", "unknown"], 2)):
                run = subprocess.run([sys.executable, "-B", list_rules.__file__, *args], capture_output=True)
                self.assertEqual(run.returncode, expected)

    def test_duplicate_registry_id_rejected(self):
        self.registry["rules"].append(self.registry["rules"][0])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "rules.json"
            p.write_text(json.dumps(self.registry))
            with self.assertRaisesRegex(ValueError, "重复"):
                list_rules.load_registry(p)

    def test_legacy_rule_ids_preserved(self):
        counts = {"YML": 5, "DESC": 3, "FILE": 6, "VER": 5, "BODY": 8,
                  "NAME": 3, "MIRROR": 3, "CLASS": 3}
        actual = {r["id"] for r in self.registry["rules"]}
        for prefix, count in counts.items():
            for number in range(1, count + 1):
                self.assertIn(f"{prefix}-{number:02}", actual)


if __name__ == "__main__":
    unittest.main()
