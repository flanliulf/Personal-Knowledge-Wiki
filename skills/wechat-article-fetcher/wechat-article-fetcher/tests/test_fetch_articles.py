"""确定性边界测试；不请求真实服务，不保存真实文章。"""

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError, URLError
from email.message import Message

spec = importlib.util.spec_from_file_location("fetch_articles", Path(__file__).resolve().parents[1] / "scripts" / "fetch_articles.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


def url(i=0):
    return "https://mp.weixin.qq.com/s/fixture" + str(i)


def article(i=0, **updates):
    value = {"status": "ok", "source_url": url(i), "title": "测试文章", "account": "测试账号",
             "published_at": "", "markdown": "# 正文\n\n原样保留：**内容**\r\n", "truncated": False, "images": []}
    value.update(updates)
    return value


class FakeClient:
    server = {"name": "fixture", "version": "test"}
    events = []

    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.batches = []
        self.connections = 0

    def connect(self):
        self.connections += 1

    def read_articles(self, urls):
        self.batches.append(urls)
        return [self.overrides.get(u, article(source_url=u)) for u in urls]


class FakeResponse:
    def __init__(self, body, status=200, mime="application/json"):
        self.body = json.dumps(body).encode() if body is not None else b""
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = mime

    def read(self, count):
        return self.body[:count]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FetchTests(unittest.TestCase):
    def test_urls_reject_video_credentials_fragment_and_bad_long_form(self):
        for bad in ("https://weixin.qq.com/sph/example", "http://mp.weixin.qq.com/s/abcdef",
                    "https://user@mp.weixin.qq.com/s/abcdef", url() + "#part", "https://mp.weixin.qq.com/s?mid=1",
                    "https://mp.weixin.qq.com.attacker.test/s/abcdef", url() + "\nextra"):
            with self.subTest(bad=bad), self.assertRaises(fetch.FetchError):
                fetch.normalize_url(bad)
        long = "https://mp.weixin.qq.com/s?__biz=a&mid=1&idx=1&sn=z&extra=x"
        self.assertEqual(fetch.normalize_url(long), long)

    def test_batching_dedup_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient()
            report, path = fetch.run([url(i) for i in range(6)] + [" " + url() + " ", "bad"], temp, client=client)
            self.assertEqual([len(b) for b in client.batches], [5, 1])
            self.assertEqual(report["counts"], {"success": 6, "partial": 0, "failed": 1})
            self.assertEqual(len(report["duplicates"]), 1)
            self.assertEqual(json.loads(path.read_text()), report)

    def test_mixed_results_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient({url(1): article(1, status="error", error_code="ACCESS_RESTRICTED", message="验证")})
            report, _ = fetch.run([url(), url(1)], temp, client=client)
            self.assertEqual(report["counts"], {"success": 1, "partial": 0, "failed": 1})
            record = report["articles"][0]
            path = Path(temp) / record["files"]["article.md"]["path"]
            self.assertEqual(path.read_bytes(), article()["markdown"].encode())
            self.assertEqual(record["files"]["article.md"]["sha256"], fetch.hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertNotIn("files", report["articles"][1])

    def test_truncated_unknown_and_invalid_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            data = article()
            del data["truncated"]
            self.assertEqual(fetch.save_article(Path(temp), data)["completeness"], "unknown")
            self.assertEqual(fetch.save_article(Path(temp), article(truncated=True))["status"], "partial")
            with self.assertRaises(fetch.FetchError):
                fetch.save_article(Path(temp), article(truncated="false"))

    def test_empty_content_never_creates_article(self):
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient({url(): article(markdown=" ")})
            report, _ = fetch.run([url()], temp, client=client)
            self.assertEqual(report["articles"][0]["error_code"], "EMPTY_CONTENT")
            self.assertEqual(list(Path(temp).rglob("article.md")), [])

    def test_name_sanitization_collisions_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = article(title="../../路径/" + "长" * 200)
            saved = fetch.save_article(root, data)
            relative = saved["files"]["article.md"]["path"]
            folder = (root / relative).parent
            self.assertEqual(folder.parent, root)
            self.assertLess(len(folder.name.encode()), 180)
            again = fetch.save_article(root, data)
            self.assertNotEqual(relative, again["files"]["article.md"]["path"])
            other = root / "existing"
            other.mkdir()
            stem = fetch.safe_stem("new") + "--" + fetch.hashlib.sha256(url().encode()).hexdigest()[:12]
            (root / stem).symlink_to(other, target_is_directory=True)
            saved = fetch.save_article(root, article(title="new"))
            self.assertIn("--2/", saved["files"]["article.md"]["path"])
            self.assertEqual(list(other.iterdir()), [])
            self.assertEqual(fetch.safe_stem("CON"), "_CON")

    def test_atomic_write_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "existing"
            target.write_bytes(b"old")
            with self.assertRaises(FileExistsError):
                fetch.atomic_write(target, b"new")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual(list(Path(temp).glob(".wechat-*")), [])

    def test_write_failure_removes_own_partial_files(self):
        with tempfile.TemporaryDirectory() as temp:
            original = fetch.atomic_write
            def fail_result(path, data):
                if path.name == "result.json":
                    raise PermissionError("fixture denied")
                return original(path, data)
            with patch.object(fetch, "atomic_write", side_effect=fail_result):
                report, _ = fetch.run([url()], temp, client=FakeClient())
            self.assertEqual(report["articles"][0]["error_code"], "WRITE_ERROR")
            self.assertEqual(list(Path(temp).rglob("article.md")), [])

    def test_output_file_and_source_package_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "file"
            file.touch()
            with self.assertRaises(OSError):
                fetch.run([url()], file, client=FakeClient())
        with self.assertRaises(fetch.FetchError):
            fetch.run([url()], Path(fetch.__file__).parent, client=FakeClient())

    def test_missing_input_name_and_output_rejected(self):
        for urls, output, name in (([], ".", None), ([url()], "", None), ([url(), url(1)], ".", "name")):
            with self.subTest(urls=urls), self.assertRaises(fetch.FetchError):
                fetch.run(urls, output, name, client=FakeClient())

    def test_all_invalid_does_not_connect(self):
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient()
            report, _ = fetch.run(["bad"], temp, client=client)
            self.assertEqual(client.connections, 0)
            self.assertEqual(report["counts"]["failed"], 1)

    def test_connection_failure_keeps_report(self):
        with tempfile.TemporaryDirectory() as temp:
            client = FakeClient()
            client.connect = Mock(side_effect=fetch.FetchError("MISSING_TOOL", "missing"))
            report, path = fetch.run([url(), url(1)], temp, client=client)
            self.assertTrue(path.exists())
            self.assertEqual(report["counts"]["failed"], 2)

    def test_report_failure_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            original = fetch.atomic_write
            def fail_report(path, data):
                if path.name.startswith("fetch-report-"):
                    raise OSError("full")
                return original(path, data)
            with patch.object(fetch, "atomic_write", side_effect=fail_report), self.assertRaises(OSError):
                fetch.run([url()], temp, client=FakeClient())

    def test_response_source_mismatch_and_error_flag(self):
        client = fetch.MCPClient()
        for items, is_error in (([article(1)], False), ([article()], True), ([article(), article()], False)):
            client.rpc = Mock(return_value={"content": [{"type": "text", "text": json.dumps({"articles": items})}], "isError": is_error})
            with self.subTest(items=items), self.assertRaises(fetch.FetchError):
                client.read_articles([url()])

    def test_response_reordered_is_matched_by_source(self):
        client = fetch.MCPClient()
        client.rpc = Mock(return_value={"content": [{"type": "text", "text": json.dumps({"articles": [article(1), article()]})}], "isError": False})
        self.assertEqual([a["source_url"] for a in client.read_articles([url(), url(1)])], [url(), url(1)])

    def test_malformed_json_and_sse_rejected(self):
        client = fetch.MCPClient()
        client.opener.open = Mock(return_value=FakeResponse({}, mime="text/event-stream"))
        with self.assertRaises(fetch.FetchError) as caught:
            client.rpc("initialize")
        self.assertEqual(caught.exception.code, "UNSUPPORTED_RESPONSE")
        client.rpc = Mock(return_value={"content": [{"type": "text", "text": "not json"}], "isError": False})
        with self.assertRaises(fetch.FetchError):
            client.read_articles([url()])

    def test_network_retry_ceiling(self):
        client = fetch.MCPClient()
        client.opener.open = Mock(side_effect=URLError("fixture"))
        with patch.object(fetch.time, "sleep") as sleep, self.assertRaises(fetch.FetchError):
            client.rpc("initialize")
        self.assertEqual(client.opener.open.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    def test_429_retry_after_and_long_wait_stop(self):
        client = fetch.MCPClient()
        error = HTTPError(fetch.ENDPOINT, 429, "limit", {"Retry-After": "7"}, io.BytesIO())
        client.opener.open = Mock(side_effect=[error, FakeResponse({"jsonrpc": "2.0", "id": 1, "result": {}})])
        with patch.object(fetch.time, "sleep") as sleep:
            self.assertEqual(client.rpc("ping"), {})
        sleep.assert_called_once_with(7)
        with self.assertRaises(fetch.FetchError):
            fetch.retry_delay("61", 0)

    def test_http_403_not_retried(self):
        client = fetch.MCPClient()
        client.opener.open = Mock(side_effect=HTTPError(fetch.ENDPOINT, 403, "forbidden", {}, io.BytesIO()))
        with patch.object(fetch.time, "sleep") as sleep, self.assertRaises(fetch.FetchError):
            client.rpc("ping")
        self.assertEqual(client.opener.open.call_count, 1)
        sleep.assert_not_called()

    def test_schema_drift_stops_before_article_call(self):
        client = fetch.MCPClient()
        client.rpc = Mock(side_effect=[{"protocolVersion": fetch.PROTOCOL, "serverInfo": {"name": "server", "version": "1"}}, None,
                                      {"tools": [{"name": "read_wechat_articles", "inputSchema": {}}]}])
        with self.assertRaises(fetch.FetchError) as caught:
            client.connect()
        self.assertEqual(caught.exception.code, "SCHEMA_CHANGED")

    def test_cli_exit_code_for_success_partial_and_local_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            for counts, expected in (({"success": 1, "partial": 0, "failed": 0}, 0),
                                     ({"success": 0, "partial": 1, "failed": 0}, 1)):
                with patch.object(fetch, "run", return_value=({"counts": counts, "articles": []}, Path(temp) / "report.json")), patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(fetch.main(["--url", url(), "--output-dir", temp]), expected)
            with patch.object(fetch, "run", side_effect=OSError("denied")), patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(fetch.main(["--url", url(), "--output-dir", temp]), 2)


if __name__ == "__main__":
    unittest.main()
