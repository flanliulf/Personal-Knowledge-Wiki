# 写作流程（Writing Workflow）

本文是 `SKILL.md` 执行流程的详细步骤，开始写作、修改或审阅前读取。步骤编号在全文连续，入口与其他资料按编号引用。

## 任务与事实（Scope and Facts）

1. 确认任务是新写、定点修改、整体改写还是只读审阅。读取目标项目中存在且适用的 `AGENTS.md` 等规约、相关文档及用户要求，确定读者、范围、术语和标题、格式约定。没有 `AGENTS.md` 不阻塞写作。修改现有文档时先标出允许改动的段落。
2. 查证文档要陈述的事实：代码、配置、接口定义、已有决策、可执行命令及其适用环境。将事实、推断和待确认项分开；不要从文件名、注释或示例推断未证实的行为。关键接口、步骤或参数缺少依据时提出具体问题；其余已核实部分可继续。

## 结构与写作（Structure and Writing）

3. 按文档类型读取 [文档结构指引](document-types.md)，先列出读者最需要的内容，再组织标题。不要为了套模板增设空章节；已有文档以其用途和结构为准。
4. 新写或整体改写时读取包内 [document-style-guide 目录](upstream/document-style-guide/README.md)与 [chinese-copywriting-guidelines 简体中文版](upstream/chinese-copywriting-guidelines/README.zh-Hans.md)。阅读前者的[标题](upstream/document-style-guide/docs/title.md)、[文本](upstream/document-style-guide/docs/text.md)、[段落](upstream/document-style-guide/docs/paragraph.md)和[标点符号](upstream/document-style-guide/docs/marks.md)原文及示例；涉及数字、单位或范围时读[数值](upstream/document-style-guide/docs/number.md)，规划整套手册、目录或文件名时读[文档体系](upstream/document-style-guide/docs/structure.md)。[参考链接](upstream/document-style-guide/docs/reference.md)是延伸阅读目录，仅在追溯其外部参考时读取。定点修改时按影响范围读取相关章节及示例。两份指南对同一事项有差异时以 `document-style-guide` 为准；第二份只补充第一份未规定或允许选择的写法。按[适用说明](writing-rules.md)判断，不用说明代替原文。
5. 根据原文规则与示例写作：一段一个要点，先说结论或动作，再补条件和原因。用具体对象、动词和短句替代笼统表述；保留代码、字段、路径和命令的原样拼写。用[Agent 写作自检](agent-review.md)检查空话、套话、含糊指代和未经证实的效果，逐处判断后修改。

## 复核与交付（Review and Delivery）

6. 复核每个技术断言和可执行示例的依据，检查前提、顺序、输入、结果、链接与交叉引用。再按[autocorrect 使用边界](autocorrect-workflow.md)处理排版：工具可用时先对授权文件运行 `--lint`；需要自动修复时只在可审查的副本上运行 `--fix`，检查差异后把范围内修改写回。工具不可用时手工检查。自动排版不代替原文示例和事实核验。只修改授权范围；发现范围外问题时指出位置。对未实际运行的命令或步骤注明未验证。
7. 交付文档和简短说明：改了什么、依据是什么、哪些关键内容仍待确认，`autocorrect` 是否运行。只读审阅给出问题位置与修改建议，不写回文件，也不运行 `--fix`。
