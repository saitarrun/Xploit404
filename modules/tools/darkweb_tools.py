#!/usr/bin/env python3
"""Install, verify, and launch dark-web tools in the terminal.

The upstream projects intentionally live under ``thirdparty/darkweb`` and are
ignored by Git.  This module keeps the reproducible install metadata in the
main repository while giving ``menu.py`` one safe, shell-free launch path.
"""

import html
import os
import platform
import shlex
import shutil
import socket
import subprocess
import time
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / 'thirdparty' / 'darkweb'
BIN_ROOT = ROOT / 'bin' / 'darkweb'
PROXYCHAINS_CONFIG = ROOT / 'config' / 'proxychains-darkweb.conf'
ONIONSEARCH_ROOT = ROOT / 'thirdparty' / 'onionsearch'
ONIONSEARCH_PACKAGES = [
    'requests', 'PySocks', 'beautifulsoup4', 'html5lib', 'tqdm', 'termcolor',
]


TOOLS = {
    'katana': {
        'name': 'Katana',
        'repo': 'https://github.com/adnane-X-tebbaa/Katana',
        'directory': 'Katana',
        'kind': 'python',
        # Katana imports urlparse from urllib.request in Tor mode.  Populate
        # those legacy names before executing its unchanged upstream script.
        'entry': [
            '-c',
            'from urllib import parse, request; '
            'request.urlparse=parse.urlparse; request.urljoin=parse.urljoin; '
            'import runpy; runpy.run_path("kds.py", run_name="__main__")',
        ],
        'default_args': ['--help'],
        'tor': False,
        'packages': [
            'requests', 'google', 'termcolor', 'colorama', 'bs4',
            'StringGenerator', 'pysocks', 'beautifulsoup4', 'Twisted',
            'txtorcon', 'aiohttp', 'aiodns', 'maxminddb',
        ],
        'no_deps_packages': ['proxybroker'],
    },
    'darkdump': {
        'name': 'Darkdump',
        'repo': 'https://github.com/josh0xA/darkdump',
        'directory': 'darkdump',
        'kind': 'python',
        'entry': ['darkdump.py'],
        'default_args': ['--help'],
        'tor': False,
        'requirements': 'requirements.txt',
    },
    'darkus': {
        'name': 'Darkus',
        'repo': 'https://github.com/Lucksi/Darkus',
        'directory': 'Darkus',
        'kind': 'python',
        # Bypass the upstream Linux-only `sudo service tor` preflight.  The
        # launcher performs a portable Tor check before invoking Engine.Main.
        'entry': ['-c', 'from Main import Engine; Engine.Main("Res")'],
        'verify_entry': ['-c', 'import Main; print("Darkus import OK")'],
        'default_args': [],
        'tor': True,
        'requirements': 'requirements.txt',
    },
    'onioff': {
        'name': 'Onioff',
        'repo': 'https://github.com/k4m4/onioff',
        'directory': 'onioff',
        'kind': 'python',
        'entry': ['onioff.py'],
        'default_args': ['--help'],
        'tor': True,
        'requirements': 'requirements.txt',
    },
    'onionscan': {
        'name': 'Onionscan',
        'repo': 'https://github.com/s-rah/onionscan',
        'directory': 'onionscan',
        'kind': 'go',
        'binary': 'onionscan',
        'default_args': ['--help'],
        'tor': True,
    },
    'onion-nmap': {
        'name': 'Onion-nmap',
        'repo': 'https://github.com/milesrichardson/docker-onion-nmap',
        'directory': 'onion-nmap',
        'kind': 'system',
        'default_args': ['--help'],
        'tor': True,
        'system_packages': [
            ('nmap', 'nmap'),
            ('proxychains4', 'proxychains-ng'),
        ],
    },
    'torbot': {
        'name': 'TorBot',
        'repo': 'https://github.com/DedSecInside/TorBot',
        'directory': 'TorBot',
        'kind': 'python',
        'entry': ['main.py'],
        'default_args': ['--help'],
        'tor': True,
        'requirements': 'requirements.txt',
        'editable': True,
    },
    'torcrawl': {
        'name': 'TorCrawl',
        'repo': 'https://github.com/MikeMeliz/TorCrawl.py',
        'directory': 'TorCrawl',
        'kind': 'python',
        'entry': ['torcrawl.py'],
        'default_args': ['--help'],
        'tor': True,
        'requirements': 'requirements.txt',
        'editable': True,
    },
    'vigilant-onion': {
        'name': 'VigilantOnion',
        'repo': 'https://github.com/andreyglauzer/VigilantOnion',
        'directory': 'VigilantOnion',
        'kind': 'python',
        'entry': ['observer.py'],
        'default_args': ['--help'],
        'tor': True,
        # The upstream pins predate Python 3.11.  These are API-compatible
        # current packages with wheels for supported platforms.
        'packages': [
            'beautifulsoup4', 'cachetools', 'certifi', 'chardet',
            'configparser', 'gunicorn', 'idna', 'lxml', 'pyasn1',
            'pyasn1-modules', 'pytz', 'PyYAML', 'requests', 'rsa', 'six',
            'uritemplate', 'urllib3', 'yara-python',
        ],
    },
    'onion-ingestor': {
        'name': 'OnionIngestor',
        'repo': 'https://github.com/danieleperera/OnionIngestor',
        'directory': 'OnionIngestor',
        'kind': 'python',
        'entry': ['-m', 'onioningestor'],
        'default_args': ['--help'],
        'tor': True,
        'packages': [
            'beautifulsoup4', 'certifi', 'chardet', 'click<8',
            'elasticsearch<8', 'langdetect', 'lxml', 'PySocks', 'PyYAML',
            'requests', 'schedule', 'selenium<4', 'six', 'stem',
            'urllib3<2', 'xlrd',
        ],
        'remove_packages': ['elastic-transport'],
        'editable': True,
        'note': 'Long-running ingestion uses onioningestor.yml and optional external data services.',
    },
    'darc': {
        'name': 'Darc',
        'repo': 'https://github.com/JarryShaw/darc',
        'directory': 'darc',
        'kind': 'python',
        'entry': ['-m', 'darc'],
        'default_args': ['--help'],
        'tor': True,
        'editable': True,
        'system_packages': [('libmagic', 'libmagic')],
        'env': {
            'TOR_PASS': '',
            'DARC_TOR': '0',
            'DARC_I2P': '0',
            'DARC_FREENET': '0',
            'DARC_ZERONET': '0',
            'DARC_REDIS': '0',
            'SAVE_DB': '0',
        },
        'note': 'Runs with external Tor and local storage defaults; advanced deployments may add Redis/database services.',
    },
    'midnight-sea': {
        'name': 'Midnight Sea',
        'repo': 'https://github.com/RicYaben/midnight_sea',
        'directory': 'midnight_sea',
        'kind': 'python',
        'python': '3.10',
        'entry': ['-m', 'crawler'],
        'default_args': ['--help'],
        'tor': True,
        'editable_paths': [
            'lib', 'workspaces/crawler', 'workspaces/scraper',
            'workspaces/storage',
        ],
        'note': 'The crawler launches locally; full marketplace workflows also require its storage/scraper services.',
    },
    'pryingdeep': {
        'name': 'Prying Deep',
        'repo': 'https://github.com/iudicium/pryingdeep',
        'directory': 'pryingdeep',
        'kind': 'go',
        'binary': 'pryingdeep',
        'go_package': './cmd/pryingdeep',
        'default_args': ['--help'],
        'tor': True,
        'note': 'Crawling requires a configured pryingdeep.yaml and PostgreSQL.',
    },
    'deepdarkcti': {
        'name': 'DeepDarkCTI',
        'repo': 'https://github.com/fastfire/deepdarkCTI',
        'directory': 'deepdarkCTI',
        'kind': 'catalog',
    },
}


