"""nuclei — template-based vulnerability scanner.

Scans for CVEs, misconfigurations, weak credentials, and known vulnerabilities.
Uses YAML templates from the community.
"""

import os
import shutil
import subprocess

from modules.tools import profiles

def binary():
    found = shutil.which('nuclei')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/nuclei', '/usr/local/bin/nuclei'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    return 'go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest'

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    return True, 'ready (update templates with: nuclei -update-templates)'

def run(target, severity='medium', out_dir=None, profile=profiles.STANDARD):
    """Run nuclei on target URL."""
    bin = binary()
    if not bin:
        raise RuntimeError('nuclei is not installed')
    command = ([bin, '-u', target, '-severity', severity]
               + profiles.args_for('nuclei', profile))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'nuclei_%s.txt' % target.replace('/', '_').replace(':', '_'))
        command.extend(['-o', out_file])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
