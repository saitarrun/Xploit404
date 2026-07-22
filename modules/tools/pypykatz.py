"""pypykatz — Python implementation of Mimikatz credential extraction.

Pure Python credential extraction from memory without requiring Mimikatz binary.
"""

import subprocess

from modules.tools import render

DESCRIPTION = 'Python credential extraction from memory (Mimikatz alternative)'


def is_installed():
    try:
        import pypykatz
        return True
    except ImportError:
        return False


def ready():
    try:
        import pypykatz
        return True, "installed (Python credential extraction)"
    except ImportError:
        return False, "not installed (pip install pypykatz)"


def extract_lsass(dump_file):
    """Extract credentials from LSASS dump file."""
    try:
        result = subprocess.run(
            ['pypykatz', 'lsa', 'minidump', dump_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {'status': 'success', 'output': result.stdout, 'credentials': result.stdout.split('\n')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def extract_registry(sam_file, system_file, security_file=None):
    """Extract credentials from registry hives."""
    try:
        cmd = ['pypykatz', 'registry', 'sam', sam_file, system_file]
        if security_file:
            cmd.extend([security_file])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def extract_dpapi(dpapi_file):
    """Extract DPAPI secrets."""
    return {
        'status': 'info',
        'method': 'DPAPI extraction',
        'file': dpapi_file,
        'note': 'Requires DPAPI master key for decryption'
    }


def cli(args):
    """CLI: pypykatz <lsass_dump_file>"""
    if not args:
        print('Usage: pypykatz <lsass_dump_file>')
        return 2
    text, code = render(extract_lsass(args[0]), desc=DESCRIPTION)
    print(text)
    return code