ENTRY_TO_SLUG = {spec['name']: slug for slug, spec in TOOLS.items()}


# Categories reference CLI slugs, so names and repository URLs stay canonical
# in TOOLS.  Tuples are terminal-rendered sites or a bundled launcher entry.
_CATEGORY_ENTRIES = [
    ('Search Engines', [
        'katana',
        ('OnionSearch', ['https://github.com/megadose/OnionSearch']),
        'darkdump',
        ('Ahmia', ['https://ahmia.fi']),
        'darkus',
        ('Onion Search Engine', [
            'https://onionsearchengine.com/',
            'http://37djtvjcpiprohcrlyvlhfil45kdlfizsyvilqskgvdrafn5mocz4cid.onion/',
        ]),
        ('IACA Dark Web Tools', ['https://iaca-darkweb-tools.com/']),
    ]),
    ('Get Onion Links', [
        ('Tor66', [
            'https://tor66.org/',
            'https://tor66.io/',
            'http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/fresh',
        ]),
        ('TorNode', ['http://tornode3tnrtzgqwd3vmxdumucddqfd6zk7icu4wzdwxo5c3zn2xqfqd.onion']),
    ]),
    ('Scan Onion Links', ['onionscan', 'onioff', 'onion-nmap']),
    ('Crawl Dark Web', [
        'torbot', 'torcrawl', 'vigilant-onion', 'onion-ingestor', 'darc',
        'midnight-sea', 'pryingdeep',
    ]),
    ('Miscellaneous', ['deepdarkcti']),
]


