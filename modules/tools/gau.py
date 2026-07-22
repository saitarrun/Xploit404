"""gau (getallurls) — fetch URLs from Wayback Machine, Common Crawl, and URLScan.

Aggregates historical and indexed URLs for a domain in one go.
"""

import os
import shutil
import subprocess

from modules.tools import profiles

def binary():
    found = shutil.which('gau')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/gau', '/usr/local/bin/gau'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    return 'go install github.com/lc/gau/v2/cmd/gau@latest'

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready'

def run(domain, sources='all', out_dir=None, profile=profiles.STANDARD):
    """Fetch URLs from archives for a domain."""
    bin = binary()
    if not bin:
        raise RuntimeError('gau is not installed')
    command = [bin] + profiles.args_for('gau', profile)
    if sources != 'all':
        command.extend(['--sources', sources])
    command.append(domain)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'gau_%s.txt' % domain.replace('/', '_'))
        print('[run] %s > %s' % (' '.join(command), out_file), flush=True)
        with open(out_file, 'w') as f:
            return subprocess.call(command, stdout=f, stderr=subprocess.DEVNULL)
    else:
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)
