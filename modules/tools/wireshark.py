"""Wireshark — Network protocol analyzer.

Wireshark is the world's foremost and widely-used network protocol analyzer.
It lets you see what's happening on your network at a microscopic level and is
the de facto (and often de jure) standard across many commercial and non-profit
enterprises, government agencies, and military organizations.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def tshark_bin():
    """Locate tshark (Wireshark CLI) binary."""
    found = shutil.which('tshark')
    if found:
        return found
    common_paths = [
        '/usr/bin/tshark',
        '/usr/local/bin/tshark',
        'C:\\Program Files\\Wireshark\\tshark.exe',
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def wireshark_bin():
    """Locate wireshark GUI binary."""
    found = shutil.which('wireshark')
    if found:
        return found
    common_paths = [
        '/usr/bin/wireshark',
        '/usr/local/bin/wireshark',
        'C:\\Program Files\\Wireshark\\Wireshark.exe',
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if Wireshark/tshark is installed."""
    return tshark_bin() is not None or wireshark_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'apt install wireshark (Linux) or brew install wireshark (macOS)'


def ready():
    """Check if Wireshark is ready."""
    binary = tshark_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--version'], capture_output=True,
                                text=True, timeout=5)
        version = result.stdout.strip().split('\n')[0] if result.stdout else 'installed'
        return True, version
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def capture_live(interface, capture_file=None, packet_count=None, filter_expr=None,
                 out_dir=None, profile=profiles.STANDARD):
    """Capture live traffic using tshark.

    Args:
        interface: Network interface (e.g., eth0, wlan0)
        capture_file: Output pcap file
        packet_count: Number of packets to capture (0 = unlimited)
        filter_expr: Capture filter (e.g., 'tcp port 80')
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = tshark_bin()
    if not binary:
        raise RuntimeError('tshark (Wireshark) is not installed')

    command = [binary, '-i', interface]

    if filter_expr:
        command.extend(['-f', filter_expr])

    if packet_count:
        command.extend(['-c', str(packet_count)])
    else:
        command.extend(['-c', '100'])  # Default 100 packets

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        capture_file = capture_file or os.path.join(out_dir, 'capture_%s.pcap' % interface)
        command.extend(['-w', capture_file])

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def read_pcap(pcap_file, filter_expr=None, output_format='text'):
    """Read and analyze pcap file.

    Args:
        pcap_file: PCAP file to read
        filter_expr: Display filter
        output_format: Output format (text, json, csv)
    """
    binary = tshark_bin()
    if not binary:
        raise RuntimeError('tshark (Wireshark) is not installed')

    command = [binary, '-r', pcap_file]

    if filter_expr:
        command.extend(['-Y', filter_expr])

    if output_format == 'json':
        command.append('-T json')
    elif output_format == 'csv':
        command.append('-T csv')

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def launch_gui():
    """Launch Wireshark GUI."""
    binary = wireshark_bin()
    if not binary:
        raise RuntimeError('Wireshark GUI is not installed')

    return subprocess.Popen([binary])
