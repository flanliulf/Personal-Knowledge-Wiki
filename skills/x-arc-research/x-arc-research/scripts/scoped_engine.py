"""内部进程。将固定上游引擎的选源范围限制在用户选择的 Arc 配置。"""
import os
from pathlib import Path
import runpy
import sys


def main():
    engine_root, profile, *args = sys.argv[1:]
    scripts = Path(engine_root) / 'scripts'
    sys.path.insert(0, str(scripts))
    from lib import chrome_cookies, env

    # 原有 Bird 后端负责认证，适配层只收窄它的站点和配置选择范围。
    if os.environ.get('FROM_BROWSER') != 'arc' or os.environ.get('BROWSER_CONSENT') != 'true':
        raise SystemExit(2)
    base, _ = chrome_cookies.CHROMIUM_BROWSER_PROFILES['arc']
    selected = base / profile
    if selected.resolve().parent != base.resolve() or not selected.is_dir() or selected.is_symlink():
        raise SystemExit(2)
    env.COOKIE_DOMAINS = {'x': env.COOKIE_DOMAINS['x']}
    env.KEYCHAIN_KEYS = ()
    env.x_extras_enabled = lambda config: False
    # 原生路径解析器只在选定配置内查找，禁用跨配置回退。
    def selected_paths(directory, denials=None):
        if directory != base:
            return []
        result = chrome_cookies._profile_cookie_db(selected, denials)
        if result is None or not result.resolve().is_relative_to(selected):
            return []
        return [result]
    chrome_cookies._find_all_chromium_cookies_dbs = selected_paths
    if args and args[0] == 'doctor':
        from lib import doctor
        doctor._probeable_sources = lambda: ()
    sys.argv = [str(scripts / 'last30days.py'), *args]
    runpy.run_path(sys.argv[0], run_name='__main__')


if __name__ == '__main__':
    main()
