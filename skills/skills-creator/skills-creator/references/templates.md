# 技能编写模板（Skill Authoring Templates）

## 使用方式（Usage）

本文件是模板写法与示例指南，放在 references 供阅读；不是直接复制到用户输出的单一模板。生成前先消费 spec-guide.md 路由的共享规则表，按实际需求裁剪。`<...>` 是示意占位符，不能留在最终入口中；不要为未确认的能力或宿主配置填值。

## 入口示例（Entry Example）

```yaml
---
name: example-workflow
description: "生成示例评审报告；用于审查示例、review example。输入为用户指定材料，输出为带证据的报告。"
metadata:
  version: "1.0.0"
  author: "<verified-author>"
  catalog: "skill-tooling"
---
```

以上 metadata 及以下正文结构是 tooling 示例；base 只必需 name、description，按需求保留扩展。正文按以下语义结构写入；不要求固定能力条数或统一措辞：

```markdown
## 技能说明（Overview）
说明用户目标与交付物。

## 核心能力（Core Capabilities）
列出完成该目标所需的实际能力。

## 执行流程（Workflow）
1. 校验用户提供的输入；说明缺失信息时的处理。
2. 在需要详细规则时读取真实 reference 路径。
3. 执行步骤并检查结果，定义完成及停止条件。

## 注意事项（Notes）
记录范围、不能推断的事实、依赖缺失处理和输出要求。
```

不要把示例步骤当作所有 Skill 的业务规则。按目标项目已确认政策附加约束，不引入其他项目的实现门禁。

## 英文镜像（English Mirror）

仅 tooling 或目标政策要求时生成 SKILL.en.md，正文使用 Overview、Core Capabilities、Workflow、Notes；完整保留中文入口的输入输出、步骤、条件、能力与引用。name、allowed-tools、license、metadata 相等；description 翻译为语义等价的英文。不要为逐字一致而在英文 mirror 强塞中文触发词。SKILL.md 始终为 canonical。

## 可选 Codex 配置（Optional Codex Configuration）

仅在目标需要时生成 agents/openai.yaml；以下配置展示可选字段，按实际需求删减，不生成空壳：

```yaml
interface:
  display_name: "示例评审"
  short_description: "审查用户指定的示例并输出证据"
policy:
  allow_implicit_invocation: false
```

false 表示仅显式调用；用户未要求此策略时不照抄，缺省允许隐式调用。需要图标时使用真实 assets 资源及正确相对路径。需要 MCP 时扩展 dependencies.tools，所需 type、value、description、transport、url 按真实服务配置填写；服务值未知时先核实，不创建虚假依赖。无 MCP 需求时不生成 dependencies。

## 辅助资源（Supporting Resources）

- references：政策、schema、背景和示例说明；从入口或详细工作流说明加载条件。
- assets：执行中复制或转换的成品模板、图片、字体；Markdown 模板可以没有代码围栏。
- scripts：必要的确定性辅助处理；不把纯阅读代码示例误当实际脚本。

脚本交付应有用途、实际参数、依赖说明、输入验证、明确输出与错误退出码。不能交付带 TODO 或 pass 占位逻辑的脚本并声称已完成。调用路径从实际 Skill 根解析，不依赖 CWD。没有确定性需求时保留 instruction-only。

## 版本记录（Version Record）

tooling 下 CHANGELOG 使用 `## [x.y.z] - YYYY-MM-DD`，记录新增、修改、兼容性变化及验证限制；与两个入口 metadata.version 同步。author 保留原值，不在每轮更新中替换为当前操作者。

## 验证与来源（Validation and Provenance）

交付前读取 testing-guide.md，执行配套 lint 与 density 工具。来源写明本 Skill 由 skills-creator 维护，实际修改同步当前授权范围的入口与资源；不要把“生成过”写成“真实执行验证通过”。如输出类型适合署名，可附来源信息；不得破坏 JSON、代码或用户要求的固定格式。
