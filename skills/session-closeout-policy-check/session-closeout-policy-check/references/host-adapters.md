# 宿主适配（Host Adapters）

## 共享核心（Shared Core）

使用一份 `SKILL.md` 和一套检查契约。宿主 Hooks 放在外部配置中，通过相同命令型处理器调用。共享入口不使用 Claude 专属 `hooks`、`context` 或 `agent` 字段，也不把 `allowed-tools` 当作权限隔离。

本源包可由 Agent 在当前会话直接读取。自动发现需要另行安装完整内层包：Codex 的已核验发现目录包括 `.agents/skills/`，Claude Code 包括 `.claude/skills/`。具体安装目标由用户确认；本轮不修改任何发现目录或宿主配置。

## 运行材料（Runtime Materials）

从以下模板复制到用户指定运行目录，并替换全部占位符：

- [可信上下文模板](../assets/session-context-template.json)：任务、授权范围、规则清单和起始记录。
- [收尾请求模板](../assets/closeout-request-template.json)：绝对路径与本次请求标识。
- [检查报告模板](../assets/review-report-template.json)：初始为 `UNVERIFIED`，不预置通过。

运行目录必须在 Skill 源包与安装包之外，默认选择仓库之外的本地目录。request/context/report 的解析路径必须互不相同，不自动从项目来源资料读取。`active=false` 时收尾 Hook 不工作；用户明确收尾后填 `active=true` 和新的 `request_id`。不使用 transcript、宿主 session id 或会话标题猜测授权。

Hook 从事件 `cwd` 解析实际 Git root，并与请求项目匹配。进入 worktree 后不能继续沿用另一个 checkout 的请求。request 旁的状态文件仅用于记录请求已提醒，不是规约检查证据。

请求在匹配的 Stop 开始检查前消费，包括已有有效报告、无 staged 改动或检查错误。未暂存产物先用 Skill 普通模式预检查；形成 index 后手动最终检查或启用一个新请求，不自动暂存。

## Codex 适配（Codex Adapter）

[Codex 模板](../assets/codex-hooks-template.json) 使用 `Stop` + `command`。将其内容合并到已确认的 `.codex/hooks.json` 或用户配置层，替换 Python、Skill 和运行目录路径。不要同时重复注册 JSON 与 TOML 表达。

当前官方支持命令和 MCP 处理器，`prompt`、`agent` 处理器会被跳过。本方案使用命令处理器，不需要额外模型 API 或 MCP。非托管 Hook 需用户审阅并信任实际定义，不能宣称源包创建即已启用。

`Stop` 接收 JSON 输入；命令退出 `0` 时返回 `{}` 或有效 JSON。缺少有效检查结果且请求未消费时，返回 `decision=block` 和明确理由，让当前 Agent 读取实际包根的 Skill 并完成检查。`stop_hook_active=true` 时直接返回 `{}`，防止连续续轮。

`SessionEnd` 在真正结束时运行，属于提示性事件，不能留下 Agent 完成修订，不用作本方案的主要检查入口。官方能力与用户本机可用性分开核验。

## Claude Code 适配（Claude Code Adapter）

[Claude Code 模板](../assets/claude-settings-template.json) 使用相同的 `Stop` + `command`，合并到已确认的 `.claude/settings.json` 或用户配置。共享 Skill 安装后可通过 `/session-closeout-policy-check` 显式调用；源入口直接读取不依赖 slash command 已发现。

`Stop` 是主 Agent 完成响应的事件，不能单凭该事件认定用户要结束会话。只在外部请求明确启用时检查。缺少有效报告时返回 `decision=block` 和 `reason`；检查 `stop_hook_active` 并消费请求标识，防止循环。

不读取 `transcript_path`。不依赖 `${CLAUDE_PROJECT_DIR}` 推断 worktree，因为实际事件 `cwd` 才对应当前执行目录。Claude 专属 prompt/agent Hooks 不作为共享核心依赖。

## Git 提交核对（Git Commit Verification）

[Git 模板](../assets/git-pre-commit-template.sh) 是可选提交核对入口。用户授权安装后，将核对命令接入已存在的 `pre-commit`，或放在已确认的 Hooks 管理方案中。保留其他检查，不修改 `core.hooksPath` 或覆盖现有文件来强行安装。

作为独立 Git Hook 安装时，脚本须具有执行权限；源模板本身没有启用任何 Git Hook。

Git 在实际提交时提供 index，脚本尊重 `GIT_INDEX_FILE`。`git commit -a`、路径提交等可能生成不同候选，因此旧报告若不匹配必须重新检查。普通 `Stop` 提醒不能覆盖人类直接运行 Git，提交核对也不能替代用户授权。

Git Hook 非零退出阻止当次提交，`--no-verify` 可绕过。此机制是日常工作检查，不能宣称不可绕过或不可伪造的安全边界。

## 安装与验收（Installation and Acceptance）

本轮仅维护源资产，不安装、不改宿主配置、不创建真实运行请求。安装时先确认宿主版本、发现位置、现有 Hook 合并方式、Python/Git 路径、运行目录和信任状态。

真实验收按 [行为用例](behavior-cases.md) 记录宿主版本、源包指纹、输入、预期和实际结果。JSON 可解析、脚本测试通过不能证明宿主发现、事件触发或 Agent 语义检查已通过。
