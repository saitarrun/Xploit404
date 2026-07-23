"""SearchSploit — Exploit-DB offline search utility.

searchsploit allows you to search for known exploits, vulnerability codes,
shellcodes, and papers from Exploit-DB directly from your terminal. It works
entirely offline, making it a critical component of penetration testing workflows.
"""

import os
import shutil
import subprocess

from modules.tools import profiles

# searchsploit does a literal substring match against Exploit-DB titles, which
# use the affected product's name ("Apache Log4j") rather than the vulnerability's
# popular/media nickname - so the nickname alone often finds nothing even though
# real entries exist. Only the most well-known name/title mismatches are worth
# hardcoding here; this is a fallback tried when the literal query comes up empty,
# not a general synonym engine.
_ALIASES = {
    'log4shell': 'log4j',
    'shellshock': 'bash',
    'eternalblue': 'ms17-010',
    'bluekeep': 'rdp',
    'heartbleed': 'openssl',
    'printnightmare': 'print spooler',
    'proxyshell': 'exchange',
    'dirtycow': 'linux kernel',
    'dirty pipe': 'linux kernel',
    'zerologon': 'netlogon',
    'krack': 'wpa2',
}


def _no_results(text):
    return 'Exploits: No Results' in text and 'Shellcodes: No Results' in text


def searchsploit_bin():
    """Locate searchsploit binary."""
    found = shutil.which('searchsploit')
    if found:
        return found
    common_paths = [
        '/usr/bin/searchsploit',
        '/usr/local/bin/searchsploit',
        os.path.expanduser('~/.local/bin/searchsploit'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if searchsploit is installed."""
    return searchsploit_bin() is not None


def install_hint():
    """Return installation instructions for searchsploit."""
    return 'apt install exploitdb (Linux) or pip install exploitdb'


def ready():
    """Check if searchsploit is ready."""
    binary = searchsploit_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--help'], capture_output=True,
                                text=True, timeout=10)
        return True, 'ready'
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def _run(binary, query, options, profile):
    command = [binary, query]
    if options:
        if isinstance(options, str):
            command.extend(options.split())
        else:
            command.extend(options)
    command.extend(profiles.args_for('searchsploit', profile))
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.run(command, capture_output=True, text=True)


def search(query, out_dir=None, options=None, profile=profiles.STANDARD):
    """Search Exploit-DB for exploits matching query.

    Args:
        query: Search term (e.g., application name, CVE, keyword)
        out_dir: Directory to save results
        options: Additional command-line flags (e.g., '-j' for JSON)
        profile: Profile for setting command limits
    """
    binary = searchsploit_bin()
    if not binary:
        raise RuntimeError('searchsploit is not installed')

    result = _run(binary, query, options, profile)
    alias = _ALIASES.get(query.strip().lower())
    if alias and _no_results(result.stdout):
        print("[!] No results for %r - Exploit-DB titles this one %r, retrying..."
              % (query, alias), flush=True)
        result = _run(binary, alias, options, profile)

    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='')

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_query = query.replace('/', '_').replace(' ', '_').replace(':', '_')
        output_file = os.path.join(out_dir, 'searchsploit_%s.txt' % safe_query)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            print('[+] Saved to %s' % output_file)
        except OSError as exc:
            print('[error] Could not save: %s' % exc)

    return result.returncode


def search_cve(cve, out_dir=None, profile=profiles.STANDARD):
    """Search for a specific CVE."""
    return search(cve, out_dir=out_dir, profile=profile)


def search_app(app_name, out_dir=None, profile=profiles.STANDARD):
    """Search for exploits for a specific application."""
    return search(app_name, out_dir=out_dir, profile=profile)


def update_database():
    """Update the Exploit-DB database."""
    binary = searchsploit_bin()
    if not binary:
        raise RuntimeError('searchsploit is not installed')

    command = [binary, '-u']
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
