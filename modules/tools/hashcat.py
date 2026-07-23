"""Hashcat — Advanced password recovery tool.

Hashcat is the world's fastest and most advanced password recovery utility,
supporting five unique modes of attack. It supports 300+ hash types and
leverages GPU acceleration for extremely fast cracking.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def hashcat_bin():
    """Locate hashcat binary."""
    found = shutil.which('hashcat')
    if found:
        return found
    common_paths = [
        '/usr/bin/hashcat',
        '/usr/local/bin/hashcat',
        os.path.expanduser('~/hashcat/hashcat.bin'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if hashcat is installed."""
    return hashcat_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'Download from hashcat.net or apt install hashcat'


def ready():
    """Check if hashcat is ready."""
    binary = hashcat_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--version'], capture_output=True,
                                text=True, timeout=5)
        version = result.stdout.strip().split('\n')[0] if result.stdout else 'installed'
        return True, version
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def crack_hashes(hash_file, hash_type, wordlist=None, rules=None, out_dir=None,
                 profile=profiles.STANDARD):
    """Crack hashes with hashcat.

    Args:
        hash_file: File containing hashes
        hash_type: Hash type ID (0=MD5, 1400=SHA2-256, 3200=bcrypt, etc)
        wordlist: Dictionary file for attack mode 0 (dictionary)
        rules: Rules file for attack mode 0
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = hashcat_bin()
    if not binary:
        raise RuntimeError('hashcat is not installed')

    command = [binary, '-m', str(hash_type)]

    if rules:
        command.extend(['-r', rules])

    # hashcat's positional args are `hashfile [wordlist|mask]`, in that
    # order - hashfile must come first, or hashcat treats the wordlist as
    # the hashfile and every line in it as a malformed hash to parse.
    command.append(hash_file)

    if wordlist:
        command.append(wordlist)
    else:
        command.extend(['-a', '3'])  # Brute force mask attack

    command.extend(profiles.args_for('hashcat', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        potfile = os.path.join(out_dir, 'hashcat.pot')
        command.extend(['--potfile-path', potfile])

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def show_results(potfile=None):
    """Display cracked results."""
    binary = hashcat_bin()
    if not binary:
        raise RuntimeError('hashcat is not installed')

    command = [binary, '--show']
    if potfile:
        command.extend(['--potfile-path', potfile])

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
