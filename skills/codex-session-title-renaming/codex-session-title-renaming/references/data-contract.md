# Data Contract（数据契约）

## Ownership（数据职责）

- 每批核心数据仅为 `proposal.json` 和 `execution.json`，分别受 `schemas/` 中同名 JSON Schema 约束。
- `proposal.json`：已展示的提案，冻结后不改写；建议变化或部分批准时另建批次。
- `execution.json`：绑定提案字节的 SHA-256、真实用户确认依据；每条执行前后立即更新。没有 `execution.json` 不能推断已有批准或执行。
- 不建立 `approval.json`、事件日志、全局增量索引或会话级状态。全局锁只协调当前操作，保存 `executionId`、`startedAt`。
- JSON 的哈希、schema 校验和 `approval.evidence` 字段都不能自行证明真实授权；Agent 必须依据当前用户消息识别批准。文档渲染脚本仅转述记录中的证据。

## Proposal（待确认清单）

| 字段 | 含义 |
| --- | --- |
| `schemaVersion` | 初版固定为字符串 `1` |
| `batchId` | 独立批次标识，与目录同名；仅字母、数字、下划线、连字符，最多 80 字符 |
| `generatedAt` | 提案生成时间，带时区的 ISO 8601；不用于标题日期 |
| `timezone` | 固定 `Asia/Shanghai` |
| `scope.description` | 实际检查来源、范围、是否有限量，以及用户是否要求主题重评 |
| `scope.unavailable` | 未读取或不支持的来源、目录及原因；空数组仅表示本次没有已知缺口，不代表全部账号历史 |
| `items[].itemId` | 本批唯一行标识 |
| `threadId`、`hostId`、`source` | 经工具确认的稳定身份；去重键为三者组合，首版 `source` 固定 `codex` |
| `createdAtSource` | 创建时间的真实工具字段/证据引用；缺失时为 `null`，不得替代推算 |
| `oldTitle`、`newTitle` | 提案原标题与建议标题，保留项两者相同 |
| `decision`、`reason` | `rename` 或 `keep`，以及有证据的理由 |
| `baseline` | 提案时观察快照，使用 `snapshot.schema.json` |

`baseline.title` 必须等于 `oldTitle`。改名项必须有可靠创建时间且 `running` 为 `false`；无法确定则本轮保留，不建立等待状态。运行中的记录可以作为 `keep` 保留在本批清单中。

## Observations（观察快照）

快照包含 `observedAt`、`title`、`createdAt`、`running`、`protected`、`unavailableProtection`、`evidence`。

- `createdAt` 是经工具单位核实后规范化的带时区 ISO 8601，未知为 `null`。`running` 是实际运行状态，未知为 `null`；不要把等待用户输入等应用字段未经检查就映射为布尔值。
- `protected` 使用统一语义键：`projectName`、`projectId`、`pinned`、`archived`、`sectionId`、`order`、`updatedAt`、`contentFingerprint`。各平台字段到这些语义键的映射须在运行时确认；值保留观察到的 JSON 结构，不假定排序字段的数据类型。
- `protected` 中的 `null` 表示实际观察到空值。无法取得的字段必须放入 `unavailableProtection`。两者互斥且共同覆盖全部八个键。
- `contentFingerprint` 仅在可通过允许的只读路径取得时记录；不能为追求完整快照而超范围读取全部正文。不能取得时明确列为未核验。
- `evidence` 写必要的工具调用或证据文件引用，不复制完整会话内容。补充证据按需保存在同批 `evidence/`；临时输入在资产 `work/`，不放到源目录内。

## Execution（执行结果）

根字段包括 `schemaVersion`、`batchId`、`proposalSha256`、`approval`、`startedAt`、`finishedAt`、`items`。`approval` 只有 `confirmedAt` 和 `evidence`；记录真实确认时间和用户消息依据，不支持伪造或自行推断批准。初版只接受完整批准批次，部分批准先生成只包含获批候选的新提案并确认其映射。

每行通过 `itemId` 关联提案，保留 `before`、`after` 实际快照、`requestOutcome`、`status`、`reason`、`error` 与 `checks`。四个标题分别来自提案原名、执行前实际值、提案目标值和回读实际值。

| `status` | 含义 |
| --- | --- |
| `not_executed` | 未执行，初始状态 |
| `skipped` | 保留、当前已为目标、当前状态变化或无法读取等；原因明确记录 |
| `unknown` | 已记录写入意图但结果不足、请求超时、回读缺失或有核验差异；不自动重试 |
| `failed` | 工具明确报错且回读仍为执行前标题 |
| `verified` | 回读达到目标，创建时间和前后都能观察的保护字段通过检查 |

`verified` 不代表未取得字段也已验证，不证明所有全局应用状态没有变化，也不单凭回读证明标题必由本次请求修改。`requestOutcome` 单独保留实际调用结果：`not_sent`、`success`、`error`、`uncertain`。

`checks` 保留标题匹配、创建时间匹配、保护字段匹配、差异键及未取得键；布尔值 `null` 代表证据不足。标题写入后发现创建时间或保护字段变化时停止本批后续写入，不自动回滚其他活动。根级 `finishedAt` 仅表示本轮执行结束，不表示全部成功。报告统计从逐条状态计算，不存储另一份手工计数。

## Persistence（保存与中断）

全局锁使用独占创建；真实入口固定使用 `~/.codex/locks/codex-session-title-renaming.lock`，不按项目、批次或安装副本各建一把锁。锁文件不设 TTL，不自动接管；锁损坏或异常遗留须人工核查后清理。

提案目录独占创建，已有批次不覆盖；JSON 更新采用同目录临时文件、刷新后替换。写入请求发出前先保存 `unknown`，每条回读后立即更新。文件与应用不是同一个原子事务，无法消除中断窗口；未知项通过后续人工核查处理。已有执行文件不能再次 `start`，不提供自动恢复与重试功能。

## Report（派生文档）

可读确认表从提案即时渲染；完整 Markdown 按需生成到同批 `reports/`。每次报告使用新文件名，不改写历史文档，包含源数据哈希、批次、时间、建议、实际观察、状态与限制。报告器不调用应用、没有改名能力，也不因发现结果缺失而执行修复。

历史 JSON 和旧脚本保持原样，不自动迁入新 schema，不以旧脚本固定的成功数量初始化新批次。
