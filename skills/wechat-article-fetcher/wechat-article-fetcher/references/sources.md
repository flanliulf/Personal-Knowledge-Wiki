# 来源与验证边界（Sources and Validation）

## 来源登记（Source Register）

核验日期：2026-11-17。本 Skill 为本项目新写的流程和客户端，不复制上游服务源代码或第三方文章全文作为分发内容。

| 来源 | 实际阅读范围 | 采用或排除 |
| --- | --- | --- |
| [wechat-article-reader](https://github.com/7l7/wechat-article-reader) | README、app.py、article_extractor.py、url_normalizer.py、PRIVACY.md、requirements.txt；本轮 main 标识为 `4ce20df5508fb8b5743dade2c133391f2ed49a4c` | 采用公开 MCP 接口和返回契约；不部署或复制服务端，不使用导入工具 |
| [隐私说明](https://github.com/7l7/wechat-article-reader/blob/4ce20df5508fb8b5743dade2c133391f2ed49a4c/PRIVACY.md) | 全文 | URL 及远程内容经服务/Render 处理；不要求 Cookie。有关日志保留等仅为上游声明，未独立审计 |
| [OpenAI Build skills](https://developers.openai.com/plugins/build/skills) | 支持资源、MCP 依赖声明和测试部分 | 核验 agents/openai.yaml 的 dependencies.tools type/value/description/transport/url；不据此声称本机安装或宿主发现已通过 |
| KnowledgeWiki 内置 skills-creator 3.1.1、skills-lint 4.2.0 | 入口、创建/检查流程、规范、模板、测试指南、共享 registry | 采用 base 和 Codex 规则；contract_version=1.0.0；不启用可选 tooling 双语要求 |

以上 GitHub 各文件是同一上游仓库的不同证据，不能当成独立验证来源。源码标识与部署服务版本分别记录；二者是否来自同一部署提交未核验。来源链接可访问也不等于服务运行永久可用。

## 已有事实（Observed Facts）

本 Skill 创建前，同一会话已对用户提供的公开文章完成 initialize → initialized → tools/list → tools/call。服务返回 0.5.0，文章 status=ok、truncated=false，正文文本长度 11,415，Markdown 长度 16,893，图片链接数 21，发布时间为空。该记录只证明当时的一次直接调用成功，不是新 Skill 脚本或宿主触发测试。

先前 `/health` 曾超时，但 MCP 实际调用成功。因此健康检查不设为硬前置。此为设计推导，不是上游保证。客户端采用 Python 标准库、原子排他写入、逐篇关联和独立清单，是本项目的实现选择。

本次创建验证：21 项确定性脚本测试通过；使用新脚本重新读取同一用户授权样例，初始化与工具调用成功，正文 16,893 个字符，truncated=false，文件回读与 SHA-256 核对通过。该实测不覆盖其他文章、其他文件系统或宿主自动触发。宿主安装、显式/隐式触发测试仍为 NOT_CHECKED。

## 验证方式（Validation）

维护者先用实际源包根解析脚本和测试，测试不访问微信，也不改动用户数据：

```sh
python3 -B -m unittest discover -s "<skill-root>/tests" -v
```

`<skill-root>` 为待替换的真实包根。创建证据保存在外层 `output/creation-1.0.0/`，按项目规则仅本机保留；克隆后不存在属预期。包内保留来源、契约和可重复测试，第三方文章及本机环境信息不随包分发。

必须分开报告：

- 静态 lint：安全 YAML、资源可达、语义、版本、密度、本机路径候选和 MCP 配置。
- 确定性脚本测试：分批和混合失败、输入缺失/无效、源链接错配、正文空值、截断/未知、重试边界、路径清理、同名与软链接保护、写入失败。
- 实际服务调用：调用新脚本读取用户授权样例，检查输出清单、原文一致性和文件 SHA-256。失败须记录，不能引用历史成功替代。
- 宿主行为：直接请求、同义请求、缺少目录、视频号排除、Python/服务缺失、边界输出。没有真实宿主执行记录则 NOT_CHECKED；脚本测试不是隐式触发通过。

本包不自动安装到 `.agents/skills` 或其他宿主目录，不修改全局 MCP 配置，不执行 Git 提交或推送。
