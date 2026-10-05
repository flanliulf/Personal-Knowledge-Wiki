# 领域关系分析报告（Domain Relationship Report）

## 范围与基线（Scope and Baseline）

- `scope`：业务目标、纳入范围及排除范围。
- `baseline`：上下文、版本/时间、当前行为/已批准目标/候选，读取和写入授权。
- `result_status`：`ready_for_review` / `needs_clarification` / `blocked`。

## 来源（Sources）

| source_id | source_kind | locator | excerpt_or_summary | context | version_or_time |
| --- | --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 实际消息/路径及行号/版本 | 最小支持信息 | 待填写 | 不可确定写 unknown |

## 概念（Concepts）

| concept_id | 名称及业务含义 | 候选分类及类/实例辨析 | scope | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- |
| 复用上游标识 | 待填写 | 不把所有名词判成实体 | 待填写 | 待填写 | 待填写 | 待填写 |

## 关系（Associations）

每种独立业务含义单列一条；同一对 A/B 的不同角色不合并。以下字段对每条关系重复填写：

| 字段 | 内容 |
| --- | --- |
| association_id | 稳定标识 |
| A / B | 两端 concept_id |
| role_A / role_B | A 端/B 端对象在本关系充当的角色 |
| statement | 用业务自然语言解释本关系 |
| A_to_B.min / A_to_B.max | 固定一个 A，所对应 B 的最少/最多；未知分别写 unknown |
| B_to_A.min / B_to_A.max | 固定一个 B，所对应 A 的最少/最多；未知分别写 unknown |
| temporal_scope | 同时/历史范围、有效期、区间及状态条件；未知不默认 |
| qualifier | 拥有端、键/类型、限定后最少/最多及依据；没有则写不适用 |
| relationship_attributes | 值的含义、所属关系及理由；关联实体候选 concept_id |
| rule_ids | 数量、资格、根/循环、历史、重叠、同时性及局部唯一规则 |
| evidence_ids | 各四问/角色/属性/时间等的 source_id；无证据候选明确标记 |
| confirmation_status | confirmed / candidate / unknown / conflicted / rejected |
| question_ids | 引用 open_questions 的 question_id，说明受影响字段；不另建问题编号 |
| implementation_implications | 关联实体、访问、唯一性或聚合一致性等候选及未知；不填写可执行 DDL |

## 规则（Rules）

| rule_id | statement | scope | evidence_ids | confirmation_status | question_ids | 实现位置与验证计划待办 |
| --- | --- | --- | --- | --- | --- | --- |
| 复用标识 | 保留条件、例外、时间范围和一致性要求 | 待填写 | 待填写 | 待填写 | 待填写 | 未研究写待评估 |

## 决策与表示检查（Decisions）

| 决策/概念映射 | 旧到新 concept_id / association_id | decision_reason | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- |
| 关联实体、属性/关联展示、候选合并或泛化辨析 | 不重编号已存在项 | 权衡及未改既有图的边界 | 待填写 | 待填写 | 待填写 |

说明每条属性/关联表达是否保留角色、类型、多重性和 rule_ids；展示省略记录在此。列出重复或冲突，不擅自删除既有图。

## 未决问题（Open Questions）

| question_id | 问题 | 所需业务/资料输入 | 依赖此答案的 concept_id / association_id / rule_id | 当前可独立推进部分 |
| --- | --- | --- | --- | --- |
| 复用标识 | 具体提问 | 待填写 | 待填写 | 待填写 |

## 检查与交接（Checks and Handoff）

- 四问读向、同对实体双角色、自关联根与循环、关系属性、历史再次加入、时间重叠和同时性：逐项写已检查/不适用/未检查及依据。
- 限定是否误替重叠约束、属性与关联是否重复、类/实例是否混淆、业务与实现是否冲突：逐项记录。
- 交接 scope、baseline、sources、concepts、rules、decisions、open_questions、result_status 及 associations。
- 聚合生命周期、不变规则与事务一致性未研究时列为后续问题；ready_for_review 不等于批准或实现授权。
