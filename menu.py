#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Interactive launcher for the bundled recon tools.

Run with no arguments for the interactive menu: pick a tool by number or name,
and the launcher collects the input that tool needs and runs it in this
terminal.  A session "target" (domain / username) set once is reused by every
tool that needs it.

Non-interactive usage::

    python menu.py <tool> [args...]     # jump straight to a tool
    python menu.py doctor               # readiness check for every tool
    python menu.py help                 # this help

Examples::

    python menu.py googledorks example.com
    python menu.py sherlock alice bob
    python menu.py domain example.com
"""

import os
import sys
import time
import subprocess

from modules.tools import profiles
from modules.tools import amass, puredns, bloodhound, gophish, proxychains
from modules.tools import chisel, sliver_c2, havoc_c2, mythic_c2
from modules.tools import pypykatz, impacket_tools, certipy, lotl_techniques
from modules.tools import mitre_caldera, atomic_red_team
from core.colors import (end, bold, red, green, yellow, blue, magenta, cyan,
                         white, info, que, bad, good, run)


HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, 'output')


def _load_dotenv_local():
    """Load KEY=VALUE pairs from .env.local into the environment - e.g.
    STRIKER_AUTHORIZED, the --intensive gate setup.sh writes there. A real
    environment variable of the same name always takes precedence."""
    try:
        with open(os.path.join(HERE, '.env.local')) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                name, _, value = line.partition('=')
                name = name.strip()
                if name and name not in os.environ:
                    os.environ[name] = value.strip()
    except OSError:
        pass


_load_dotenv_local()


# --- Session target ---------------------------------------------------------
# Set once (via the 'target' command or the first tool that asks) and reused as
# the default for every tool that needs the same domain or username.
SESSION = {
    'domain': None,
    'username': None,
    'email': None,
    'profile': profiles.STANDARD,
}


def prompt_save(input_func=input, default=True):
    """Ask once whether this run's results should be written to a file under
    output/.  Every tool wrapper already treats out_dir=None as "print to the
    terminal only, don't write a file" - this just decides which one to pass.
    Returns OUTPUT_DIR (save) or None (don't save)."""
    suffix = 'Y/n' if default else 'y/N'
    raw = input_func('%s Save results to a file under output/? (%s): '
                     % (que, suffix)).strip().lower()
    save = default if not raw else raw in ('y', 'yes')
    return OUTPUT_DIR if save else None


def session_prompt(field, label, input_func=input):
    """Prompt for a value, defaulting to the current session target.  An empty
    reply keeps the default; a non-empty reply updates the session."""
    current = SESSION.get(field)
    suffix = ' [%s]' % current if current else ''
    raw = input_func('%s %s%s: ' % (que, label, suffix)).strip()
    value = raw or current
    if value:
        SESSION[field] = value
    return value


def set_target(input_func=input):
    """Interactively set (or clear) the session domain/username.  A single '-'
    clears a field; a blank reply keeps it."""
    print('%s Session target - blank keeps current, "-" clears.' % info)
    domain = input_func('%s Domain [%s]: '
                        % (que, SESSION['domain'] or '')).strip()
    if domain == '-':
        SESSION['domain'] = None
    elif domain:
        SESSION['domain'] = domain
    username = input_func('%s Username [%s]: '
                          % (que, SESSION['username'] or '')).strip()
    if username == '-':
        SESSION['username'] = None
    elif username:
        SESSION['username'] = username
    email = input_func('%s Email [%s]: '
                       % (que, SESSION['email'] or '')).strip()
    if email == '-':
        SESSION['email'] = None
    elif email:
        SESSION['email'] = email
    print('%s Target set: domain=%s  username=%s  email=%s'
          % (good, SESSION['domain'] or '-', SESSION['username'] or '-',
             SESSION['email'] or '-'))


def activate_profile(name, authorized=False):
    """Activate a bounded tool profile, requiring authorization for intensive."""
    profile = profiles.normalize(name)
    if profiles.is_intensive(profile) and not authorized:
        raise PermissionError('intensive mode requires authorization confirmation')
    SESSION['profile'] = profile
    return profile


def set_profile(input_func=input):
    """Select the standard or intensive authorized-testing profile."""
    current = SESSION['profile']
    raw = input_func('%s Profile (standard/intensive) [%s]: '
                     % (que, current)).strip() or current
    try:
        profile = profiles.normalize(raw)
    except ValueError:
        print('%s Unknown profile: %r' % (bad, raw))
        return False
    authorized = False
    if profiles.is_intensive(profile):
        print('%s Intensive mode performs broader active checks with bounded '
              'rates. Use it only on targets you are authorized to test.' % info)
        confirmation = input_func('%s Type AUTHORIZED to continue: ' % que).strip()
        authorized = confirmation == 'AUTHORIZED'
        if not authorized:
            print('%s Profile unchanged.' % info)
            return False
    activate_profile(profile, authorized=authorized)
    print('%s Profile set to %s.' % (good, profile))
    return True


def _missing_mods(mods):
    """Return the subset of `mods` that cannot be imported in this interpreter."""
    import importlib.util
    missing = []
    for module in mods:
        try:
            if importlib.util.find_spec(module) is None:
                missing.append(module)
        except (ImportError, ValueError):
            missing.append(module)
    return missing


def _unimportable_mods(mods):
    """Return modules that are absent or fail while being imported."""
    import importlib
    broken = []
    for module in mods:
        try:
            importlib.import_module(module)
        except Exception:  # noqa: BLE001 - readiness must catch dependency errors
            broken.append(module)
    return broken


# --- Tool cores + interactive + CLI wrappers --------------------------------
# Each tool has a core `_do_*` (used by both paths), a `run_*` interactive
# wrapper (prompts, using the session target), and often a `cli_*` handler for
# non-interactive `python menu.py <tool> ...` use.

def _do_domain_scan(domain):
    scanner = os.path.join(HERE, 'osint_tools.py')
    if not os.path.isfile(scanner):
        print('%s Domain scanner (osint_tools.py) not found.' % bad)
        return 1
    # osint_tools.py reads the target from argv[1] and loads its db/ relative to
    # its own directory, so run it as a script in this same interpreter.
    return subprocess.run([sys.executable, scanner, domain]).returncode


def run_domain_scanner():
    domain = session_prompt('domain', 'Domain to scan (e.g. example.com)')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    _do_domain_scan(domain)


def cli_domain(args):
    if not args:
        print('%s Usage: domain <domain>' % bad)
        return 2
    SESSION['domain'] = args[0]
    return _do_domain_scan(args[0])


def ready_domain():
    if not os.path.isfile(os.path.join(HERE, 'osint_tools.py')):
        return False, 'osint_tools.py missing'
    missing = _missing_mods(['requests'])
    return (not missing), ('missing: %s' % ', '.join(missing) if missing else 'ready')


def _do_sublist3r(domain, out_dir=OUTPUT_DIR):
    script = os.path.join(HERE, 'thirdparty', 'sublist3r.py')
    if not os.path.isfile(script):
        print('%s Sublist3r not found in thirdparty/.' % bad)
        return 1
    # Sublist3r imports its bundled subbrute/dns via its own directory on
    # sys.path[0], so invoking the vendored script directly Just Works.
    # -o is optional upstream - it prints subdomains to the terminal either
    # way, and only writes a copy to file when a path is given.
    command = [sys.executable, script, '-d', domain]
    save = None
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        save = os.path.join(out_dir, 'sublist3r_%s.txt' % domain.replace('/', '_'))
        command.extend(['-o', save])
    command.extend(profiles.args_for('sublist3r', SESSION['profile']))
    result = subprocess.run(command)
    if result.returncode == 0 and save and os.path.isfile(save):
        print('%s Subdomains saved to %s' % (good, os.path.relpath(save, HERE)))
    return result.returncode


def run_sublist3r():
    domain = session_prompt('domain', 'Domain to enumerate (e.g. example.com)')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    _do_sublist3r(domain, out_dir=prompt_save())


def cli_sublist3r(args):
    if not args:
        print('%s Usage: sublist3r <domain>' % bad)
        return 2
    SESSION['domain'] = args[0]
    return _do_sublist3r(args[0])


def ready_sublist3r():
    if not os.path.isfile(os.path.join(HERE, 'thirdparty', 'sublist3r.py')):
        return False, 'thirdparty/sublist3r.py missing'
    missing = _missing_mods(['requests'])
    return (not missing), ('missing: %s' % ', '.join(missing) if missing else 'ready')


SHERLOCK_DIR = os.path.join(HERE, 'thirdparty', 'sherlock')
SHERLOCK_DEPS = ['requests', 'requests_futures', 'pandas', 'openpyxl',
                 'colorama', 'socks', 'stem', 'certifi']


def _do_sherlock(usernames, out_dir=OUTPUT_DIR):
    ok, detail = ready_sherlock()
    if not ok:
        print('%s Sherlock not ready: %s' % (bad, detail))
        if 'missing:' in detail:
            print('    Install them with: %s -m pip install -r requirements.txt'
                  % os.path.basename(sys.executable))
        return 1
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    env = os.environ.copy()
    env['PYTHONPATH'] = SHERLOCK_DIR + os.pathsep + env.get('PYTHONPATH', '')
    # Sherlock's own --txt flag (off by default upstream) controls whether it
    # writes a per-username .txt file at all; it always prints hits to the
    # terminal either way, so out_dir=None just leaves that flag off.
    extra = ['--txt'] if out_dir else []
    command = ([sys.executable, '-m', 'sherlock_project'] + extra
               + profiles.args_for('sherlock', SESSION['profile'])
               + list(usernames))
    result = subprocess.run(
        command,
        cwd=OUTPUT_DIR, env=env)
    if out_dir:
        print('%s Any hits were written under %s/'
              % (good, os.path.relpath(OUTPUT_DIR, HERE)))
    return result.returncode


def run_sherlock():
    default = SESSION.get('username') or ''
    suffix = ' [%s]' % default if default else ''
    raw = input('%s Username(s) to search (space-separated)%s: '
                % (que, suffix)).strip()
    targets = (raw or default).split()
    if not targets:
        print('%s No username provided.' % bad)
        return
    SESSION['username'] = targets[0]
    _do_sherlock(targets, out_dir=prompt_save())


def cli_sherlock(args):
    if not args:
        print('%s Usage: sherlock <username> [username...]' % bad)
        return 2
    SESSION['username'] = args[0]
    return _do_sherlock(args)


def ready_sherlock():
    entry = os.path.join(SHERLOCK_DIR, 'sherlock_project', '__main__.py')
    if not os.path.isfile(entry):
        return False, 'thirdparty/sherlock source missing'
    missing = _missing_mods(SHERLOCK_DEPS)
    return (not missing), ('missing: %s' % ', '.join(missing) if missing else 'ready')


def run_phoneinfoga():
    from modules.tools.phoneinfoga import phoneinfoga
    number = input('%s Phone number (E164, e.g. +14152007986): ' % que).strip()
    if not number:
        print('%s No number provided.' % bad)
        return
    phoneinfoga(number)


def cli_phoneinfoga(args):
    if not args:
        print('%s Usage: phoneinfoga <+E164number>' % bad)
        return 2
    from modules.tools.phoneinfoga import phoneinfoga
    return 0 if phoneinfoga(args[0]) else 1


def ready_phoneinfoga():
    from modules.tools.phoneinfoga import _binary, _platform_binary_name
    binary = _binary()
    if binary:
        return True, os.path.basename(binary)
    return False, 'binary missing (expected bin/%s)' % _platform_binary_name()


OSINTGRAM_DEPS = ['requests_toolbelt', 'geopy', 'prettytable',
                  'instagram_private_api', 'hikerapi']


def _osintgram_dependencies():
    readline = 'pyreadline' if os.name == 'nt' else 'gnureadline'
    return OSINTGRAM_DEPS + [readline]


def run_osintgram():
    import getpass
    import configparser

    osint_dir = os.path.join(HERE, 'thirdparty', 'Osintgram')
    main_py = os.path.join(osint_dir, 'main.py')
    if not os.path.isfile(main_py):
        print('%s Osintgram not found in thirdparty/Osintgram.' % bad)
        return

    # Osintgram pulls in several third-party packages that are too heavy to
    # vendor cross-platform; verify they're importable before launching.
    unavailable = _unimportable_mods(_osintgram_dependencies())
    if unavailable:
        print('%s Osintgram dependencies are unavailable: %s'
              % (bad, ', '.join(unavailable)))
        print('    Install them with: %s -m pip install -r %s'
              % (os.path.basename(sys.executable),
                 os.path.join('thirdparty', 'Osintgram', 'requirements.txt')))
        return

    # Instagram login or a HikerAPI token is required for any results.
    creds_path = os.path.join(osint_dir, 'config', 'credentials.ini')
    creds = configparser.ConfigParser()
    creds.read(creds_path)
    if not creds.has_section('Credentials'):
        creds.add_section('Credentials')
    has_login = (creds.get('Credentials', 'username', fallback='').strip() and
                 creds.get('Credentials', 'password', fallback='').strip())
    from modules.tools.phoneinfoga import _load_keys
    has_token = (creds.get('Credentials', 'hikerapi_token', fallback='').strip() or
                 os.environ.get('HIKERAPI_TOKEN') or
                 _load_keys().get('HIKERAPI_TOKEN'))
    if not (has_login or has_token):
        print('%s Osintgram needs Instagram credentials before it can run.' % info)
        try:
            username = input('%s Instagram username: ' % que).strip()
            # getpass keeps the password off the screen and out of shell history.
            password = getpass.getpass('%s Instagram password: ' % que)
        except (EOFError, KeyboardInterrupt):
            print('\n%s Cancelled, no credentials saved.' % info)
            return
        if not (username and password):
            print('%s Username and password are both required.' % bad)
            return
        creds.set('Credentials', 'username', username)
        creds.set('Credentials', 'password', password)
        try:
            with open(creds_path, 'w') as f:
                creds.write(f)
        except OSError as e:
            print('%s Could not write credentials to %s: %s'
                  % (bad, creds_path, e))
            return
        print('%s Saved credentials to %s'
              % (good, os.path.relpath(creds_path, HERE)))

    target = session_prompt('username', 'Target Instagram username')
    if not target:
        print('%s No target provided.' % bad)
        return
    # main.py uses relative imports and reads config from its own dir.
    subprocess.run([sys.executable, main_py, target], cwd=osint_dir)


def ready_osintgram():
    if not os.path.isfile(os.path.join(HERE, 'thirdparty', 'Osintgram', 'main.py')):
        return False, 'thirdparty/Osintgram source missing'
    unavailable = _unimportable_mods(_osintgram_dependencies())
    detail = 'unavailable: %s' % ', '.join(unavailable) if unavailable else 'ready'
    return not unavailable, detail


def run_googledorks():
    # Terminal-native reimplementation of the Advanced Google Dork Generator
    # (github.com/str1k3r0p/GoogleDorks); builds dork queries in this shell.
    from modules.tools.googledorks import run as dorks_run
    domain = session_prompt('domain', 'Target domain (e.g. example.com)')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    dorks_run(input_func=lambda prompt: input('%s %s' % (que, prompt)),
              out_dir=OUTPUT_DIR, domain=domain)


def cli_googledorks(args):
    if not args:
        print('%s Usage: googledorks <domain> [category-index]' % bad)
        return 2
    from modules.tools.googledorks import build_dorks, format_dorks, DORK_CATEGORIES
    SESSION['domain'] = args[0]
    categories = None
    if len(args) > 1:
        try:
            index = int(args[1])
            if not 1 <= index <= len(DORK_CATEGORIES):
                raise ValueError
            categories = [index - 1]
        except ValueError:
            print('%s Invalid category index: %r (1-%d)'
                  % (bad, args[1], len(DORK_CATEGORIES)))
            return 2
    text = format_dorks(build_dorks(args[0], categories))
    print(text)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, 'googledorks_%s.txt' % args[0].replace('/', '_'))
    try:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text + '\n')
        print('%s Saved to %s' % (good, os.path.relpath(path, HERE)))
    except OSError as exc:
        print('%s Could not save: %s' % (bad, exc))
    return 0


