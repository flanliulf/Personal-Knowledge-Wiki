# Workflow（运行指南）

## Setup（路径与能力）

先确认工具、Python 和真实资产根目录。本仓库源包位于 `skills/codex-session-title-renaming/codex-session-title-renaming/`，其父目录承载 `work/`、`output/`、`examples/`。示例命令以本机路径展示；在其他安装位置使用已核实的绝对路径。

```sh
asset_root='/Users/fancyliu/AIBase/KnowledgeWiki/skills/codex-session-title-renaming'
script_path="$asset_root/codex-session-title-renaming/scripts/title_records.py"
python3 "$script_path" --help
```

此源包没有自带应用连接器。脚本不导入 Codex SDK、不执行历史数据库修复、不假设工具返回字段。实际读取与改名由 Agent 通过可用专用工具完成，脚本接收 Agent 整理的真实证据。存放源包不等于已安装；安装、真实改名与定时配置须分别在授权范围内进行。

## Lock（全局执行锁）

```sh
python3 "$script_path" acquire
```

将返回的 `executionId` 作为 `--lock-token`；锁占用时退出码为 2，直接报告并结束。手动、定期、所有资产副本都使用默认锁路径。`--lock-path` 仅用于测试隔离，不用于规避实际占用。默认目录不可写时报告权限限制，不偷偷换锁路径。

每个操作结束后（包括可处理的异常）释放自己的锁：

```sh
python3 "$script_path" release --lock-token '<executionId>'
```

等待用户确认期间释放锁。脚本进程 ID 不能代表仍在执行的 Agent：锁需要跨多次工具调用存续。若进程中断留下锁，先报告记录并人工确认；不因记录较旧就删除，不提供强制解锁命令。正常解锁拒绝其他执行标识。

## Audit（提案）

由 Agent 调用应用工具收集真实输入，按 `schemas/proposal.schema.json` 在 `work/<batch-id>-input.json` 保存完整提案。只在本轮读取范围内进行判断，不宣称已覆盖不可访问范围。可参考外层 `examples/example-input.json` 的虚构数据格式，不能把示例当作真实执行输入。

```sh
python3 "$script_path" prepare --asset-root "$asset_root" --batch-id '<batch-id>' --input "$asset_root/work/<batch-id>-input.json" --lock-token '<executionId>'
python3 "$script_path" review --asset-root "$asset_root" --batch-id '<batch-id>'
python3 "$script_path" release --lock-token '<executionId>'
```

将 `review` 的完整对照表、批次和提案哈希展示给用户。必要时按同名会话的来源、主机、项目在表外分组，表头不增加列。候选为空或全部保留时结束，无需确认。

## Apply（执行）

仅在用户确认具体批次后，将确认依据保存到 `work/<batch-id>-approval-input.json`：

```json
{
  "confirmedAt": "2026-09-08T10:00:00+08:00",
  "evidence": "示例占位：须替换为用户真实确认消息及可追溯引用"
}
```

重新取得锁并保存批准信息。日期和哈希必须来自实际确认，不能照抄示例。

```sh
python3 "$script_path" acquire
python3 "$script_path" start --asset-root "$asset_root" --batch-id '<batch-id>' --input "$asset_root/work/<batch-id>-approval-input.json" --proposal-sha256 '<获批提案哈希>' --lock-token '<executionId>'
```

逐条执行以下步骤；不并行发出改名请求：

1. 根据提案的主机和 ID 调用只读工具，收集最新 `snapshot.schema.json` 快照，保存在 `work/<batch-id>-<item-id>-before.json`。真实工具调用对象必须与输入的 `itemId` 对应，不能只靠原名匹配。
2. 运行 `before`。只有输出 `eligible: true` 才调用 `set_thread_title`，使用返回的 `threadId`、`hostId` 和 `newTitle`；实际工具若没有主机参数，先确认当前工具确实能作用于该主机，不能静默改到其他主机。

```sh
python3 "$script_path" before --asset-root "$asset_root" --batch-id '<batch-id>' --item-id '<item-id>' --input "$asset_root/work/<batch-id>-<item-id>-before.json" --lock-token '<executionId>'
```

3. 调用改名工具后独立回读。保存输入对象 `{"requestOutcome":"success","after":<快照对象>,"error":null}`，再运行 `record`。工具明确报错用 `error`，超时或调用结果不明确用 `uncertain`；无法回读时 `after` 为 `null`。此处三字段对象是记录命令输入，不是第三份批次核心数据。

```sh
python3 "$script_path" record --asset-root "$asset_root" --batch-id '<batch-id>' --item-id '<item-id>' --input "$asset_root/work/<batch-id>-<item-id>-result-input.json" --lock-token '<executionId>'
```

4. 若尚未调用写入工具且无法读取该条，使用 `skip --item-id ... --reason ...`。若已调用 `before`，之后请求未发出或中断，保留 `unknown` 并说明，不使用 `skip` 掩盖未明确结果。不要再次 `before` 或重发请求。
5. `record` 返回 `stopRequired: true` 时立即停止后续写入。异常由用户决定下一步。
6. 调用 `finish` 保存执行结束时间，剩余未执行项保持 `not_executed`；释放锁并报告摘要。结束不等于全部成功。

```sh
python3 "$script_path" finish --asset-root "$asset_root" --batch-id '<batch-id>' --lock-token '<executionId>'
python3 "$script_path" release --lock-token '<executionId>'
```

所有写操作都要求当前锁标识。已有批次不能重复创建提案或覆盖执行结果；未知项和中断批次需人工核查后另行决定，不自动续跑。

## Report（按需报告）

用户说“生成记录文档”时，根据当前上下文定位明确批次；多个候选无法区分时询问。报告只读取文件：

```sh
python3 "$script_path" acquire
python3 "$script_path" report --asset-root "$asset_root" --batch-id '<batch-id>' --lock-token '<executionId>'
python3 "$script_path" release --lock-token '<executionId>'
```

只有提案时可生成提案报告，但必须显示没有执行证据。存在结果则显示逐项执行前后对比与限制。无需重新读取真实应用。`validate` 可只读校验指定批次的 schema、身份关联与提案哈希，无需取得锁。

## Verification（本地验证）

```sh
python3 -B -m unittest discover -s "$asset_root/codex-session-title-renaming/tests" -v
```

测试只在临时目录创建模拟锁和虚构数据，不读写真实会话，不创建真实全局锁。真实运行前仍须确认应用工具能力及字段映射；不能用单元测试代替真实回读验证。
