# Changelog

本文件记录 `skills-lint` 技能的版本变更历史。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [Semantic Versioning](https://semver.org/)。

## [3.0.0] - 2026-09-09

### Changed（变更）
- 唯一维护源迁入 KnowledgeWiki 的 `skills/skills-lint/skills-lint/`；原 forge 保留停止维护的最终快照，后续在新项目使用、维护和迭代。
- 区分 base、Codex 宿主与可选 tooling 项目约定；纠正固定白名单、尖括号、双语触发配额、全局前缀等误判。
- 创建和检查共同消费 skills-lint 的 rule-registry.json；规则数量动态计算，静态、行为和未检查证据分开报告。
- 同步英文 mirror、参考资料和资源加载路径，保留原作者及旧版历史。

### Compatibility（兼容性）
- 外部目标默认 base；旧通用严格双语约定须明确选择 tooling，不隐式应用到 KnowledgeWiki 其他资产。
- 配套 creator 2.0.0 / lint 3.0.0，规则契约 1.0.0。密度 JSON 升级 schema_version=2，缺失/歧义指标改为 null；旧消费者需适配。
- 源迁移不代表安装副本已更新；未执行真实宿主行为验收。

## [2.3.0] - 2026-05-26

### Added

- 新增只读脚本 `scripts/check_skill_density.py`，用于统计 SKILL.md 与 SKILL.en.md 的正文长度、Workflow 长度、占比和 workflow reference 引用情况。
- 新增 BODY-07 Workflow density 与 BODY-08 Workflow extraction 两条规则，规则总数从 32 条增加到 34 条。
- 新增 `references/lint-workflow.md`，承载完整扫描流程，降低入口 Workflow 体积。
- 新增 metadata 字段契约说明，覆盖 `metadata.version`、`metadata.author` 和可选 `metadata.catalog` 的检查边界。

### Changed

- allowed-tools 增加 Bash，仅用于运行只读 density checker。
- SKILL.md 与 SKILL.en.md 的 Workflow 改为阶段路由，详细扫描步骤转入 reference。
- Workflow 入口明确“完整步骤见 `references/lint-workflow.md`”，执行细则以 reference 为准。

## [2.2.0] - 2026-05-25

### Added

- 新增 `SKILL.en.md` mirror 检查规则：文件存在、版本一致、YAML frontmatter 对齐、英文章节齐备和引用路径同步。
- 新增中文 canonical 语言规则检查：SKILL.md 章节标题使用 English（中文）形式，正文内容使用中文，技术标识使用英文。
- 新增 `skill-tooling` catalog，用于归类 Skill 创建、检查、升级工具链。

### Changed

- 规则总数从 28 条增加到 32 条，检查维度从 7 个扩展为 8 个。
- 必需章节检查从旧的中文标题更新为 `[Overview（技能说明）]` 等 English（中文）标题。

## [2.1.0] - 2026-04-09

### Added

- 新增 VER-04 规则：检查 `metadata.author` 字段是否存在且非空（Warning 级别）
- references/check-rules.md 新增 VER-04 详细说明，包含检查标准和缺失时的修复建议

### Changed

- 规则总数从 27 条增加到 28 条
- 版本一致性检查维度从 3 条扩展为 4 条（VER-01 ~ VER-04）

## [2.0.0] - 2026-04-08

### Changed

- Skill 更名：`skill-lint` → `skills-lint`，与项目命名规范（skills-creator 等）保持一致
- YAML `name` 字段由 `skill-lint` 改为 `skills-lint`
- description 中新增触发词 `'skills-lint'`，同时保留旧触发词（`'skill lint'`、`'lint skill'` 等）向后兼容
- 正文中对 `skill-upgrade` 的引用更新为 `skills-upgrade`

## [1.1.0] - 2026-04-08

### Added

- 新增文件分类合理性检查维度（CLASS-01 ~ CLASS-03）：检测模板文件是否误放 references/、脚本文件是否误放 references/ 或 assets/、纯知识文档是否误放 assets/
- 新增 BODY-05 核心能力条数检查：[核心能力] 章节内 `- **` 开头的行数应在 4-8 范围内
- 新增 VER-03 CHANGELOG 日期格式检查：版本标题中的日期必须匹配 YYYY-MM-DD 格式
- 模糊表述检测词列表新增"必要时"

### Changed

- 检查维度从 6 个扩展为 7 个，规则总数从 22 条增加到 27 条
- 检查报告总结行从 X/22 更新为 X/27

## [1.0.0] - 2026-03-25

### 初始版本

- YAML Frontmatter 验证：name 格式、description 长度、顶级属性合法性、安全检查
- description 质量分析：三段式结构验证、中英文双语触发词覆盖、触发词具体性
- 文件结构合规检查：SKILL.md 大写、目录名 kebab-case、无 README.md、CHANGELOG.md 存在
- 版本一致性检查：SKILL.md metadata.version 与 CHANGELOG.md 最新版本号一致
- 正文约束检查：字数限制、必需章节、引用路径、无模糊表述
- 命名规范检查：references/scripts/assets 文件命名格式
- 结构化表格报告输出，区分 Error 和 Warning

### 已知问题

- 暂无

---

版本变更类型说明：
- **Added**：新增功能
- **Changed**：已有功能的变更
- **Fixed**：缺陷修复
- **Removed**：移除的功能

后续版本更新时，在最新版本记录之前插入新版本记录，并同步更新 SKILL.md 中的 metadata.version。
已知问题修复后，用删除线标注并注明修复版本，如：
- ~~**问题描述**~~ → 已在 vX.Y.Z 修复
