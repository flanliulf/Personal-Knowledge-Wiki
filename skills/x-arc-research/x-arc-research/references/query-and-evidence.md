# 检索与证据（Queries and Evidence）

## 方向检索（Topic Search）

以下命令从 Skill 源包目录运行。将 `<output-dir>` 替换为用户指定目录，从其他目录运行时也要将脚本路径换成已核实的路径。

```sh
python3 -B scripts/run_research.py --topic '公众号文章读取工具' \
  --query '公众号文章 MCP' --exact 'wechat-article-reader' \
  --output-dir '<output-dir>'
```

优先使用用户用词、项目原名和社区常用同义词。每次最多四个不同查询，含可选的一个精确短语。精确短语经同一 Bird 后端提交，在原始返回帖文的可见摘录中再做字面匹配。通过引擎筛选的帖子进入主结果。额外字面命中单独列为待核验线索。

`--handle` 和 `--exclude` 可重复提供，分别筛作者和排除词。`--language zh` 同时向 X 传语言条件。上游没有逐帖语言标签时记为 `needs_review`，引用前由宿主核对原文语种。`--days` 默认 30，`--as-of YYYY-MM-DD` 指定截止日。日期取上游报告边界，按包含起止日筛选。`--limit` 控制报告展示数，完整合格样本仍保存在 JSON 中。

## 领域热点（Topic Discovery）

```sh
python3 -B scripts/run_research.py --mode hot --topic 'Claude Code' \
  --query 'Claude Code workflow' --query 'Claude Code agents' \
  --query 'Claude Code review' --no-save
```

根据领域选二至四个不同角度。先按正分讨论组汇集帖子，再按去重账号数、帖子数排序。在报告中列出观测日期、账号数、可用互动数与代表帖。来自同一账号的多条帖仅算一个账号；单账号组标为线索。多个账号可能引用同一消息，判断独立来源时还需核对原帖。缺少历史对照时不推断增长率。X 官方趋势榜与上游跨平台 `--discover` 均属于不同的数据范围。

## 输出判读（Reading Results）

| 文件 | 内容 |
| --- | --- |
| `report.md` | 中文样本摘要、分组、日期和代表原帖 |
| `posts.json` | 合格原帖、账号、摘录、时间、已有的互动数、命中查询及分组 |
| `literal-leads.json` | 额外的精确词线索，不参与热点数量统计 |
| `query-plan.json` | 实际传给引擎的查询和选源 |
| `run-manifest.json` | 模式、范围、运行状态、依赖版本与输出数量 |
| `engine/coverage.json` | X 来源状态、筛选前记录数与上游组数 |

先按原帖 ID 去重。只引用可解析的 HTTPS 原帖链接、带日期且落在窗口内的记录。主样本还须通过引擎候选和讨论组评分，且无实体不匹配标记。分数用于取样，不能独立证明帖子陈述属实。

`success` 表示有合格帖子；`no_results` 表示 X 来源报告无返回；`no_relevant_evidence` 表示未取得合格证据。这三种状态退出码均为 0。`partial` 表示来源覆盖不完整，已有结果可带限制引用。运行失败或部分成功返回 1；依赖或授权在运行前失败返回 2。无结果及故障均不得推断“没人讨论”。原帖不可访问时注明核验限制。
