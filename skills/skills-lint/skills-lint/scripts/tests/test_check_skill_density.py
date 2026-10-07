import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from check_skill_density import extract_workflow, inspect_file


FILE_RESULT_KEYS = {
    "file",
    "workflow_status",
    "workflow_section_count",
    "body_chars",
    "workflow_chars",
    "workflow_ratio",
    "near_body_limit",
    "has_workflow_reference",
    "triggered_density_warning",
}


class ExtractWorkflowTests(unittest.TestCase):
    def test_extracts_supported_workflow_sections_without_notes(self) -> None:
        cases = [
            (
                "SKILL.md",
                "[Workflow（执行流程）]\n步骤一\n[Notes]\n不要包含",
                "[Workflow（执行流程）]\n步骤一\n",
            ),
            (
                "SKILL.en.md",
                "[Workflow]\nStep one\n[Notes]\nDo not include",
                "[Workflow]\nStep one\n",
            ),
            (
                "SKILL.md",
                "## Workflow（工作流）\n步骤一\n### Detail\n细节\n## Notes\n不要包含",
                "## Workflow（工作流）\n步骤一\n### Detail\n细节\n",
            ),
            (
                "SKILL.md",
                "## 执行流程（Workflow）\n步骤一\n### 细节（Detail）\n细节\n## 注意事项（Notes）\n不要包含",
                "## 执行流程（Workflow）\n步骤一\n### 细节（Detail）\n细节\n",
            ),
            (
                "SKILL.md",
                "[工作流（Workflow）]\n步骤一\n[注意事项（Notes）]\n不要包含",
                "[工作流（Workflow）]\n步骤一\n",
            ),
            (
                "SKILL.en.md",
                "## Workflow\nStep one\n### Detail\nDetails\n## Notes\nDo not include",
                "## Workflow\nStep one\n### Detail\nDetails\n",
            ),
        ]

        for filename, body, expected in cases:
            with self.subTest(filename=filename, header=body.splitlines()[0]):
                self.assertEqual(extract_workflow(body, filename), expected)


class DensityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = "## Workflow（工作流）\n" + ("步" * 1501) + "\n"
        self.body = self.workflow + "## Notes\n不要计入 Workflow\n"
        self.skill_text = "---\nname: temporary-skill\n---\n" + self.body

    def test_inspect_file_reports_schema_warning_and_markdown_workflow_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            skill_path = Path(temporary_dir) / "SKILL.md"
            skill_path.write_text(self.skill_text, encoding="utf-8")

            result = inspect_file(skill_path)

        self.assertEqual(set(result), FILE_RESULT_KEYS)
        self.assertEqual(result["file"], "SKILL.md")
        self.assertEqual(result["body_chars"], len(self.body))
        self.assertEqual(result["workflow_chars"], len(self.workflow))
        self.assertIsInstance(result["triggered_density_warning"], bool)
        self.assertIs(result["triggered_density_warning"], True)

    def test_cli_preserves_json_schema_and_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            skill_dir = Path(temporary_dir)
            (skill_dir / "SKILL.md").write_text(self.skill_text, encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_skill_density.py"), str(skill_dir)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        result = json.loads(completed.stdout)
        self.assertEqual(set(result), {"schema_version", "skill_dir", "thresholds", "files"})
        self.assertEqual(
            result["thresholds"],
            {
                "workflow_chars": 1500,
                "workflow_ratio": 0.5,
                "near_body_limit": 4500,
            },
        )
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(len(result["files"]), 1)
        file_result = result["files"][0]
        self.assertEqual(set(file_result), FILE_RESULT_KEYS)
        self.assertEqual(file_result["workflow_chars"], len(self.workflow))
        self.assertIsInstance(file_result["triggered_density_warning"], bool)
        self.assertIs(file_result["triggered_density_warning"], True)


if __name__ == "__main__":
    unittest.main()
