# 聚合设计分析（Aggregate Design Analysis）

## 填写说明（Completion Instructions）

按证据与交接契约填写。未知值写 unknown 并引用 question_ids；没有数据时说明不适用依据，不留空表后宣布完成。所有关键项使用 confirmation_status；检查状态和执行状态不能替代它。默认对话交付，保存需有用户要求和指定位置。

## 范围与基线（Scope and Baseline）

- scope：
- baseline：区分当前行为、批准目标和候选。
- context / version_or_time：
- 已授权读取与输出范围：
- result_status：ready_for_review / needs_clarification / blocked。
- 核心结论及其状态：

## 证据（Sources）

| source_id | source_kind | locator | excerpt_or_summary | context | version_or_time |
| --- | --- | --- | --- | --- | --- |

## 概念（Concepts）

| concept_id | 业务含义 | 身份与生命周期要求 | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- |

## 规则与一致性（Rules and Consistency）

| rule_id | statement：条件、例外、时域 | scope | 涉及概念与命令 | 违反后果 | consistency_requirement及可接受延迟 | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 并发场景（Concurrency Scenarios）

| scenario_id | rule_ids | 操作与交错顺序 | 各方读取基线 | 可能破坏与预期结果 | 观测事实或设计推演 | evidence_ids | confirmation_status |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 边界候选（Boundary Candidates）

| aggregate_id | root_concept_id | member_concept_ids | rule_ids | 业务整体与身份范围 | 外部引用 | 冲突与加载代价 | evidence_ids | confirmation_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 跨边界规则（Cross-Boundary Rules）

| rule_id | 涉及边界 | 即时性要求 | 候选策略与责任 | 失败窗口与代价 | evidence_ids | confirmation_status | question_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 修改与保存契约（Mutation and Persistence Contract）

| 入口或通道 | aggregate_id / rule_ids | 校验与封装 | 必需加载及重建策略 | update_semantics与字段缺席含义 | 保存及失败处理 | evidence_ids | confirmation_status |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 并发保护覆盖（Concurrency Protection Coverage）

| 已知写入通道 | 保护对象及机制 | 仅改子对象如何原子比较并推进令牌或等价保护 | 成功判定与冲突后动作 | 部分失败的原子性 | 实现位置或候选 | evidence_ids | confirmation_status | question_ids | 检查状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

检查状态使用已核验、未核验或不适用；它不替代 confirmation_status。

## 决策（Decisions）

| decision_id | 候选与选择 | decision_reason | evidence_ids | confirmation_status | 复议条件 |
| --- | --- | --- | --- | --- | --- |

## 验证计划（Verification Plan）

| case_id | rule_ids / scenario_ids | 输入和动作顺序 | 可观察结果与判定 | 执行状态 | 实际证据 |
| --- | --- | --- | --- | --- | --- |

执行状态未有运行证据时填写 NOT_CHECKED。不能将设计推演填为 PASS。

## 未决问题（Open Questions）

| question_id | 缺失或冲突事实 | 影响的规则与候选 | 已有 evidence_ids | 需要谁提供什么信息 |
| --- | --- | --- | --- | --- |

## 自检与交接（Review and Handoff）

- rules、边界、场景及机制的追溯结果：
- 写入通道覆盖及仍未核验的通道：
- 继承上游标识及合并/拆分映射：
- 留给关联分析的概念或多重性问题：
- 下一步所需输入；ready_for_review 不代表设计批准或实现授权：