def ready_googledorks():
    try:
        from modules.tools import googledorks
        return True, '%d categories, %d dorks' % (
            len(googledorks.DORK_CATEGORIES),
            sum(len(d) for _, d in googledorks.DORK_CATEGORIES))
    except Exception as exc:  # noqa: BLE001 - report any import failure
        return False, str(exc)


def _ready_http():
    """Readiness for the built-in HTTP-only lookups: they just need requests."""
    missing = _missing_mods(['requests'])
    return (not missing), ('requests not installed' if missing else 'ready')


def run_crtsh():
    from modules.tools import crtsh
    domain = session_prompt('domain', 'Domain for CT-log lookup (e.g. example.com)')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    crtsh.run(domain, prompt_save())


def cli_crtsh(args):
    if not args:
        print('%s Usage: crtsh <domain>' % bad)
        return 2
    from modules.tools import crtsh
    SESSION['domain'] = args[0]
    return crtsh.run(args[0], OUTPUT_DIR)


def run_whois():
    from modules.tools import whoislookup
    domain = session_prompt('domain', 'Domain for WHOIS lookup')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    whoislookup.run(domain, prompt_save())


def cli_whois(args):
    if not args:
        print('%s Usage: whois <domain>' % bad)
        return 2
    from modules.tools import whoislookup
    SESSION['domain'] = args[0]
    return whoislookup.run(args[0], OUTPUT_DIR)


def run_wayback():
    from modules.tools import wayback
    domain = session_prompt('domain', 'Domain for Wayback URL history')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    limit = profiles.setting('wayback_limit', SESSION['profile'])
    wayback.run(domain, prompt_save(), limit=limit)


def cli_wayback(args):
    if not args:
        print('%s Usage: wayback <domain>' % bad)
        return 2
    from modules.tools import wayback
    SESSION['domain'] = args[0]
    limit = profiles.setting('wayback_limit', SESSION['profile'])
    return wayback.run(args[0], OUTPUT_DIR, limit=limit)


def run_ipgeo():
    from modules.tools import ipgeo
    host = session_prompt('domain', 'IP or host to geolocate')
    if not host:
        print('%s No IP or host provided.' % bad)
        return
    ipgeo.run(host, prompt_save())


def cli_ipgeo(args):
    if not args:
        print('%s Usage: ipgeo <ip|host>' % bad)
        return 2
    from modules.tools import ipgeo
    return ipgeo.run(args[0], OUTPUT_DIR)


def run_nmap():
    from modules.tools import nmap_scan
    if not nmap_scan.is_installed():
        print('%s nmap is not installed.' % bad)
        print('    Install it with: %s' % nmap_scan.install_hint())
        return
    target = session_prompt('domain', 'Target host/domain/IP to scan')
    if not target:
        print('%s No target provided.' % bad)
        return
    print('%s Scan profiles:' % info)
    for key in sorted(nmap_scan.PROFILES):
        label, args = nmap_scan.PROFILES[key]
        print('   %s[%s]%s %-38s %s%s%s'
              % (green, key, end, label, magenta, ' '.join(args), end))
    print('   %s[c]%s Custom flags' % (green, end))
    default_profile = profiles.setting('nmap_profile', SESSION['profile'])
    sel = (input('%s Profile [%s]: ' % (que, default_profile)).strip().lower()
           or default_profile)
    if sel in ('c', 'custom'):
        args = input('%s nmap flags (e.g. -sV -p 80,443): ' % que).strip().split()
    elif sel in nmap_scan.PROFILES:
        args = nmap_scan.PROFILES[sel][1]
    else:
        print('%s Invalid profile: %r' % (bad, sel))
        return
    is_root = getattr(os, 'geteuid', lambda: 0)() == 0
    if any(flag in args for flag in ('-A', '-O', '-sS')) and not is_root:
        print('%s That scan needs root for OS/SYN features; run the launcher '
              'with sudo, or Nmap will do what it can unprivileged.' % info)
    nmap_scan.run(target, args, prompt_save())


def cli_nmap(args):
    from modules.tools import nmap_scan
    if not args:
        print('%s Usage: nmap <target> [nmap flags...]' % bad)
        return 2
    if not nmap_scan.is_installed():
        print('%s nmap is not installed (%s).' % (bad, nmap_scan.install_hint()))
        return 1
    target = args[0]
    default_profile = profiles.setting('nmap_profile', SESSION['profile'])
    flags = args[1:] if len(args) > 1 else nmap_scan.PROFILES[default_profile][1]
    SESSION['domain'] = target
    return nmap_scan.run(target, flags, OUTPUT_DIR)


def ready_nmap():
    from modules.tools import nmap_scan
    return nmap_scan.ready()


def _do_holehe(email):
    if _missing_mods(['holehe']):
        print('%s holehe is not installed.' % bad)
        print('    Install it with: %s -m pip install holehe'
              % os.path.basename(sys.executable))
        return 1
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # holehe ships no __main__; call its console entry point directly.  Results
    # (an optional CSV) land in output/ because that is the working directory.
    return subprocess.run(
        [sys.executable, '-c', 'from holehe.core import main; main()',
         email, '--only-used'],
        cwd=OUTPUT_DIR).returncode


def run_holehe():
    email = session_prompt('email', 'Email address to check')
    if not email:
        print('%s No email provided.' % bad)
        return
    _do_holehe(email)


def cli_holehe(args):
    if not args:
        print('%s Usage: holehe <email>' % bad)
        return 2
    SESSION['email'] = args[0]
    return _do_holehe(args[0])


def ready_holehe():
    missing = _missing_mods(['holehe'])
    return (not missing), ('not installed (pip install holehe)' if missing else 'ready')


def _do_userscanner(username=None, email=None):
    if _missing_mods(['user_scanner']):
        print('%s user-scanner is not installed.' % bad)
        print('    Install it with: %s -m pip install user-scanner'
              % os.path.basename(sys.executable))
        return 1
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # -u and -e are mutually exclusive upstream, so run one pass per identifier.
    # --only-found trims the output to hits; results land in output/ (cwd).
    rc = 0
    for flag, value in (('-u', username), ('-e', email)):
        if value:
            result = subprocess.run(
                [sys.executable, '-m', 'user_scanner', flag, value, '--only-found'],
                cwd=OUTPUT_DIR)
            rc = rc or result.returncode
    return rc


def run_userscanner():
    username = session_prompt('username', 'Username to scan (blank to skip)')
    email = session_prompt('email', 'Email to scan (blank to skip)')
    if not (username or email):
        print('%s Provide a username, an email, or both.' % bad)
        return
    _do_userscanner(username, email)


def cli_userscanner(args):
    if not args:
        print('%s Usage: userscanner <username|email> [more...]' % bad)
        return 2
    # Split args into emails vs usernames by the presence of '@'.
    emails = [a for a in args if '@' in a]
    users = [a for a in args if '@' not in a]
    if users:
        SESSION['username'] = users[0]
    if emails:
        SESSION['email'] = emails[0]
    rc = 0
    for user in users:
        rc = rc or _do_userscanner(username=user)
    for mail in emails:
        rc = rc or _do_userscanner(email=mail)
    return rc


def ready_userscanner():
    missing = _missing_mods(['user_scanner'])
    return (not missing), ('not installed (pip install user-scanner)'
                           if missing else 'ready')


def _gh_token():
    from modules.tools.phoneinfoga import _load_keys
    return os.environ.get('GH_TOKEN') or _load_keys().get('GH_TOKEN')


def _ensure_githubdorks():
    from modules.tools import github_dorks
    if github_dorks.ready()[0]:
        return True
    if not github_dorks.is_installed():
        print('%s github-dorks is not set up yet (one-time clone + deps).' % info)
    if input('%s Set it up now? (Y/n): ' % que).strip().lower() == 'n':
        return False
    try:
        github_dorks.install()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('%s github-dorks setup failed: %s' % (bad, exc))
        return False
    return github_dorks.ready()[0]


