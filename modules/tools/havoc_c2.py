"""Havoc — Modern C++ command and control framework.

High-performance C2 framework with custom obfuscation and EDR evasion.
"""

import subprocess
import os

from modules.tools import render

DESCRIPTION = 'Modern C++ C2 framework with custom obfuscation'


def is_installed():
    try:
        result = subprocess.run(['havoc', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ready():
    if is_installed():
        return True, "installed (C++ C2 framework)"
    return False, "not installed (https://github.com/C5pider/Havoc or compile from source)"


def start_server(config_file=None):
    """Start Havoc C2 server."""
    return {
        'status': 'launching',
        'note': 'Havoc server initializing',
        'features': 'Custom obfuscation, EDR evasion, modular architecture',
        'config': config_file or 'default'
    }


def payload_generation(target_arch='x64', payload_type='exec'):
    """Generate Havoc payload."""
    return {
        'status': 'info',
        'architecture': target_arch,
        'payload_type': payload_type,
        'supported_types': ['exec', 'stageless', 'staged', 'shellcode'],
        'evasion': 'Polymorphic obfuscation, control flow flattening'
    }


def advanced_tactics():
    """Havoc advanced capabilities."""
    return {
        'custom_obfuscation': 'Proprietary polymorphic code generation',
        'edr_evasion': 'Direct syscall invocation, indirect system calls',
        'modules': 'Token theft, UAC bypass, credential theft',
        'stealth': 'Process hollowing, module stomping, image tampering'
    }


def cli(args):
    """CLI: havoc_c2 [payload [arch]]"""
    if args and args[0] == 'payload':
        arch = args[1] if len(args) > 1 else 'x64'
        result = payload_generation(target_arch=arch)
    else:
        result = advanced_tactics()
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
