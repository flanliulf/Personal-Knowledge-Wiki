# 示例说明（Examples）

[example-input.json](example-input.json) 是虚构提案输入，仅用于格式演示和隔离测试。`example-thread` 不是实际会话 ID，证据字符串不是实际工具回读。

例中的 `createdAt` 为 `2025-12-31T16:30:00Z`，转换到 `Asia/Shanghai` 后是 `2026-01-01`，标题前缀应为 `260101`。`contentFingerprint` 未取得，明确放在 `unavailableProtection`，不能报告正文已核验。

正式使用时须由 Agent 收集真实输入、取得执行锁并输出完整待确认表。不能将本示例当作用户确认或实际改名输入。
