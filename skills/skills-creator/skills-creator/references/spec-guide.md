# 技能规范指南（Skill Specification Guide）

## 规范来源（Sources）

2026-09-09 核验：[OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) 与 [Plugin skill authoring](https://developers.openai.com/plugins/build/skills)。官方资料指导入口、渐进式加载、可选配置与工作流设计；本文选用的字符预算、双语和版本管理是本工具的 `tooling` 约定，不是官方完整解析器 schema。

## 共享契约（Shared Contract）

规则的唯一权威是配套 skills-lint 的 `references/rule-registry.json`；本文件不复制另一套规则。当前兼容 contract_version `1.0.0`。按以下证据定位 `{lint-root}`：

1. 用户指定配套源包时核实其 SKILL.md 的 name 为 skills-lint、version 为 4.0.1，以及 registry 契约。
2. KnowledgeWiki 中，源包相对路径为 `../../skills-lint/skills-lint`（从本 Skill 根计算）；从本参考文件可访问 [共享规则表](../../../skills-lint/skills-lint/references/rule-registry.json)。
3. 安装环境中读取实际可用 Skill 清单或已知安装根；同级 skills-lint 只作为候选，核验后才采用。不得依赖 CWD，也不得退回已停止维护的 forge 副本。

记录最终绝对路径、版本和 registry SHA-256。配套缺失、版本不符或契约不兼容时保留已完成草稿，将依赖检查标记 NOT_CHECKED 并报告缺口；不得从旧文档重建猜测规则。未来配套升级应先更新此契约与验收。

## 规则范围（Profiles）

| 选择 | 适用范围 |
| --- | --- |
| `base` | 所有目标的基础格式、目标边界、资源与证据质量；默认。 |
| `tooling` | 仅显式采用双语版本化约定的目标，叠加 base。本次迁入的两个工具自身采用。 |
| `--host codex` | 明确以 Codex 为目标时叠加可选配置、调用和依赖检查。 |

其他项目约定单独附录来源和规则，不暗中映射为 tooling，不引入某业务项目的命名空间、模块、实现门禁或路径。

## 编写原则（Authoring Principles）

SKILL.md 必须提供非空 name、description；描述让宿主识别目标和触发，正文承载步骤，资源按需读取。unknown 字段需核验消费方，不能根据固定白名单直接删除。安全 YAML 解析拒绝执行型自定义 tag 和歧义键；合法 `>` 标量及普通尖括号文本不构成错误。

`tooling` 的 name 与目录同名、kebab-case、最多 64 字符；description 最多 1024 字符；每个入口正文最多 5000 字符。这些只是本工具选择的预算。没有全局保留前缀禁令。metadata.version 和 author 必填，catalog 可选且保持语义分类；扩展字段不一概禁止。

中文入口章节用 中文（English），英文 mirror 使用英文标题并保留等价执行语义。name、allowed-tools、license、metadata 保持一致，description 可翻译。CHANGELOG 与两个入口版本同步，保留原作者及历史记录。

## 宿主与资源（Host and Resources）

需要时生成 agents/openai.yaml。按真实需求选择 interface、policy 和 dependencies；不猜测服务 URL。`allow_implicit_invocation: false` 用于只显式调用，缺省允许隐式调用。`allowed-tools` 不替代真实权限与 MCP 配置。

KnowledgeWiki 源目录不是 Codex 自动发现目录。源包、已安装副本和分发包分别核验；同名 Skill 不自动合并。资源从实际包根解析，示例占位符只作说明。具体资源写法见 templates.md；测试与交付证据见 testing-guide.md。