def _do_githubdorks(target, out_dir=OUTPUT_DIR):
    from modules.tools import github_dorks
    token = _gh_token()
    if not token:
        print('%s No GH_TOKEN set - GitHub search is heavily rate-limited '
              'without one.' % info)
        print('    Add GH_TOKEN to config/keys.env (or export it) for real use.')
    is_repo = '/' in target
    return github_dorks.run(target, is_repo=is_repo, token=token,
                            out_dir=out_dir)


def run_githubdorks():
    from modules.tools import github_dorks  # noqa: F401 - ensure import works
    if not _ensure_githubdorks():
        return
    target = input('%s GitHub user/org, or owner/repo: ' % que).strip()
    if not target:
        print('%s No target provided.' % bad)
        return
    _do_githubdorks(target, out_dir=prompt_save())


def cli_githubdorks(args):
    from modules.tools import github_dorks
    if not args:
        print('%s Usage: githubdorks <user|org|owner/repo>' % bad)
        return 2
    if not github_dorks.ready()[0]:
        print('%s github-dorks is not set up. Run it from the menu once to '
              'install it.' % bad)
        return 1
    return _do_githubdorks(args[0])


def ready_githubdorks():
    from modules.tools import github_dorks
    return github_dorks.ready()


# --- new OSINT tools: assetfinder, subfinder, httpx, nuclei, gau, unfurl, exiftool, smtp_enum ---

def run_assetfinder():
    from modules.tools import assetfinder
    if not assetfinder.is_installed():
        print('%s assetfinder is not installed.' % bad)
        print('    %s' % assetfinder.install_hint())
        return
    domain = session_prompt('domain', 'Domain to find assets for')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    assetfinder.run(domain, prompt_save())

def cli_assetfinder(args):
    from modules.tools import assetfinder
    if not args:
        print('%s Usage: assetfinder <domain>' % bad)
        return 2
    if not assetfinder.is_installed():
        print('%s assetfinder is not installed.' % bad)
        return 1
    SESSION['domain'] = args[0]
    return assetfinder.run(args[0], OUTPUT_DIR)

def ready_assetfinder():
    from modules.tools import assetfinder
    return assetfinder.ready()


def run_subfinder():
    from modules.tools import subfinder
    if not subfinder.is_installed():
        print('%s subfinder is not installed.' % bad)
        print('    %s' % subfinder.install_hint())
        return
    domain = session_prompt('domain', 'Domain to enumerate subdomains')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    subfinder.run(domain, prompt_save(), profile=SESSION['profile'])

def cli_subfinder(args):
    from modules.tools import subfinder
    if not args:
        print('%s Usage: subfinder <domain>' % bad)
        return 2
    if not subfinder.is_installed():
        print('%s subfinder is not installed.' % bad)
        return 1
    SESSION['domain'] = args[0]
    return subfinder.run(args[0], OUTPUT_DIR, profile=SESSION['profile'])

def ready_subfinder():
    from modules.tools import subfinder
    return subfinder.ready()


def run_httpx():
    from modules.tools import httpx
    if not httpx.is_installed():
        print('%s httpx is not installed.' % bad)
        print('    %s' % httpx.install_hint())
        return
    target = input('%s Target URL or domain: ' % que).strip()
    if not target:
        print('%s No target provided.' % bad)
        return
    flags = input('%s Flags (e.g. -title -status-code) [leave blank for defaults]: ' % que).strip()
    SESSION['domain'] = target
    httpx.run(target, flags or None, prompt_save(), profile=SESSION['profile'])

def cli_httpx(args):
    from modules.tools import httpx
    if not args:
        print('%s Usage: httpx <target> [flags...]' % bad)
        return 2
    if not httpx.is_installed():
        print('%s httpx is not installed.' % bad)
        return 1
    target = args[0]
    flags = ' '.join(args[1:]) if len(args) > 1 else None
    SESSION['domain'] = target
    return httpx.run(target, flags, OUTPUT_DIR, profile=SESSION['profile'])

def ready_httpx():
    from modules.tools import httpx
    return httpx.ready()


def run_nuclei():
    from modules.tools import nuclei
    if not nuclei.is_installed():
        print('%s nuclei is not installed.' % bad)
        print('    %s' % nuclei.install_hint())
        print('    After install, update templates: nuclei -update-templates')
        return
    target = input('%s Target URL: ' % que).strip()
    if not target:
        print('%s No target provided.' % bad)
        return
    default_severity = profiles.setting('nuclei_severity', SESSION['profile'])
    severity = input('%s Severity [%s]: ' % (que, default_severity)).strip()
    severity = severity or default_severity
    SESSION['domain'] = target
    nuclei.run(target, severity, prompt_save(), profile=SESSION['profile'])

def cli_nuclei(args):
    from modules.tools import nuclei
    if not args:
        print('%s Usage: nuclei <target> [severity]' % bad)
        return 2
    if not nuclei.is_installed():
        print('%s nuclei is not installed.' % bad)
        return 1
    target = args[0]
    default_severity = profiles.setting('nuclei_severity', SESSION['profile'])
    severity = args[1] if len(args) > 1 else default_severity
    SESSION['domain'] = target
    return nuclei.run(target, severity, OUTPUT_DIR, profile=SESSION['profile'])

def ready_nuclei():
    from modules.tools import nuclei
    return nuclei.ready()


def run_gau():
    from modules.tools import gau
    if not gau.is_installed():
        print('%s gau is not installed.' % bad)
        print('    %s' % gau.install_hint())
        return
    domain = session_prompt('domain', 'Domain to fetch URLs for')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    gau.run(domain, 'all', prompt_save(), profile=SESSION['profile'])

def cli_gau(args):
    from modules.tools import gau
    if not args:
        print('%s Usage: gau <domain>' % bad)
        return 2
    if not gau.is_installed():
        print('%s gau is not installed.' % bad)
        return 1
    SESSION['domain'] = args[0]
    return gau.run(args[0], 'all', OUTPUT_DIR, profile=SESSION['profile'])

def ready_gau():
    from modules.tools import gau
    return gau.ready()


def run_unfurl():
    from modules.tools import unfurl
    if not unfurl.is_installed():
        print('%s unfurl is not installed.' % bad)
        print('    %s' % unfurl.install_hint())
        return
    url = input('%s URL to parse: ' % que).strip()
    if not url:
        print('%s No URL provided.' % bad)
        return
    mode = input('%s Mode (domains/subdomains/paths/keys/values) [domains]: ' % que).strip() or 'domains'
    unfurl.run(url, mode, prompt_save())

def cli_unfurl(args):
    from modules.tools import unfurl
    if not args:
        print('%s Usage: unfurl <url> [mode]' % bad)
        return 2
    if not unfurl.is_installed():
        print('%s unfurl is not installed.' % bad)
        return 1
    url = args[0]
    mode = args[1] if len(args) > 1 else 'domains'
    return unfurl.run(url, mode, OUTPUT_DIR)

def ready_unfurl():
    from modules.tools import unfurl
    return unfurl.ready()


def run_exiftool():
    from modules.tools import exiftool
    if not exiftool.is_installed():
        print('%s exiftool is not installed.' % bad)
        print('    %s' % exiftool.install_hint())
        return
    file_path = input('%s File path to extract metadata: ' % que).strip()
    if not file_path:
        print('%s No file provided.' % bad)
        return
    exiftool.run(file_path, prompt_save())

def cli_exiftool(args):
    from modules.tools import exiftool
    if not args:
        print('%s Usage: exiftool <file_path>' % bad)
        return 2
    if not exiftool.is_installed():
        print('%s exiftool is not installed.' % bad)
        return 1
    return exiftool.run(args[0], OUTPUT_DIR)

def ready_exiftool():
    from modules.tools import exiftool
    return exiftool.ready()


def run_smtp_enum():
    from modules.tools import smtp_enum
    email = input('%s Email address or file path (one per line): ' % que).strip()
    if not email:
        print('%s No email/file provided.' % bad)
        return
    if email.startswith('/') or os.path.isfile(email):
        smtp_enum.run(email, prompt_save())
    else:
        SESSION['email'] = email
        smtp_enum.run(email, OUTPUT_DIR)

def cli_smtp_enum(args):
    from modules.tools import smtp_enum
    if not args:
        print('%s Usage: smtp_enum <email|file>' % bad)
        return 2
    return smtp_enum.run(args[0], OUTPUT_DIR)

def ready_smtp_enum():
    return True, 'built-in (Python socket)'


def _ensure_theharvester():
    from modules.tools import theharvester
    ok, _ = theharvester.ready()
    if ok:
        return True
    if not theharvester.is_installed():
        print('%s theHarvester is not set up yet (one-time clone + venv build).'
              % info)
    if input('%s Set it up now? (Y/n): ' % que).strip().lower() == 'n':
        return False
    try:
        theharvester.install()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('%s theHarvester setup failed: %s' % (bad, exc))
        return False
    return theharvester.ready()[0]


def run_theharvester():
    from modules.tools import theharvester
    if not _ensure_theharvester():
        return
    domain = session_prompt('domain', 'Domain to harvest (e.g. example.com)')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    theharvester.run(domain, out_dir=prompt_save())


def cli_theharvester(args):
    from modules.tools import theharvester
    if not args:
        print('%s Usage: theharvester <domain>' % bad)
        return 2
    if not theharvester.ready()[0]:
        print('%s theHarvester is not set up. Run it from the menu once to '
              'install it.' % bad)
        return 1
    SESSION['domain'] = args[0]
    return theharvester.run(args[0], out_dir=OUTPUT_DIR)


def ready_theharvester():
    from modules.tools import theharvester
    return theharvester.ready()


def _port_open(host, port, timeout=3):
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _find_tor():
    import shutil
    tor = shutil.which('tor')
    if tor:
        return tor
    # Common Homebrew locations that may not be on PATH in the launcher.
    for cand in ('/opt/homebrew/bin/tor', '/usr/local/bin/tor'):
        if os.path.isfile(cand):
            return cand
    return None


def _tor_install_hint():
    import platform
    system = platform.system().lower()
    return {
        'darwin': 'brew install tor',
        'linux': 'sudo apt install tor   (or dnf/pacman equivalent)',
        'windows': 'choco install tor   (or use the Tor Browser bundle)',
    }.get(system, 'install the Tor package for your OS')


def _start_tor(tor_bin, host, port, results_dir, wait=90):
    """Launch a throwaway `tor` instance and wait for it to bootstrap. Returns
    the process on success, else None."""
    import time
    data_dir = os.path.join(results_dir, 'tor-data')
    os.makedirs(data_dir, exist_ok=True)
    os.chmod(data_dir, 0o700)  # tor refuses a world-readable DataDirectory
    logpath = os.path.join(results_dir, 'tor.log')
    socks = str(port) if host in ('localhost', '127.0.0.1') else '%s:%d' % (host, port)
    try:
        logfile = open(logpath, 'wb')
        proc = subprocess.Popen(
            [tor_bin, '--SocksPort', socks, '--DataDirectory', data_dir],
            stdout=logfile, stderr=subprocess.STDOUT)
    except OSError as exc:
        print('%s Could not start tor: %s' % (bad, exc))
        return None
    print('%s Bootstrapping Tor (up to %ds)...' % (run, wait))
    for _ in range(wait):
        if proc.poll() is not None:
            print('%s tor exited early - see %s'
                  % (bad, os.path.relpath(logpath, HERE)))
            return None
        try:
            with open(logpath, 'r', errors='ignore') as f:
                if 'Bootstrapped 100%' in f.read():
                    print('%s Tor ready on %s:%d' % (good, host, port))
                    return proc
        except OSError:
            pass
        time.sleep(1)
    print('%s Tor did not finish bootstrapping in time; stopping it.' % bad)
    proc.terminate()
    return None


