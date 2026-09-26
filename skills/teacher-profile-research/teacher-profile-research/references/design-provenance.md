# Design Provenance（方案来源与映射）

## Source（来源）

设计依据：用户在本次任务补充的完整粘贴方案，主题为教师公开信息画像与教学决策研究。其对应分享链接为 https://chatgpt.com/share/6aa0c28d-744c-83e9-9165-87363bd643c4 。创建时分享正文无法读取，以用户提供文本为实际依据，不宣称已核验完整历史。

原始粘贴文本作为创建输入保存在外层资产 `work/source-plan.txt`；这不是安装后运行依赖。原文中的具体人物与履历仅为用户提供的历史案例，本包未将其固化为真实数据。运行时不需要该分享链接可访问。

用户指定的旧 skills-creator forge 入口已声明停止维护并指向本项目新源，因此实际使用 KnowledgeWiki skills-creator 2.0.0 与 skills-lint 3.0.0 的 contract_version 1.0.0。采用 base profile、宿主 unspecified，不强制双语 tooling 约定，不安装或同步任何副本。

## Mapping（需求映射）

| 方案要点 | 本包落点 |
| --- | --- |
| 单一 MVP、名称 teacher-profile-research | SKILL.md；不创建三个子 Skill |
| System Prompt + Skill 双层结构 | research-principles.md + teacher-profile-research-workflow.md；不修改真实宿主设置 |
| Intake、Identity、Search、Extraction、Verification | 工作流 Phase 1–4 |
| A–D 来源及检索优先级 | evidence-levels.md、source-priority.md |
| 五种互斥事实状态 | claim-status.md、fact-registry.md |
| Claim-Level Verification、相邻人物串位 | Phase 3–4、虚构反例 c001–c003 |
| 任教时间轴、班型、风格、教研竞赛及成果 | Phase 5、报告 Part B |
| 班主任独立建模与 A–E 成熟度 | Phase 5：班主任经历证据分型，保留类型定义及证据限制 |
| 多轮事实库和纠错 | fact-registry.md、Phase 7、新批次快照及 corrections |
| 单人后团队、多维角色和风险 | Phase 6、报告 Part C，区分已证实约束与信息缺口 |
| A–D 四部分报告、每人 11 个维度 | assets/report-template.md |
| 示例与反例 | references/teacher-team-example.md，全部虚构 |

## Clarifications（实施澄清）

- “confirmed by user context”在五态契约中统一为 USER_PROVIDED，避免将用户确认偷换成公开确认。
- 截图按可验证出处评级，不按文件格式永久定 D；学校侧口述保持 D。
- “未找到完整周期”不等于“未完成完整周期”；A–E 改以经历证据覆盖呈现，不宣称成熟度量表经过验证。
- 一般履历猜想保留 UNVERIFIED 假设，不挤入 STRONGLY_INFERRED。
- 方案示意中的 report-template.md 是可复制成品，按创建器的资源用途规则放 assets；详细解释仍放 references。
- Fact Registry 由 Agent 按 JSON 契约维护；不把简单脚本宣称为能自动判定人物身份或事实真实性的实现。
