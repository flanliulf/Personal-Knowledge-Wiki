# 版本记录（Changelog）

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
