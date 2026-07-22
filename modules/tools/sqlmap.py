"""SQLmap — Automatic SQL injection and database takeover tool.

SQLmap is an open source penetration testing tool that automates the detection
and exploitation of SQL injection flaws. It comes with a powerful detection
engine and many features for database extraction.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def sqlmap_bin():
    """Locate sqlmap binary."""
    found = shutil.which('sqlmap')
    if found:
        return found
    common_paths = [
        '/usr/bin/sqlmap',
        '/usr/local/bin/sqlmap',
        os.path.expanduser('~/sqlmap/sqlmap.py'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if SQLmap is installed."""
    return sqlmap_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap'


def ready():
    """Check if SQLmap is ready."""
    binary = sqlmap_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '-h'], capture_output=True,
                                text=True, timeout=10)
        return True, 'ready'
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def scan_url(url, technique=None, out_dir=None, profile=profiles.STANDARD):
    """Scan URL for SQL injection vulnerabilities.

    Args:
        url: Target URL
        technique: Injection technique (B=Boolean, E=Error, U=Union, S=Stacked, T=Time)
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = sqlmap_bin()
    if not binary:
        raise RuntimeError('SQLmap is not installed')

    command = [binary, '-u', url, '--batch', '--risk=2', '--level=2']

    if technique:
        command.extend(['--technique=%s' % technique])

    command.extend(profiles.args_for('sqlmap', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_url = url.replace('/', '_').replace(':', '_').replace('?', '_')
        output_file = os.path.join(out_dir, 'sqlmap_%s.txt' % safe_url)
        with open(output_file, 'w') as f:
            print('[run] %s > %s' % (' '.join(command), output_file), flush=True)
            return subprocess.call(command, stdout=f, stderr=subprocess.STDOUT)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def scan_request(request_file, out_dir=None, profile=profiles.STANDARD):
    """Scan from HTTP request file."""
    binary = sqlmap_bin()
    if not binary:
        raise RuntimeError('SQLmap is not installed')

    command = [binary, '-r', request_file, '--batch', '--risk=2', '--level=2']
    command.extend(profiles.args_for('sqlmap', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
