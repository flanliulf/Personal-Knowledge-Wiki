# KnowledgeWiki（AI 源资产与写作参考资料库）

本项目用于集中存放本机收集的 AI 源资产与写作参考资料，包括提示词（prompts）、技能（skills）和外部规范指南（guidelines），便于查阅、整理和复用。

## Directory Guide（目录职责）

| 路径 | 职责与当前内容 |
| --- | --- |
| [prompts/](prompts/) | 按独立资产子目录存放提示词及其配套内容；当前收录 Codex 会话标题整理提示词。 |
| [skills/](skills/) | 按独立资产子目录存放 Agent 技能及配套内容；当前维护 Codex 会话标题整理、通用技能创建、规范检查、教师公开信息研究和中文技术文档写作五个源包。 |
| [guidelines/](guidelines/) | 按上游项目收录规范指南原文、许可与来源记录；当前收录两份中文写作指南，均为外部参考资料。 |
| [AGENTS.md](AGENTS.md) | AI LLM / Agent 分析和维护本项目时的顶层规约。 |
| [CLAUDE.md](CLAUDE.md) | 指向 AGENTS.md 的软链接，共用同一份规约。 |

## Asset Organization（资产组织）

以下为硬性约束：

1. `prompts/` 和 `skills/` 的下一级必须全部是子目录，每个子目录承载一项资产的所有相关信息，禁止直接放置文件。
2. `prompts/<prompt-name>/` 下只允许存放该 prompt 的源 `.md` 文档，以及与其同级的相关子目录，如 `work/`（运行依赖）、`output/`（输出）、`examples/`（历史示例）等。禁止存放其他任何独立文档；会话 handoff 历史等须归入相关子目录。
3. `skills/<skill-name>/` 使用相同组织规则，但源定义是与 skill 同名的子目录 `<skill-name>/`，其中包含 `SKILL.md` 及其他技能定义文件、子目录。配套的 `work/`、`output/`、`examples/` 等与该源目录同级，资产目录下禁止放置独立文档。
4. `guidelines/<project>/source/` 保存未经改写的上游文件与许可文本；同级 `SOURCE.md` 记录来源、版本、收录范围及使用边界。Skill 需要独立携带参考资料时，可将经核对的原文和许可文件复制到其 `references/upstream/`，并在包内注明版本与许可。外部指南仅供参考，不自动成为项目规约；本项目自写文档遵循 English（中文）标题格式，两处上游原文保留原样。

规范结构示意（配套子目录按需创建）：

```text
prompts/<prompt-name>/
├── <prompt-name>.md
├── work/
├── output/
└── examples/

skills/<skill-name>/
├── <skill-name>/
│   └── SKILL.md                       # 同目录内可包含其他技能定义文件及子目录
├── work/
├── output/
└── examples/

guidelines/<project>/
├── SOURCE.md                          # 本项目编写的来源与使用边界记录
└── source/                            # 保留上游文件与许可文本原样
```

当前目录结构：

```text
prompts/
└── codex-session-title-renaming/
    ├── codex-session-title-renaming.md
    ├── work/                         # 本次会话工作文件、执行证据与迁移清单
    └── output/                       # 两版对照表、执行结果、handoff 与迁移记录
skills/
├── codex-session-title-renaming/
│   ├── codex-session-title-renaming/  # 入口、references、schemas、scripts、tests
│   ├── work/                         # 后续运行的临时输入，当前为空
│   ├── output/                       # 后续批次数据与按需报告，当前为空
│   └── examples/                     # 虚构提案输入示例
├── skills-creator/
│   ├── skills-creator/                # 双语入口、CHANGELOG、创建参考资料
│   ├── work/                         # 迁移前 forge 完整快照和 hash 清单
│   └── output/                       # 迁移记录与验证证据
├── skills-lint/
│   ├── skills-lint/                   # 双语入口、共享规则表、统计与测试脚本
│   ├── work/                         # 迁移前 forge 完整快照和 hash 清单
│   └── output/                       # 迁移记录与验证证据
├── teacher-profile-research/
│   ├── teacher-profile-research/      # 中文入口、CHANGELOG、研究规则和成品模板
│   ├── work/                         # 用户原方案与创建前 README 快照
│   └── output/                       # 创建验证证据及按独立批次保存的教师研究报告
└── chinese-technical-writing/
    ├── chinese-technical-writing/    # 中文入口、写作自检、文档类型指引与包内指南原文
    │   └── references/upstream/      # 两份指南的原文副本及许可文件
    └── output/                       # 创建、历次修订与检查结果
guidelines/
├── document-style-guide/
│   ├── SOURCE.md                     # 来源、上游 commit、许可及使用边界
│   └── source/                       # 上游 README 与 docs 七个章节
└── chinese-copywriting-guidelines/
    ├── SOURCE.md                     # 来源、上游 commit、许可及使用边界
    └── source/                       # 上游繁简中文 README 与 LICENSE
```

