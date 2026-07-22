"""github-dorks integration - search a GitHub user, org, or repo against a list
of "dorks" that reveal leaked secrets (keys, tokens, credentials).

The upstream project (github.com/techgaun/github-dorks) is a source script with
a bundled dork list and is not on PyPI, so it is vendored on demand under
``thirdparty/github-dorks`` and run with this interpreter.  A GitHub token
(``GH_TOKEN``) is strongly recommended - the GitHub search API is heavily
rate-limited without one.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'thirdparty' / 'github-dorks'
REPO = 'https://github.com/techgaun/github-dorks'
SCRIPT = SRC / 'github-dork.py'
DORK_FILE = SRC / 'github-dorks.txt'
DEPS = ['github3.py', 'feedparser']
_IMPORT_NAMES = ('github3', 'feedparser')


def is_installed():
    return SCRIPT.is_file()


def ready():
    if not SCRIPT.is_file():
        return False, 'not installed (select it once to set up)'
    import importlib.util
    missing = [name for name in _IMPORT_NAMES
               if importlib.util.find_spec(name) is None]
    if missing:
        return False, 'missing deps: %s' % ', '.join(missing)
    return True, 'ready'


def install():
    """Clone the project (once) and install its two dependencies."""
    if not SRC.is_dir():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        print('[install] cloning github-dorks ...', flush=True)
        subprocess.check_call(['git', 'clone', '--depth', '1', REPO, str(SRC)])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade']
                          + DEPS)


def run(target, is_repo=False, token=None, out_dir=None):
    if not SCRIPT.is_file():
        raise RuntimeError('github-dorks is not installed')
    env = os.environ.copy()
    if token:
        env['GH_TOKEN'] = token
    command = [sys.executable, str(SCRIPT), ('-r' if is_repo else '-u'), target,
               '-d', str(DORK_FILE)]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe = target.replace('/', '_')
        command.extend(['-o', os.path.join(out_dir, 'github_dorks_%s.csv' % safe)])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command, env=env)
