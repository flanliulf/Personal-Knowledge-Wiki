#!/usr/bin/env python3
"""使用仓库固定版本的 last30days 对指定 X 样本进行研究。"""
import argparse
from collections import Counter
from datetime import date, datetime, timezone
from html import escape
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

PACKAGE = Path(__file__).resolve().parents[1]
MANIFEST = '60b8d6ba32e6c09ef44146a000db4e5fee007ab51ee8d7414d2e5df2fc001763'
PIN = 'd2c8949ad189929c0423d3d67018ae1326fc6a31'
PROFILE = re.compile(r'Default|Profile [0-9]+')
HANDLE = re.compile(r'[A-Za-z0-9_]{1,15}')
GOOD = {'success', 'no_results', 'no_relevant_evidence'}


class Failure(Exception):
    """适合显示的诊断。消息不得包含上游日志或认证材料。"""


def dependencies(explicit):
    root = Path(explicit).expanduser().resolve() if explicit else PACKAGE.parents[1] / 'X-last30days/X-last30days'
    manifest = root / 'UPSTREAM-MANIFEST.json'
    if not manifest.is_file() or hashlib.sha256(manifest.read_bytes()).hexdigest() != MANIFEST:
        raise Failure('请指定 KnowledgeWiki 收录的 last30days 4.1.0 包根，版本清单不匹配')
    entries = json.loads(manifest.read_text())['files']
    for item in entries:
        p = root / item['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            raise Failure('依赖文件与收录时的哈希不一致')
    return root


def select_profile(base, requested):
    if not base.is_dir():
        raise Failure('本机未找到 Arc 用户配置目录')
    choices = sorted(p.name for p in base.iterdir() if PROFILE.fullmatch(p.name) and p.is_dir() and not p.is_symlink())
    if requested is None and len(choices) == 1:
        requested = choices[0]
    if requested not in choices:
        raise Failure('请用 --profile 选择 Arc 配置。可选项为 ' + (', '.join(choices) or '无'))
    return requested


def preferences():
    """只消费授权、浏览器选择和导出目录这三个非机密选项。"""
    keys = ('BROWSER_CONSENT', 'FROM_BROWSER', 'LAST30DAYS_MEMORY_DIR')
    settings = {}
    config_dir = os.environ.get('LAST30DAYS_CONFIG_DIR', str(Path.home() / '.config/last30days'))
    if not config_dir:
        return {k: os.environ[k] for k in keys if k in os.environ}
    file = Path(config_dir) / '.env'
    if file.is_file():
        with file.open(encoding='utf-8') as stream:
            for line in stream:
                key, sep, value = line.strip().partition('=')
                if sep and key in keys:
                    settings[key] = value.strip().strip('"').strip("'")
    for key in keys:
        if key not in os.environ:
            continue
        stored = settings.get(key, '').strip().lower()
        if key == 'BROWSER_CONSENT' and key in settings and stored not in ('true', 'on', '1', 'yes'):
            continue
        if key == 'FROM_BROWSER' and stored == 'off':
            continue
        settings[key] = os.environ[key]
    return settings


def require_consent(settings, approved):
    consent = settings.get('BROWSER_CONSENT', '').lower()
    browser = settings.get('FROM_BROWSER', '').lower()
    if any(os.environ.get(k, '').lower() in ('true', 'on', '1', 'yes') for k in
           ('CI', 'LAST30DAYS_SCHEDULED_RUN', 'LAST30DAYS_DISABLE_BROWSER_COOKIES')):
        raise Failure('仅支持本机交互式授权检索')
    if ('BROWSER_CONSENT' in settings and consent not in ('true', 'on', '1', 'yes')) or browser == 'off':
        raise Failure('当前浏览器读取设置已关闭')
    if not approved and not (consent in ('true', 'yes', 'on', '1') and browser == 'arc'):
        raise Failure('需取得本次 Arc/X 读取授权后再传 --allow-arc')


def child_environment(scratch):
    # 配置隔离在引擎第一次 import 之前生效，仅传必要的运行环境。
    keys = ('PATH', 'HOME', 'TMPDIR', 'LANG', 'LC_ALL', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY',
            'http_proxy', 'https_proxy', 'no_proxy', 'SSL_CERT_FILE', 'SSL_CERT_DIR', 'NODE_EXTRA_CA_CERTS')
    env = {key: os.environ[key] for key in keys if key in os.environ}
    env.update(LAST30DAYS_CONFIG_DIR=str(scratch), LAST30DAYS_TRUST_PROJECT_CONFIG='0',
               LAST30DAYS_SKIP_KEYCHAIN='1', LAST30DAYS_LIBRARY_CONTEXT='off', FROM_BROWSER='arc',
               BROWSER_CONSENT='true', REDDIT_BROWSER_CONSENT='false', AGENTCOOKIE='off',
               LAST30DAYS_X_BACKEND='bird', INCLUDE_SOURCES='x', LAST30DAYS_MEMORY_DIR='',
               LAST30DAYS_NATIVE_SEARCH='1', PASSWORD_STORE_DIR=str(scratch / 'empty-pass'))
    if any(env.get(key) for key in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY')):
        env['NODE_USE_ENV_PROXY'] = '1'
    return env


def make_plan(topic, queries, mode):
    queries = list(dict.fromkeys(q.strip() for q in queries if q.strip())) or [topic]
    if len(queries) > 4 or (mode == 'hot' and len(queries) < 2):
        raise Failure('请给出最多四组查询，领域热点至少需要两组不同查询')
    return {'intent': 'breaking_news' if mode == 'hot' else 'concept', 'freshness_mode': 'strict_recent',
            'cluster_mode': 'story' if mode == 'hot' else 'none',
            'subqueries': [{'label': f'q{i+1}', 'search_query': q, 'ranking_query': topic,
                            'sources': ['x'], 'weight': 1.0 if i == 0 else 0.8} for i,q in enumerate(queries)]}


def execute(root, profile, env, args, payload, timeout):
    cmd = [sys.executable, '-I', '-B', str(PACKAGE / 'scripts/scoped_engine.py'), str(root), profile, *args]
    with subprocess.Popen(cmd, cwd=env['LAST30DAYS_CONFIG_DIR'], env=env, start_new_session=True,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        try:
            stdout, stderr = proc.communicate(input=payload, timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            if isinstance(exc, KeyboardInterrupt):
                raise
            raise Failure('timeout') from exc
    if proc.returncode or not stdout.strip():
        # 将可能含帖子文本或私有参数的上游日志压缩为有限类别。
        err = stderr.lower()
        for words, kind in [((b'429', b'rate limit'), 'rate_limited'),
                            ((b'401', b'not authenticated', b'no authentication'), 'auth_failed'),
                            ((b'timed out', b'timeout'), 'timeout'),
                            ((b'connection', b'unreachable'), 'network_error')]:
            if any(w in err for w in words):
                raise Failure(kind)
        raise Failure('engine_error (exit ' + str(proc.returncode) + ')')
    try:
        return json.loads(stdout)
    except (UnicodeError, ValueError):
        raise Failure('schema_error') from None


def public_fields(row, start, end, handles, excludes, language):
    if row['source'] != 'x':
        return None
    url = urlsplit(row['url'])
    match = re.fullmatch(r'/([A-Za-z0-9_]{1,15})/status/([0-9]{1,20})/?', url.path)
    if url.scheme != 'https' or url.netloc not in ('x.com', 'twitter.com', 'www.x.com', 'www.twitter.com') or not match:
        return None
    author, post_id = match.groups()
    stamp = row.get('published_at') or ''
    try:
        when = date.fromisoformat(stamp[:10])
    except ValueError:
        return None
    if not start <= when <= end or (handles and author.lower() not in handles):
        return None
    excerpt = row.get('body') or row.get('snippet') or row.get('title') or ''
    if not excerpt.strip() or any(word in excerpt.casefold() for word in excludes):
        return None
    lang = (row.get('metadata') or {}).get('lang')
    if language and lang and lang.split('-')[0].lower() != language:
        return None
    return {'id': post_id, 'url': f'https://x.com/{author}/status/{post_id}', 'author': author,
            'published_at': stamp, 'excerpt': excerpt[:500], 'language': lang or ('needs_review' if language else None),
            'engagement': {k: v for k, v in (row.get('engagement') or {}).items()
                           if k in ('likes', 'replies', 'reposts', 'quotes', 'views') and type(v) in (int, float)}}


def collect(raw, handles, excludes, language, exact=None):
    observed = raw.get('source_status', {}).get('x', {})
    state = observed.get('state')
    if state not in ('ok', 'partial', 'no-results'):
        return [], [], {'auth-failed':'auth_failed', 'rate-limited':'rate_limited', 'unreachable':'network_error',
                        'schema-drift':'schema_error', 'payment-required':'payment_required',
                        'timeout':'timeout', 'skipped-unconfigured':'session_unavailable'}.get(state, 'engine_error')
    window = (date.fromisoformat(raw['range_from']), date.fromisoformat(raw['range_to']))
    filters = (*window, handles, excludes, language)
    clusters = {cid: (c['cluster_id'], c['title']) for c in raw['clusters'] if c['score'] > 0 for cid in c['candidate_ids']}
    posts = {}
    for candidate in raw['ranked_candidates']:
        cid = candidate['candidate_id']
        if (cid not in clusters or candidate['final_score'] <= 0
                or 'entity-miss' in (candidate.get('explanation') or '').lower()):
            continue
        for row in candidate['source_items']:
            post = public_fields(row, *filters)
            if post:
                post.update(group_id=clusters[cid][0], group=clusters[cid][1], queries=candidate['subquery_labels'], origin='last30days/bird')
                posts.setdefault(post['id'], post)
    leads = {}
    if exact:
        for row in raw.get('items_by_source', {}).get('x', []):
            post = public_fields(row, *filters)
            if post and post['id'] not in posts and exact.casefold() in post['excerpt'].casefold():
                post.update(origin='last30days/bird-literal', matched=exact)
                leads.setdefault(post['id'], post)
    if state == 'partial' or observed.get('lane_failure_state'):
        outcome = 'partial'
    elif posts:
        outcome = 'success'
    elif state == 'no-results' and not raw.get('items_by_source', {}).get('x'):
        outcome = 'no_results'
    else:
        outcome = 'no_relevant_evidence'
    return list(posts.values()), list(leads.values()), outcome


def emit(root, values):
    if root is None:
        print(json.dumps(values, ensure_ascii=False))
        return
    root.mkdir(parents=True, exist_ok=True)
    label = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:12]
    dest = root / label
    with tempfile.TemporaryDirectory(dir=root, prefix='.research-') as temp:
        stage = Path(temp) / label
        stage.mkdir(mode=0o700)
        for name,obj in values.items():
            p = stage / name
            p.parent.mkdir(exist_ok=True)
            p.write_text(obj if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        stage.rename(dest)
    print(json.dumps({'status':values['run-manifest.json']['status'],'posts':len(values['posts.json']),
                      'report':str(dest/'report.md')},ensure_ascii=False))


def plain(value):
    value = ' '.join(value.split())
    return re.sub(r'([\\`*_{}\[\]()#!|~])', r'\\\1', escape(value, quote=False))


def run(a):
    settings = preferences()
    require_consent(settings, a.allow_arc)
    if platform.system() != 'Darwin' or sys.version_info < (3,12):
        raise Failure('需要 macOS 和 Python 3.12+')
    root = dependencies(a.engine_root)
    node = shutil.which('node')
    if not node or int(subprocess.check_output([node,'-v'], text=True).strip().lstrip('v').split('.')[0]) < 22:
        raise Failure('Bird 需要 Node.js 22+')
    profile = select_profile(Path.home()/'Library/Application Support/Arc/User Data', a.profile)
    topic = a.topic.strip()
    if not topic or a.days < 1 or a.limit < 1:
        raise Failure('主题、时间窗口与展示数必须有效')
    handles = {h.removeprefix('@').lower() for h in a.handle}
    if any(not HANDLE.fullmatch(h) for h in handles):
        raise Failure('账号格式无效')
    queries = list(a.query) or [topic]
    if a.exact:
        if not a.exact.strip() or any(c in a.exact for c in '"\n\r'):
            raise Failure('精确词应为单行非空文本，不能含双引号')
        queries.append(f'"{a.exact}"')
    plan = make_plan(topic, queries, a.mode)
    configured = settings.get('LAST30DAYS_MEMORY_DIR', str(Path.home()/'Documents/Last30Days'))
    directory = a.output_dir if a.output_dir is not None else configured
    dest = None if a.no_save or directory == '' else Path(directory).expanduser().resolve()
    if dest and (dest.is_relative_to(PACKAGE) or dest.is_relative_to(root)):
        raise Failure('成果目录必须位于 Skill 源包以外')
    raw = {}
    posts = []
    leads = []
    doctor = 'unknown'
    with tempfile.TemporaryDirectory(prefix='x-arc-run-') as tmp:
        env = child_environment(Path(tmp))
        if env.get('NODE_USE_ENV_PROXY') and '--use-env-proxy' not in subprocess.check_output([node, '--help'], text=True):
            raise Failure('当前代理配置需要支持 --use-env-proxy 的 Node.js')
        try:
            health = execute(root, profile, env, ['doctor','--cached','--json'], None, 65)
            doctor = (health.get('sources',{}).get('x') or {}).get('active_backend') or 'unverified'
            if doctor not in ('bird','unverified'):
                raise Failure('backend_mismatch')
            flags = ['--research-only','--search=x','--emit=json','--json-profile=raw','--save-dir=',
                     '--max-source-fetches='+str(len(plan['subqueries'])), '--days='+str(a.days),'--as-of='+a.as_of.isoformat(),'--plan=-']
            if a.language:
                for q in plan['subqueries']:
                    q['search_query'] += ' lang:'+a.language
            if handles:
                filt = '('+' OR '.join('from:'+h for h in sorted(handles))+')'
                for q in plan['subqueries']:
                    q['search_query'] += ' '+filt
            raw = execute(root, profile, env, [*flags,'--',topic], json.dumps(plan).encode(), 300)
            posts, leads, status = collect(raw, handles, [w.casefold() for w in a.exclude], a.language, a.exact)
        except Failure as exc:
            status = str(exc)
        except (TypeError, KeyError, ValueError, AttributeError):
            raw = {}
            status = 'schema_error'
    groups = {}
    for post in posts:
        groups.setdefault(post['group_id'], []).append(post)
    if a.mode == 'hot':
        groups = dict(sorted(groups.items(), key=lambda item: (-len({p['author'].lower() for p in item[1]}),-len(item[1]))))
    shown = (list(group[0] for group in groups.values()) +
             [p for group in groups.values() for p in group[1:]]) if a.mode == 'hot' else posts
    shown = shown[:a.limit]
    manifest = {'version':'1.0.0','upstream':PIN,'mode':a.mode,'topic':topic,'status':status,
                'doctor_backend':doctor,'days':a.days,'as_of':a.as_of.isoformat(),'range_from':raw.get('range_from'),
                'range_to':raw.get('range_to'),'sampled_at':datetime.now(timezone.utc).isoformat(),
                'eligible_posts':len(posts),'literal_leads':len(leads),'displayed':len(shown),'language_filter':a.language,
                'handles':sorted(handles),'exclude_terms':a.exclude}
    lines = ['# '+plain(topic), '', '本轮状态 `'+status+'`。领域内检索样本共 '+str(len(posts))+' 条合格帖子。','']
    returned = len(raw.get('items_by_source', {}).get('x', []))
    if manifest['range_from'] and manifest['range_to']:
        lines.append(f"检索窗口 {manifest['range_from']} 至 {manifest['range_to']}。X 返回 {returned} 条原始记录。")
    if a.mode == 'hot':
        lines += ['## 样本中的讨论（Discussion Groups）','']
        for group in list(groups.values())[:a.limit]:
            title = group[0]['group']
            counts = Counter(p['author'].lower() for p in group)
            stamps = sorted(p['published_at'][:10] for p in group)
            likes = [p['engagement']['likes'] for p in group if 'likes' in p['engagement']]
            metrics = f'，已观测点赞合计 {sum(likes)}' if likes else ''
            kind = '多账号讨论' if len(counts) >= 2 else '单账号线索'
            lines.append(f"- {kind} · {plain(title)}（{len(group)} 帖，{len(counts)} 个账号，"
                         f"{stamps[0]} 至 {stamps[-1]}{metrics}）。[代表帖]({group[0]['url']})")
    lines += ['','## 代表帖子（Posts）','']
    for post in shown:
        excerpt = ' '.join(post['excerpt'].split())[:220]
        lines.append(f"- {post['published_at'][:10]} · {plain(excerpt)} [@{post['author']}]({post['url']})")
    if a.exact:
        lines.extend(['', '## 精确词线索（Literal Matches）', '',
                      f'有 {len(leads)} 条额外帖子命中精确词，需核对原帖。'])
        for post in leads[:a.limit]:
            lines.append(f"- {post['published_at'][:10]} · {plain(post['excerpt'][:220])} [原帖]({post['url']})")
    emit(dest, {'literal-leads.json': leads, 'report.md':'\n'.join(lines)+'\n','posts.json':posts,'query-plan.json':plan,
                'run-manifest.json':manifest,'engine/coverage.json':{'x_state':raw.get('source_status',{}).get('x',{}).get('state'),
                'returned':len(raw.get('items_by_source',{}).get('x',[])), 'clusters':len(raw.get('clusters',[]))}})
    return 0 if status in GOOD else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--topic',required=True)
    p.add_argument('--mode',choices=('topic','hot'),default='topic')
    p.add_argument('--query',action='append',default=[])
    p.add_argument('--exact', help='另加一组带引号的检索词，分别列出字面命中的待核验帖子')
    p.add_argument('--handle',action='append',default=[])
    p.add_argument('--exclude',action='append',default=[])
    p.add_argument('--language',type=lambda v: v if re.fullmatch(r'[a-z]{2,3}',v) else p.error('语言应为小写语言代码'))
    p.add_argument('--limit',type=int,default=10)
    p.add_argument('--days',type=int,default=30)
    p.add_argument('--as-of',type=date.fromisoformat,default=date.today())
    p.add_argument('--engine-root')
    p.add_argument('--profile')
    p.add_argument('--allow-arc',action='store_true',help='仅用于本次已明确授权的 Arc/X 检索')
    output = p.add_mutually_exclusive_group()
    output.add_argument('--output-dir')
    output.add_argument('--no-save',action='store_true')
    try:
        return run(p.parse_args())
    except (Failure, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
