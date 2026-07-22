"""Aircrack-ng — Wireless network security auditing toolkit.

Aircrack-ng is a complete suite of tools to assess WiFi network security.
It focuses on different areas of WiFi security: monitoring, attacking, testing,
and cracking.
"""

import os
import platform
import shutil
import subprocess

from modules.tools import profiles


def aircrack_bin():
    """Locate aircrack-ng binary."""
    found = shutil.which('aircrack-ng')
    if found:
        return found
    common_paths = ['/usr/bin/aircrack-ng', '/usr/local/bin/aircrack-ng']
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def airodump_bin():
    """Locate airodump-ng binary."""
    found = shutil.which('airodump-ng')
    if found:
        return found
    common_paths = ['/usr/bin/airodump-ng', '/usr/local/bin/airodump-ng']
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if aircrack-ng suite is installed."""
    return aircrack_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'apt install aircrack-ng (Linux) or brew install aircrack-ng (macOS)'


def ready():
    """Check if aircrack-ng suite is ready."""
    binary = aircrack_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '-h'], capture_output=True,
                                text=True, timeout=5)
        return True, 'ready (monitor mode required for active attacks)'
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def crack_handshake(capture_file, wordlist=None, out_dir=None, profile=profiles.STANDARD):
    """Crack WPA/WPA2 handshake.

    Args:
        capture_file: .cap file with handshake
        wordlist: Dictionary file for cracking
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = aircrack_bin()
    if not binary:
        raise RuntimeError('aircrack-ng is not installed')

    command = [binary, '-w', wordlist or '/usr/share/wordlists/rockyou.txt', capture_file]
    command.extend(profiles.args_for('aircrack', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def list_interfaces():
    """List available wireless interfaces.

    `iwconfig` is Linux-only (wireless-tools); macOS has no equivalent
    command, so this dispatches per platform instead of assuming Linux.
    """
    binary = aircrack_bin()
    if not binary:
        raise RuntimeError('aircrack-ng is not installed')

    print('[*] Wireless interfaces available:')

    if platform.system() == 'Darwin':
        try:
            result = subprocess.run(['networksetup', '-listallhardwareports'],
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            print('[-] Could not list interfaces: %s' % exc)
            return 1
        lines = result.stdout.splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip() == 'Hardware Port: Wi-Fi' and i + 1 < len(lines):
                device = lines[i + 1].strip().replace('Device: ', '')
                print('    %s (Wi-Fi)' % device)
                found = True
        if not found:
            print('[-] No Wi-Fi hardware port found via networksetup.')
            return 1
        return 0

    # Linux: prefer the modern `iw`, since `iwconfig` (wireless-tools) is
    # deprecated and often not installed on current distros.
    if shutil.which('iw'):
        return subprocess.call(['iw', 'dev'])
    if shutil.which('iwconfig'):
        return subprocess.call(['iwconfig'])
    print('[-] Neither `iw` nor `iwconfig` is installed '
          '(apt install iw, or iwconfig via wireless-tools).')
    return 1
