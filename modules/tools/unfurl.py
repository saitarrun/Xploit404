"""unfurl — parse and filter URLs.

Extract domains, subdomains, paths, query params. Filter URLs by criteria.
"""

import os
import shutil
import subprocess

def binary():
    found = shutil.which('unfurl')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/unfurl', '/usr/local/bin/unfurl'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    return 'go install github.com/tomnomnom/unfurl@latest'

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready'

def run(url, mode='domains', out_dir=None):
    """Parse URLs. Modes: domains, subdomains, paths, keys, values."""
    bin = binary()
    if not bin:
        raise RuntimeError('unfurl is not installed')
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        # Read from stdin, write to file
        out_file = os.path.join(out_dir, 'unfurl_%s.txt' % mode)
        print('[run] echo "%s" | %s %s > %s' % (url, bin, mode, out_file), flush=True)
        with open(out_file, 'w') as f:
            p = subprocess.Popen([bin, mode], stdin=subprocess.PIPE, stdout=f,
                                stderr=subprocess.DEVNULL, text=True)
            p.communicate(url + '\n')
            return p.returncode
    else:
        print('[run] echo "%s" | %s %s' % (url, bin, mode), flush=True)
        p = subprocess.Popen([bin, mode], stdin=subprocess.PIPE, text=True)
        p.communicate(url + '\n')
        return p.returncode