def darkweb_categories():
    """Return menu-ready categories derived from the canonical tool specs."""
    categories = []
    for label, entries in _CATEGORY_ENTRIES:
        tools = []
        for entry in entries:
            if isinstance(entry, str):
                spec = TOOLS[entry]
                tools.append((spec['name'], [spec['repo']]))
            else:
                tools.append(entry)
        categories.append((label, tools))
    return categories


def website_entries():
    """Return non-CLI menu entries for availability verification."""
    entries = []
    for _, category_entries in _CATEGORY_ENTRIES:
        for entry in category_entries:
            if not isinstance(entry, str) and entry[0] != 'OnionSearch':
                entries.append(entry)
    return entries


def source_dir(spec):
    return SOURCE_ROOT / spec['directory']


def venv_python(spec):
    directory = source_dir(spec) / '.venv'
    windows = directory / 'Scripts' / 'python.exe'
    return windows if windows.is_file() else directory / 'bin' / 'python'


def bundled_onionsearch_python():
    directory = ONIONSEARCH_ROOT / '.venv'
    windows = directory / 'Scripts' / 'python.exe'
    return windows if windows.is_file() else directory / 'bin' / 'python'


def find_python(version='3.11'):
    candidates = ['python%s' % version]
    if platform.system() == 'Darwin':
        candidates.append('/opt/homebrew/bin/python%s' % version)
    candidates.extend(['python3', 'python'])
    wanted = tuple(int(part) for part in version.split('.'))
    for candidate in candidates:
        path = shutil.which(candidate) if '/' not in candidate else candidate
        if not path or not os.path.isfile(path):
            continue
        result = subprocess.run(
            [path, '-c', 'import sys; print(sys.version_info[0], sys.version_info[1])'],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            found = tuple(int(part) for part in result.stdout.split())
            compatible_default = version == '3.11' and (3, 9) <= found <= (3, 12)
            if found == wanted or compatible_default:
                return path
    raise RuntimeError('Python %s is required but was not found.' % version)


def _run_checked(command, cwd=None, env=None):
    print('[install] %s' % ' '.join(shlex.quote(str(part)) for part in command), flush=True)
    subprocess.check_call([str(part) for part in command], cwd=cwd, env=env)


def _clone(spec):
    directory = source_dir(spec)
    if directory.is_dir():
        return directory
    directory.parent.mkdir(parents=True, exist_ok=True)
    _run_checked(['git', 'clone', '--depth', '1', spec['repo'], str(directory)])
    return directory


def _ensure_homebrew_package(command, formula):
    if formula == 'libmagic':
        candidates = [
            Path('/opt/homebrew/opt/libmagic/lib/libmagic.dylib'),
            Path('/usr/local/opt/libmagic/lib/libmagic.dylib'),
            Path('/usr/lib/libmagic.so'),
        ]
        if any(path.exists() for path in candidates):
            return
    if shutil.which(command):
        return
    brew = shutil.which('brew')
    if not brew:
        raise RuntimeError('%s is missing; install package %s first.' % (command, formula))
    _run_checked([brew, 'install', formula])


def _install_python(spec):
    directory = _clone(spec)
    interpreter = find_python(spec.get('python', '3.11'))
    python = venv_python(spec)
    if not python.is_file():
        _run_checked([interpreter, '-m', 'venv', str(directory / '.venv')])
    has_pip = subprocess.run(
        [str(python), '-m', 'pip', '--version'],
        capture_output=True, text=True,
    ).returncode == 0
    if not has_pip:
        _run_checked([str(python), '-m', 'ensurepip', '--upgrade'])
    _run_checked([str(python), '-m', 'pip', 'install', '--upgrade', 'pip'])
    env = os.environ.copy()
    env['SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL'] = 'True'
    if spec.get('requirements'):
        _run_checked(
            [str(python), '-m', 'pip', 'install', '-r', spec['requirements']],
            cwd=directory, env=env,
        )
    if spec.get('remove_packages'):
        _run_checked(
            [str(python), '-m', 'pip', 'uninstall', '-y'] + spec['remove_packages'],
            cwd=directory, env=env,
        )
    if spec.get('packages'):
        _run_checked([str(python), '-m', 'pip', 'install'] + spec['packages'], cwd=directory, env=env)
    if spec.get('no_deps_packages'):
        _run_checked(
            [str(python), '-m', 'pip', 'install', '--no-deps'] + spec['no_deps_packages'],
            cwd=directory, env=env,
        )
    editable_paths = spec.get('editable_paths', [])
    if spec.get('editable'):
        editable_paths = editable_paths + ['.']
    if editable_paths:
        command = [str(python), '-m', 'pip', 'install']
        for path in editable_paths:
            command.extend(['-e', path])
        _run_checked(command, cwd=directory, env=env)


def install_bundled_onionsearch():
    """Create the isolated interpreter used by the bundled OnionSearch."""
    if not (ONIONSEARCH_ROOT / 'core.py').is_file():
        raise RuntimeError('Bundled OnionSearch source is missing.')
    python = bundled_onionsearch_python()
    if not python.is_file():
        _run_checked([
            find_python(), '-m', 'venv', str(ONIONSEARCH_ROOT / '.venv'),
        ])
    _run_checked([str(python), '-m', 'pip', 'install', '--upgrade', 'pip'])
    _run_checked([str(python), '-m', 'pip', 'install'] + ONIONSEARCH_PACKAGES)
    ok, detail = verify_bundled_onionsearch()
    if not ok:
        raise RuntimeError('OnionSearch installation failed: %s' % detail)
    print('[ok] OnionSearch: %s' % detail)


def _install_go(spec):
    directory = _clone(spec)
    if not shutil.which('go'):
        raise RuntimeError('Go is required to build %s.' % spec['name'])
    BIN_ROOT.mkdir(parents=True, exist_ok=True)
    if spec['binary'] == 'onionscan' and not (directory / 'go.mod').is_file():
        _run_checked(['go', 'mod', 'init', 'github.com/s-rah/onionscan'], cwd=directory)
        _run_checked(['go', 'mod', 'tidy'], cwd=directory)
    package = spec.get('go_package', '.')
    _run_checked(['go', 'build', '-o', str(BIN_ROOT / spec['binary']), package], cwd=directory)


def install_tool(slug):
    spec = TOOLS[slug]
    if spec.get('tor'):
        _ensure_homebrew_package('tor', 'tor')
    for command, formula in spec.get('system_packages', []):
        _ensure_homebrew_package(command, formula)
    if spec['kind'] == 'python':
        _install_python(spec)
    elif spec['kind'] == 'go':
        _install_go(spec)
    elif spec['kind'] == 'system':
        _clone(spec)
    elif spec['kind'] == 'catalog':
        _clone(spec)
    else:
        raise RuntimeError('Unsupported tool kind: %s' % spec['kind'])
    if spec.get('tor') and not ensure_tor():
        raise RuntimeError('Tor installed but its SOCKS proxy did not start.')
    ok, detail = verify_tool(slug)
    if not ok:
        raise RuntimeError('%s installed but verification failed: %s' % (spec['name'], detail))
    print('[ok] %s: %s' % (spec['name'], detail))


def is_installed(slug):
    spec = TOOLS[slug]
    if spec['kind'] == 'python':
        return venv_python(spec).is_file()
    if spec['kind'] == 'go':
        return (BIN_ROOT / spec['binary']).is_file()
    if spec['kind'] == 'system':
        return all(shutil.which(command) for command in ('tor', 'nmap', 'proxychains4'))
    return source_dir(spec).is_dir()


def _command_for(spec, verify=False):
    directory = source_dir(spec)
    env = os.environ.copy()
    env.update(spec.get('env', {}))
    if spec['name'] == 'Darc' and platform.system() == 'Darwin':
        libmagic = '/opt/homebrew/opt/libmagic/lib'
        current = env.get('DYLD_LIBRARY_PATH')
        env['DYLD_LIBRARY_PATH'] = libmagic if not current else libmagic + os.pathsep + current
    if spec['kind'] == 'python':
        entry = spec.get('verify_entry') if verify else None
        entry = entry or spec['entry']
        return [str(venv_python(spec))] + entry, directory, env
    if spec['kind'] == 'go':
        return [str(BIN_ROOT / spec['binary'])], directory, env
    if spec['kind'] == 'system':
        command = [
            shutil.which('proxychains4') or 'proxychains4', '-q', '-f',
            str(PROXYCHAINS_CONFIG), shutil.which('nmap') or 'nmap',
        ]
        if not verify:
            command.extend(['-sT', '-Pn', '-n'])
        return command, ROOT, env
    raise RuntimeError('%s is not executable.' % spec['name'])


def verify_tool(slug):
    spec = TOOLS[slug]
    if not is_installed(slug):
        return False, 'not installed'
    if spec['kind'] == 'catalog':
        markdown = list(source_dir(spec).glob('*.md'))
        return (bool(markdown), '%d Markdown files available' % len(markdown))
    if spec.get('tor') and not tor_ready():
        return False, 'Tor SOCKS proxy is not running on 127.0.0.1:9050'
    command, cwd, env = _command_for(spec, verify=True)
    if spec['kind'] == 'system':
        command.append('--version')
    elif not spec.get('verify_entry'):
        command.extend(['--help'])
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True,
            timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout + '\n' + result.stderr).strip().splitlines()
    detail = output[-1] if output else 'exit code %d' % result.returncode
    return result.returncode == 0, detail


