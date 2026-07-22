"""John the Ripper — Password cracking tool.

John the Ripper is a free password cracking software tool. Originally designed
for the Unix operating system, it now runs on fifteen different platforms.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def john_bin():
    """Locate john binary."""
    found = shutil.which('john')
    if found:
        return found
    common_paths = [
        '/usr/bin/john',
        '/usr/local/bin/john',
        '/opt/john/john',
        os.path.expanduser('~/john/john'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if John the Ripper is installed."""
    return john_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'apt install john (Linux) or brew install john-jumbo (macOS)'


def ready():
    """Check if John is ready."""
    binary = john_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--version'], capture_output=True,
                                text=True, timeout=5)
        version = result.stdout.splitlines()[0] if result.stdout else 'installed'
        return True, version.strip()
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def crack_hash(hash_file, wordlist=None, format_type=None, out_dir=None,
               profile=profiles.STANDARD):
    """Crack password hashes with John.

    Args:
        hash_file: File containing hashes
        wordlist: Wordlist file for dictionary attack
        format_type: Hash format (auto-detected if None)
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = john_bin()
    if not binary:
        raise RuntimeError('John the Ripper is not installed')

    command = [binary]

    if format_type:
        command.extend(['--format=%s' % format_type])

    if wordlist:
        command.extend(['--wordlist=%s' % wordlist])
    else:
        command.append('--incremental')

    command.extend(profiles.args_for('john', profile))
    command.append(hash_file)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def show_results(john_pot_file=None):
    """Display cracked passwords from John's pot file."""
    binary = john_bin()
    if not binary:
        raise RuntimeError('John the Ripper is not installed')

    command = [binary, '--show']
    if john_pot_file:
        command.extend(['--pot=%s' % john_pot_file])

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
