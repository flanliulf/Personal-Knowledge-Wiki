"""仅使用临时目录、虚构观察值；不连接或改名真实会话。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('title_records', SOURCE / 'scripts/title_records.py')
records = importlib.util.module_from_spec(spec)
spec.loader.exec_module(records)


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proposal = records.read(SOURCE.parent / 'examples/example-input.json')
        self.directory = self.root / 'output' / 'example-batch'

    def started(self):
        saved = records.prepare(self.directory, self.proposal)
        records.start(self.directory, {'confirmedAt': records.now(), 'evidence': '模拟用户明确确认本批，非真实授权'}, saved['proposalSha256'])

    def snapshot(self, title=None):
        snapshot = copy.deepcopy(self.proposal['items'][0]['baseline'])
        snapshot['observedAt'] = records.now()
        if title is not None:
            snapshot['title'] = title
        return snapshot

    def test_atomic_lock_has_only_one_winner_and_owner_release(self):
        lock = self.root / 'global.lock'
        command = [sys.executable, '-B', str(SOURCE / 'scripts/title_records.py'), 'acquire', '--lock-path', str(lock)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: subprocess.run(command, capture_output=True, text=True), range(6)))
        self.assertEqual(sum(p.returncode == 0 for p in results), 1)
        self.assertEqual(sum(p.returncode == 2 for p in results), 5)
        with self.assertRaises(ValueError):
            records.release('different-owner', lock)
        self.assertTrue(lock.exists())
        records.release(records.read(lock)['executionId'], lock)
        self.assertFalse(lock.exists())

    def test_cli_refuses_mutation_without_lock(self):
        input_path = self.root / 'input.json'
        input_path.write_bytes(records.encode(self.proposal))
        result = subprocess.run([sys.executable, '-B', str(SOURCE / 'scripts/title_records.py'), 'prepare',
                                 '--asset-root', str(self.root), '--batch-id', 'example-batch', '--input', str(input_path),
                                 '--lock-path', str(self.root / 'missing.lock')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.directory.exists())

    def test_cli_roundtrip_with_isolated_lock_and_mock_observations(self):
        lock = self.root / 'test.lock'
        def run(command, *args):
            process = subprocess.run([sys.executable, '-B', str(SOURCE / 'scripts/title_records.py'), command,
                                      '--lock-path', str(lock), *args], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            return process.stdout
        def input_file(name, data):
            path = self.root / name
            path.write_bytes(records.encode(data))
            return str(path)
        token = json.loads(run('acquire'))['executionId']
        common = ['--asset-root', str(self.root), '--batch-id', 'example-batch', '--lock-token', token]
        prepared = json.loads(run('prepare', *common, '--input', input_file('proposal-input.json', self.proposal)))
        self.assertIn('| 原名 |修改后名|', run('review', *common))
        run('release', '--lock-token', token)
        self.assertFalse(lock.exists())  # 人工确认等待期间不持锁
        token = json.loads(run('acquire'))['executionId']
        common = ['--asset-root', str(self.root), '--batch-id', 'example-batch', '--lock-token', token]
        run('start', *common, '--input', input_file('approval-input.json', {'confirmedAt': records.now(), 'evidence': '仅模拟用户确认'}),
            '--proposal-sha256', prepared['proposalSha256'])
        before = json.loads(run('before', *common, '--item-id', 'item-1', '--input', input_file('before-input.json', self.snapshot())))
        self.assertTrue(before['eligible'])
        payload = {'requestOutcome': 'success', 'after': self.snapshot(self.proposal['items'][0]['newTitle']), 'error': None}
        outcome = json.loads(run('record', *common, '--item-id', 'item-1', '--input', input_file('result-input.json', payload)))
        self.assertEqual(outcome['status'], 'verified')
        self.assertEqual(json.loads(run('finish', *common)), {'verified': 1})
        self.assertTrue(json.loads(run('validate', *common))['valid'])
        self.assertTrue(Path(json.loads(run('report', *common))['report']).is_file())
        run('release', '--lock-token', token)

    def test_shanghai_year_boundary_and_category(self):
        records.check_proposal(self.proposal)
        for title in ['251231 | 分析 | 分析示例报告', '260101 | 审计 | 分析示例报告', '^260101 | 分析 | 分析示例报告']:
            changed = copy.deepcopy(self.proposal)
            changed['items'][0]['newTitle'] = title
            with self.assertRaises(ValueError):
                records.check_proposal(changed)

    def test_missing_created_time_and_duplicate_identity_rejected(self):
        changed = copy.deepcopy(self.proposal)
        changed['items'][0]['baseline']['createdAt'] = None
        with self.assertRaises(ValueError):
            records.check_proposal(changed)
        changed = copy.deepcopy(self.proposal)
        changed['items'].append(copy.deepcopy(changed['items'][0]))
        changed['items'][1]['itemId'] = 'different-item'
        with self.assertRaises(ValueError):
            records.check_proposal(changed)

    def test_keep_unknown_time_allowed_but_missing_protection_must_be_declared(self):
        changed = copy.deepcopy(self.proposal)
        item = changed['items'][0]
        item.update(decision='keep', newTitle=item['oldTitle'], createdAtSource=None)
        item['baseline']['createdAt'] = None
        records.check_proposal(changed)
        item['baseline']['unavailableProtection'] = []
        with self.assertRaises(ValueError):
            records.check_proposal(changed)

    def test_proposal_and_execution_cannot_be_overwritten(self):
        self.started()
        with self.assertRaises(FileExistsError):
            records.prepare(self.directory, self.proposal)
        with self.assertRaises(ValueError):
            records.start(self.directory, {'confirmedAt': records.now(), 'evidence': '模拟确认'}, records.load_batch(self.directory)[1])

    def test_approval_hash_and_later_tampering_rejected(self):
        saved = records.prepare(self.directory, self.proposal)
        approval = {'confirmedAt': records.now(), 'evidence': '模拟确认'}
        with self.assertRaises(ValueError):
            records.start(self.directory, approval, '0' * 64)
        records.start(self.directory, approval, saved['proposalSha256'])
        path = self.directory / 'proposal.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            records.before(self.directory, 'item-1', self.snapshot())
        with self.assertRaises(ValueError):
            records.report(self.directory)

    def test_external_rename_skipped_without_write_intent(self):
        self.started()
        self.assertFalse(records.before(self.directory, 'item-1', self.snapshot('用户后来修改的标题'))['eligible'])
        row = records.load_execution(self.directory)[1]['items'][0]
        self.assertEqual(row['status'], 'skipped')
        self.assertEqual(row['requestOutcome'], 'not_sent')

    def test_already_target_is_not_attributed_as_success(self):
        self.started()
        self.assertFalse(records.before(self.directory, 'item-1', self.snapshot(self.proposal['items'][0]['newTitle']))['eligible'])
        self.assertEqual(records.finish(self.directory), {'skipped': 1})

    def test_running_or_protected_change_before_write_is_skipped(self):
        for field in ['running', 'pinned']:
            with self.subTest(field=field):
                self.directory = self.root / field / 'example-batch'
                self.started()
                snapshot = self.snapshot()
                if field == 'running':
                    snapshot['running'] = True
                else:
                    snapshot['protected']['pinned'] = True
                self.assertFalse(records.before(self.directory, 'item-1', snapshot)['eligible'])

    def test_crash_window_preserves_unknown_and_does_not_repeat(self):
        self.started()
        self.assertTrue(records.before(self.directory, 'item-1', self.snapshot())['eligible'])
        row = records.load_execution(self.directory)[1]['items'][0]
        self.assertEqual(row['status'], 'unknown')
        self.assertIsNone(row['after'])
        with self.assertRaises(ValueError):
            records.before(self.directory, 'item-1', self.snapshot())
        self.assertEqual(records.finish(self.directory), {'unknown': 1})

    def test_timeout_without_readback_remains_unknown(self):
        self.started()
        records.before(self.directory, 'item-1', self.snapshot())
        outcome = records.record(self.directory, 'item-1', {'requestOutcome': 'uncertain', 'after': None, 'error': '模拟超时'})
        self.assertEqual(outcome['status'], 'unknown')

    def test_error_with_original_title_is_failed(self):
        self.started()
        records.before(self.directory, 'item-1', self.snapshot())
        outcome = records.record(self.directory, 'item-1', {'requestOutcome': 'error', 'after': self.snapshot(), 'error': '模拟写入失败'})
        self.assertEqual(outcome['status'], 'failed')

    def test_protected_change_after_write_stops_next_item(self):
        second = copy.deepcopy(self.proposal['items'][0])
        second.update(itemId='item-2', threadId='another-example-thread')
        self.proposal['items'].append(second)
        self.started()
        records.before(self.directory, 'item-1', self.snapshot())
        after = self.snapshot(self.proposal['items'][0]['newTitle'])
        after['protected']['updatedAt'] = '2026-09-08T12:00:00Z'
        outcome = records.record(self.directory, 'item-1', {'requestOutcome': 'success', 'after': after, 'error': None})
        self.assertTrue(outcome['stopRequired'])
        self.assertEqual(outcome['status'], 'unknown')
        with self.assertRaises(ValueError):
            records.before(self.directory, 'item-2', self.snapshot())
        self.assertEqual(records.finish(self.directory), {'unknown': 1, 'not_executed': 1})

    def test_verified_report_regeneration_preserves_core_and_limits(self):
        self.started()
        records.before(self.directory, 'item-1', self.snapshot())
        outcome = records.record(self.directory, 'item-1', {'requestOutcome': 'success', 'after': self.snapshot(self.proposal['items'][0]['newTitle']), 'error': None})
        self.assertEqual(outcome['status'], 'verified')
        records.finish(self.directory)
        baseline = {name: (self.directory / name).read_bytes() for name in ['proposal.json', 'execution.json']}
        first, second = Path(records.report(self.directory)), Path(records.report(self.directory))
        self.assertNotEqual(first, second)
        for name, data in baseline.items():
            self.assertEqual((self.directory / name).read_bytes(), data)
        text = first.read_text()
        self.assertIn('contentFingerprint', text)
        self.assertIn('260101', text)
        self.assertNotIn('344', text)
        self.assertIn('| 原名 |修改后名|\n| --- | --- |', text)
        for heading in ('# 改名记录（Rename Record）', '## 提案明细（Proposal Details）', '## 执行结果（Execution）'):
            self.assertIn('\n' + heading + '\n', '\n' + text)

    def test_proposal_only_report_cannot_claim_execution(self):
        records.prepare(self.directory, self.proposal)
        text = Path(records.report(self.directory)).read_text()
        self.assertIn('没有本批已批准或已执行', text)
        self.assertFalse((self.directory / 'execution.json').exists())

    def test_schema_and_json_reject_unknown_keys_and_duplicate_fields(self):
        changed = copy.deepcopy(self.proposal)
        changed['approved'] = True
        with self.assertRaises(ValueError):
            records.check_proposal(changed)
        path = self.root / 'duplicate.json'
        path.write_text('{"approved":true,"approved":false}')
        with self.assertRaises(ValueError):
            records.read(path)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            records.batch_path(self.root, '../outside')

    def test_review_escapes_title_markup(self):
        changed = self.proposal['items'][0]
        changed['oldTitle'] = changed['baseline']['title'] = '<script>\n[a](x)|text'
        records.prepare(self.directory, self.proposal)
        text = records.review(self.directory)
        self.assertIn('&lt;script&gt;', text)
        self.assertIn('\\|text', text)
        self.assertNotIn('<script>', text)


if __name__ == '__main__':
    unittest.main()
