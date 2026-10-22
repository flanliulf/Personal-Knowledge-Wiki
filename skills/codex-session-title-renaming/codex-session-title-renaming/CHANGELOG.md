# 版本记录（Changelog）

## [3.0.0] - 2026-10-22

### 新增（Added）

- 主题取证改为同时读会话首尾：最早约 10 条（跳过命令与 Skill 注入后的初始请求）和最近约 10 条。平台映射新增“首尾读取”小节，记录 2026-10-22 实测的 Claude 读法：`list_events(limit=1)` 取总条数，再用 `limit=总条数` 读到最早记录；本地 JSONL 作为备选并说明其依赖内部格式。
- `review` 在固定表头的对照表后单独列出 `reason` 以 `低置信：` 开头的建议；新增对应单元测试。

### 变更（Changed）

- 命名规则：首尾证据仍不足时不再保留原名，改为给出低置信建议并标注；主题无法概括时沿用原标题作主题、只补日期和分类。仅分类也无法判断时保留原名。判定方向由“保留”改为“建议改名”，按 VER-07 升主版本。
- 平台映射注明 Claude 内部元数据中 `titleSource` 为 `user` 时，改名会触发应用内批准；Codex 的首尾读取能力标为未核验。

### 限制（Limitations）

- 首尾读取方法只在 1 个 405 条的会话上测过全量返回，更长会话的返回上限未验证。低置信规则尚未在真实批次中使用；`set_session_title` 对活动时间的影响仍待单条试点确认。

## [2.0.0] - 2026-10-22

### 新增（Added）

- 支持 Claude Code 桌面应用（Code 标签页）的本机会话，`source` 新增 `claude`。新增 `references/provider-mapping.md`，记录 Claude 的目录、详情、主题证据和改名工具，以及字段到八个保护语义键的映射（2026-10-22 依据 `list_sessions`、`get_session` 实际返回确定）。
- `prepare` 校验同一批次只含一种来源，且 `claude` 来源的 `hostId` 必须为 `local`；新增对应单元测试。
- 操作规则新增：某来源首次真实 `apply` 只批准一条改名项作为试点。

### 变更（Changed）

- description 与范围由仅 Codex 扩展为 Codex 与 Claude Code 桌面本机会话，并明确 claude.ai 网页对话、Claude Code CLI 终端会话、远程或云端会话不在范围内。触发边界变化，按 VER-07 升主版本。
- 依赖、运行指南、操作规则与数据契约中“首版只支持 Codex”“`set_thread_title`”等表述改为按来源区分。Skill 名称、全局锁路径与 JSON 结构保持不变，已有 Codex 批次仍可读取。

### 限制（Limitations）

- 未在真实 Claude 会话上运行改名；`set_session_title` 是否更新 `lastActivityAt` 或排序未验证，需首个试点批次确认。源包未安装，宿主发现及真实触发未验证。

## [1.0.0] - 2026-10-08

### 变更（Changed）

- 首次记录版本号。此前未编号的变更：2026-09-26 收录源包；2026-10-07 章节标题与生成报告标题改为 中文（English）形式；2026-10-08 入口新增执行流程，Audit、Apply、Report 三节详细规则移入 `references/operation-rules.md`。
- 运行指南的示例 `asset_root` 由旧机器绝对路径改为 `<资产根目录绝对路径>` 占位符，并说明替换要求。

### 限制（Limitations）

- 采用 base profile；未设置 `metadata.author`。源包未安装，未运行真实改名或配置定时任务，真实宿主行为未验证。
