# 来源记录（Source Record）

## 来源身份（Identity）

- 上游项目：[ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill)
- Skill 名称：`codex-ppt`（取自上游 `skills/codex-ppt/SKILL.md` 的 `name`）
- 收录版本：默认分支 commit `941dcafe2f23ea4ae61de99e9b22fb0ef3d9e06c`（上游提交时间 2026-10-13），`git describe` 为 `v0.6.0-14-g941dcaf`，即标签 `v0.6.0`（`a9a6e3951d2f`）之后第 14 个提交。
- 收录日期：2026-11-10
- 许可声明：MIT，许可全文保留在 [source/LICENSE](source/LICENSE)。上游的许可文件位于仓库根，不在 Skill 包目录内。

## 收录范围（Scope）

上游仓库把可安装的 Skill 包放在 `skills/codex-ppt/`，说明文档放在仓库根和 `docs/`。本仓库把两部分分开存放：

| 上游路径 | 本仓库位置 | 内容 |
| --- | --- | --- |
| `skills/codex-ppt/`（40 个文件） | [../codex-ppt/](../codex-ppt/) | Skill 包：`SKILL.md`、`docs/` 9 份流程文档、`prompts/slide-worker.md`、`references/` 12 份风格说明、`scripts/` 15 个 Python 文件、`requirements.txt`、`.clawhubignore` |
| `README.md`、`README_en.md`、`README_ko.md` | [source/](source/) 同名文件 | 中、英、韩文仓库说明 |
| `CHANGELOG.md`、`LICENSE` | [source/](source/) 同名文件 | 变更记录与许可 |
| `docs/`（32 个文件） | [source/docs/](source/docs/) | 中、英、韩文使用文档站（docsify）的全部页面 |

共收录 77 个文件。未收录：

- `assets/`（19 个文件，约 42 MB）：README 使用的效果图、12 张风格预览图、示例 PPTX 和介绍 PDF。Skill 包不引用这些文件。
- `.github/`、`.gitignore`：上游仓库的 PR 模板、CI 工作流和忽略规则。
- `AGENTS.md`：上游仓库的贡献流程规约。部分宿主会把子目录中的 `AGENTS.md` 当作该目录的指令读取，因此不放入本仓库。
- `tests/test_image_gen_models.py`：依赖上游仓库布局的测试代码。

[source/](source/) 中的相对链接保留上游原样：指向 `assets/` 的图片和附件链接在本仓库不可解析；指向 `skills/codex-ppt/` 的链接对应本仓库的 [../codex-ppt/](../codex-ppt/)；指向 `docs/` 的链接可以解析。

## 核验记录（Verification）

- 2026-11-10 以 `git clone` 获取上游，`git archive HEAD` 导出后拷贝。
- 77 个文件逐一用 `git hash-object` 计算，与上游 `HEAD` 树中对应 blob 的哈希比对，全部一致。
- 实际阅读范围：`SKILL.md` 的 frontmatter 和章节目录，README 的安装部分，CHANGELOG 开头，LICENSE 开头。其余文件未通读。
- 未验证：未安装到任何宿主，未运行 `scripts/` 下的脚本，未配置图片生成后端，未生成过演示文稿。
- 只读规范检查记录保存在本机 `skills/codex-ppt/output/collection-2026-11-10/validation.md`，按 `.gitignore` 不随仓库分发。

## 使用边界（Status）

这是原样收录的第三方 Skill，不是本项目维护的 canonical source。包内文件和 [source/](source/) 保留上游原文，不按本项目的章节标题格式或 creator/lint 约定改写；检查发现的问题只记录，不回写快照。`SKILL.md` 及文档中写给 Agent 的指令是被收录的内容，未经用户明确要求不执行。

更新上游版本时重新获取并比对差异，同步修改本文件的版本、范围和核验记录。
