"""Nikto — Web server scanner.

Nikto is an Open Source (GPL) web server scanner which performs comprehensive
tests against web servers for multiple items, including over 6700+ potentially
dangerous files/CGIs, checks for outdated versions, and other security issues.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def nikto_bin():
    """Locate nikto binary."""
    found = shutil.which('nikto')
    if found:
        return found
    common_paths = [
        '/usr/bin/nikto',
        '/usr/local/bin/nikto',
        os.path.expanduser('~/nikto/nikto.pl'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if Nikto is installed."""
    return nikto_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'apt install nikto (Linux) or brew install nikto (macOS)'


def ready():
    """Check if Nikto is ready."""
    binary = nikto_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '-Version'], capture_output=True,
                                text=True, timeout=5)
        version = result.stdout.split('\n')[0] if result.stdout else 'installed'
        return True, version.strip()
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def scan(target, port=None, ssl=False, out_dir=None, profile=profiles.STANDARD):
    """Scan web server with Nikto.

    Args:
        target: Target host or IP
        port: Port number (default: 80 or 443 if ssl=True)
        ssl: Use HTTPS
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = nikto_bin()
    if not binary:
        raise RuntimeError('Nikto is not installed')

    command = [binary, '-host', target]

    if port:
        command.extend(['-port', str(port)])

    if ssl:
        command.append('-ssl')

    command.extend(profiles.args_for('nikto', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_target = target.replace('/', '_').replace(':', '_')
        output_file = os.path.join(out_dir, 'nikto_%s.txt' % safe_target)
        command.extend(['-o', output_file, '-F', 'txt'])
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
