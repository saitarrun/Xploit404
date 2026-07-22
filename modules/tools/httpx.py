"""httpx — fast multi-threaded HTTP prober.

Checks if hosts are alive, gets status codes, titles, headers, redirects, response times.
"""

import os
import shlex
import shutil
import subprocess

from modules.tools import profiles

def binary():
    found = shutil.which('httpx')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/httpx', '/usr/local/bin/httpx'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    return 'go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest'

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready'

def run(target, flags=None, out_dir=None, profile=profiles.STANDARD):
    """Run httpx on target (URL, IP, or domain list file)."""
    bin = binary()
    if not bin:
        raise RuntimeError('httpx is not installed')
    user_args = shlex.split(flags) if isinstance(flags, str) else flags
    user_args = profiles.validate_user_args('httpx', user_args, profile)
    command = ([bin, '-u', target] + user_args
               + profiles.args_for('httpx', profile))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'httpx_%s.txt' % target.replace('/', '_').replace(':', '_'))
        command.extend(['-o', out_file])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
