"""subfinder — comprehensive subdomain enumeration across 20+ sources.

Combines Certificate Transparency, DNS APIs, WHOIS, and web scraping.
More coverage than assetfinder but may be slower.
"""

import os
import shutil
import subprocess

from modules.tools import profiles

def binary():
    found = shutil.which('subfinder')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/subfinder', '/usr/local/bin/subfinder'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    return 'go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest'

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready'

def run(domain, out_dir=None, profile=profiles.STANDARD):
    bin = binary()
    if not bin:
        raise RuntimeError('subfinder is not installed')
    command = [bin, '-d', domain] + profiles.args_for('subfinder', profile)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'subfinder_%s.txt' % domain.replace('/', '_'))
        command.extend(['-o', out_file])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