会话标题整理资产的 `work/` 与原 `outputs/` 已分别迁入该资产的 `work/` 和 `output/`；handoff 已归入 `output/`，资产根目录只保留提示词源文档。原会话目录保留兼容符号链接，不保留重复数据。

- [会话 handoff](prompts/codex-session-title-renaming/output/codex-session-title-renaming.handoff-2026-09-07.md)
- [年份补全对照表](prompts/codex-session-title-renaming/output/会话标题年份补全对照表.md)
- [资产迁移记录](prompts/codex-session-title-renaming/output/会话资产迁移记录.md)

## Asset Inventory（资产清单）

| 资产 | 内容摘要 |
| --- | --- |
| [Codex 会话标题整理提示词](prompts/codex-session-title-renaming/codex-session-title-renaming.md) | 历史源资产，原文与历史执行证据保留；后续运行规则由同名 Skill 维护。 |
| [Codex 会话标题整理 Skill](skills/codex-session-title-renaming/codex-session-title-renaming/SKILL.md) | 人工或定期调用的简化流程：一个全局执行锁、每批 `proposal.json` / `execution.json`、用户确认后逐条改名与回读、按需生成 Markdown 记录。源包已建立，未安装，未运行真实改名或配置定时任务。 |
| [skills-creator](skills/skills-creator/skills-creator/SKILL.md) | 2.0.0：通用 Skill 创建与迭代，按基础、宿主与可选 tooling 约定生成源包；与 skills-lint 共享规则契约。由旧 forge 1.5.0 迁入。 |
| [skills-lint](skills/skills-lint/skills-lint/SKILL.md) | 3.0.0：只读规则审查、动态规则清单、密度 schema v2 和行为证据边界。由旧 forge 2.3.0 迁入。 |
| [teacher-profile-research](skills/teacher-profile-research/teacher-profile-research/SKILL.md) | 1.0.0：教师公开信息画像与教学决策研究；身份消歧、A–D 来源分级、五态逐条核验、任教与班主任轨迹、团队分析及多轮纠错。单 Skill 源包，采用 base；未安装，已按源入口完成首轮公开信息研究。 |
| [chinese-technical-writing](skills/chinese-technical-writing/chinese-technical-writing/SKILL.md) | 1.1.1：基于项目事实写作和定点修订中文技术文档；包内直接引用两份指南原文，重叠规则以 `document-style-guide` 为准，增加 Agent 写作自检和可选 `autocorrect` 检查。采用 base；未安装，真实宿主行为未验证。 |
| [document-style-guide](guidelines/document-style-guide/SOURCE.md) | 中文技术文档写作参考；保留上游 README 与标题、文本、段落、数值、标点、文档体系、参考链接七个章节。 |
| [chinese-copywriting-guidelines](guidelines/chinese-copywriting-guidelines/SOURCE.md) | 中文文案排版参考；保留上游繁简中文 README 和 MIT 许可文本。 |

## Skill Usage（技能使用）

### Session Titles（会话标题整理）

- [运行指南](skills/codex-session-title-renaming/codex-session-title-renaming/references/workflow.md)：`audit`、`apply`、`report` 三个入口及辅助脚本命令。
- [数据契约](skills/codex-session-title-renaming/codex-session-title-renaming/references/data-contract.md)：提案、批准绑定、实际回读、保护字段与结果限制。
- [虚构输入示例](skills/codex-session-title-renaming/examples/example-input.json)：仅供格式参考，不代表真实会话或授权。

会话标题整理 Skill 只维护运行规则和确定性辅助工具；实际改名依赖 Agent 环境中的专用工具。其所有真实入口使用同一默认全局锁，等待人工确认期间释放锁。不维护增量索引、会话级状态、自动重试或事件日志。完整记录文档由用户要求后从已有 JSON 生成。

本地验证命令（不访问真实会话）：

```sh
python3 -B -m unittest discover -s skills/codex-session-title-renaming/codex-session-title-renaming/tests -v
```

### Skill Tooling（技能创建与检查）

**所有新开展的 session 在本项目创建或更新 Skill 时，必须使用内置 [skills-creator](skills/skills-creator/skills-creator/SKILL.md) 创建或修订，再使用内置 [skills-lint](skills/skills-lint/skills-lint/SKILL.md) 检查最新源包并记录结果。** 两者通过共享规则契约维护本项目 canonical source 定义的一致性；即使宿主未自动发现，也须读取本项目源入口执行。该约束由 [AGENTS.md](AGENTS.md) 与其软链接 [CLAUDE.md](CLAUDE.md) 共同提供，profile/host 按目标适用规则选择。

在本项目使用、维护和迭代这两个源包。旧 `/Users/fancyliu/Repos/skills-creator/forge/skill-tooling/` 中的同名包已停止维护，只保留带迁移声明的最终冻结快照；不再向旧 forge 回写或从旧源安装。迁移前的未提交内容完整保存在各资产 `work/migration-2026-09-09/` 的压缩快照中。

