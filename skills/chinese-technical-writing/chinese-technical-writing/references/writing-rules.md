# Writing Rules（指南适用说明）

## Purpose（用途）

这份说明只处理适用顺序和两份指南之间的差异。写作规则与示例以包内 [document-style-guide 原文](upstream/document-style-guide/README.md)和 [chinese-copywriting-guidelines 简体中文版](upstream/chinese-copywriting-guidelines/README.zh-Hans.md)为准。不要仅凭本页写作或审稿。

## Priority（适用顺序）

1. 用户明确指定的范围、格式和语气，以及目标项目适用的强制规约，决定交付边界。目标文件已有术语与风格可在更高优先级允许时沿用；两项强制要求冲突时指出具体冲突并询问。
2. 技术事实须由目标项目的代码、配置、接口、正式决策或用户提供的权威材料核实。写作指南不能证明功能已实现，也不能把预计结果写成实测结果。
3. 前两项未规定时，`document-style-guide` 的相关章节及示例在内容、结构、语言和排版上均优先。`chinese-copywriting-guidelines` 只补充第一份未规定的事项，或在第一份允许多种写法时提供选择；不能用第二份的例外覆盖第一份的明确规则。
4. `autocorrect` 的报告和修复建议低于两份指南。逐处核对后，只对授权范围应用符合上述顺序的修改；工具建议不自动成为规则。

## Differences（差异与例外）

- [文本](upstream/document-style-guide/docs/text.md)允许中文与数字之间留空格或不留空格，但要求全文一致；[排版指北](upstream/chinese-copywriting-guidelines/README.zh-Hans.md)要求留空格。现有文档若统一不留空格，不将其判错，也不为了第二份指南改排版；新文档无约定时可选择留一个半角空格，并保持一致。
- [标点符号](upstream/document-style-guide/docs/marks.md)规定中文使用弯引号 `“ ”`，内层用 `‘ ’`；排版指北将简体中文直角引号列为可选的争议写法。没有更高优先级的明确要求时，按第一份使用弯引号。定点修改不得以统一引号为由改动授权范围外的段落。
- [数值](upstream/document-style-guide/docs/number.md)要求阿拉伯数字一律使用半角；排版指北允许设计稿、海报中的少量全角数字。技术文档按第一份使用半角数字，不套用第二份的例外。
- [文档体系](upstream/document-style-guide/docs/structure.md)的目录与文件名建议适用于新规划的文档体系。现有文件名、目标项目目录规则和用户指定路径优先；不要为套用示例擅自重命名。
- 代码、命令、路径、URL、接口字段、序列化数据和正式产品名须保持原义与拼写。自动排版建议与这些内容冲突时，逐处人工判断。