def tor_ready(host='127.0.0.1', port=9050):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def ensure_tor():
    if tor_ready():
        return True
    print('[tor] SOCKS proxy is not running; starting Tor...')
    brew = shutil.which('brew')
    tor = shutil.which('tor')
    if brew and platform.system() == 'Darwin':
        subprocess.run([brew, 'services', 'start', 'tor'], check=False)
    elif tor:
        data_dir = ROOT / 'output' / 'tor-runtime'
        data_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [tor, '--RunAsDaemon', '1', '--SocksPort', '9050',
             '--DataDirectory', str(data_dir)],
            check=False,
        )
    else:
        print('[error] Tor is not installed.')
        return False
    for _ in range(45):
        if tor_ready():
            print('[tor] SOCKS proxy is ready on 127.0.0.1:9050.')
            return True
        time.sleep(1)
    print('[error] Tor did not become ready within 45 seconds.')
    return False


def run_tool(slug, input_func=input):
    spec = TOOLS[slug]
    if not ensure_installed(slug, input_func):
        return 1
    if spec.get('tor') and not ensure_tor():
        return 1
    if spec.get('note'):
        print('[note] %s' % spec['note'])
    command, cwd, env = _command_for(spec)
    default = ' '.join(spec.get('default_args', []))
    prompt = 'Arguments'
    if default:
        prompt += ' [%s]' % default
    raw = input_func('%s: ' % prompt).strip()
    try:
        arguments = shlex.split(raw) if raw else list(spec.get('default_args', []))
    except ValueError as exc:
        print('[error] Invalid arguments: %s' % exc)
        return 2
    print('[run] %s' % ' '.join(shlex.quote(part) for part in command + arguments), flush=True)
    return subprocess.call(command + arguments, cwd=cwd, env=env)


