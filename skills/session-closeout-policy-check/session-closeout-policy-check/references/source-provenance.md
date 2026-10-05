# 来源与核验（Sources and Verification）

## 设计来源（Design Origin）

本技能由 KnowledgeWiki 内置 `skills-creator` 创建，以配套 `skills-lint` 的共享契约 `1.0.0` 检查，采用 `base` 并检查 Codex 适用项。Claude Code 兼容性另依据官方文档核验，不伪造不存在的 lint host profile。

需求来自本次用户提出的日常会话收尾与提交前检查：遵循不同项目的规约，评估规约迭代，支持 Codex 和 Claude Code，并将自身作为源资产维护。共享 Skill、薄 Hook 适配、快照绑定与一次提醒是本方案设计推导，不是官方内置完整工作流。

## 官方资料（Official References）

核验日期：2026-10-05。以下资料实际阅读与采用范围为相关功能段落；未镜像上游全文。仅记录说明性依据，不执行页面中的配置示例。

| 来源 | 实际阅读与采用范围 |
| --- | --- |
| [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) | Skill 入口、渐进加载、本地发现、显式调用及可选配置 |
| [Codex Hooks](https://learn.chatgpt.com/docs/hooks) | 配置层、信任、命令处理器、输入输出、Stop 与 SessionEnd 边界 |
| [Claude Code Skills](https://code.claude.com/docs/en/skills) | 共享 SKILL.md、发现、slash command 与宿主专属扩展 |
| [Claude Code Hooks](https://code.claude.com/docs/en/hooks) | command Hook、Stop 输入输出、重复续轮与 cwd 边界 |
| [Git githooks](https://git-scm.com/docs/githooks) | pre-commit 时机、非零退出和可绕过性 |

原始页面地址即上表规范地址；用户未为这些官方页面提供带参数的链接集合。原检索使用的 Codex skills 地址 `https://developers.openai.com/codex/skills` 跳转到上表 Build skills，两者关联为同一资源。

## 验证边界（Verification Boundaries）

静态规则检查、辅助脚本测试、官方能力核验和宿主真实行为分别报告。未安装源包，未注册 Hooks，未读取用户 transcript，未运行真实 Claude Code 或 Codex 收尾事件。运行数据模板为待填写输入，不代表真实授权或已通过报告。

本项目允许现有 `skills/<skill-name>/<skill-name>/` 结构保存入口、references、assets、scripts 与 tests。新增资产无需新增顶层分类或修改项目规约；README 应更新资产清单和使用入口。
