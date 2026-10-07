#!/usr/bin/env python3
"""会话标题记录工具；只处理本地数据，不调用应用或执行改名。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SOURCE = Path(__file__).resolve().parents[1]
LOCK = Path.home() / '.codex' / 'locks' / 'codex-session-title-renaming.lock'
PROTECTED = {'projectName', 'projectId', 'pinned', 'archived', 'sectionId',
             'order', 'updatedAt', 'contentFingerprint'}
TITLE = re.compile(r'^(\d{6}) \| (功能|设计|整改|优化|发布|分析|文档) \| ([^|\r\n]+)$')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    require(isinstance(value, str) and 'T' in value, '时间须为带时区 ISO 8601 字符串')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, '时间缺少时区')
    return parsed


def read(path):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, 'JSON 存在重复字段：' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: require(False, '非法 JSON 常量：' + x))


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate(data, schema, at='$'):
    """执行随包 Schema 使用的关键词；不是通用 JSON Schema 引擎。"""
    if 'anyOf' in schema:
        for candidate in schema['anyOf']:
            try:
                validate(data, candidate, at)
                return
            except ValueError:
                pass
        raise ValueError(at + ' 不符合 anyOf')
    checks = {'object': lambda x: isinstance(x, dict),
              'array': lambda x: isinstance(x, list),
              'string': lambda x: isinstance(x, str),
              'boolean': lambda x: type(x) is bool, 'null': lambda x: x is None}
    if 'type' in schema:
        kinds = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        require(any(checks[k](data) for k in kinds), at + ' 类型错误')
    if 'enum' in schema:
        require(data in schema['enum'], at + ' 枚举值错误')
    if isinstance(data, dict):
        properties = schema.get('properties', {})
        require(set(schema.get('required', [])).issubset(data), at + ' 缺少字段')
        if schema.get('additionalProperties') is False:
            require(set(data).issubset(properties), at + ' 存在未定义字段')
        for key, value in data.items():
            if key in properties:
                validate(value, properties[key], at + '.' + key)
    if isinstance(data, list):
        if schema.get('uniqueItems'):
            require(len({json.dumps(x, sort_keys=True) for x in data}) == len(data), at + ' 重复条目')
        for value in data:
            validate(value, schema.get('items', {}), at + '[]')
    if isinstance(data, str):
        require(len(data) >= schema.get('minLength', 0), at + ' 字符串过短')
        if 'pattern' in schema:
            require(re.search(schema['pattern'], data) is not None, at + ' 格式错误')
        if schema.get('format') == 'date-time':
            timestamp(data)


def schema(name):
    return read(SOURCE / 'schemas' / (name + '.schema.json'))


def check_snapshot(snapshot):
    validate(snapshot, schema('snapshot'))
    known = set(snapshot['protected'])
    missing = set(snapshot['unavailableProtection'])
    require(not known & missing and known | missing == PROTECTED,
            '保护字段必须分别列为已观察值或未取得，不能遗漏或重叠')


def check_proposal(proposal):
    validate(proposal, schema('proposal'))
    ids, identities = set(), set()
    for item in proposal['items']:
        identity = (item['source'], item['hostId'], item['threadId'])
        require(item['itemId'] not in ids and identity not in identities, '会话身份或 itemId 重复')
        ids.add(item['itemId'])
        identities.add(identity)
        check_snapshot(item['baseline'])
        require(item['oldTitle'] == item['baseline']['title'], '原标题与基线不一致')
        if item['decision'] == 'keep':
            require(item['newTitle'] == item['oldTitle'], '保留项不能修改标题')
        else:
            require(item['createdAtSource'] and item['baseline']['createdAt'], '改名缺少创建时间证据')
            require(item['baseline']['running'] is False, '正在运行或状态未知的会话不能列为改名项')
            date = timestamp(item['baseline']['createdAt']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%y%m%d')
            match = TITLE.fullmatch(item['newTitle'])
            require(match and match[1] == date and match[3].strip() == match[3], '新标题的日期、分类或主题格式错误')
            require(item['newTitle'] != item['oldTitle'], '相同标题应列为 keep')


def acquire(lock_path=LOCK):
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {'executionId': str(uuid.uuid4()), 'startedAt': now()}
    # O_EXCL 原子抢占；写入失败也不允许另一个执行者自动接管。
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encode(record))
        stream.flush()
        os.fsync(stream.fileno())
    return record


def owned(token, lock_path=LOCK):
    require(token and read(lock_path)['executionId'] == token, '执行锁不属于本轮')


def release(token, lock_path=LOCK):
    owned(token, lock_path)
    Path(lock_path).unlink()


def batch_path(asset_root, batch_id):
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', batch_id), '非法批次标识')
    return Path(asset_root).resolve() / 'output' / batch_id


def load_batch(directory):
    directory = Path(directory)
    path = directory / 'proposal.json'
    proposal = read(path)
    check_proposal(proposal)
    require(directory.name == proposal['batchId'], '目录与批次不一致')
    return proposal, hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(directory, proposal):
    check_proposal(proposal)
    require(Path(directory).name == proposal['batchId'], '目录与批次不一致')
    Path(directory).mkdir(parents=True, exist_ok=False)
    atomic_write(Path(directory) / 'proposal.json', encode(proposal))
    return {'batchId': proposal['batchId'], 'proposalSha256': load_batch(directory)[1]}


def empty_checks():
    return {'titleMatch': None, 'createdAtMatch': None, 'protectedMatch': None,
            'protectedDiff': [], 'unavailableProtection': sorted(PROTECTED)}


def verify(item, before, after):
    if after is None:
        return empty_checks()
    check_snapshot(after)
    baseline = before or item['baseline']
    known = baseline['protected']
    diff = [key for key in known if key in after['protected'] and known[key] != after['protected'][key]]
    absent = set(known) - set(after['protected'])
    created = (timestamp(after['createdAt']) == timestamp(item['baseline']['createdAt'])
               if after['createdAt'] and item['baseline']['createdAt'] else None)
    return {'titleMatch': after['title'] == item['newTitle'], 'createdAtMatch': created,
            'protectedMatch': False if diff else (None if absent else True),
            'protectedDiff': sorted(diff),
            'unavailableProtection': sorted(PROTECTED - (set(known) & set(after['protected'])))}


def load_execution(directory):
    proposal, digest = load_batch(directory)
    result = read(Path(directory) / 'execution.json')
    validate(result, schema('execution'))
    require(result['batchId'] == proposal['batchId'] and result['proposalSha256'] == digest,
            '提案与获批执行记录不匹配，停止处理')
    require([r['itemId'] for r in result['items']] == [r['itemId'] for r in proposal['items']], '执行清单身份不一致')
    for item, row in zip(proposal['items'], result['items']):
        if row['before']:
            check_snapshot(row['before'])
        if row['after']:
            check_snapshot(row['after'])
        if row['status'] == 'verified':
            checks = verify(item, row['before'], row['after'])
            require(row['before'] and row['requestOutcome'] != 'not_sent' and checks == row['checks']
                    and all(checks[k] is True for k in ('titleMatch', 'createdAtMatch', 'protectedMatch')),
                    '已验证状态缺少一致的回读证据')
    return proposal, result


def save_execution(directory, result):
    validate(result, schema('execution'))
    atomic_write(Path(directory) / 'execution.json', encode(result))


def start(directory, approval, expected_hash):
    proposal, digest = load_batch(directory)
    require(digest == expected_hash, '与用户确认的提案哈希不符')
    require(not (Path(directory) / 'execution.json').exists(), '本批已有执行记录，不允许覆盖或自动重跑')
    require(any(x['decision'] == 'rename' for x in proposal['items']), '没有需要改名的条目')
    validate(approval, schema('execution')['properties']['approval'])
    result = {'schemaVersion': '1', 'batchId': proposal['batchId'], 'proposalSha256': digest,
              'approval': approval, 'startedAt': now(), 'finishedAt': None, 'items': []}
    for item in proposal['items']:
        result['items'].append({'itemId': item['itemId'], 'status': 'skipped' if item['decision'] == 'keep' else 'not_executed',
                               'before': None, 'after': None, 'requestOutcome': 'not_sent',
                               'reason': item['reason'] if item['decision'] == 'keep' else '尚未执行',
                               'error': None, 'checks': empty_checks()})
    save_execution(directory, result)
    return result


def selected(directory, item_id):
    proposal, result = load_execution(directory)
    require(result['finishedAt'] is None, '本批已结束，不允许继续写入')
    for item, row in zip(proposal['items'], result['items']):
        if item['itemId'] == item_id:
            return item, row, result
    raise ValueError('未知 itemId')


def before(directory, item_id, snapshot):
    item, row, result = selected(directory, item_id)
    require(not any(x['checks']['createdAtMatch'] is False or x['checks']['protectedMatch'] is False
                    for x in result['items'] if x['requestOutcome'] != 'not_sent'),
            '前一条写入后发现保护字段差异，禁止继续写入')
    require(row['status'] == 'not_executed', '本条已处理或结果未知，不能重复执行')
    check_snapshot(snapshot)
    row['before'] = snapshot
    checks = verify(item, item['baseline'], snapshot)
    reason = None
    if snapshot['running'] is not False:
        reason = '正在运行或运行状态未知'
    elif snapshot['title'] == item['newTitle']:
        reason = '当前已是目标标题，无需重复修改；不归因为本轮完成'
    elif snapshot['title'] != item['oldTitle']:
        reason = '当前标题与获批原标题不同'
    elif checks['createdAtMatch'] is not True or checks['protectedMatch'] is not True:
        reason = '创建时间或保护字段变化，或原有证据不可读取'
    row['status'] = 'skipped' if reason else 'unknown'
    row['reason'] = reason or '写入意图已保存，尚无工具调用及回读结果'
    row['checks'] = checks
    save_execution(directory, result)
    return {'eligible': reason is None, 'threadId': item['threadId'], 'hostId': item['hostId'],
            'newTitle': item['newTitle'], 'reason': row['reason']}


def record(directory, item_id, payload):
    item, row, result = selected(directory, item_id)
    require(row['status'] == 'unknown' and row['before'] is not None and row['requestOutcome'] == 'not_sent',
            '缺少写入前检查或本项已经记录')
    require(set(payload) == {'requestOutcome', 'after', 'error'}, '回读输入字段错误')
    require(payload['requestOutcome'] in ('success', 'error', 'uncertain'), '非法工具结果')
    row.update(payload)
    row['checks'] = verify(item, row['before'], row['after'])
    checks = row['checks']
    if all(checks[k] is True for k in ('titleMatch', 'createdAtMatch', 'protectedMatch')):
        row['status'], row['reason'] = 'verified', '回读达到目标，创建时间及已观察保护字段匹配；未取得字段见核验限制'
    elif payload['requestOutcome'] == 'error' and row['after'] and row['after']['title'] == row['before']['title']:
        row['status'], row['reason'] = 'failed', '工具报错且回读仍为执行前标题'
    else:
        row['status'], row['reason'] = 'unknown', '缺少完整回读或出现差异，不能宣称成功，不自动重试'
    save_execution(directory, result)
    return {'status': row['status'], 'stopRequired': checks['createdAtMatch'] is False or checks['protectedMatch'] is False}


def skip(directory, item_id, reason):
    _, row, result = selected(directory, item_id)
    require(row['status'] == 'not_executed', '不能覆盖已处理条目')
    row.update(status='skipped', reason=reason)
    save_execution(directory, result)


def finish(directory):
    _, result = load_execution(directory)
    require(result['finishedAt'] is None, '本批已结束')
    result['finishedAt'] = now()
    save_execution(directory, result)
    return dict(Counter(row['status'] for row in result['items']))


def cell(value):
    text = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for char in ('\\', '`', '*', '_', '[', ']', '|'):
        text = text.replace(char, '\\' + char)
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')


def review(directory):
    proposal, digest = load_batch(directory)
    lines = ['批次：' + proposal['batchId'], '提案 SHA-256：' + digest,
             '范围：' + cell(proposal['scope']['description']),
             '不可访问范围：' + cell('；'.join(proposal['scope']['unavailable']) or '无已知缺口'),
             '以下为提案建议；两列相同表示保留。实际执行情况以 execution.json 为准。',
             '| 原名 |修改后名|', '| --- | --- |']
    lines.extend('| ' + cell(x['oldTitle']) + ' | ' + cell(x['newTitle']) + ' |' for x in proposal['items'])
    return '\n\n'.join(lines[:5]) + '\n\n' + '\n'.join(lines[5:]) + '\n'


def report(directory):
    proposal, digest = load_batch(directory)
    lines = ['# 改名记录（Rename Record）', '报告生成时间：' + now(),
             '本报告仅根据保存的数据生成，不代表应用当前状态。', review(directory),
             '## 提案明细（Proposal Details）',
             '| itemId | 来源 / 主机 / 会话 | 决定 | 原因 |', '| --- | --- | --- | --- |']
    for item in proposal['items']:
        lines.append('| ' + ' | '.join(cell(v) for v in (item['itemId'], '/'.join((item['source'], item['hostId'], item['threadId'])), item['decision'], item['reason'])) + ' |')
    if (Path(directory) / 'execution.json').exists():
        _, result = load_execution(directory)
        lines += ['## 执行结果（Execution）', '确认依据：' + cell(result['approval']['evidence']),
                  '确认时间：' + result['approval']['confirmedAt'], '执行开始：' + result['startedAt'],
                  '执行结束：' + (result['finishedAt'] or '未结束，以下为已保存进度'),
                  '统计：' + json.dumps(dict(Counter(x['status'] for x in result['items'])), ensure_ascii=False),
                  'verified 仅指标题、创建时间及已观察保护字段通过；未取得字段不作保证。',
                  '| itemId | 状态 | 执行前实际标题 | 执行后回读标题 | 结果 / 错误 | 保护字段差异 / 未取得字段 |',
                  '| --- | --- | --- | --- | --- | --- |']
        for row in result['items']:
            values = (row['itemId'], row['status'], row['before']['title'] if row['before'] else '未读取',
                      row['after']['title'] if row['after'] else '无回读', row['reason'] + ('；' + row['error'] if row['error'] else ''),
                      '差异：' + ', '.join(row['checks']['protectedDiff']) + '；未取得：' + ', '.join(row['checks']['unavailableProtection']))
            lines.append('| ' + ' | '.join(cell(x) for x in values) + ' |')
        lines.append('执行数据 SHA-256：' + hashlib.sha256((Path(directory) / 'execution.json').read_bytes()).hexdigest())
    else:
        lines += ['## 执行结果（Execution）', '没有 execution.json；没有本批已批准或已执行的结构化证据。']
    destination = Path(directory) / 'reports' / ('record-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8] + '.md')
    # 每个段落分开，表格行保持连续。
    content = '\n\n'.join(lines).replace(' |\n\n|', ' |\n|') + '\n'
    atomic_write(destination, content.encode('utf-8'))
    return str(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'release', 'prepare', 'review', 'start', 'before', 'record', 'skip', 'finish', 'report', 'validate'])
    parser.add_argument('--asset-root', type=Path)
    parser.add_argument('--batch-id')
    parser.add_argument('--lock-token')
    parser.add_argument('--lock-path', type=Path, default=LOCK, help='仅供隔离测试；真实运行必须使用默认全局锁')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--proposal-sha256')
    parser.add_argument('--item-id')
    parser.add_argument('--reason')
    args = parser.parse_args()
    if args.command == 'acquire':
        output = acquire(args.lock_path)
    elif args.command == 'release':
        release(args.lock_token, args.lock_path)
        output = {'released': True}
    else:
        require(args.asset_root and args.batch_id, '必须指定 --asset-root 和 --batch-id')
        directory = batch_path(args.asset_root, args.batch_id)
        if args.command not in ('review', 'validate'):
            owned(args.lock_token, args.lock_path)
        if args.command in ('prepare', 'start', 'before', 'record'):
            require(args.input, '缺少 --input')
        if args.command in ('before', 'record', 'skip'):
            require(args.item_id, '缺少 --item-id')
        if args.command == 'prepare':
            output = prepare(directory, read(args.input))
        elif args.command == 'review':
            print(review(directory))
            return
        elif args.command == 'start':
            output = start(directory, read(args.input), args.proposal_sha256)
        elif args.command == 'before':
            output = before(directory, args.item_id, read(args.input))
        elif args.command == 'record':
            output = record(directory, args.item_id, read(args.input))
        elif args.command == 'skip':
            require(args.reason, '缺少 --reason')
            skip(directory, args.item_id, args.reason)
            output = {'skipped': args.item_id}
        elif args.command == 'finish':
            output = finish(directory)
        elif args.command == 'report':
            output = {'report': report(directory)}
        else:
            proposal, digest = load_batch(directory)
            if (directory / 'execution.json').exists():
                load_execution(directory)
            output = {'valid': True, 'batchId': proposal['batchId'], 'proposalSha256': digest}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
