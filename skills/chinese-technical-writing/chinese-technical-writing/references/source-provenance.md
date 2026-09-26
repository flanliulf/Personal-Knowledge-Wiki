# Source Provenance（来源与许可）

## Bundled Guides（包内指南）

| 上游 | 包内位置 | 上游 commit | 许可与范围 |
| --- | --- | --- | --- |
| [ruanyf/document-style-guide](https://github.com/ruanyf/document-style-guide) | [document-style-guide/README.md](upstream/document-style-guide/README.md) 及其 `docs/*.md` | `571951731efb4b83b1939af1d3dd830441ebef45` | README 标明公共领域；收录 README 和七个章节。 |
| [sparanoid/chinese-copywriting-guidelines](https://github.com/sparanoid/chinese-copywriting-guidelines) | [chinese-copywriting-guidelines/README.zh-Hans.md](upstream/chinese-copywriting-guidelines/README.zh-Hans.md)、繁体 README 与 [LICENSE](upstream/chinese-copywriting-guidelines/LICENSE) | `9a5fbeb842f39644352fd79b5d8c6764718105cc` | MIT；收录繁简中文 README 和完整许可文本。 |

包内文件从 KnowledgeWiki `guidelines/` 的对应快照逐字节复制。更新上游版本时先核实来源、许可和差异，再同步两处副本；不在原文上直接加入本 Skill 的写作规则。包内原文可随 Skill 单独携带，运行时不依赖仓库级 `guidelines/`。

## Design References（设计参考）

[leter/zh-tech-writing](https://github.com/leter/zh-tech-writing) 启发了写作后再做 Agent 语气自检、排版工具辅助和人工复核的流程。本包的 [Agent 写作自检](agent-review.md)与 [AutoCorrect 流程](autocorrect-workflow.md)为独立编写，不收录该项目原文。`autocorrect` 的能力与命令以其[官方仓库](https://github.com/huacnlee/autocorrect)为参考。
