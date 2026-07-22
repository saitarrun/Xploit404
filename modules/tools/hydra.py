"""Hydra — Fast network logon cracker.

Hydra is a parallelized login cracker supporting numerous protocols to attack.
It is very fast and flexible, and new modules are easy to add. This tool makes
password testing against login services fast and efficient.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def hydra_bin():
    """Locate hydra binary."""
    found = shutil.which('hydra')
    if found:
        return found
    common_paths = ['/usr/bin/hydra', '/usr/local/bin/hydra', '/opt/hydra/hydra']
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if hydra is installed."""
    return hydra_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'apt install hydra (Linux) or brew install hydra (macOS)'


def ready():
    """Check if hydra is ready."""
    binary = hydra_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '-h'], capture_output=True,
                                text=True, timeout=5)
        return True, 'ready'
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def attack(target, protocol, username_file=None, password_file=None,
           username=None, password=None, out_dir=None, profile=profiles.STANDARD):
    """Run Hydra attack against target.

    Args:
        target: Target host:port
        protocol: Protocol (ssh, ftp, http-post, mysql, etc)
        username_file: File with usernames (one per line)
        password_file: File with passwords (one per line)
        username: Single username
        password: Single password
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = hydra_bin()
    if not binary:
        raise RuntimeError('hydra is not installed')

    command = [binary, '-f']

    if username_file:
        command.extend(['-L', username_file])
    elif username:
        command.extend(['-l', username])
    else:
        raise ValueError('Provide username or username_file')

    if password_file:
        command.extend(['-P', password_file])
    elif password:
        command.extend(['-p', password])
    else:
        raise ValueError('Provide password or password_file')

    command.extend(['-t', '4', target, protocol])
    command.extend(profiles.args_for('hydra', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_target = target.replace(':', '_').replace('/', '_')
        output_file = os.path.join(out_dir, 'hydra_%s_%s.txt' % (safe_target, protocol))
        with open(output_file, 'w') as f:
            print('[run] %s > %s' % (' '.join(command), output_file), flush=True)
            return subprocess.call(command, stdout=f, stderr=subprocess.STDOUT)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
