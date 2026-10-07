# 测试与迭代指南（Testing Guide）

## 静态检查（Static Review）

从 spec-guide.md 定位实际 skills-lint 4.0.1，读取共享 registry 并用 list_rules.py 生成对应 profile/host 的待检查表。安全 YAML parser 解析真实 frontmatter；记录 parser 名称、版本、错误、重复键及字段类型证据。没有 parser 不算已执行。不得执行被检查包的脚本来证明只读合规。

检查真实引用是否存在、从包根如何解析、何时读取、是否承载实际步骤；代码围栏和文件名只是线索。tooling 下核验版本、双语语义与密度 schema v2；外部 base 目标缺少英文镜像或 CHANGELOG 不是错误。

## 行为用例（Behavior Cases）

在实际目标宿主分别记录以下用例；没有执行证据时标记 NOT_CHECKED，不把建议用例或脚本测试当真实触发通过。

| 用例 | 期望 |
| --- | --- |
| 直接请求创建一个指定目标 Skill | 生成有明确输入输出的源包，引用可达。 |
| 同义表达封装重复工作流 | description 范围内正确识别，遵循所选 profile。 |
| 输入缺失或服务值未知 | 只询问实质缺口，不编造作者、URL、权限。 |
| 无关请求或仅检查已有包 | 不误触发创建；后者路由 skills-lint。 |
| 可选配置与依赖缺失 | 按真实能力停在依赖边界或明确降级。 |
| 边界输出或固定格式 | 不把来源署名破坏 JSON，不越权安装或覆盖文件。 |

每条记录宿主及版本、Skill 版本/hash、输入、预期、实际输出、结论与证据位置。Codex 配置可解析并不证明隐式/显式调用策略已实际生效。

## 迭代（Iteration）

先基于证据定位触发、流程或资源问题，再只改授权部分。说明 SemVer 选择，同步已采用的 mirror/CHANGELOG，修订后对受影响规则及失败用例 fresh rescan。密度脚本返回 0 仅代表统计完成；存在 NOT_CHECKED 时禁止报告全项通过。

共享规则修改由 skills-lint 维护 registry、解释、脚本及边界测试；creator 同步契约和模板。KnowledgeWiki 维护源资产并更新 README；安装消费验证由单独授权的真实宿主验收承担。