def run_onionsearch():
    from modules.tools.darkweb_tools import (
        bundled_onionsearch_python,
        install_bundled_onionsearch,
        verify_bundled_onionsearch,
    )

    thirdparty = os.path.join(HERE, 'thirdparty')
    if not os.path.isdir(os.path.join(thirdparty, 'onionsearch')):
        print('%s OnionSearch not found in thirdparty/onionsearch.' % bad)
        return

    ok, detail = verify_bundled_onionsearch()
    if not ok:
        print('%s OnionSearch runtime is not ready: %s' % (info, detail))
        if input('%s Install it now? (Y/n): ' % que).strip().lower() == 'n':
            return
        try:
            install_bundled_onionsearch()
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            print('%s OnionSearch installation failed: %s' % (bad, exc))
            return
    launcher_python = str(bundled_onionsearch_python())

    results_dir = OUTPUT_DIR
    os.makedirs(results_dir, exist_ok=True)

    proxy = (input('%s Tor SOCKS proxy [localhost:9050]: ' % que).strip()
             or 'localhost:9050')
    host, _, port_s = proxy.partition(':')
    host = host or 'localhost'
    try:
        port = int(port_s or 9050)
    except ValueError:
        port = 9050

    # OnionSearch reaches .onion engines only through Tor. If nothing is
    # listening, offer to auto-start the system `tor` daemon.
    tor_proc = None
    if not _port_open(host, port):
        tor_bin = _find_tor()
        if tor_bin and host in ('localhost', '127.0.0.1'):
            print('%s No Tor proxy on %s:%d.' % (info, host, port))
            if input('%s Start Tor now? (Y/n): ' % que).strip().lower() != 'n':
                tor_proc = _start_tor(tor_bin, host, port, results_dir)
        else:
            print('%s Tor proxy not reachable at %s, and no `tor` binary found.'
                  % (info, proxy))
            print('    Install Tor with: %s' % _tor_install_hint())
            print('    or start Tor Browser (its SOCKS proxy is localhost:9150).')
        if not _port_open(host, port):
            if input('%s Tor is not ready. Continue anyway? (y/N): '
                     % que).strip().lower() != 'y':
                if tor_proc:
                    tor_proc.terminate()
                return

    try:
        search = input('%s Search query: ' % que).strip()
        if not search:
            print('%s No query provided.' % bad)
            return
        env = os.environ.copy()
        env['PYTHONPATH'] = thirdparty + os.pathsep + env.get('PYTHONPATH', '')
        print('%s Searching darkweb engines for "%s" via %s ...'
              % (run, search, proxy))
        sys.stdout.flush()  # emit the line before the subprocess writes to the fd
        # Invoke the way its console script does; argv is parsed at import time.
        subprocess.run(
            [launcher_python, '-c', 'from onionsearch.core import scrape; scrape()',
             search, '--proxy', proxy],
            cwd=results_dir, env=env,
        )
        print('%s CSV results saved under %s/'
              % (good, os.path.relpath(results_dir, HERE)))
    finally:
        if tor_proc:
            print('%s Stopping Tor.' % info)
            tor_proc.terminate()


def ready_onionsearch():
    from modules.tools.darkweb_tools import ONIONSEARCH_ROOT, bundled_onionsearch_python
    if not (ONIONSEARCH_ROOT / '__init__.py').is_file():
        return False, 'bundled source missing'
    if not bundled_onionsearch_python().is_file():
        return False, 'runtime venv not installed (run the installer)'
    return True, 'bundled runtime present'


def _darkweb_category(label, tools):
    from modules.tools.darkweb_tools import entry_status, run_entry

    while True:
        print('\n%s %s%s tools %s' % (blue, bold, label, end))
        for i, (name, urls) in enumerate(tools, 1):
            status = entry_status(name)
            print('   %s[%d]%s %s%-20s%s %s%-22s%s'
                  % (green, i, end, bold + white, name, end,
                     magenta, '[%s]' % status, end))
        print('   %s[0]%s Back' % (red, end))
        sel = input('\n%s Select a tool: ' % que).strip().lower()
        if sel in ('0', 'b', 'back', ''):
            return
        try:
            idx = int(sel) - 1
            if idx < 0:
                raise IndexError
            name, urls = tools[idx]
        except (ValueError, IndexError):
            print('%s Invalid choice: %r' % (bad, sel))
            continue
        print('\n%s Launching %s%s%s in this terminal...'
              % (run, bold + white, name, end))
        if name == 'OnionSearch':
            run_onionsearch()
        else:
            try:
                run_entry(name, urls)
            except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
                print('%s %s failed: %s' % (bad, name, exc))


def run_darkweb():
    # Nested selection tab: pick a category, then a tool from the directory.
    from modules.tools.darkweb_tools import darkweb_categories

    categories = darkweb_categories()
    while True:
        print('\n%s %sDark Web OSINT categories%s' % (blue, bold, end))
        for i, (label, _) in enumerate(categories, 1):
            print('   %s[%d]%s %s%s%s' % (green, i, end, bold + white, label, end))
        print('   %s[0]%s Back to main menu' % (red, end))
        sel = input('\n%s Select a category: ' % que).strip().lower()
        if sel in ('0', 'b', 'back', ''):
            return
        try:
            idx = int(sel) - 1
            if idx < 0:
                raise IndexError
            label, tools = categories[idx]
        except (ValueError, IndexError):
            print('%s Invalid choice: %r' % (bad, sel))
            continue
        _darkweb_category(label, tools)


def ready_darkweb():
    from modules.tools.darkweb_tools import TOOLS as DW_TOOLS, is_installed
    installed = sum(1 for slug in DW_TOOLS if is_installed(slug))
    total = len(DW_TOOLS)
    return installed > 0, '%d/%d tools installed' % (installed, total)


def run_metasploit():
    from modules.tools import metasploit
    if not metasploit.is_installed():
        print('%s msfconsole is not installed.' % bad)
        print('    %s' % metasploit.install_hint())
        return
    mode = input('%s Mode (interactive/search) [interactive]: ' % que).strip().lower() or 'interactive'
    if mode == 'search':
        query = input('%s Search query (e.g., wordpress, apache): ' % que).strip()
        if not query:
            print('%s No query provided.' % bad)
            return
        metasploit.search_exploit(query, OUTPUT_DIR)
    else:
        metasploit.run_interactive(OUTPUT_DIR)


def cli_metasploit(args):
    from modules.tools import metasploit
    if not metasploit.is_installed():
        print('%s msfconsole is not installed.' % bad)
        return 1
    if not args:
        return metasploit.run_interactive(OUTPUT_DIR)
    if args[0] == 'search' and len(args) > 1:
        return metasploit.search_exploit(' '.join(args[1:]), OUTPUT_DIR)
    if args[0] == 'help':
        print('%s Usage: metasploit [search <query>]' % good)
        return 0
    print('%s Usage: metasploit [search <query>]' % bad)
    return 2


def ready_metasploit():
    from modules.tools import metasploit
    return metasploit.ready()


def run_searchsploit():
    from modules.tools import searchsploit
    if not searchsploit.is_installed():
        print('%s searchsploit is not installed.' % bad)
        print('    %s' % searchsploit.install_hint())
        return
    query = input('%s Search query (CVE, app name, or keyword): ' % que).strip()
    if not query:
        print('%s No query provided.' % bad)
        return
    options = input('%s Additional options (e.g., -j for JSON) [blank]: ' % que).strip()
    searchsploit.search(query, prompt_save(), options=options or None, profile=SESSION['profile'])


def cli_searchsploit(args):
    from modules.tools import searchsploit
    if not args:
        print('%s Usage: searchsploit <query> [options...]' % bad)
        return 2
    if not searchsploit.is_installed():
        print('%s searchsploit is not installed.' % bad)
        return 1
    query = args[0]
    options = args[1:] if len(args) > 1 else None
    SESSION['domain'] = query
    return searchsploit.search(query, OUTPUT_DIR, options=options, profile=SESSION['profile'])


def ready_searchsploit():
    from modules.tools import searchsploit
    return searchsploit.ready()


def run_hydra():
    from modules.tools import hydra
    if not hydra.is_installed():
        print('%s Hydra is not installed.' % bad)
        print('    %s' % hydra.install_hint())
        return
    target = input('%s Target (host:port): ' % que).strip()
    if not target:
        print('%s No target provided.' % bad)
        return
    protocol = input('%s Protocol (ssh/ftp/http/mysql/etc): ' % que).strip() or 'ssh'
    username = input('%s Username (or leave blank for -L file): ' % que).strip()
    password = input('%s Password (or leave blank for -P file): ' % que).strip()
    hydra.attack(target, protocol, username=username or None, password=password or None,
                 out_dir=prompt_save(), profile=SESSION['profile'])


def cli_hydra(args):
    from modules.tools import hydra
    if not hydra.is_installed():
        print('%s Hydra is not installed.' % bad)
        return 1
    if len(args) < 3:
        print('%s Usage: hydra <target:port> <protocol> <username> [password]' % bad)
        return 2
    target, protocol, username = args[0], args[1], args[2]
    password = args[3] if len(args) > 3 else None
    return hydra.attack(target, protocol, username=username, password=password, out_dir=OUTPUT_DIR)


def ready_hydra():
    from modules.tools import hydra
    return hydra.ready()


def run_john():
    from modules.tools import john
    if not john.is_installed():
        print('%s John the Ripper is not installed.' % bad)
        print('    %s' % john.install_hint())
        return
    hash_file = input('%s Hash file path: ' % que).strip()
    if not hash_file or not os.path.isfile(hash_file):
        print('%s Invalid hash file.' % bad)
        return
    wordlist = input('%s Wordlist (leave blank for incremental): ' % que).strip()
    format_type = input('%s Format (leave blank for auto): ' % que).strip()
    john.crack_hash(hash_file, wordlist=wordlist or None, format_type=format_type or None,
                    out_dir=OUTPUT_DIR, profile=SESSION['profile'])


def cli_john(args):
    from modules.tools import john
    if not john.is_installed():
        print('%s John the Ripper is not installed.' % bad)
        return 1
    if not args:
        print('%s Usage: john <hash_file> [wordlist] [format]' % bad)
        return 2
    return john.crack_hash(args[0], wordlist=args[1] if len(args) > 1 else None,
                           format_type=args[2] if len(args) > 2 else None, out_dir=OUTPUT_DIR)


def ready_john():
    from modules.tools import john
    return john.ready()


def run_sqlmap():
    from modules.tools import sqlmap
    if not sqlmap.is_installed():
        print('%s SQLmap is not installed.' % bad)
        print('    %s' % sqlmap.install_hint())
        return
    url = input('%s Target URL (with parameter): ' % que).strip()
    if not url:
        print('%s No URL provided.' % bad)
        return
    sqlmap.scan_url(url, out_dir=prompt_save(), profile=SESSION['profile'])


def cli_sqlmap(args):
    from modules.tools import sqlmap
    if not sqlmap.is_installed():
        print('%s SQLmap is not installed.' % bad)
        return 1
    if not args:
        print('%s Usage: sqlmap <url> [technique]' % bad)
        return 2
    technique = args[1] if len(args) > 1 else None
    return sqlmap.scan_url(args[0], technique=technique, out_dir=OUTPUT_DIR)


def ready_sqlmap():
    from modules.tools import sqlmap
    return sqlmap.ready()


def run_nikto():
    from modules.tools import nikto
    if not nikto.is_installed():
        print('%s Nikto is not installed.' % bad)
        print('    %s' % nikto.install_hint())
        return
    target = input('%s Target host/IP: ' % que).strip()
    if not target:
        print('%s No target provided.' % bad)
        return
    port = input('%s Port [80]: ' % que).strip() or '80'
    ssl = input('%s Use SSL/HTTPS? [y/N]: ' % que).strip().lower() == 'y'
    try:
        nikto.scan(target, port=int(port), ssl=ssl, out_dir=prompt_save(), profile=SESSION['profile'])
    except ValueError:
        print('%s Invalid port number.' % bad)


def cli_nikto(args):
    from modules.tools import nikto
    if not nikto.is_installed():
        print('%s Nikto is not installed.' % bad)
        return 1
    if not args:
        print('%s Usage: nikto <host> [port]' % bad)
        return 2
    port = int(args[1]) if len(args) > 1 else 80
    return nikto.scan(args[0], port=port, out_dir=OUTPUT_DIR)