class _TextExtractor(HTMLParser):
    _HIDDEN_TAGS = {'script', 'style', 'template', 'noscript'}

    def __init__(self):
        HTMLParser.__init__(self)
        self.text = []
        self.links = []
        self._hidden_depth = 0

    def handle_data(self, data):
        if self._hidden_depth:
            return
        value = ' '.join(data.split())
        if value:
            self.text.append(value)

    def handle_starttag(self, tag, attrs):
        if tag in self._HIDDEN_TAGS:
            self._hidden_depth += 1
            return
        if tag == 'a':
            href = dict(attrs).get('href')
            if href and href not in self.links:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in self._HIDDEN_TAGS and self._hidden_depth:
            self._hidden_depth -= 1


def _fetch_response(url, timeout=45, force_tor=False):
    curl = shutil.which('curl')
    if not curl:
        return None, None, 'curl is required for terminal site access.'
    command = [
        curl, '--silent', '--show-error', '--location', '--max-time',
        str(timeout), '--write-out', '\n__OSINT_HTTP_STATUS__:%{http_code}',
    ]
    if force_tor or '.onion' in url:
        command.extend(['--socks5-hostname', '127.0.0.1:9050'])
    command.append(url)
    result = subprocess.run(command, capture_output=True, text=True)
    marker = '\n__OSINT_HTTP_STATUS__:'
    body, separator, status_text = result.stdout.rpartition(marker)
    try:
        status = int(status_text.strip()) if separator else 0
    except ValueError:
        status = 0
    error = result.stderr.strip()
    if result.returncode != 0:
        return body, status, error or 'curl exited with code %d' % result.returncode
    if status >= 400 or status == 0:
        return body, status, 'HTTP %s' % (status or 'status unavailable')
    blocked_markers = (
        'sorry, you have been blocked',
        'error 522',
        'web server is returning an unknown error',
        'access denied | cloudflare',
    )
    lowered = body.casefold()
    blocked = next((value for value in blocked_markers if value in lowered), None)
    if blocked:
        return body, status, 'blocked/error page detected: %s' % blocked
    return body, status, None


