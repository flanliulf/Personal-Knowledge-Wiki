# 检查规则（Check Rules）

## 权威来源（Authority）

[rule-registry.json](rule-registry.json) 是本包和配套 skills-creator 消费的唯一规则表，contract_version 为 `1.0.0`。规则包含 id、title、scope、source、severity、method、criteria；状态和条数由实际清单计算，不维护另一份手抄矩阵。

2026-09-09 核验的官方来源：[Build skills](https://learn.chatgpt.com/docs/build-skills)、[Plugin skills](https://developers.openai.com/plugins/build/skills)。官方文档、目标宿主支持和本工具质量约定必须分开表述。Error 表示违反所选范围的必要条件，未必是官方限制；Warning 表示该范围的质量建议。

## 工具项目约定（Tooling Policy）

默认 base；显式采用 tooling 时才启用这些约定：name 与目录名一致、kebab-case、最多 64 字符；description 最多 1024 字符；两个入口正文各不超过 5000 字符；中文 canonical、英文 mirror、CHANGELOG 和 SemVer；中文入口章节标题使用 中文（English）形式，英文 mirror 使用英文标题；metadata.version/author 必填，catalog 可选且使用 kebab-case 语义分类，不要求目录中存在 catalog 层。

本次迁入的两个工具自身采用 tooling；KnowledgeWiki 其他资产不自动采用。无全局保留前缀禁令；未知 metadata 或顶级字段应核验消费方，不因未知删除。中文 description 与英文译文按用户目标、触发及排除语义比对；身份字段相等。不要强制 description 三段式、固定触发词数量或能力条数。

tooling 中不创建冗余包内 README；宿主或项目有明确用途时允许说明理由。镜像不是另一个自动发现入口。安全 YAML parser 验证重复键、类型和自定义 tag；合法折叠标量、普通尖括号文本不直接构成注入证据。

## 密度契约（Density Contract）

只能用本包 scripts/check_skill_density.py 的 JSON 作为密度证据。schema_version=2：新增 workflow_status 和 workflow_section_count；missing/ambiguous 时 workflow_chars、workflow_ratio、triggered_density_warning 为 null。无 SKILL.md、读取失败或 YAML 无结束标记返回 1，目录不存在返回 2；0 只表示统计完成，仍需读 warning。

tooling 中 workflow_chars >1500 且 workflow_ratio >0.5 时 WARN，4500 为接近正文预算提醒；命中后检查详细流程是否已抽取且实际可达。Workflow 章节识别 `Workflow`、`Workflow（执行流程）` 与 `执行流程（Workflow）` 等中英文顺序，以及方括号标题；只有中文、没有 Workflow 的标题记为 missing，两种顺序同时出现记为 ambiguous。文件名正则只是路由线索；缺失、歧义或未运行不得判为 PASS。base 可以查看统计，但这些预算不决定通用合规。

## 证据与状态（Evidence）

| 状态 | 含义 |
| --- | --- |
| PASS | 已按规则方法检查并有支持证据。 |
| FAIL | 已确认违反适用 Error 规则。 |
| WARN | 已确认适用 Warning 问题。 |
| N/A | scope 不适用，或已证实具体适用条件不成立；说明理由。 |
| NOT_CHECKED | 尚未执行、证据不足、支持性未知或无法判定；不能算 PASS。 |

list_rules.py 只生成候选清单，executed_count 恒为 0。实际报告应记录目标及文件 hash、host/profile、registry path/hash、逐项证据、parser/脚本输出、运行时间及状态汇总。有适用 NOT_CHECKED 时禁止“全项通过”。静态通过、宿主发现和真实行为通过分别报告。

## 规则演进（Evolution）

保留原通用 36 个 rule id，修正旧文档写成 34 条的漂移；新增 YML-06、BODY-11、CDX-01 至 CDX-04、TEST-01。不引入派生业务包的 ECO 规则、BODY-09/10 实现路径门禁。计数以 registry 为准。

这些 id 保留不代表旧 criteria 不变：YML-01 改为 name 存在性，格式由 FILE-02 承担；FILE-05 改为基于证据的命名边界；YML-05 改为安全解析。升级使用者需接受 density schema v2 的 null，并重新选择 profile，不能沿用全项默认合规假设。
