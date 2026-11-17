#!/usr/bin/env python3
"""通过指定 MCP 获取公众号文章；仅使用 Python 3.9+ 标准库。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import ssl
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid


ENDPOINT = "https://wechat-article-reader-mcp.onrender.com/mcp"
PROTOCOL = "2025-06-18"
MAX_RESPONSE_BYTES = 8_000_000
TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


class FetchError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_url(value):
    """只接受完整文章 URL；不从自由文本提取，也不删除查询参数。"""
    value = value.strip()
    if not value or len(value) > 5000 or any(c.isspace() or ord(c) < 32 for c in value):
        raise FetchError("INVALID_URL", "请输入完整、无空白的公众号文章 HTTPS 链接")
    try:
        p = urlsplit(value)
        if (p.scheme != "https" or p.hostname != "mp.weixin.qq.com"
                or p.username is not None or p.password is not None
                or p.port not in (None, 443) or p.fragment):
            raise ValueError()
        short = re.fullmatch(r"/s/[A-Za-z0-9_-]{6,256}", p.path)
        query = parse_qs(p.query)
        long = p.path == "/s" and all(len(query.get(k, [])) == 1 for k in ("__biz", "mid", "idx", "sn"))
        if not (short or long):
            raise ValueError()
    except ValueError as exc:
        raise FetchError("INVALID_URL", "仅支持 mp.weixin.qq.com 的公开文章链接，不支持视频号") from exc
    return urlunsplit(("https", "mp.weixin.qq.com", p.path, p.query, ""))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def retry_delay(value, attempt):
    if value is None:
        return 2 ** (attempt + 1)
    try:
        seconds = int(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return 2 ** (attempt + 1)
    if seconds > 60:
        raise FetchError("RETRY_LATER", "服务要求等待超过 60 秒；本轮停止重试，请稍后重新执行")
    return max(0, seconds)


class MCPClient:
    def __init__(self, timeout=45, retries=2):
        self.timeout = timeout
        self.retries = retries
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        self.opener = build_opener(NoRedirect())
        self.next_id = 0
        self.server = None
        self.events = []

    def rpc(self, method, params=None, notification=False):
        payload = {"jsonrpc": "2.0", "method": method}
        if not notification:
            self.next_id += 1
            payload["id"] = self.next_id
        if params is not None:
            payload["params"] = params
        for attempt in range(self.retries + 1):
            request = Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"), headers=self.headers)
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    raw = response.read(MAX_RESPONSE_BYTES + 1)
                    self.events.append({"method": method, "attempt": attempt + 1, "http_status": response.status})
                    if len(raw) > MAX_RESPONSE_BYTES:
                        raise FetchError("RESPONSE_TOO_LARGE", "MCP 响应超过本地 8 MB 上限")
                    session = response.headers.get("Mcp-Session-Id")
                    if session:
                        self.headers["Mcp-Session-Id"] = session
                    if notification:
                        if response.status != 202 or raw.strip():
                            raise FetchError("PROTOCOL_ERROR", "初始化通知未返回预期的空 202 响应")
                        return None
                    if response.headers.get_content_type() != "application/json":
                        raise FetchError("UNSUPPORTED_RESPONSE", "仅支持该服务已验证的 JSON 响应，不处理 SSE")
                    try:
                        body = json.loads(raw)
                    except (ValueError, UnicodeError) as exc:
                        raise FetchError("PROTOCOL_ERROR", "MCP 返回无效 JSON") from exc
                    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or body.get("id") != payload["id"]:
                        raise FetchError("PROTOCOL_ERROR", "JSON-RPC 版本或请求 ID 不匹配")
                    if "error" in body:
                        raise FetchError("RPC_ERROR", "MCP 返回 JSON-RPC 错误：" + json.dumps(body["error"], ensure_ascii=False)[:500])
                    if not isinstance(body.get("result"), dict):
                        raise FetchError("PROTOCOL_ERROR", "MCP 缺少 result 对象")
                    return body["result"]
            except HTTPError as exc:
                self.events.append({"method": method, "attempt": attempt + 1, "http_status": exc.code})
                code = exc.code
                wait_header = exc.headers.get("Retry-After")
                exc.close()
                if code not in TRANSIENT_HTTP or attempt == self.retries:
                    raise FetchError("HTTP_ERROR", "MCP HTTP " + str(code)) from exc
                time.sleep(retry_delay(wait_header, attempt))
            except (URLError, TimeoutError, socket.timeout) as exc:
                reason = getattr(exc, "reason", exc)
                if isinstance(reason, ssl.SSLError):
                    raise FetchError("TLS_ERROR", "TLS 验证或连接失败；未关闭证书验证") from exc
                self.events.append({"method": method, "attempt": attempt + 1, "error": "NETWORK_ERROR"})
                if attempt == self.retries:
                    raise FetchError("NETWORK_ERROR", "MCP 网络请求失败，已达到重试上限") from exc
                time.sleep(retry_delay(None, attempt))

    def connect(self):
        result = self.rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                         "clientInfo": {"name": "wechat-article-fetcher", "version": "1.0.0"}})
        if result.get("protocolVersion") != PROTOCOL:
            raise FetchError("PROTOCOL_ERROR", "服务协商版本与已验证协议不一致")
        self.server = result.get("serverInfo")
        if not isinstance(self.server, dict) or not all(isinstance(self.server.get(k), str) and self.server[k] for k in ("name", "version")):
            raise FetchError("PROTOCOL_ERROR", "服务身份字段缺失")
        self.headers["MCP-Protocol-Version"] = PROTOCOL
        self.rpc("notifications/initialized", notification=True)
        tools = self.rpc("tools/list").get("tools")
        if not isinstance(tools, list) or not all(isinstance(t, dict) for t in tools):
            raise FetchError("PROTOCOL_ERROR", "工具清单格式无效")
        matches = [t for t in tools if t.get("name") == "read_wechat_articles"]
        if len(matches) != 1:
            raise FetchError("MISSING_TOOL", "服务未提供唯一的 read_wechat_articles")
        schema = matches[0].get("inputSchema", {})
        expected = {"type": "object", "properties": {"urls": {"type": "array", "items": {"type": "string"},
                    "minItems": 1, "maxItems": 5}}, "required": ["urls"], "additionalProperties": False}
        if schema != expected:
            raise FetchError("SCHEMA_CHANGED", "工具输入契约发生变化，须核验后再调用")

    def read_articles(self, urls):
        result = self.rpc("tools/call", {"name": "read_wechat_articles", "arguments": {"urls": urls}})
        blocks = result.get("content")
        if (type(result.get("isError")) is not bool or not isinstance(blocks, list) or len(blocks) != 1
                or not isinstance(blocks[0], dict) or blocks[0].get("type") != "text"):
            raise FetchError("PROTOCOL_ERROR", "工具结果不符合已验证的文本 JSON 契约")
        try:
            parsed = json.loads(blocks[0]["text"])
            articles = parsed["articles"]
        except (KeyError, TypeError, ValueError) as exc:
            raise FetchError("PROTOCOL_ERROR", "工具结果缺少有效 articles 数组") from exc
        if not isinstance(articles, list) or len(articles) != len(urls) or not all(isinstance(a, dict) for a in articles):
            raise FetchError("PROTOCOL_ERROR", "返回篇数与请求不一致")
        by_url = {}
        for article in articles:
            source = article.get("source_url")
            if not isinstance(source, str) or source not in urls or source in by_url:
                raise FetchError("PROTOCOL_ERROR", "返回来源链接缺失、重复或与请求不匹配")
            if article.get("status") not in ("ok", "error"):
                raise FetchError("PROTOCOL_ERROR", "文章状态字段无效")
            by_url[source] = article
        if result["isError"] != all(a["status"] == "error" for a in articles):
            raise FetchError("PROTOCOL_ERROR", "工具错误标志与逐篇结果不一致")
        return [by_url[url] for url in urls]


def safe_stem(text):
    text = unicodedata.normalize("NFC", text)
    text = "".join("_" if unicodedata.category(c).startswith("C") or c in '<>:"/\\|?*' else c for c in text)
    text = text.strip(" .") or "article"
    text = text.encode("utf-8")[:120].decode("utf-8", errors="ignore").rstrip(" .") or "article"
    if text.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))}:
        text = "_" + text
    return text


def atomic_write(path, data):
    """先校验临时文件，再以硬链接排他发布；不覆盖已有目标。"""
    fd, temp = tempfile.mkstemp(prefix=".wechat-write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if Path(temp).read_bytes() != data:
            raise OSError("临时文件回读与原始内容不一致")
        os.link(temp, path)
        if path.read_bytes() != data:
            raise OSError("最终文件回读与原始内容不一致")
    finally:
        Path(temp).unlink(missing_ok=True)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def save_article(root, article, requested_name=None):
    md = article.get("markdown")
    if not isinstance(md, str) or not md.strip():
        raise FetchError("EMPTY_CONTENT", "服务返回成功，但 Markdown 正文为空")
    title = article.get("title")
    if title is not None and not isinstance(title, str):
        raise FetchError("PROTOCOL_ERROR", "文章标题类型无效")
    truncation = article.get("truncated")
    if truncation is not None and type(truncation) is not bool:
        raise FetchError("PROTOCOL_ERROR", "truncated 必须是布尔值")
    digest = hashlib.sha256(article["source_url"].encode("utf-8")).hexdigest()[:12]
    stem = safe_stem(requested_name or title or "article") + "--" + digest
    for index in range(1, 10001):
        folder = root / (stem if index == 1 else stem + "--" + str(index))
        try:
            folder.mkdir(mode=0o700)
            break
        except FileExistsError:
            continue
    else:
        raise FetchError("OUTPUT_CONFLICT", "同名目录过多，未覆盖任何现有目录")
    try:
        contents = {"article.md": md.encode("utf-8"), "result.json": json_bytes(article)}
        for name, data in contents.items():
            atomic_write(folder / name, data)
        saved = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        if saved != article or (folder / "article.md").read_bytes().decode("utf-8") != saved["markdown"]:
            raise OSError("正文与 result.json 回读不一致")
    except (OSError, ValueError):
        # 仅清理本次排他创建的目录中的已知产物，不触碰既有目录。
        for name in ("article.md", "result.json"):
            (folder / name).unlink(missing_ok=True)
        folder.rmdir()
        raise
    return {
        "status": "success" if truncation is False else "partial",
        "completeness": "not_truncated_by_service" if truncation is False else "truncated" if truncation is True else "unknown",
        "title": title, "account": article.get("account"), "published_at": article.get("published_at"),
        "markdown_characters": len(md), "text_length": article.get("text_length"),
        "image_count": len(article["images"]) if isinstance(article.get("images"), list) else None,
        "files": {name: {"path": (folder / name).relative_to(root).as_posix(),
                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in contents.items()},
    }


def run(urls, output_dir, name=None, client=None):
    if not urls:
        raise FetchError("INVALID_INPUT", "至少需要一个链接")
    if name is not None and (len(urls) != 1 or not name.strip()):
        raise FetchError("INVALID_INPUT", "--name 仅适用于单个输入链接，且不得为空")
    if not str(output_dir).strip():
        raise FetchError("INVALID_OUTPUT", "必须指定非空输出目录")
    root = Path(output_dir).expanduser().resolve()
    package_root = Path(__file__).resolve().parents[1]
    if root == package_root or package_root in root.parents:
        raise FetchError("INVALID_OUTPUT", "不得将运行数据写入 Skill 源包")
    root.mkdir(parents=True, exist_ok=True)
    # 同时检查文件系统支持原子发布；不等下载后才发现只读或不支持硬链接。
    probe = root / (".wechat-probe-" + uuid.uuid4().hex)
    try:
        atomic_write(probe, b"probe")
    finally:
        probe.unlink(missing_ok=True)
    report = {"schema_version": 1, "skill_version": "1.0.0", "started_at": utc_now(),
              "endpoint": ENDPOINT, "articles": [], "duplicates": []}
    seen = set()
    queue = []
    for raw in urls:
        entry = {"input_url": raw, "status": "failed"}
        try:
            normalized = normalize_url(raw)
            if normalized in seen:
                report["duplicates"].append({"input_url": raw, "source_url": normalized})
                continue
            seen.add(normalized)
            entry["source_url"] = normalized
            queue.append(entry)
        except FetchError as exc:
            entry.update(error_code=exc.code, message=str(exc))
        report["articles"].append(entry)
    client = client or MCPClient()
    connected = False
    if queue:
        try:
            client.connect()
            connected = True
        except (FetchError, OSError) as exc:
            for entry in queue:
                entry.update(error_code=getattr(exc, "code", "NETWORK_ERROR"), message=str(exc))
    if connected:
        for offset in range(0, len(queue), 5):
            batch = queue[offset:offset + 5]
            try:
                articles = client.read_articles([e["source_url"] for e in batch])
            except (FetchError, OSError) as exc:
                for entry in batch:
                    entry.update(error_code=getattr(exc, "code", "NETWORK_ERROR"), message=str(exc))
                continue
            for entry, article in zip(batch, articles):
                entry["retrieved_at"] = utc_now()
                if article["status"] == "error":
                    entry.update(error_code=article.get("error_code", "REMOTE_ERROR"),
                                 message=article.get("message", "服务返回文章读取失败"), remote_result=article)
                    continue
                try:
                    entry.update(save_article(root, article, name))
                except (FetchError, OSError, UnicodeError) as exc:
                    entry.update(status="failed", error_code=getattr(exc, "code", "WRITE_ERROR"), message=str(exc))
    report.update(finished_at=utc_now(), server=client.server, events=client.events)
    report["counts"] = {status: sum(e["status"] == status for e in report["articles"]) for status in ("success", "partial", "failed")}
    report_path = root / ("fetch-report-" + uuid.uuid4().hex + ".json")
    atomic_write(report_path, json_bytes(report))
    return report, report_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="读取公开公众号文章，原样保存 Markdown、返回对象和执行清单")
    parser.add_argument("--url", action="append", required=True, help="公众号文章链接；批量时重复此参数")
    parser.add_argument("--output-dir", required=True, help="输出目录；相对路径以当前工作目录解析")
    parser.add_argument("--name", help="单篇输出名称；不改变文章标题或正文")
    args = parser.parse_args(argv)
    try:
        report, path = run(args.url, args.output_dir, args.name)
    except (FetchError, OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error_code": getattr(exc, "code", "LOCAL_ERROR"), "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"counts": report["counts"], "report": str(path), "output_dir": str(path.parent),
                      "articles": [{k: v for k, v in e.items() if k not in ("remote_result",)} for e in report["articles"]]}, ensure_ascii=False, indent=2))
    return 0 if report["counts"]["failed"] == report["counts"]["partial"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