def terminal_fetch(url):
    if '.onion' in url and not ensure_tor():
        return 1
    print('[fetch] %s' % url)
    body, status, error = _fetch_response(url)
    if error:
        print('[error] %s (%s)' % (error, url))
        return 1
    parser = _TextExtractor()
    parser.feed(body)
    lines = []
    for value in parser.text:
        value = html.unescape(value)
        if value not in lines:
            lines.append(value)
    print('\n'.join(lines[:200]))
    if parser.links:
        print('\nLinks:')
        print('\n'.join('  %s' % link for link in parser.links[:80]))
    return 0


def verify_tor_transport():
    """Confirm the local SOCKS proxy actually exits through Tor."""
    if not ensure_tor():
        return False, 'Tor SOCKS proxy did not start'
    body, status, error = _fetch_response(
        'https://check.torproject.org/api/ip', timeout=30, force_tor=True,
    )
    if error:
        return False, error
    compact = ''.join((body or '').split()).casefold()
    if '"istor":true' not in compact:
        return False, 'Tor check returned HTTP %s without IsTor=true' % status
    return True, 'Tor SOCKS transport reports IsTor=true'


def verify_site(name, urls):
    """Verify that at least one terminal endpoint returns usable content."""
    failures = []
    for url in urls:
        if '.onion' in url and not tor_ready():
            failures.append('%s: Tor is not running' % url)
            continue
        body, status, error = _fetch_response(url, timeout=20)
        if not error and body and len(body.strip()) >= 40:
            return True, '%s (HTTP %s)' % (url, status)
        failures.append('%s: %s' % (url, error or 'empty response'))
    return False, '; '.join(failures)