def ready_nikto():
    from modules.tools import nikto
    return nikto.ready()


def run_aircrack():
    from modules.tools import aircrack
    if not aircrack.is_installed():
        print('%s aircrack-ng suite is not installed.' % bad)
        print('    %s' % aircrack.install_hint())
        return
    print('%s aircrack-ng - Wireless network security suite' % info)
    print('    1. Crack WPA/WPA2 handshake')
    print('    2. List interfaces')
    choice = input('%s Select option: ' % que).strip()
    if choice == '1':
        capture_file = input('%s Capture file (.cap): ' % que).strip()
        wordlist = input('%s Wordlist [rockyou.txt]: ' % que).strip()
        aircrack.crack_handshake(capture_file, wordlist=wordlist or None, out_dir=OUTPUT_DIR)
    elif choice == '2':
        aircrack.list_interfaces()


def cli_aircrack(args):
    from modules.tools import aircrack
    if not aircrack.is_installed():
        print('%s aircrack-ng is not installed.' % bad)
        return 1
    if not args:
        print('%s Usage: aircrack <capture_file> [wordlist]' % bad)
        return 2
    return aircrack.crack_handshake(args[0], wordlist=args[1] if len(args) > 1 else None, out_dir=OUTPUT_DIR)


def ready_aircrack():
    from modules.tools import aircrack
    return aircrack.ready()


def run_hashcat():
    from modules.tools import hashcat
    if not hashcat.is_installed():
        print('%s Hashcat is not installed.' % bad)
        print('    %s' % hashcat.install_hint())
        return
    hash_file = input('%s Hash file: ' % que).strip()
    if not hash_file or not os.path.isfile(hash_file):
        print('%s Invalid hash file.' % bad)
        return
    hash_type = input('%s Hash type ID (0=MD5, 1400=SHA2-256, 3200=bcrypt, etc): ' % que).strip()
    wordlist = input('%s Wordlist (optional): ' % que).strip()
    hashcat.crack_hashes(hash_file, hash_type, wordlist=wordlist or None, out_dir=prompt_save())


def cli_hashcat(args):
    from modules.tools import hashcat
    if not hashcat.is_installed():
        print('%s Hashcat is not installed.' % bad)
        return 1
    if len(args) < 2:
        print('%s Usage: hashcat <hash_file> <hash_type> [wordlist]' % bad)
        return 2
    wordlist = args[2] if len(args) > 2 else None
    return hashcat.crack_hashes(args[0], args[1], wordlist=wordlist, out_dir=OUTPUT_DIR)


def ready_hashcat():
    from modules.tools import hashcat
    return hashcat.ready()


def run_gobuster():
    from modules.tools import gobuster
    if not gobuster.is_installed():
        print('%s Gobuster is not installed.' % bad)
        print('    %s' % gobuster.install_hint())
        return
    mode = input('%s Mode (dir/dns) [dir]: ' % que).strip().lower() or 'dir'
    if mode == 'dns':
        domain = input('%s Domain to enumerate: ' % que).strip()
        if not domain:
            print('%s No domain provided.' % bad)
            return
        wordlist = input('%s Wordlist: ' % que).strip()
        gobuster.dns_bust(domain, wordlist=wordlist or None, out_dir=prompt_save())
    else:
        url = input('%s Target URL: ' % que).strip()
        if not url:
            print('%s No URL provided.' % bad)
            return
        extensions = input('%s Extensions (e.g. php,html): ' % que).strip()
        wordlist = input('%s Wordlist: ' % que).strip()
        gobuster.dir_bust(url, wordlist=wordlist or None, extensions=extensions or None, out_dir=prompt_save())


def cli_gobuster(args):
    from modules.tools import gobuster
    if not gobuster.is_installed():
        print('%s Gobuster is not installed.' % bad)
        return 1
    if len(args) < 2:
        print('%s Usage: gobuster <dir|dns> <url|domain> [wordlist]' % bad)
        return 2
    mode, target = args[0], args[1]
    wordlist = args[2] if len(args) > 2 else None
    if mode == 'dns':
        return gobuster.dns_bust(target, wordlist=wordlist, out_dir=OUTPUT_DIR)
    else:
        return gobuster.dir_bust(target, wordlist=wordlist, out_dir=OUTPUT_DIR)


def ready_gobuster():
    from modules.tools import gobuster
    return gobuster.ready()


def run_wireshark():
    from modules.tools import wireshark
    if not wireshark.is_installed():
        print('%s Wireshark is not installed.' % bad)
        print('    %s' % wireshark.install_hint())
        return
    mode = input('%s Mode (capture/read/gui) [gui]: ' % que).strip().lower() or 'gui'
    if mode == 'capture':
        interface = input('%s Network interface: ' % que).strip()
        if not interface:
            print('%s No interface provided.' % bad)
            return
        packet_count = input('%s Packet count [100]: ' % que).strip()
        wireshark.capture_live(interface, packet_count=int(packet_count) if packet_count else 100,
                               out_dir=prompt_save())
    elif mode == 'read':
        pcap_file = input('%s PCAP file: ' % que).strip()
        if not pcap_file or not os.path.isfile(pcap_file):
            print('%s Invalid PCAP file.' % bad)
            return
        wireshark.read_pcap(pcap_file)
    else:
        wireshark.launch_gui()


def cli_wireshark(args):
    from modules.tools import wireshark
    if not wireshark.is_installed():
        print('%s Wireshark is not installed.' % bad)
        return 1
    if not args:
        wireshark.launch_gui()
        return 0
    if args[0] == 'capture' and len(args) > 1:
        return wireshark.capture_live(args[1], packet_count=int(args[2]) if len(args) > 2 else 100)
    elif args[0] == 'read' and len(args) > 1:
        return wireshark.read_pcap(args[1])
    else:
        print('%s Usage: wireshark [capture <interface> [count] | read <pcap_file>]' % bad)
        return 2


def ready_wireshark():
    from modules.tools import wireshark
    return wireshark.ready()


def run_cipher_toolkit():
    from modules.tools import cipher_toolkit
    print('%s Cipher Toolkit - Encryption/Decryption' % info)
    print('    1. Analyze cipher type (auto-detect)')
    print('    2. Encrypt text')
    print('    3. Decrypt text')
    print('    4. Base64 encode/decode')
    print('    5. Hex encode/decode')
    print('    6. Caesar cipher')
    print('    7. ROT13')
    print('    8. Vigenère cipher')
    print('    9. Hash text (MD5/SHA1/SHA256)')
    choice = input('%s Select option (1-9): ' % que).strip()

    if choice == '1':
        text = input('%s Enter text to analyze: ' % que).strip()
        analysis, suggestions = cipher_toolkit.analyze_cipher(text)
        print('%s Analysis Results:' % good)
        for cipher_type, detected in analysis.items():
            status = 'POSSIBLE' if detected else 'unlikely'
            print(f'  {cipher_type}: {status}')
        if suggestions:
            print('%s Suggestions: %s' % (info, ', '.join(suggestions)))
            auto_results = cipher_toolkit.auto_decrypt(text)
            print('%s Auto-decryption attempts:' % info)
            for method, result in list(auto_results.items())[:5]:
                print(f'  {method}: {result[:50]}...' if len(str(result)) > 50 else f'  {method}: {result}')

    elif choice == '2':
        text = input('%s Text to encrypt: ' % que).strip()
        method = input('%s Method (base64/hex/caesar/vigenere) [base64]: ' % que).strip() or 'base64'
        if method == 'base64':
            result = cipher_toolkit.base64_encode(text)
            print('%s Base64 Encoded: %s' % (good, result))
        elif method == 'hex':
            result = cipher_toolkit.hex_encode(text)
            print('%s Hex Encoded: %s' % (good, result))
        elif method == 'caesar':
            shift = input('%s Shift amount [3]: ' % que).strip() or '3'
            result = cipher_toolkit.caesar_encrypt(text, int(shift))
            print('%s Caesar Encrypted: %s' % (good, result))
        elif method == 'vigenere':
            key = input('%s Encryption key: ' % que).strip()
            result = cipher_toolkit.vigenere_encrypt(text, key)
            print('%s Vigenère Encrypted: %s' % (good, result))

    elif choice == '3':
        text = input('%s Text to decrypt: ' % que).strip()
        print('%s Attempting auto-decryption...' % run)
        results = cipher_toolkit.auto_decrypt(text)
        print('%s Possible decryptions:' % good)
        for method, result in results.items():
            print(f'  [{method}]: {result[:50]}...' if len(str(result)) > 50 else f'  [{method}]: {result}')
        save_dir = prompt_save()
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            output_file = os.path.join(save_dir, 'cipher_decryption_results.txt')
            with open(output_file, 'w') as f:
                for method, result in results.items():
                    f.write(f'{method}: {result}\n')
            print('%s Results saved to %s' % (good, os.path.relpath(output_file, HERE)))

    elif choice == '4':
        text = input('%s Text: ' % que).strip()
        op = input('%s Operation (encode/decode) [decode]: ' % que).strip().lower() or 'decode'
        if op == 'encode':
            result = cipher_toolkit.base64_encode(text)
            print('%s Base64: %s' % (good, result))
        else:
            result = cipher_toolkit.base64_decode(text)
            print('%s Decoded: %s' % (good, result))

    elif choice == '5':
        text = input('%s Text: ' % que).strip()
        op = input('%s Operation (encode/decode) [decode]: ' % que).strip().lower() or 'decode'
        if op == 'encode':
            result = cipher_toolkit.hex_encode(text)
            print('%s Hex: %s' % (good, result))
        else:
            result = cipher_toolkit.hex_decode(text)
            print('%s Decoded: %s' % (good, result))

    elif choice == '6':
        text = input('%s Text: ' % que).strip()
        shift = input('%s Shift [3]: ' % que).strip() or '3'
        results = cipher_toolkit.caesar_decrypt(text, int(shift))
        print('%s Caesar cipher attempts (all 26 shifts):' % good)
        for shift_val, result in results.items():
            print(f'  {shift_val}: {result}')

    elif choice == '7':
        text = input('%s Text: ' % que).strip()
        result = cipher_toolkit.rot13(text)
        print('%s ROT13: %s' % (good, result))

    elif choice == '8':
        text = input('%s Text: ' % que).strip()
        key = input('%s Encryption key: ' % que).strip()
        op = input('%s Operation (encrypt/decrypt) [decrypt]: ' % que).strip().lower() or 'decrypt'
        if op == 'encrypt':
            result = cipher_toolkit.vigenere_encrypt(text, key)
        else:
            result = cipher_toolkit.vigenere_decrypt(text, key)
        print('%s Result: %s' % (good, result))

    elif choice == '9':
        text = input('%s Text to hash: ' % que).strip()
        hash_type = input('%s Hash type (md5/sha1/sha256) [sha256]: ' % que).strip().lower() or 'sha256'
        if hash_type == 'md5':
            result = cipher_toolkit.md5_hash(text)
        elif hash_type == 'sha1':
            result = cipher_toolkit.sha1_hash(text)
        else:
            result = cipher_toolkit.sha256_hash(text)
        print('%s %s: %s' % (good, hash_type.upper(), result))


