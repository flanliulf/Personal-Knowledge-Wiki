# 依赖契约（Dependency Contract）

源包调用 KnowledgeWiki 的 `X-last30days/X-last30days` 同级资产。独立安装时用 `--engine-root` 传入这份收录包的实际根目录。它须包含项目生成的 `UPSTREAM-MANIFEST.json`。脚本校验清单本身及清单内各文件的 SHA-256。

固定上游为 [last30days-skill 4.1.0 源码](https://github.com/mvanhorn/last30days-skill/tree/d2c8949ad189929c0423d3d67018ae1326fc6a31/skills/last30days)。版本更新时复核以下接口。

- `scripts/last30days.py` 的 `doctor --cached --json` 是运行前诊断，实际查询是否成功以报告的 X 来源状态为准。`--research-only --search=x --plan=- --json-profile=raw` 提供研究接口。`--max-source-fetches` 随实际查询数设置。
- [范围适配脚本](../scripts/scoped_engine.py) 在子进程内收窄上游站点、配置选择和诊断探测。Arc 登录处理沿用上游实现。适配仅对固定版本有效。
- `scripts/lib/schema.py` 定义来源状态、原帖、候选、分组、互动和日期。对缺失或无法识别的结构报告错误，避免将依赖变更当成无结果。
- 回归验证应含一个正向领域、一个狭窄方向、精确词候选、缺少授权、配置选择、限流、部分结果和超出日期窗口的帖子。检查输出中只出现允许导出的字段，然后用项目内置 skills-lint 检查最新源包。