def verify_bundled_onionsearch():
    core = ONIONSEARCH_ROOT / 'core.py'
    package = ONIONSEARCH_ROOT / '__init__.py'
    if not (core.is_file() and package.is_file()):
        return False, 'bundled OnionSearch source is missing'
    try:
        compile(core.read_text(encoding='utf-8'), str(core), 'exec')
    except (OSError, SyntaxError) as exc:
        return False, str(exc)
    python = bundled_onionsearch_python()
    if not python.is_file():
        return False, 'isolated runtime is missing'
    env = os.environ.copy()
    thirdparty = str(ROOT / 'thirdparty')
    env['PYTHONPATH'] = thirdparty + os.pathsep + env.get('PYTHONPATH', '')
    probe = (
        'import onionsearch, html5lib, socks, termcolor; '
        'print("OnionSearch import OK")'
    )
    result = subprocess.run(
        [str(python), '-c', probe, 'smoke'],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return False, result.stderr.strip() or 'runtime import failed'
    return True, result.stdout.strip()


def _choose_url(urls, input_func):
    if len(urls) == 1:
        return urls[0]
    for index, url in enumerate(urls, 1):
        print('  [%d] %s' % (index, url))
    raw = input_func('Endpoint [1]: ').strip()
    try:
        index = int(raw or '1') - 1
        return urls[index]
    except (ValueError, IndexError):
        print('[error] Invalid endpoint selection.')
        return None


def search_catalog(slug='deepdarkcti', input_func=input):
    spec = TOOLS[slug]
    if not ensure_installed(slug, input_func, noun='data'):
        return 1
    query = input_func('Keyword to search: ').strip().casefold()
    if not query:
        print('[error] A keyword is required.')
        return 2
    count = 0
    for path in sorted(source_dir(spec).glob('*.md')):
        try:
            lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            if query in line.casefold():
                print('%s:%d: %s' % (path.name, number, line.strip()))
                count += 1
                if count >= 150:
                    print('[note] Result limit reached (150).')
                    return 0
    if not count:
        print('No matches found.')
    return 0


def entry_status(name):
    if name == 'OnionSearch':
        return 'bundled'
    slug = ENTRY_TO_SLUG.get(name)
    if not slug:
        return 'terminal site'
    spec = TOOLS[slug]
    if spec['kind'] == 'catalog':
        return 'local catalog' if is_installed(slug) else 'catalog install needed'
    return 'installed' if is_installed(slug) else 'install needed'


def ensure_installed(slug, input_func=input, noun='tool'):
    """Verify an installation and offer to install or repair it."""
    spec = TOOLS[slug]
    installed = is_installed(slug)
    if installed:
        ok, detail = verify_tool(slug)
        if ok:
            return True
        print('[error] %s verification failed: %s' % (spec['name'], detail))
    action = 'Repair' if installed else 'Install'
    prompt = '%s %s %s now? (Y/n): ' % (action, spec['name'], noun)
    if input_func(prompt).strip().lower() == 'n':
        return False
    install_tool(slug)
    return True


def run_entry(name, urls, input_func=input):
    slug = ENTRY_TO_SLUG.get(name)
    if slug:
        if TOOLS[slug]['kind'] == 'catalog':
            return search_catalog(slug, input_func)
        return run_tool(slug, input_func)
    url = _choose_url(urls, input_func)
    return terminal_fetch(url) if url else 2
