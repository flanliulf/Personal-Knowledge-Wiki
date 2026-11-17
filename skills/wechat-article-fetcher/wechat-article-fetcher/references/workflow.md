# 执行规则（Workflow）

## 输入与授权（Input and Authorization）

`urls` 和 `output_dir` 必需；`name` 仅用于一个输入链接。链接须是完整 URL，不从任意文本中猜测目标。目录必须由用户或已确认上下文提供。相对路径以调用时 CWD 解析；`~` 展开为当前用户目录。空目录字符串、指向文件的路径或不可写目录必须报错。

输出目录不得位于当前 Skill 源包内。实际运行时检查目标项目 AGENTS.md；特别是公开仓库中，不自动收录第三方文章原文。源包的创建验证将真实文章保存在外层、本机忽略的 `output/`，不作为包内测试夹具分发。

对规范化后相同的 URL 去重，保留原始输入和重复项记录。仅统一 HTTPS 主机和默认端口，不移除查询参数、不合并不同参数链接。短链接与长链接即使实际指向同一篇文章，也不在缺少证据时强行去重。

## 调用方式（Invocation）

将 `<skill-root>` 替换为本次实际解析的 Skill 源包绝对路径，将输出目录和 URL 替换为用户值。所有示例占位符都不是运行默认值。

```sh
python3 "<skill-root>/scripts/fetch_articles.py" \
  --url "https://mp.weixin.qq.com/s/<article-id>" \
  --output-dir "<用户指定目录>"
```

多篇重复 `--url`；单篇可追加 `--name "<输出名称>"`。参数通过安全的参数数组传递；宿主只支持 shell 时，对每个用户参数做 shell 引号转义。不得将 `$()`、反引号或换行误当命令执行。

脚本使用 Python 3.9+ 标准库，不安装 Python 包。只访问固定 Article Lens MCP 端点，不携带本机认证信息。由服务访问微信，第三方服务的数据处理边界见 [来源记录](sources.md)。尊重现有网络权限，不变更代理和 TLS 验证。

## 请求与失败（Requests and Failures）

1. 验证链接、创建输出目录并探测排他写入能力。
2. 初始化、发送初始化完成通知、发现工具并校验输入 schema。
3. 每批最多 5 篇，顺序调用；单篇失败不丢弃同批成功项。
4. 按 `source_url` 关联输入与输出；篇数、来源或状态矛盾则整批协议失败，不能按错误顺序保存。
5. HTTP/网络层每次请求最多 3 次尝试（首次加 2 次重试），单次超时 45 秒。只对网络超时及 HTTP 408/429/500/502/503/504 重试。默认间隔 2、4 秒；有效 `Retry-After` 优先，超过 60 秒则本轮停止重试。证书错误不重试。
6. 返回到文章层的 `ACCESS_RESTRICTED`、`NETWORK_ERROR`、`CONTENT_NOT_FOUND` 等原样记录，不自动重试该篇或切换抓取路线；用户后续可明确要求重试。
7. 输入 schema、协议版本或响应类型变化时停止相关调用。客户端仅支持已验证的 JSON 返回，不宣称支持通用 MCP SSE。

不以 `/health` 的成功或失败代替 MCP 实际验证。客户端不跟随 MCP 端点的重定向。

## 文件与状态（Files and Status）

```text
<output_dir>/
├── <清理后的标题或名称>--<来源链接 SHA-256 前 12 位>/
│   ├── article.md
│   └── result.json
└── fetch-report-<随机唯一标识>.json
```

标题按 UTF-8 字节限制长度，清理路径分隔符、控制字符及跨平台非法名称。无标题时使用 `article` 作为文件名，元数据仍保留缺失状态。相同目录已存在时增加 `--2` 等后缀，既有文件和软链接都不覆盖。

`article.md` 严格保存返回的 Markdown，不附加标题、来源或 frontmatter；这些信息保存在完整返回对象 `result.json`。保留图片链接，不下载图片。`result.json` 与正文必须回读一致。

临时文件在目标目录内创建，写入后 flush/fsync、回读比较，再用排他硬链接发布为最终文件。该方式不覆盖既有文件，但要求文件系统支持硬链接；不支持时明确失败。文章子目录用排他 mkdir 预留。失败时只清理本次生成的已知文件；进程被强制终止可能留下临时或不完整目录，不自动删除未知残留。

| 状态 | 判定 |
| --- | --- |
| `success` | 服务返回 `ok`、Markdown 非空、`truncated` 严格为 false、两文件保存及回读通过 |
| `partial` | 正文已保存，`truncated=true` 或字段缺失/null；区分 `truncated` 和 `unknown` |
| `failed` | 链接不支持、服务错误、协议异常、正文为空或本地写入失败 |

`truncated` 非布尔且非 null 时判协议错误。`success` 不代表与网页逐字比对、图片离线可用或元数据完整。发布时间缺失保留空值，不以获取时间替代。

执行清单 schema_version 为 1，含 `skill_version`、`started_at`、`finished_at`、`endpoint`、`server`、`events`、`articles`、`duplicates` 和 `counts`。逐篇记录输入、来源、状态、错误、相对文件路径、字节数和 SHA-256；失败不生成空正文。会话标识仅驻内存，不写入清单。报告自身无法保存时，整体交付未完成，即使部分正文已写入。

退出码：`0` 全部成功；`1` 清单已写入但含 partial/failed；`2` 参数、输出目录或清单落盘失败。终端输出 JSON 摘要，诊断到 stderr。将文件链接转成绝对路径展示给用户。