- [创建流程](skills/skills-creator/skills-creator/references/skill-creation-workflow.md)与[配套契约](skills/skills-creator/skills-creator/references/spec-guide.md)：按目标项目政策生成，外部目标默认 base。
- [检查流程](skills/skills-lint/skills-lint/references/lint-workflow.md)与[共享规则表](skills/skills-lint/skills-lint/references/rule-registry.json)：tooling 为显式选择的双语版本化约定，不自动约束本库其他资产；Codex 规则按宿主选择。
- [creator 迁移记录](skills/skills-creator/output/migration-2026-09-09.md)与[lint 迁移记录](skills/skills-lint/output/migration-2026-09-09.md)：来源、版本、停用决策、验证及限制。

从项目根运行本地检查：

```sh
python3 -B skills/skills-lint/skills-lint/scripts/list_rules.py skills/skills-creator/skills-creator --profile tooling --host codex
python3 -B skills/skills-lint/skills-lint/scripts/check_skill_density.py skills/skills-creator/skills-creator
python3 -B skills/skills-lint/skills-lint/scripts/test_skill_tools.py
python3 -B -m unittest discover -s skills/skills-lint/skills-lint/scripts/tests -v
```

list_rules 只生成待检查清单，density 只提供统计，不等于完整 lint 或真实宿主行为通过。源包已迁入，安装副本未同步；使用时读取本项目源入口，若要通过宿主发现则按另行授权安装内层完整包，creator 和 lint 应配套提供。

### Teacher Research（教师公开信息研究）

读取 [Skill 入口](skills/teacher-profile-research/teacher-profile-research/SKILL.md)，可用于“调研指定学校教师的履历和带班经历”“核验这份教师介绍”“根据新证据更新师资团队分析”。运行需要宿主具备公开检索和正文读取能力；能力缺失时明确降级为材料审查。

- [研究总约束](skills/teacher-profile-research/teacher-profile-research/references/research-principles.md)与[详细工作流](skills/teacher-profile-research/teacher-profile-research/references/teacher-profile-research-workflow.md)：先身份、再证据、后评价。
- [事实库契约](skills/teacher-profile-research/teacher-profile-research/references/fact-registry.md)与[报告模板](skills/teacher-profile-research/teacher-profile-research/assets/report-template.md)：逐条追溯、保留修订、同步重审受影响结论。
- [虚构案例与行为用例](skills/teacher-profile-research/teacher-profile-research/references/teacher-team-example.md)：不包含本次核实过的真实教师数据。
- [创建验证报告](skills/teacher-profile-research/output/creation-validation.md)：静态检查、密度统计与尚未执行的宿主行为验证分开报告。
- [武汉中学2026级15班首轮研究](skills/teacher-profile-research/output/research-20260909-001/report.md)：2026年秋季入学、武华班型；六人画像、事实库、检索日志与最小核验摘记。任课名单由用户提供，同名候选与已确认职业记录分开。
- [武汉中学2026级15班官网补证版（当前）](skills/teacher-profile-research/output/research-20260909-002/report.md)：补足物理、英语身份与多位教师履历，保留生物职称冲突和化学身份缺口；修订日志与事实历史完整保留。

### Technical Writing（中文技术文档写作）

- [Skill 入口](skills/chinese-technical-writing/chinese-technical-writing/SKILL.md)：写作、定点修改或只读审阅中文技术文档；仅提问时不写回文件。
- [包内技术文档指南](skills/chinese-technical-writing/chinese-technical-writing/references/upstream/document-style-guide/README.md)与[包内中文排版指南](skills/chinese-technical-writing/chinese-technical-writing/references/upstream/chinese-copywriting-guidelines/README.zh-Hans.md)：保留上游规范和示例；[来源与许可](skills/chinese-technical-writing/chinese-technical-writing/references/source-provenance.md)记录收录版本。
- [指南适用说明](skills/chinese-technical-writing/chinese-technical-writing/references/writing-rules.md)、[文档类型指引](skills/chinese-technical-writing/chinese-technical-writing/references/document-types.md)、[Agent 写作自检](skills/chinese-technical-writing/chinese-technical-writing/references/agent-review.md)与[autocorrect 流程](skills/chinese-technical-writing/chinese-technical-writing/references/autocorrect-workflow.md)：先核实事实，再依原文组织内容，最后审稿和校对排版。
- 检查结果保存在本机 `skills/chinese-technical-writing/output/`，按创建与修订版本留存；该目录遵循 `.gitignore`，不随源包推送。最新 `revision-1.1.0/validation.md` 区分静态检查和未执行的真实宿主行为验证。

## Maintenance（维护说明）

项目发生变更时，必须重新思考 README.md 的内容组织，并按实际情况更新目录职责、资产清单和摘要，保持说明与项目现状一致。