def cli_cipher_toolkit(args):
    from modules.tools import cipher_toolkit
    if not args:
        print('%s Usage: cipher_toolkit <analyze|encrypt|decrypt|base64|hex|caesar|rot13|vigenere|hash> [args...]' % bad)
        return 2

    command = args[0].lower()
    if command == 'analyze' and len(args) > 1:
        text = ' '.join(args[1:])
        analysis, suggestions = cipher_toolkit.analyze_cipher(text)
        for cipher_type, detected in analysis.items():
            print(f'{cipher_type}: {"DETECTED" if detected else "no"}')
        return 0

    elif command == 'auto' and len(args) > 1:
        text = ' '.join(args[1:])
        results = cipher_toolkit.auto_decrypt(text)
        for method, result in results.items():
            print(f'{method}: {result}')
        return 0

    elif command == 'base64' and len(args) > 1:
        text = ' '.join(args[1:])
        result = cipher_toolkit.base64_encode(text)
        print(result)
        return 0

    elif command == 'hex' and len(args) > 1:
        text = ' '.join(args[1:])
        result = cipher_toolkit.hex_encode(text)
        print(result)
        return 0

    elif command == 'rot13' and len(args) > 1:
        text = ' '.join(args[1:])
        result = cipher_toolkit.rot13(text)
        print(result)
        return 0

    elif command == 'caesar' and len(args) > 1:
        # A trailing numeric arg is the shift, not part of the text - it
        # must be excluded from `text` or it gets decrypted as if it were
        # part of the message (e.g. "caesar Khoor Zruog 3" would otherwise
        # try to decrypt "Khoor Zruog 3" instead of "Khoor Zruog").
        if args[-1].isdigit():
            shift = int(args[-1])
            text = ' '.join(args[1:-1])
        else:
            shift = 3
            text = ' '.join(args[1:])
        results = cipher_toolkit.caesar_decrypt(text, shift)
        for shift_val, result in results.items():
            print(f'{shift_val}: {result}')
        return 0

    print('%s Unknown command: %s' % (bad, command))
    return 2


def ready_cipher_toolkit():
    from modules.tools import cipher_toolkit
    return cipher_toolkit.ready()


def run_advanced_crypto():
    from modules.tools import advanced_crypto
    ok, detail = advanced_crypto.ready()
    if not ok:
        print('%s Advanced crypto not ready: %s' % (bad, detail))
        print('    Install with: pip install cryptography')
        return

    print('%s Advanced Cryptography - Fernet & Modern Encryption' % info)
    print('    1. Generate new encryption key')
    print('    2. Encrypt text (Fernet)')
    print('    3. Decrypt text (Fernet)')
    print('    4. Derive key from password')
    print('    5. Brute force with common passwords')
    choice = input('%s Select option (1-5): ' % que).strip()

    if choice == '1':
        result = advanced_crypto.generate_fernet_key()
        if isinstance(result, dict):
            print('%s Generated Key: %s' % (good, result['key']))
            print('%s %s' % (info, result['note']))
        else:
            print('%s Error: %s' % (bad, result))

    elif choice == '2':
        text = input('%s Text to encrypt: ' % que).strip()
        key_choice = input('%s Use existing key? (y/n) [n]: ' % que).strip().lower()
        if key_choice == 'y':
            key = input('%s Encryption key: ' % que).strip()
        else:
            key = None
        result = advanced_crypto.fernet_encrypt(text, key)
        if isinstance(result, dict):
            print('%s Encrypted: %s' % (good, result['encrypted']))
            print('%s Key: %s' % (info, result['key']))
            print('%s %s' % (info, result['note']))
        else:
            print('%s Error: %s' % (bad, result))

    elif choice == '3':
        encrypted = input('%s Encrypted text: ' % que).strip()
        key = input('%s Decryption key: ' % que).strip()
        result = advanced_crypto.fernet_decrypt(encrypted, key)
        if isinstance(result, str) and not result.startswith('Decryption failed'):
            print('%s Decrypted: %s' % (good, result))
        else:
            print('%s Error: %s' % (bad, result))

    elif choice == '4':
        password = input('%s Password: ' % que).strip()
        result = advanced_crypto.derive_key_from_password(password)
        if isinstance(result, dict):
            print('%s Derived Key: %s' % (good, result['key']))
            print('%s Salt: %s' % (info, result['salt']))
            print('%s %s' % (info, result['note']))
        else:
            print('%s Error: %s' % (bad, result))

    elif choice == '5':
        encrypted = input('%s Encrypted text: ' % que).strip()
        wordlist = input('%s Wordlist file (optional): ' % que).strip()
        print('%s Attempting to crack with common passwords...' % run)
        results = advanced_crypto.try_common_passwords(encrypted, wordlist or None)
        if results and 'status' not in results:
            print('%s Successful decryptions found:' % good)
            for password, decrypted in results.items():
                print(f'  Password: {password}')
                print(f'  Decrypted: {decrypted[:50]}...' if len(decrypted) > 50 else f'  Decrypted: {decrypted}')
        else:
            print('%s No successful decryptions' % info)


def cli_advanced_crypto(args):
    from modules.tools import advanced_crypto
    if not args:
        print('%s Usage: advanced_crypto <generate|encrypt|decrypt> [args...]' % bad)
        return 2

    command = args[0].lower()
    if command == 'generate':
        result = advanced_crypto.generate_fernet_key()
        if isinstance(result, dict):
            print(result['key'])
            return 0
        print('%s Error: %s' % (bad, result))
        return 1

    print('%s Unknown command: %s' % (bad, command))
    return 2


def ready_advanced_crypto():
    from modules.tools import advanced_crypto
    return advanced_crypto.ready()


# --- Tool registry ----------------------------------------------------------
# Every tool runs directly in this terminal; nothing opens a browser or a repo.
# key: menu number.  aliases: names accepted at the prompt and on the CLI.
# runner: interactive.  cli: non-interactive handler (or None).  ready: health.

# Red Team & Advanced Testing Tools Handlers (Tools 38-52)
#
# Each module owns its own cli(args) - the formatting, subprocess calls, and
# exit code all live in modules/tools/<name>.py.  menu.py only prompts (to
# stay consistent with the other tool families above) and hands off.

def ready_amass():
    return amass.ready()

def cli_amass(args):
    return amass.cli(args)

def run_amass():
    domain = session_prompt('domain', 'Target domain for Amass')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    amass.cli([domain])

# PureDNS
def ready_puredns():
    return puredns.ready()

def cli_puredns(args):
    return puredns.cli(args)

def run_puredns():
    domain = session_prompt('domain', 'Target domain for PureDNS')
    if not domain:
        print('%s No domain provided.' % bad)
        return
    puredns.cli([domain])

# BloodHound
def ready_bloodhound():
    return bloodhound.ready()

def cli_bloodhound(args):
    return bloodhound.cli(args)

def run_bloodhound():
    print('%s BloodHound - AD attack path visualization' % info)
    print('%s Available: collect, query_paths <source> <target>, list_admins' % info)
    bloodhound.cli([])

# Gophish
def ready_gophish():
    return gophish.ready()

def cli_gophish(args):
    return gophish.cli(args)

def run_gophish():
    gophish.cli([])

# Proxychains
def ready_proxychains():
    return proxychains.ready()

def cli_proxychains(args):
    return proxychains.cli(args)

def run_proxychains():
    print('%s Proxychains - traffic routing through SOCKS proxy' % info)
    proxychains.cli([])

# Chisel
def ready_chisel():
    return chisel.ready()

def cli_chisel(args):
    return chisel.cli(args)

def run_chisel():
    mode = input('%s Mode (server/client): ' % que).strip().lower()
    if mode == 'client':
        server_url = input('%s Server URL: ' % que).strip()
        chisel.cli(['client', server_url] if server_url else [])
    else:
        chisel.cli(['server'])

# Sliver C2
def ready_sliver_c2():
    return sliver_c2.ready()

def cli_sliver_c2(args):
    return sliver_c2.cli(args)

def run_sliver_c2():
    sliver_c2.cli([])

# Havoc C2
def ready_havoc_c2():
    return havoc_c2.ready()

def cli_havoc_c2(args):
    return havoc_c2.cli(args)

def run_havoc_c2():
    havoc_c2.cli([])

# Mythic C2
def ready_mythic_c2():
    return mythic_c2.ready()

def cli_mythic_c2(args):
    return mythic_c2.cli(args)

def run_mythic_c2():
    mythic_c2.cli([])

# pypykatz
def ready_pypykatz():
    return pypykatz.ready()

def cli_pypykatz(args):
    return pypykatz.cli(args)

def run_pypykatz():
    dump_file = input('%s LSASS dump file path: ' % que).strip()
    if not dump_file:
        print('%s No file provided.' % bad)
        return
    pypykatz.cli([dump_file])

# Impacket
def ready_impacket_tools():
    return impacket_tools.ready()

def cli_impacket_tools(args):
    return impacket_tools.cli(args)

def run_impacket_tools():
    print('%s Impacket - Windows protocol exploitation' % info)
    impacket_tools.cli(['utilities'])

# Certipy
def ready_certipy():
    return certipy.ready()

def cli_certipy(args):
    return certipy.cli(args)

def run_certipy():
    print('%s Certipy - Active Directory Certificate Services exploitation' % info)
    certipy.cli(['vulns'])

# LotL Techniques
def ready_lotl_techniques():
    return lotl_techniques.ready()

def cli_lotl_techniques(args):
    return lotl_techniques.cli(args)

def run_lotl_techniques():
    lotl_techniques.cli([])

# MITRE CALDERA
def ready_mitre_caldera():
    return mitre_caldera.ready()

def cli_mitre_caldera(args):
    return mitre_caldera.cli(args)

def run_mitre_caldera():
    print('%s MITRE CALDERA - automated adversary emulation' % info)
    mitre_caldera.cli(['techniques'])

# Atomic Red Team
def ready_atomic_red_team():
    return atomic_red_team.ready()

def cli_atomic_red_team(args):
    return atomic_red_team.cli(args)

def run_atomic_red_team():
    print('%s Atomic Red Team - tightly scoped security tests' % info)
    atomic_red_team.cli(['tests'])

