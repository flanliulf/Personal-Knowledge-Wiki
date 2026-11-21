# 登录态与依赖（Session and Dependencies）

在登录 X 的同一台 Mac 上运行。需要 Python 3.12+、Node.js 22+、KnowledgeWiki 收录的 last30days 4.1.0，以及用户选择的 Arc 配置。配置了 HTTP 代理时，Node 还需支持 `--use-env-proxy`。首次运行可能出现 macOS 钥匙串授权窗口，由用户在系统窗口处理。沿用上游等待时限。若该窗口超时，在确认登录及本次授权后手动重试。

脚本采用现有 `BROWSER_CONSENT=true` 和 `FROM_BROWSER=arc` 授权，也可在用户明确同意本次操作后传 `--allow-arc`。已有关闭设置时停止。多个配置须使用 `--profile 'Profile 1'` 等目录名选定一个。不可向用户索要 Cookie、密码或 Bearer Token。

使用上游原生 Bird 后端。脚本把检索来源设为 X，只提供本次运行所需的环境变量，忽略其他供应商的密钥。运行不要求 X API 充值。遇到网络错误，先核对 Arc 中的 X 与本机代理；遇到登录错误，先核对选定配置；遇到限流，报告当次状态并结束。访问被拒绝时尊重系统或用户决定。远程无头主机、CI 和定时任务不适用。

默认读取 last30days 配置目录的 `.env` 中的授权、浏览器和输出目录选项，支持 `LAST30DAYS_CONFIG_DIR`。用户指定的 `--output-dir` 优先，其次为 `LAST30DAYS_MEMORY_DIR`，均未指定时写入用户文稿目录下的 `Last30Days`。空目录设置或 `--no-save` 将报告输出到标准输出。保存模式每次新建独立子目录，仅在全部文件写完后公开该目录。
