"""assetfinder — fast passive subdomain discovery via APIs.

Uses Certificate Transparency, DNS, WHOIS, and other public data sources.
Typically faster and broader than crt.sh alone.
"""

import os
import shutil
import subprocess

def binary():
    found = shutil.which('assetfinder')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/assetfinder', '/usr/local/bin/assetfinder'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    import platform
    hints = {
        'darwin': 'brew install tomnomnom/assetfinder/assetfinder   or   go install github.com/tomnomnom/assetfinder@latest',
        'linux': 'go install github.com/tomnomnom/assetfinder@latest   (requires Go)',
        'windows': 'go install github.com/tomnomnom/assetfinder@latest   (requires Go)',
    }
    return hints.get(platform.system().lower(), 'see https://github.com/tomnomnom/assetfinder')

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready'

def run(domain, out_dir=None):
    bin = binary()
    if not bin:
        raise RuntimeError('assetfinder is not installed')
    command = [bin, domain]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'assetfinder_%s.txt' % domain.replace('/', '_'))
        print('[run] %s > %s' % (' '.join(command), out_file), flush=True)
        with open(out_file, 'w') as f:
            return subprocess.call(command, stdout=f, stderr=subprocess.DEVNULL)
    else:
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)
