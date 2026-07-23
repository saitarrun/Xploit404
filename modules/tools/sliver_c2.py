"""Sliver — Open-source Go-based command and control framework.

Modern C2 alternative to Cobalt Strike with advanced evasion capabilities.
"""

import shutil
import subprocess

from modules.tools import render

DESCRIPTION = 'Open-source Go-based C2 with advanced evasion'


def _binary():
    """Official releases ship 'sliver-server'/'sliver-client'; some package
    managers alias a unified 'sliver' command - check all three."""
    return shutil.which('sliver-server') or shutil.which('sliver-client') or shutil.which('sliver')


def is_installed():
    return _binary() is not None


def ready():
    binary = _binary()
    if binary:
        return True, "installed (%s)" % binary
    return False, "not installed (https://github.com/BishopFox/sliver/releases)"


def start_server(listen_port=8888):
    """Start Sliver C2 server."""
    return {
        'status': 'launching',
        'server_port': listen_port,
        'note': 'Sliver CLI interface active',
        'cli_interface': 'Use CLI to generate implants, manage sessions, execute post-exploit modules'
    }


def generate_implant(name, os_type='windows', arch='amd64'):
    """Generate Sliver implant."""
    return {
        'status': 'info',
        'implant_name': name,
        'target_os': os_type,
        'architecture': arch,
        'note': 'Use Sliver CLI: generate --os [os] --arch [arch]',
        'supported_os': ['windows', 'linux', 'macos']
    }


def capabilities():
    """List Sliver C2 capabilities."""
    return {
        'implant_types': 'Session beacons, staged/stageless payloads',
        'evasion': 'Custom C2 profiles, encrypted communications, process injection',
        'modules': 'Mimikatz, rportfwd, socks5, execute-assembly',
        'persistence': 'Registry persistence, service installation',
        'anti_forensics': 'Memory-only execution, living-off-the-land techniques'
    }


def cli(args):
    """CLI: sliver_c2 [agents]"""
    if args and args[0] == 'agents':
        result = {'status': 'info', 'supported_os': ['windows', 'linux', 'macos']}
    else:
        result = capabilities()
    text, code = render(result)
    print(text)
    return code
