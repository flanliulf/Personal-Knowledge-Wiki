# Changelog

本文件记录 `skills-creator` 技能的版本变更历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [Semantic Versioning](https://semver.org/)。

## [3.0.1] - 2026-10-07

### 变更（Changed）
- references 文档的章节标题改为 中文（English）形式；配套契约核实的 lint 版本同步为 4.0.1，创建流程与模板语义不变。

## [3.0.0] - 2026-10-07

### 变更（Changed）
- 中文入口与入口示例模板的章节标题改为 中文（English）形式，与配套 lint 4.0.0 的 BODY-06 一致；英文 mirror 继续使用英文标题。
- 配套契约改为核实 skills-lint 4.0.0；spec-guide 与 testing-guide 同步版本及标题说明。

### 兼容性（Compatibility）
- 破坏性变更：按 tooling 生成的新入口改用中文在前的标题，旧 English（中文）标题需迁移。规则契约 1.0.0 不变，不再与 lint 3.0.0 配套。
- 未执行真实宿主行为验收，安装副本未同步。

## [2.0.0] - 2026-09-09

### Changed（变更）
- 唯一维护源迁入 KnowledgeWiki 的 `skills/skills-creator/skills-creator/`；原 forge 保留停止维护的最终快照，后续在新项目使用、维护和迭代。
- 区分 base、Codex 宿主与可选 tooling 项目约定；纠正固定白名单、尖括号、双语触发配额、全局前缀等误判。
- 创建和检查共同消费 skills-lint 的 rule-registry.json；规则数量动态计算，静态、行为和未检查证据分开报告。
- 同步英文 mirror、参考资料和资源加载路径，保留原作者及旧版历史。

### Compatibility（兼容性）
- 外部目标默认 base；旧通用严格双语约定须明确选择 tooling，不隐式应用到 KnowledgeWiki 其他资产。
- 配套 creator 2.0.0 / lint 3.0.0，规则契约 1.0.0。密度 JSON 升级 schema_version=2，缺失/歧义指标改为 null；旧消费者需适配。
- 源迁移不代表安装副本已更新；未执行真实宿主行为验收。

## [1.5.0] - 2026-05-26

### Added

- 新增 Workflow density gate 创建规则：生成草稿后使用 `skills-lint` 的 deterministic checker 统计正文长度、Workflow 长度和占比。
- 新增 `references/skill-creation-workflow.md`，承载完整创建流程，降低入口 Workflow 体积。
- references 模板、规范和测试指南新增 density gate、workflow reference 抽取和验证要求。
- 新增 metadata 字段契约，明确 `metadata.version`、`metadata.author` 和可选 `metadata.catalog` 的生成与同步规则。

### Changed

- SKILL.md 与 SKILL.en.md 的 Workflow 改为阶段路由，详细创建步骤转入 reference。
- 命中 `workflow_chars > 1500` 且 `workflow_ratio > 0.5` 时，创建阶段必须抽取 `references/<skill-name>-workflow.md` 或等价 workflow reference。

## [1.4.0] - 2026-05-25

### Added

- 新增 `SKILL.en.md` 英文 mirror 生成规则，要求创建 Skill 时与中文 canonical `SKILL.md` 同步生成。
- 新增中文 canonical 语言规则：正文内容始终使用中文，章节标题使用 English（中文）形式，技术标识和专有技术术语使用英文。
- 新增 `skill-tooling` catalog，用于归类创建、检查、升级 Skill 本身的元 Skill。

### Changed

- 文件结构规划、生成标注和测试检查清单扩展为 SKILL.md / SKILL.en.md / CHANGELOG.md 三件套。
- 版本更新指引调整为通过 skills-upgrade 同步维护 SKILL.md、SKILL.en.md 和实际安装副本。

## [1.3.0] - 2026-04-17

### Added

- YAML metadata 新增可选 `catalog` 字段：用于统一 forge/vault/output 三个目录下的子目录归属
- 需求收集阶段 Q7 新增 catalog 分类询问：提供已有分类参考列表，支持选择已有分类、填写新分类或留空
- 需求确认清单新增 Catalog 分类项

### Changed

- 输出路径规则从固定 `<group>` 改为基于 `metadata.catalog` 动态决策：有 catalog 时归入对应子目录，无 catalog 时放在根目录
- forge/ 强制优先规则、output/ 输出物管理规则同步更新为基于 catalog 的路径方案
- SKILL.md 模板（references/templates.md）metadata 区域增加 `catalog` 可选字段

## [1.2.0] - 2026-04-09

### Added

- YAML frontmatter 新增 `metadata.author` 字段支持：创建 Skill 时自动写入原始作者名
- author 自动获取策略：优先从 `git config user.name` 读取，失败时提示用户手动提供
- SKILL.md 模板（references/templates.md）metadata 区域增加 `author: "<author-name>"` 字段

### Changed

- Step 6 生成规则扩展：YAML 头部字段列表新增 `metadata.author`
- [注意事项] 新增 `metadata.author` 自动获取策略说明

## [1.1.0] - 2026-03-25

### Added

- description 中英文双语触发词覆盖规则：触发关键词必须同时包含中文和英文常用表述
- Step 6 生成规则新增双语触发词检查和生成指引
- Q3 提问模板新增中英文双语覆盖要求

### Changed

- spec-guide.md 示例更新为包含中英文双语触发词的版本，新增仅英文触发词的错误示例
- templates.md description 生成规则增加双语要求和双语示例
- testing-guide.md 新增双语触发词覆盖检查项

### Fixed

- skills-creator 自身 description 缺少中文触发关键词（新增 '创建 skill'、'新建技能'、'生成技能' 等 7 个中文触发词）

## [1.0.0] - 2026-03-25

### 初始版本

- 渐进式需求挖掘：通过结构化问答（一次最多 3 题）收集用户需求
- 五大工作流模式智能匹配：顺序工作流、多 MCP 协调、迭代优化、上下文感知、领域专有智能
- 规范转译：自动生成三段式 description、kebab-case 命名、allowed-tools 配置
- 渐进式披露架构设计：按三层加载系统（触发层→核心层→按需层）分配内容
- 完整文件包生成：SKILL.md、CHANGELOG.md、references/、scripts/、assets/
- 脚本编写：包含 docstring、错误处理、输入验证、正确退出码的 Python/Shell 脚本
- 触发测试指导：三类测试方案（明确相关/同义替换/无关查询）和迭代优化建议
- 质量把控：YAML 安全检查、正文字数控制、命名规范验证

### 已知问题

- 暂无

---

版本变更类型说明：
- **Added**：新增功能
- **Changed**：已有功能的变更
- **Fixed**：缺陷修复
- **Removed**：移除的功能

后续版本更新时，在最新版本记录之前插入新版本记录，并同步更新两个入口中的 metadata.version。
已知问题修复后，用删除线标注并注明修复版本，如：
- ~~**问题描述**~~ → 已在 vX.Y.Z 修复
