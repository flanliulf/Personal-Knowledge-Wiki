# MCP 契约（MCP Contract）

## 服务与范围（Service and Scope）

- 固定端点：`https://wechat-article-reader-mcp.onrender.com/mcp`。
- 本轮已观察服务名 `wechat-article-reader`、版本 `0.5.0`；版本是运行记录，不保证未来不变。
- 客户端发送协议 `2025-06-18`，校验协商结果。传输为 HTTPS Streamable HTTP；本客户端仅实现该服务已验证的 JSON 请求/响应分支。
- 当前公开端点不要求 API Key。不得自行添加 X Token、微信 Cookie、Arc 数据或其他凭据。

## 调用顺序（Call Sequence）

1. `initialize`：发送 `protocolVersion`、空 `capabilities` 和客户端名称/版本；读取实际 serverInfo。
2. `notifications/initialized`：无请求 ID，预期空 202 响应。
3. `tools/list`：确认唯一 `read_wechat_articles`，严格检查已核验 schema。变化时先核验，不猜测兼容性。
4. `tools/call`：调用 `read_wechat_articles`，参数仅为 `urls`。

POST 头为 `Content-Type: application/json`、`Accept: application/json, text/event-stream`；协商后增加 `MCP-Protocol-Version`。服务若返回 `Mcp-Session-Id`，仅在本次内存中保存并回传同一固定服务。

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_wechat_articles",
    "arguments": {"urls": ["https://mp.weixin.qq.com/s/<article-id>"]}
  }
}
```

`<article-id>` 为示意占位符，运行时替换为真实链接。schema 为 object，required 仅 `urls`，additionalProperties 为 false；urls 为 string 数组，minItems=1、maxItems=5。

## 返回与判断（Response and Validation）

先检查 JSON-RPC `error`，再读取 `result`。当前服务通过唯一 `content[0]` 文本块返回 JSON 字符串，解析得到 `articles`。`isError` 严格为 boolean；只有全部文章返回 error 才为 true，混合成功时为 false。必须检查每篇，不能只看 HTTP 200 或 `isError=false`。

成功对象提供 `status`、`source_url`、`title`、`account`、`published_at`、`description`、`display_type`、`markdown`、`truncated`、`images`、`text_length`、`source_method`。某些元数据可能为空或不准确；本次先前实测 `description` 含样式片段，因此仅原样归档，不作为正文或摘要使用。

上游当前限制：Markdown 最多 75,000 字符，images 最多 100 个链接，远程 HTML 最多 8 MB。`truncated` 只反映上游 Markdown 截断，不保证所有图片已列出；不得用它声称全媒体完整。客户端另有每次 MCP 响应 8 MB 上限。

错误对象保留 `error_code` 和 `message`，可能包含 `redirect_path` 等附加字段。访问验证页返回 `ACCESS_RESTRICTED`；这不能证明链接永久失效。服务的 `import_wechat_article` 不在本 Skill 首版范围内，不自动用于获取受限页面。

## 契约更新（Contract Updates）

修订前按 [来源记录](sources.md) 核对上游实现、实际工具发现结果和本地错误测试。不得只修改 schema 比较逻辑放行未知返回。更新版本与 CHANGELOG 后重新执行项目 lint，区分服务源码、部署版本和本地客户端验证。
