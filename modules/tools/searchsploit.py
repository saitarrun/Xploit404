"""SearchSploit — Exploit-DB offline search utility.

searchsploit allows you to search for known exploits, vulnerability codes,
shellcodes, and papers from Exploit-DB directly from your terminal. It works
entirely offline, making it a critical component of penetration testing workflows.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


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

    command = [binary, query]
    if options:
        if isinstance(options, str):
            command.extend(options.split())
        else:
            command.extend(options)

    command.extend(profiles.args_for('searchsploit', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_query = query.replace('/', '_').replace(' ', '_').replace(':', '_')
        output_file = os.path.join(out_dir, 'searchsploit_%s.txt' % safe_query)
        # Redirect output to file
        with open(output_file, 'w') as f:
            print('[run] %s > %s' % (' '.join(command), output_file), flush=True)
            return subprocess.call(command, stdout=f, stderr=subprocess.STDOUT)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


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