TOOLS = [
    # Domain & Network (1-11)
    {'key': '1', 'name': 'Domain Scanner', 'cat': 'Domain & Network',
     'aliases': ['domain', 'scan', 'scanner'],
     'desc': 'Full domain recon & vuln scan',
     'runner': run_domain_scanner, 'cli': cli_domain, 'ready': ready_domain},
    {'key': '2', 'name': 'Sublist3r', 'cat': 'Domain & Network',
     'aliases': ['sublist3r', 'subdomains', 'subs'],
     'desc': 'Subdomain enumeration (active)',
     'runner': run_sublist3r, 'cli': cli_sublist3r, 'ready': ready_sublist3r},
    {'key': '3', 'name': 'crt.sh', 'cat': 'Domain & Network',
     'aliases': ['crtsh', 'crt', 'ct'],
     'desc': 'Passive subdomains from CT logs',
     'runner': run_crtsh, 'cli': cli_crtsh, 'ready': _ready_http},
    {'key': '4', 'name': 'WHOIS', 'cat': 'Domain & Network',
     'aliases': ['whois'],
     'desc': 'Domain registration lookup',
     'runner': run_whois, 'cli': cli_whois, 'ready': _ready_http},
    {'key': '5', 'name': 'Wayback', 'cat': 'Domain & Network',
     'aliases': ['wayback', 'archive', 'wb'],
     'desc': 'Historical URLs from the Web Archive',
     'runner': run_wayback, 'cli': cli_wayback, 'ready': _ready_http},
    {'key': '6', 'name': 'theHarvester', 'cat': 'Domain & Network',
     'aliases': ['theharvester', 'harvester', 'th'],
     'desc': 'Emails, hosts & names from public sources',
     'runner': run_theharvester, 'cli': cli_theharvester, 'ready': ready_theharvester},
    {'key': '7', 'name': 'IP Geo', 'cat': 'Domain & Network',
     'aliases': ['ipgeo', 'geo', 'ip'],
     'desc': 'IP geolocation & ASN/ISP lookup',
     'runner': run_ipgeo, 'cli': cli_ipgeo, 'ready': _ready_http},
    {'key': '8', 'name': 'Nmap', 'cat': 'Domain & Network',
     'aliases': ['nmap', 'portscan', 'ports'],
     'desc': 'Port & service scan (profiles)',
     'runner': run_nmap, 'cli': cli_nmap, 'ready': ready_nmap},
    {'key': '9', 'name': 'assetfinder', 'cat': 'Domain & Network',
     'aliases': ['assetfinder', 'assets'],
     'desc': 'Fast passive subdomain discovery',
     'runner': run_assetfinder, 'cli': cli_assetfinder, 'ready': ready_assetfinder},
    {'key': '10', 'name': 'subfinder', 'cat': 'Domain & Network',
     'aliases': ['subfinder', 'findsub'],
     'desc': 'Comprehensive subdomain enumeration (20+ sources)',
     'runner': run_subfinder, 'cli': cli_subfinder, 'ready': ready_subfinder},
    {'key': '11', 'name': 'httpx', 'cat': 'Domain & Network',
     'aliases': ['httpx', 'http', 'probe'],
     'desc': 'Fast HTTP prober (status, title, headers)',
     'runner': run_httpx, 'cli': cli_httpx, 'ready': ready_httpx},
    # Identity & Social (12-17)
    {'key': '12', 'name': 'Sherlock', 'cat': 'Identity & Social',
     'aliases': ['sherlock', 'username', 'user'],
     'desc': 'Hunt usernames across social networks',
     'runner': run_sherlock, 'cli': cli_sherlock, 'ready': ready_sherlock},
    {'key': '13', 'name': 'holehe', 'cat': 'Identity & Social',
     'aliases': ['holehe', 'email', 'mail'],
     'desc': 'Find sites where an email is registered',
     'runner': run_holehe, 'cli': cli_holehe, 'ready': ready_holehe},
    {'key': '14', 'name': 'User Scanner', 'cat': 'Identity & Social',
     'aliases': ['userscanner', 'uscan', 'usc'],
     'desc': 'Email + username OSINT (350+ sites)',
     'runner': run_userscanner, 'cli': cli_userscanner, 'ready': ready_userscanner},
    {'key': '15', 'name': 'PhoneInfoga', 'cat': 'Identity & Social',
     'aliases': ['phoneinfoga', 'phone'],
     'desc': 'Phone number OSINT',
     'runner': run_phoneinfoga, 'cli': cli_phoneinfoga, 'ready': ready_phoneinfoga},
    {'key': '16', 'name': 'Osintgram', 'cat': 'Identity & Social',
     'aliases': ['osintgram', 'instagram', 'ig'],
     'desc': 'Instagram OSINT',
     'runner': run_osintgram, 'cli': None, 'ready': ready_osintgram},
    {'key': '17', 'name': 'SMTP Enum', 'cat': 'Identity & Social',
     'aliases': ['smtp', 'email-enum', 'smtpenum'],
     'desc': 'Email validation via SMTP probing',
     'runner': run_smtp_enum, 'cli': cli_smtp_enum, 'ready': ready_smtp_enum},
    # Search & Dorks (18-21)
    {'key': '18', 'name': 'GoogleDorks', 'cat': 'Search & Dorks',
     'aliases': ['googledorks', 'dorks', 'dork'],
     'desc': 'Google dork search-query builder',
     'runner': run_googledorks, 'cli': cli_googledorks, 'ready': ready_googledorks},
    {'key': '19', 'name': 'GitHub Dorks', 'cat': 'Search & Dorks',
     'aliases': ['githubdorks', 'ghdorks', 'github'],
     'desc': 'Find leaked secrets in a user/org/repo (GH_TOKEN)',
     'runner': run_githubdorks, 'cli': cli_githubdorks, 'ready': ready_githubdorks},
    {'key': '20', 'name': 'gau', 'cat': 'Search & Dorks',
     'aliases': ['gau', 'getallurls', 'urls'],
     'desc': 'Fetch URLs from Wayback/Common Crawl/URLScan',
     'runner': run_gau, 'cli': cli_gau, 'ready': ready_gau},
    {'key': '21', 'name': 'unfurl', 'cat': 'Search & Dorks',
     'aliases': ['unfurl', 'parse'],
     'desc': 'Parse and filter URLs',
     'runner': run_unfurl, 'cli': cli_unfurl, 'ready': ready_unfurl},
    # Vulnerability & Analysis (22-23)
    {'key': '22', 'name': 'nuclei', 'cat': 'Vulnerability & Analysis',
     'aliases': ['nuclei', 'vuln', 'templates'],
     'desc': 'Template-based vulnerability scanner',
     'runner': run_nuclei, 'cli': cli_nuclei, 'ready': ready_nuclei},
    {'key': '23', 'name': 'exiftool', 'cat': 'Vulnerability & Analysis',
     'aliases': ['exiftool', 'metadata', 'exif'],
     'desc': 'Extract metadata from files/images/PDFs',
     'runner': run_exiftool, 'cli': cli_exiftool, 'ready': ready_exiftool},
    # Dark Web (24-25)
    {'key': '24', 'name': 'OnionSearch', 'cat': 'Dark Web',
     'aliases': ['onionsearch', 'onion'],
     'desc': 'Darkweb .onion search (needs Tor)',
     'runner': run_onionsearch, 'cli': None, 'ready': ready_onionsearch},
    {'key': '25', 'name': 'Dark Web OSINT', 'cat': 'Dark Web',
     'aliases': ['darkweb', 'dark', 'dw'],
     'desc': 'Dark-web OSINT tool directory',
     'runner': run_darkweb, 'cli': None, 'ready': ready_darkweb},
    # Exploitation & Frameworks (26-27)
    {'key': '26', 'name': 'Metasploit', 'cat': 'Exploitation & Frameworks',
     'aliases': ['metasploit', 'msf', 'msfconsole'],
     'desc': 'Penetration testing framework & exploit manager',
     'runner': run_metasploit, 'cli': cli_metasploit, 'ready': ready_metasploit},
    {'key': '27', 'name': 'SearchSploit', 'cat': 'Exploitation & Frameworks',
     'aliases': ['searchsploit', 'exploit-db', 'exploitdb'],
     'desc': 'Search Exploit-DB for known exploits & vulnerabilities',
     'runner': run_searchsploit, 'cli': cli_searchsploit, 'ready': ready_searchsploit},
    # Web Application Testing (28-30)
    {'key': '28', 'name': 'SQLmap', 'cat': 'Web Application Testing',
     'aliases': ['sqlmap', 'sqli'],
     'desc': 'Automatic SQL injection detection and exploitation',
     'runner': run_sqlmap, 'cli': cli_sqlmap, 'ready': ready_sqlmap},
    {'key': '29', 'name': 'Nikto', 'cat': 'Web Application Testing',
     'aliases': ['nikto', 'webserver'],
     'desc': 'Web server vulnerability scanner (6700+ checks)',
     'runner': run_nikto, 'cli': cli_nikto, 'ready': ready_nikto},
    {'key': '30', 'name': 'Gobuster', 'cat': 'Web Application Testing',
     'aliases': ['gobuster', 'fuzz', 'dir'],
     'desc': 'Directory/DNS/VHOST brute force utility',
     'runner': run_gobuster, 'cli': cli_gobuster, 'ready': ready_gobuster},
    # Credential Testing (31-33)
    {'key': '31', 'name': 'Hydra', 'cat': 'Credential Testing',
     'aliases': ['hydra', 'brute', 'bruteforce'],
     'desc': 'Fast network logon cracker (SSH/FTP/HTTP/etc)',
     'runner': run_hydra, 'cli': cli_hydra, 'ready': ready_hydra},
    {'key': '32', 'name': 'John the Ripper', 'cat': 'Credential Testing',
     'aliases': ['john', 'crack', 'password'],
     'desc': 'Fast password cracking tool',
     'runner': run_john, 'cli': cli_john, 'ready': ready_john},
    {'key': '33', 'name': 'Hashcat', 'cat': 'Credential Testing',
     'aliases': ['hashcat', 'gpu-crack'],
     'desc': 'GPU-accelerated password recovery (300+ hashes)',
     'runner': run_hashcat, 'cli': cli_hashcat, 'ready': ready_hashcat},
    # Wireless & Network (34-35)
    {'key': '34', 'name': 'Aircrack-ng', 'cat': 'Wireless & Network',
     'aliases': ['aircrack', 'wireless', 'wifi'],
     'desc': 'Wireless network security auditing suite',
     'runner': run_aircrack, 'cli': cli_aircrack, 'ready': ready_aircrack},
    {'key': '35', 'name': 'Wireshark', 'cat': 'Wireless & Network',
     'aliases': ['wireshark', 'tshark', 'pcap', 'sniffer'],
     'desc': 'Network protocol analyzer & packet capture',
     'runner': run_wireshark, 'cli': cli_wireshark, 'ready': ready_wireshark},
    # Cryptography & Cipher Tools (36-37)
    {'key': '36', 'name': 'Cipher Toolkit', 'cat': 'Cryptography & Cipher Tools',
     'aliases': ['cipher', 'crypto', 'encode', 'decode'],
     'desc': 'Encryption/decryption with automatic cipher detection',
     'runner': run_cipher_toolkit, 'cli': cli_cipher_toolkit, 'ready': ready_cipher_toolkit},
    {'key': '37', 'name': 'Advanced Crypto', 'cat': 'Cryptography & Cipher Tools',
     'aliases': ['advanced_crypto', 'fernet', 'aes', 'encryption'],
     'desc': 'Modern encryption (Fernet/AES) with password derivation',
     'runner': run_advanced_crypto, 'cli': cli_advanced_crypto, 'ready': ready_advanced_crypto},
    # Phase 1: Advanced Reconnaissance
    {
        'key': '38',
        'name': 'Amass',
        'cat': 'Advanced Reconnaissance',
        'aliases': ['amass', 'dns', 'enum'],
        'desc': amass.DESCRIPTION,
        'runner': run_amass,
        'cli': cli_amass,
        'ready': ready_amass,
    },
    {
        'key': '39',
        'name': 'PureDNS',
        'cat': 'Advanced Reconnaissance',
        'aliases': ['puredns', 'dns_brute', 'resolver'],
        'desc': puredns.DESCRIPTION,
        'runner': run_puredns,
        'cli': cli_puredns,
        'ready': ready_puredns,
    },
    {
        'key': '40',
        'name': 'BloodHound',
        'cat': 'Advanced Reconnaissance',
        'aliases': ['bloodhound', 'ad_mapping', 'attack_paths'],
        'desc': bloodhound.DESCRIPTION,
        'runner': run_bloodhound,
        'cli': cli_bloodhound,
        'ready': ready_bloodhound,
    },
    # Phase 2: Initial Access & Delivery
    {
        'key': '41',
        'name': 'Gophish',
        'cat': 'Initial Access & Delivery',
        'aliases': ['gophish', 'phishing', 'awareness'],
        'desc': gophish.DESCRIPTION,
        'runner': run_gophish,
        'cli': cli_gophish,
        'ready': ready_gophish,
    },
    {
        'key': '42',
        'name': 'Proxychains',
        'cat': 'Initial Access & Delivery',
        'aliases': ['proxychains', 'proxy', 'socks'],
        'desc': proxychains.DESCRIPTION,
        'runner': run_proxychains,
        'cli': cli_proxychains,
        'ready': ready_proxychains,
    },
    {
        'key': '43',
        'name': 'Chisel',
        'cat': 'Initial Access & Delivery',
        'aliases': ['chisel', 'tunnel', 'pivot'],
        'desc': chisel.DESCRIPTION,
        'runner': run_chisel,
        'cli': cli_chisel,
        'ready': ready_chisel,
    },
    # Phase 3: Command & Control
    {
        'key': '44',
        'name': 'Sliver C2',
        'cat': 'C2 & Command Control',
        'aliases': ['sliver', 'open_c2', 'implant'],
        'desc': sliver_c2.DESCRIPTION,
        'runner': run_sliver_c2,
        'cli': cli_sliver_c2,
        'ready': ready_sliver_c2,
    },
    {
        'key': '45',
        'name': 'Havoc C2',
        'cat': 'C2 & Command Control',
        'aliases': ['havoc', 'c++_c2', 'evasion'],
        'desc': havoc_c2.DESCRIPTION,
        'runner': run_havoc_c2,
        'cli': cli_havoc_c2,
        'ready': ready_havoc_c2,
    },
    {
        'key': '46',
        'name': 'Mythic C2',
        'cat': 'C2 & Command Control',
        'aliases': ['mythic', 'modular_c2', 'docker_c2'],
        'desc': mythic_c2.DESCRIPTION,
        'runner': run_mythic_c2,
        'cli': cli_mythic_c2,
        'ready': ready_mythic_c2,
    },
    # Phase 4: Post-Exploitation & Privilege Escalation
    {
        'key': '47',
        'name': 'pypykatz',
        'cat': 'Post-Exploitation',
        'aliases': ['pypykatz', 'credential_extraction', 'lsass'],
        'desc': pypykatz.DESCRIPTION,
        'runner': run_pypykatz,
        'cli': cli_pypykatz,
        'ready': ready_pypykatz,
    },
    {
        'key': '48',
        'name': 'Impacket',
        'cat': 'Post-Exploitation',
        'aliases': ['impacket', 'psexec', 'wmiexec'],
        'desc': impacket_tools.DESCRIPTION,
        'runner': run_impacket_tools,
        'cli': cli_impacket_tools,
        'ready': ready_impacket_tools,
    },
    {
        'key': '49',
        'name': 'Certipy',
        'cat': 'Post-Exploitation',
        'aliases': ['certipy', 'adcs', 'pkinit'],
        'desc': certipy.DESCRIPTION,
        'runner': run_certipy,
        'cli': cli_certipy,
        'ready': ready_certipy,
    },
    {
        'key': '50',
        'name': 'LotL Techniques',
        'cat': 'Post-Exploitation',
        'aliases': ['lotl', 'living_off_land', 'windows_native'],
        'desc': lotl_techniques.DESCRIPTION,
        'runner': run_lotl_techniques,
        'cli': cli_lotl_techniques,
        'ready': ready_lotl_techniques,
    },
    # Phase 5: Continuous Security Validation
    {
        'key': '51',
        'name': 'MITRE CALDERA',
        'cat': 'Continuous Security Testing',
        'aliases': ['caldera', 'mitre', 'adversary_emulation'],
        'desc': mitre_caldera.DESCRIPTION,
        'runner': run_mitre_caldera,
        'cli': cli_mitre_caldera,
        'ready': ready_mitre_caldera,
    },
    {
        'key': '52',
        'name': 'Atomic Red Team',
        'cat': 'Continuous Security Testing',
        'aliases': ['atomic', 'att&k_tests', 'security_tests'],
        'desc': atomic_red_team.DESCRIPTION,
        'runner': run_atomic_red_team,
        'cli': cli_atomic_red_team,
        'ready': ready_atomic_red_team,
    },
]

