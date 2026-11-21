import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_research as research


def sample():
    post = {'source': 'x', 'body': 'project reader', 'published_at': '2026-11-06',
            'url': 'https://x.com/reader/status/123?s=1', 'engagement': {'likes': 0}}
    return {'range_from': '2026-10-22', 'range_to': '2026-11-21',
            'source_status': {'x': {'state': 'ok'}}, 'items_by_source': {'x': [post]},
            'clusters': [{'cluster_id': 'g1', 'candidate_ids': ['c1'], 'title': 'reader', 'score': 1}],
            'ranked_candidates': [{'candidate_id': 'c1', 'subquery_labels': ['q1'], 'final_score': 1,
                                   'source_items': [post, post]}]}


def collect(raw, handles=(), excludes=(), language=None, exact=None):
    return research.collect(raw, handles, excludes, language, exact)


class ResearchTests(unittest.TestCase):
    def test_distinct_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / 'Default').mkdir()
            (base / 'Profile 2').symlink_to(base / 'Default')
            self.assertEqual(research.select_profile(base, None), 'Default')
            (base / 'Profile 1').mkdir()
            with self.assertRaises(research.Failure):
                research.select_profile(base, None)
            for name in ('../Default', 'Profile 2'):
                with self.assertRaises(research.Failure):
                    research.select_profile(base, name)

    def test_consent(self):
        with patch.dict(os.environ, {}, clear=True):
            for settings in ({'BROWSER_CONSENT': 'false'}, {'FROM_BROWSER': 'off'}, {'BROWSER_CONSENT': 'invalid'}):
                with self.assertRaises(research.Failure):
                    research.require_consent(settings, True)
            with self.assertRaises(research.Failure):
                research.require_consent({}, False)
            research.require_consent({'BROWSER_CONSENT': 'true', 'FROM_BROWSER': 'arc'}, False)
            research.require_consent({}, True)

    def test_saved_refusal(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
                os.environ, {'LAST30DAYS_CONFIG_DIR': temp, 'BROWSER_CONSENT': 'true'}, clear=True):
            (Path(temp) / '.env').write_text('BROWSER_CONSENT=false\n')
            with self.assertRaises(research.Failure):
                research.require_consent(research.preferences(), True)

    def test_provider_isolation(self):
        with patch.dict(os.environ, {'X_BEARER_TOKEN': 'private-test-value', 'AUTH_TOKEN': 'private-test-value',
                                     'HTTPS_PROXY': 'https://example.invalid'}, clear=True):
            env = research.child_environment(Path('sandbox'))
            self.assertNotIn('private-test-value', env.values())
            self.assertEqual((env['LAST30DAYS_X_BACKEND'], env['INCLUDE_SOURCES'], env['NODE_USE_ENV_PROXY']),
                             ('bird', 'x', '1'))

    def test_dependency_mismatch(self):
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(research.Failure):
            research.dependencies(temp)

    def test_topic_and_hot_plan(self):
        self.assertEqual(research.make_plan('a', ['a', 'a'], 'topic')['subqueries'][0]['sources'], ['x'])
        self.assertEqual(len(research.make_plan('a', ['a', 'b'], 'hot')['subqueries']), 2)
        with self.assertRaises(research.Failure):
            research.make_plan('a', ['a', 'a'], 'hot')

    def test_evidence(self):
        posts, leads, state = collect(sample(), exact='reader')
        self.assertEqual((len(posts), leads, state), (1, [], 'success'))
        self.assertEqual(posts[0]['url'], 'https://x.com/reader/status/123')
        self.assertEqual(posts[0]['engagement'], {'likes': 0})

    def test_failure_types(self):
        for state, expected in [('auth-failed', 'auth_failed'), ('rate-limited', 'rate_limited'),
                                ('unreachable', 'network_error'), ('schema-drift', 'schema_error')]:
            with self.subTest(state=state):
                self.assertEqual(collect({'source_status': {'x': {'state': state}}}), ([], [], expected))

    def test_empty_and_partial(self):
        raw = sample()
        raw['source_status']['x']['state'] = 'partial'
        self.assertEqual(collect(raw)[2], 'partial')
        raw['source_status']['x']['state'] = 'no-results'
        raw['ranked_candidates'].clear()
        raw['items_by_source']['x'].clear()
        self.assertEqual(collect(raw)[2], 'no_results')

    def test_exact_lead_after_rejection(self):
        for rejection in ('entity-miss', 'zero-score'):
            raw = sample()
            if rejection == 'entity-miss':
                raw['ranked_candidates'][0]['explanation'] = rejection
            else:
                raw['clusters'][0]['score'] = 0
            posts, leads, state = collect(raw, exact='READER')
            self.assertEqual((posts, len(leads), state), ([], 1, 'no_relevant_evidence'))

    def test_invalid_dates_and_urls(self):
        for field, value in [('published_at', ''), ('published_at', '2025-11-06'),
                             ('url', 'https://x.com.example.invalid/reader/status/123')]:
            raw = sample()
            raw['items_by_source']['x'][0][field] = value
            self.assertEqual(collect(raw, exact='reader')[:2], ([], []))

    def test_direction_filters(self):
        self.assertFalse(collect(sample(), handles={'another'})[0])
        self.assertFalse(collect(sample(), excludes=['reader'])[0])
        self.assertEqual(collect(sample(), language='zh')[0][0]['language'], 'needs_review')
        raw = sample()
        raw['items_by_source']['x'][0]['metadata'] = {'lang': 'en'}
        self.assertFalse(collect(raw, language='zh')[0])

    def test_atomic_save_and_stdout(self):
        values = {'posts.json': [], 'run-manifest.json': {'status': 'no_results'}, 'report.md': '正文'}
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            root = Path(temp)
            research.emit(root, values)
            research.emit(root, values)
            self.assertEqual([p.read_text() for p in root.glob('*/report.md')], ['正文', '正文'])
            with redirect_stdout(io.StringIO()) as out:
                research.emit(None, values)
            self.assertEqual(json.loads(out.getvalue()), values)

    def test_escape(self):
        text = research.plain('[link](https://example.invalid)\n<img>')
        self.assertNotIn('[link](', text)
        self.assertNotIn('<img>', text)
