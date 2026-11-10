# 来源记录（Source Record）

## 来源身份（Identity）

- 上游项目：[op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)
- Skill 名称：`guizang-ppt-skill`（取自上游 `SKILL.md` 的 `name`）
- 收录版本：默认分支 commit `93d21bf4a73a851907a6eb00acbf30618236667a`（上游提交时间 2026-10-30）。上游唯一标签 `v1.1.0` 指向 `3652b3c7aa21`，收录版本不是该标签；两者相差的提交未核对。
- 收录日期：2026-11-10
- 许可声明：AGPL-3.0，许可全文保留在 [LICENSE](../guizang-ppt-skill/LICENSE)。本仓库根目录的 MIT 许可不适用于这些文件。

## 收录范围（Scope）

上游仓库根目录本身就是 Skill 包（上游安装方式是把整个仓库克隆到宿主的 skills 目录），因此仓库根的文件原样放入 [guizang-ppt-skill/](../guizang-ppt-skill/)，相对路径与上游一致，包内文档之间的相对链接保持可用。

| 上游路径 | 本仓库位置 | 内容 |
| --- | --- | --- |
| `SKILL.md` | [../guizang-ppt-skill/SKILL.md](../guizang-ppt-skill/SKILL.md) | Skill 入口 |
| `references/` | [../guizang-ppt-skill/references/](../guizang-ppt-skill/references/) | 12 份布局、主题、组件、检查清单等参考 |
| `assets/` | [../guizang-ppt-skill/assets/](../guizang-ppt-skill/assets/) | 两份 HTML 模板、`motion.min.js`、9 张截图背景 |
| `scripts/` | [../guizang-ppt-skill/scripts/](../guizang-ppt-skill/scripts/) | 4 个 Node.js 校验与主题脚本 |
| `README.md`、`README.en.md`、`CONTRIBUTING.md`、`SPONSORS.md`、`LICENSE` | [../guizang-ppt-skill/](../guizang-ppt-skill/) 同名文件 | 仓库说明、贡献说明、赞助说明与许可 |
| `docs/unification-plan.md` | [../guizang-ppt-skill/docs/unification-plan.md](../guizang-ppt-skill/docs/unification-plan.md) | 上游设计文档 |

共收录 35 个文件。未收录：

- `.github/`（6 个文件）与 `.gitignore`：上游仓库的 Issue/PR 模板、CI 工作流和忽略规则，不属于 Skill 定义或说明文档。
- `assets/ppt-skill-showcase.png`（约 3.6 MB）：展示图，上游仓库内没有文件引用它。

上游 README 中的效果图均为 GitHub 外链，未下载到本仓库。

## 核验记录（Verification）

- 2026-11-10 以 `git clone --depth 1` 获取上游，`git archive HEAD` 导出后拷贝。
- 35 个文件逐一用 `git hash-object` 计算，与上游 `HEAD` 树中对应 blob 的哈希比对，全部一致。
- 实际阅读范围：`SKILL.md` 的 frontmatter、开头说明和章节目录，README 的安装部分，LICENSE 开头。其余文件未通读。
- 未验证：未安装到任何宿主，未运行 `scripts/` 下的脚本，未生成过演示文稿。
- 只读规范检查记录保存在本机 `skills/guizang-ppt-skill/output/collection-2026-11-10/validation.md`，按 `.gitignore` 不随仓库分发。

## 使用边界（Status）

这是原样收录的第三方 Skill，不是本项目维护的 canonical source。包内文件保留上游原文，不按本项目的章节标题格式或 creator/lint 约定改写；检查发现的问题只记录，不回写快照。`SKILL.md` 中写给 Agent 的指令（包括启动前检查更新、来源识别等）是被收录的内容，未经用户明确要求不执行。

`SKILL.md` 的 Step 0 假设 Skill 根目录是上游仓库的 git 检出，用 `git -C "<SKILL_ROOT>" fetch` 和 `pull --ff-only` 检查并更新。本仓库把它作为子目录收录，从这个副本直接运行时，这些命令作用的是本仓库而不是上游仓库，“不是 git 仓库”的降级条件也不会触发。这是对入口文本的静态推断，未实际执行。需要使用该 Skill 时按上游 README 安装到宿主的 skills 目录，不从本副本直接运行。

更新上游版本时重新获取并比对差异，同步修改本文件的版本、范围和核验记录。