# Main menu loop and execution
BANNER = r"""
   ██  ██  █████   ██       ████   ██████  ██████  ██  ██   ████   ██  ██
    ████   ██  ██  ██      ██  ██    ██      ██    ██  ██  ██  ██  ██  ██
     ██    █████   ██      ██  ██    ██      ██    ██████  ██ ███  ██████
    ████   ██      ██      ██  ██    ██      ██        ██  ███ ██      ██
   ██  ██  ██      ██████   ████   ██████    ██        ██   ████       ██"""


def print_banner():
    """Print the Striker ASCII banner and subtitle."""
    print('%s%s%s' % (cyan, BANNER, end))
    print('%s%s%s' % (cyan, '═' * 76, end))
    print('   >> Striker - Penetration Testing Toolkit')
    print('   >> Xploit404 Edition | Red Team Operations')
    print('%s%s%s' % (cyan, '═' * 76, end))


def interactive_loop():
    """Main interactive menu loop."""
    print_banner()
    list_tools()
    print('%s%s%s' % (cyan, '═' * 70, end))
    print(' Commands: [#] run tool | target | profile | doctor | list | help | quit')
    print('%s%s%s' % (cyan, '═' * 70, end))

    while True:
        try:
            cmd = input('\n%s striker> ' % que).strip().lower()

            if not cmd:
                continue
            
            # Parse command
            parts = cmd.split()
            tool_id = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Handle special commands
            if tool_id in ['quit', 'exit', 'q']:
                print('%s Exiting...' % good)
                break
            
            elif tool_id == 'help' or tool_id == '?':
                print_help()
                continue
            
            elif tool_id == 'doctor':
                run_doctor_check()
                continue
            
            elif tool_id == 'profile':
                set_profile()
                continue
            
            elif tool_id == 'target':
                set_target()
                continue
            
            elif tool_id == 'list' or tool_id == 'ls':
                list_tools()
                continue
            
            # Find and run tool by ID or alias
            tool = None
            
            # Try direct numeric ID
            for t in TOOLS:
                if t['key'] == tool_id or t['key'] == tool_id.lstrip('0'):
                    tool = t
                    break
            
            # Try alias match
            if not tool:
                for t in TOOLS:
                    if tool_id in t.get('aliases', []):
                        tool = t
                        break
            
            if tool:
                # Check if tool is ready
                ready_func = tool.get('ready')
                if ready_func:
                    is_ready, status = ready_func()
                    if not is_ready:
                        print('%s Tool not available: %s' % (bad, status))
                        continue

                # A one-line reminder of what this tool actually does, shown
                # before it asks for input or runs - every TOOLS entry already
                # carries this description for the menu listing, so this is
                # just showing it again at the point it's actually useful.
                if tool.get('desc'):
                    print('%s %s' % (info, tool['desc']))

                # Run tool with CLI handler if args provided, otherwise runner.
                # Every tool prints its own output and returns an exit code (cli)
                # or None (runner) - the dispatcher has nothing left to print.
                if args:
                    cli_func = tool.get('cli')
                    if cli_func:
                        cli_func(args)
                else:
                    # Loop the interactive runner by default so one selection
                    # can cover several searches/scans (e.g. searchsploit,
                    # then a follow-up query) instead of forcing a full
                    # return-to-menu and re-select for every single use.
                    # No y/n confirmation between runs - looping again is the
                    # default (just press Enter); typing quit is the only way
                    # out, same as the single-shot pause below. Only the
                    # args-less path loops - a fixed `tool args` invocation
                    # would just repeat identical results.
                    runner_func = tool.get('runner')
                    if runner_func:
                        while True:
                            runner_func()
                            if input('\n').strip().lower() in ('quit', 'exit', 'q'):
                                break
                        continue

                # Hold on the finished output until the user is ready to move
                # on, instead of immediately reprinting the menu prompt.
                # This always returns to the menu, whatever is typed here -
                # "quit" pops up one level (tool -> menu); the same word at
                # the striker> prompt itself (handled above) pops up the next
                # level (menu -> exit program).
                input('\n')
            else:
                print('%s Unknown command: %s' % (bad, tool_id))
                print('%s Type "help" for available commands' % info)
        
        except KeyboardInterrupt:
            print('\n%s Interrupted' % bad)
            break
        except Exception as e:
            print('%s Error: %s' % (bad, str(e)))


def print_help():
    """Print help menu."""
    print('''
%s Available Commands:

  Tools:
    <number>              Run tool by ID (1-52)
    <alias>               Run tool by alias (e.g., "nmap", "cipher")
    list                  List all tools
    doctor                Check tool readiness & configuration

  Session:
    target                Set domain/username target
    profile               Set testing profile (standard/intensive)

  System:
    help, ?               Show this help
    quit, exit            Exit program
    clear                 Clear screen

  Examples:
    1                     Run Domain Scanner
    38                    Run Amass
    nmap example.com      Run Nmap against example.com
    cipher analyze "text" Run Cipher Toolkit analysis

%s Version 2.0 | 52 Tools | Red Team Edition
''' % (cyan, good))


def list_tools():
    """List all available tools, grouped by category, with a ready/not-ready
    status icon per tool (mirrors doctor's readiness check)."""
    current_cat = None
    for tool in TOOLS:
        cat = tool.get('cat', 'Unknown')

        if cat != current_cat:
            print('\n%s[%s]%s' % (cyan, cat, end))
            print('-' * 70)
            current_cat = cat

        ready_func = tool.get('ready')
        try:
            is_ready, _ = ready_func() if ready_func else (True, '')
        except Exception:  # noqa: BLE001 - a broken readiness check shouldn't break listing
            is_ready = False
        icon = ('%s✓%s' % (green, end)) if is_ready else ('%s✗%s' % (red, end))

        key = tool['key'].rjust(2)
        name = tool['name'].ljust(28)
        desc = tool['desc'][:35]
        print('  [%s] %s %s - %s' % (key, icon, name, desc))

    print()


def run_doctor_check():
    """Run toolkit doctor check."""
    print('\n%s Checking toolkit status...\n' % info)
    
    ready_count = 0
    not_ready_count = 0
    
    current_cat = None
    for tool in TOOLS:
        cat = tool.get('cat', 'Unknown')
        
        if cat != current_cat:
            print('\n%s[%s]%s' % (cyan, cat, end))
            current_cat = cat

        ready_func = tool.get('ready')
        if ready_func:
            is_ready, status = ready_func()
            status_icon = good + '✓' + end if is_ready else bad + '✗' + end
            
            if is_ready:
                ready_count += 1
            else:
                not_ready_count += 1
            
            name = tool['name'].ljust(25)
            print('  %s  %s %s' % (status_icon, name, status))
    
    print('\n%s Summary: %d ready, %d not ready' % (info, ready_count, not_ready_count))
    print('%s Toolkit completion: %d%% (%d/%d)\n' % (good, 
          100 * ready_count // len(TOOLS), ready_count, len(TOOLS)))


def main(argv=None):
    """CLI entry point. Parses argv, gates --intensive behind STRIKER_AUTHORIZED
    (so intensive mode can't be scripted/CI'd without an explicit opt-in), then
    dispatches to a tool or falls back to the interactive menu. Returns an
    int exit code rather than calling sys.exit directly, so it stays testable."""
    argv = sys.argv[1:] if argv is None else argv

    if argv and argv[0] == '--intensive':
        if os.environ.get('STRIKER_AUTHORIZED') != '1':
            print('%s Intensive mode requires STRIKER_AUTHORIZED=1 to confirm '
                  'you are authorized to test the target.' % bad)
            return 2
        activate_profile('intensive', authorized=True)
        argv = argv[1:]
        if not argv:
            print_help()
            return 2

    if argv:
        tool_arg = argv[0]
        tool_args = argv[1:]

        if tool_arg in ('help', '?'):
            print_help()
        elif tool_arg == 'doctor':
            run_doctor_check()
        elif tool_arg in ('list', 'ls'):
            list_tools()
        elif tool_arg in ('quit', 'exit'):
            pass
        else:
            tool = None
            for t in TOOLS:
                if t['key'] == tool_arg or t['key'].lstrip('0') == tool_arg or tool_arg in t.get('aliases', []):
                    tool = t
                    break

            if tool:
                try:
                    # cli() prints its own output and returns an exit code,
                    # which becomes this process's exit status; runner()
                    # prints its own output and returns None (interactive
                    # path, no code to give). Wrapped in try/except so an
                    # unexpected failure deep inside a tool (a subprocess
                    # raising OSError, Ctrl+C mid-scan, etc.) prints a clean
                    # error instead of a raw traceback - interactive_loop()
                    # already has this safety net per-command; the
                    # non-interactive `python menu.py <tool> <args>` path
                    # (this branch) previously did not.
                    if tool_args:
                        cli_func = tool.get('cli')
                        if cli_func:
                            return cli_func(tool_args) or 0
                    else:
                        runner_func = tool.get('runner')
                        if runner_func:
                            runner_func()
                except KeyboardInterrupt:
                    print('\n%s Interrupted' % bad)
                    return 130
                except Exception as e:  # noqa: BLE001 - never let a tool crash the CLI raw
                    print('%s Error: %s' % (bad, e))
                    return 1
            else:
                print('%s Unknown tool: %s' % (bad, tool_arg))
                return 1
        return 0

    # No arguments - interactive mode (beautiful UI, falling back to the
    # plain REPL if menu_ui/colorama isn't available)
    try:
        from menu_ui import interactive_menu
        interactive_menu()
    except ImportError:
        interactive_loop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
