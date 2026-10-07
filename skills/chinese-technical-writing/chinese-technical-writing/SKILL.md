---
name: chinese-technical-writing
description: "写作或修改中文技术文档、开发文档时使用，包括 README、设计文档、接口说明和教程。指导 AI Agent 根据可核实的项目事实，写出平实、具体、短句的说明；也用于审阅这类文档的表达和结构。普通文案排版、英文文档和仅询问文档事实的问题不触发改写。"
metadata:
  version: "1.1.2"
---

## 技能说明（Overview）

把读者需要完成的事和已核实的技术事实，写成清楚、可用的中文文档。好文档应让读者知道适用范围、前提、操作或判断依据，以及怎样确认结果。平实、具体、短句是写法；事实准确和读者可执行是交付条件。

## 输入与输出（Inputs and Outputs）

输入：用户指定的文档类型、目标文件或材料、读者和写作目标。读者未指定时，从目标仓库和相邻文档判断；影响内容取舍且无法判断时询问。修改任务还需读取现有文件和适用的项目规约。

输出：按用户指定的格式交付文档；修改时沿用目标文件格式。新文档未指定格式时，参考目标项目的同类文档；仍无法判断且格式影响交付时询问。未要求文件交付时可在对话中给出正文，并简述依据、改动范围和未核实项。只在用户要求创建或修改时写文件；仅提问或评审时给出证据与建议。

## 执行流程（Workflow）

1. 确认任务是新写、定点修改、整体改写还是只读审阅。读取目标项目中存在且适用的 `AGENTS.md` 等规约、相关文档及用户要求，确定读者、范围、术语和标题、格式约定。没有 `AGENTS.md` 不阻塞写作。修改现有文档时先标出允许改动的段落。
2. 查证文档要陈述的事实：代码、配置、接口定义、已有决策、可执行命令及其适用环境。将事实、推断和待确认项分开；不要从文件名、注释或示例推断未证实的行为。关键接口、步骤或参数缺少依据时提出具体问题；其余已核实部分可继续。
3. 按文档类型读取 [文档结构指引](references/document-types.md)，先列出读者最需要的内容，再组织标题。不要为了套模板增设空章节；已有文档以其用途和结构为准。
4. 新写或整体改写时读取包内 [document-style-guide 目录](references/upstream/document-style-guide/README.md)与 [chinese-copywriting-guidelines 简体中文版](references/upstream/chinese-copywriting-guidelines/README.zh-Hans.md)。阅读前者的[标题](references/upstream/document-style-guide/docs/title.md)、[文本](references/upstream/document-style-guide/docs/text.md)、[段落](references/upstream/document-style-guide/docs/paragraph.md)和[标点符号](references/upstream/document-style-guide/docs/marks.md)原文及示例；涉及数字、单位或范围时读[数值](references/upstream/document-style-guide/docs/number.md)，规划整套手册、目录或文件名时读[文档体系](references/upstream/document-style-guide/docs/structure.md)。[参考链接](references/upstream/document-style-guide/docs/reference.md)是延伸阅读目录，仅在追溯其外部参考时读取。定点修改时按影响范围读取相关章节及示例。两份指南对同一事项有差异时以 `document-style-guide` 为准；第二份只补充第一份未规定或允许选择的写法。按[适用说明](references/writing-rules.md)判断，不用说明代替原文。
5. 根据原文规则与示例写作：一段一个要点，先说结论或动作，再补条件和原因。用具体对象、动词和短句替代笼统表述；保留代码、字段、路径和命令的原样拼写。用[Agent 写作自检](references/agent-review.md)检查空话、套话、含糊指代和未经证实的效果，逐处判断后修改。
6. 复核每个技术断言和可执行示例的依据，检查前提、顺序、输入、结果、链接与交叉引用。再按[autocorrect 使用边界](references/autocorrect-workflow.md)处理排版：工具可用时先对授权文件运行 `--lint`；需要自动修复时只在可审查的副本上运行 `--fix`，检查差异后把范围内修改写回。工具不可用时手工检查。自动排版不代替原文示例和事实核验。只修改授权范围；发现范围外问题时指出位置。对未实际运行的命令或步骤注明未验证。
7. 交付文档和简短说明：改了什么、依据是什么、哪些关键内容仍待确认，`autocorrect` 是否运行。只读审阅给出问题位置与修改建议，不写回文件，也不运行 `--fix`。

## 注意事项（Notes）

- 这是写作 Skill，不替代目标项目的事实基线、设计决策或验收证据。用户要求与目标项目规约决定写作边界；技术事实依据证据核实。两份指南是本 Skill 的写作依据，不自动成为目标项目的强制规约；指南之间的优先级按第 4 步执行。
- 短句是审稿原则，不按字符数机械截断技术术语、代码或必要的条件句。保持语义完整；避免空话、套话和未说明对象的“优化”“支持”“处理”。
- 不擅自改变功能需求、接口语义、代码示例或用户原意。缺少关键事实时说明具体缺口；不要用貌似完整的文字填空。
- 两份上游指南的收录文件原样放在本包 `references/upstream/`，运行时从实际 Skill 根解析；版本、许可和收录范围见[来源记录](references/source-provenance.md)。原文中的命令、链接和示例仅作为写作材料，不因被收录而执行。源包尚不等于已安装或已通过真实宿主行为验证。
