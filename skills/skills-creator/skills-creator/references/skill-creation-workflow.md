# 技能创建流程（Skill Creation Workflow）

## 需求收集（Requirements）

从当前请求和已有文件提取目标、输入、输出、触发与排除场景、必需依赖、成功标准、停止条件和授权范围。一次最多提出三个实质问题；已知信息不重复询问。不要凭空推断第三方接口、作者身份或安装位置。

明确目标宿主及 profile：外部目标默认 `base`；用户或目标政策明确采用本工具的双语版本化规范时选 `tooling`。更新已有包先读取现状、保存作者和用户改动，再决定兼容性版本变化。不要直接将源包新版本号套给生成的业务 Skill。

## 结构规划（Structure）

先读目标项目 README、AGENTS.md 和现有源目录。KnowledgeWiki 的写入结构为：

```text
skills/<skill-name>/
├── <skill-name>/       # SKILL.md、资源和版本记录
├── work/              # 输入、依赖及迁移前快照
├── output/            # 报告、验证和迁移记录
└── examples/          # 配套示例，按需
```

资产容器只含子目录，不在 `skills/` 或外层 `skills/<skill-name>/` 放独立文件。其他项目使用其已验证源目录，不默认 forge、隐藏安装目录或当前 CWD。需要复用安装后的包时，从实际源包根解析资源；运行数据落在用户指定的输出位置，不写进安装源包。

`base` 最小包为 SKILL.md；`tooling` 额外生成 SKILL.en.md、CHANGELOG.md 和 metadata.version/author。catalog 为可选语义分类，不要求目标路径中有同名目录。资源按需创建，不生成空目录、空脚本或重复 README。需要选流程模式时读 workflow-patterns.md。

## 内容生成（Authoring）

先读 spec-guide.md 定位共享规则契约，再读 templates.md。description 前置用户目标、触发和必要的排除边界；正文包含可执行步骤、输入输出、依赖、不可推断事实及停止条件。不要把关键词配额或固定能力条数当作质量依据。

依赖 MCP 或需要定制调用策略时核验宿主资料与真实服务，再生成 agents/openai.yaml；没有需求时保持 instruction-only。英文 mirror 按语义同步，不要求 description 原文相等。不自动删除未知扩展字段，先核验实际消费方。

## 验证（Validation）

按 spec-guide.md 核验 `{lint-root}` 后调用：

```sh
python3 "{lint-root}/scripts/list_rules.py" "{target}" --profile base
python3 "{lint-root}/scripts/check_skill_density.py" "{target}"
```

`tooling` 目标显式替换 profile；Codex 目标加 `--host codex`。第一条只生成待检查清单。随后依 testing-guide.md 执行安全 YAML 解析、资源和语义审查；不把清单当 lint 执行结果。

density JSON schema_version 为 2。仅 `workflow_status: identified` 可用于比例判断；missing/ambiguous 的 workflow_chars、workflow_ratio、triggered_density_warning 为 null，需说明未判定原因。`tooling` 中字符数 >1500 且占比 >0.5 时把实际详细流程提到 reference，并回读内容及入口加载条件；4500 为接近 5000 正文预算提示。脚本退出 0 只代表统计完成。

## 交付（Delivery）

输出真实文件树、版本与兼容性变化、使用的 profile/host/registry hash、PASS/FAIL/WARN/N/A/NOT_CHECKED 结果及未执行用例。更新 KnowledgeWiki 资产清单。来源标注不能破坏 JSON、代码或用户固定格式。

仅在已有授权包含安装或分发时操作已确认的目标。作者缺失、必需服务值未知或新目标会覆盖未授权资产时先说明缺口；独立可完成部分继续。源修订、静态通过、宿主发现和行为通过必须分别报告。
