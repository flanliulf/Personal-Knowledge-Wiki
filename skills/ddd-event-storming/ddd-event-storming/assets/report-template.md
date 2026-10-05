# 事件风暴分析报告（Event Storming Analysis Report）

## 填写说明（Completion Instructions）

按本模板交付，默认在对话中填写。保存须有用户明确要求和指定位置。复用已存在的标识；单元格无事实依据时写 unknown 并关联 question_ids。只有经证据确认没有数据时才写 none。不存在的 source_id 不得伪造。confirmation_status 只能用 confirmed、candidate、unknown、conflicted、rejected。

每个 section 对应统一字段 scope、baseline、sources、concepts、rules、decisions、open_questions 和 result_status；本报告的业务事件、命令、查询和覆盖矩阵是专用扩展。填写无记录的表时说明“当前范围不适用”及依据，或说明尚未取得资料；不得留下空表后宣布完成。

## 范围（Scope）

- scope：业务过程、上下文、本次问题、范围内与范围外事项。
- 本次方法：协作式事件分析、材料分析或复用已有用例；记录选择理由和业务参与者。
- 覆盖结论：列出核对过的需求基线；没有功能全集时明确限制。

## 输入基线（Baseline）

| 项目 | 内容 |
| --- | --- |
| 当前行为 | 待填写 |
| 已批准目标 | 待填写；无批准依据时写 unknown |
| 候选方案 | 待填写；与目标分开 |
| 资料版本或时间 | 待填写；不确定写 unknown |
| 已授权读取范围 | 待填写 |
| 已授权写入范围 | 待填写；仅分析时写 none |
| 既有需求产物 | 用例、用户故事、功能清单及其版本；无基线时写 unknown |

## 来源（Sources）

| source_id | source_kind | locator | excerpt_or_summary | context | version_or_time |
| --- | --- | --- | --- | --- | --- |

locator 必须可复核；仅登记 URL 不意味着已读取正文。excerpt_or_summary 保留支持结论所需的条件和例外。

## 事件与命令（Events and Commands）

| event_id | event | command_id | command | actor_roles | required_read_data | read_data_ids | candidate_nouns | concept_ids | path_kind | condition_and_order_note | rule_ids | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

path_kind 使用 main、optional 或 exception。condition_and_order_note 区分证据支持的适用条件、严格约束与粗略顺序。事件涉及多个名词时复用 event_id，不复制成不同事件。若命令、角色和读取的确认程度不同，在下表分别记录，事件的状态不能代替整行各字段的状态。

## 命令事实（Command Facts）

| command_id | fact_field | fact_value | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- |

fact_field 使用 command、actor_roles、required_read_data。支持多角色与多读取；经确认没有所需读取才写 none。没有事实答案时写 unknown。

## 查询需求（Query Requirements）

| read_data_id | query_purpose | actor_roles | data_needed | filters_and_scope | permission_and_freshness | linked_command_ids | requirement_ids | rule_ids | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

linked_command_ids 为 none 的记录表示独立查询。filters_and_scope、permission_and_freshness 只填写已有证据的要求；未知时提出问题，不自动补 API 或表结构。

## 功能覆盖矩阵（Function Coverage Matrix）

| requirement_id | baseline_locator | function | requirement_kind | event_ids | command_ids | read_data_ids | coverage_status | missing_or_excluded_reason | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

requirement_kind 使用 command、query 或其他已说明的需求类型；coverage_status 使用 covered、gap、out_of_scope、unknown。仅在功能清单保存且事件视图省略时，在 missing_or_excluded_reason 说明该功能已登记而未展开。是否需要修改、删除等操作由证据决定，不能默认新增或忽略。

## 候选概念（Concepts）

| concept_id | name | meaning | scope | related_event_ids | related_command_ids | candidate_interpretation | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

candidate_interpretation 可记录实体、值对象、角色、属性、合并或拆分的待建模问题。名词识别本身不确认模型类型。

## 统一术语（Ubiquitous Language）

| term | aliases | definition | scope | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- |

## 业务规则（Rules）

| rule_id | statement | scope | conditions_and_exceptions | temporal_and_consistency_requirements | related_event_ids | related_concept_ids | evidence_ids | confirmation_status | question_ids | implementation_or_verification_followup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

statement 连同条件、例外、时间和一致性要求共同表达规则。实现位置和验证计划未取得时记录待办，不宣布已经实现。

## 分析决策（Decisions）

| decision_id | subject | selected_or_retained_option | alternatives | decision_reason | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 未决问题（Open Questions）

| question_id | question | reason | affected_ids | required_input | confirmation_role | blocking_effect |
| --- | --- | --- | --- | --- | --- | --- |

blocking_effect 说明缺口阻止哪些结论；可独立完成的部分可以继续。不能通过没有授权的跨任务消息自动联系确认角色。

## 自检与交接（Review and Handoff）

| 检查项 | 结果与证据 |
| --- | --- |
| 范围、版本与来源可追溯 | 待填写 |
| 事件、命令、角色与查询区分清楚 | 待填写 |
| 技术事件排除，纯查询保留 | 待填写 |
| 主路径、可选与异常保留，顺序没有被过度推断 | 待填写 |
| 已有功能逐项映射，修改删除等没有凭默认忽略 | 待填写 |
| 概念仍是候选，规则保留条件例外 | 待填写 |
| 证据状态与未决问题一致 | 待填写 |
| 输出权限与稳定标识遵守契约 | 待填写 |

- result_status：选择 ready_for_review、needs_clarification 或 blocked，并说明理由。
- 可交接关联分析：concepts、角色解释、多种关联或时间问题、sources、rules 和 open_questions。
- 可交接聚合设计：业务命令、相关概念、不变规则、时间与一致性线索及未决问题。
- 下一步所需输入：待填写。其他 Skill 未安装不阻止本报告交付；报告不代表设计批准或实现授权。
