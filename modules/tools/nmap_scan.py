"""Nmap port / service scanner integration.

Nmap is a system package (not vendored); this module locates the binary, offers
a few ready-made scan profiles, and streams the scan to the terminal while
saving a normal-format report under ``output/``.

Some profiles (aggressive / OS detection / SYN scan) need root - run the
launcher with sudo for those; otherwise Nmap falls back to a TCP connect scan.
"""

import os
import shutil
import subprocess

# key -> (label, nmap arguments).  -Pn skips host discovery so hosts that block
# ping are still scanned; -T4 keeps timing brisk.
PROFILES = {
    '1': ('Quick (top 100 ports)', ['-F', '-T4', '-Pn']),
    '2': ('Service & version detection', ['-sV', '-T4', '-Pn']),
    '3': ('Full TCP (all 65535 ports)', ['-p-', '-T4', '-Pn']),
    '4': ('Aggressive (OS, scripts, traceroute)', ['-A', '-T4', '-Pn']),
    '5': ('Default scripts + versions', ['-sC', '-sV', '-T4', '-Pn']),
    '6': ('Intensive authorized (all TCP + versions + default scripts)',
          ['-p-', '-sV', '--version-all', '-sC', '-T4', '-Pn']),
}
DEFAULT_PROFILE = '2'
INTENSIVE_PROFILE = '6'


def nmap_bin():
    found = shutil.which('nmap')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/nmap', '/usr/local/bin/nmap'):
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    return nmap_bin() is not None


def install_hint():
    import platform
    return {
        'darwin': 'brew install nmap',
        'linux': 'sudo apt install nmap   (or dnf/pacman equivalent)',
        'windows': 'choco install nmap   (or download from nmap.org)',
    }.get(platform.system().lower(), 'install the nmap package for your OS')


def ready():
    binary = nmap_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--version'], capture_output=True,
                                text=True, timeout=10)
        version = result.stdout.splitlines()[0].strip() if result.stdout else 'installed'
    except (OSError, subprocess.SubprocessError):
        version = 'installed'
    return True, version


def run(target, args, out_dir=None):
    binary = nmap_bin()
    if not binary:
        raise RuntimeError('nmap is not installed')
    command = [binary] + list(args) + [target]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe = target.replace('/', '_').replace(':', '_')
        command.extend(['-oN', os.path.join(out_dir, 'nmap_%s.txt' % safe)])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
