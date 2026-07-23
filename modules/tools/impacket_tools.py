"""Impacket — Network protocol library and exploitation suite.

Python scripts for executing commands via SMB, WMI, and other Windows protocols.
"""

import subprocess

from modules.tools import render

DESCRIPTION = 'Python Windows protocol exploitation (psexec, secretsdump)'


def is_installed():
    try:
        import impacket
        return True
    except ImportError:
        return False


def ready():
    try:
        import impacket
        return True, "installed (Windows protocol exploitation)"
    except ImportError:
        return False, "not installed (pip install impacket)"


def psexec(target, username, password, command, hash_type=None):
    """Execute command via PSExec."""
    try:
        if hash_type == 'ntlm':
            auth = f'{username}:@{target}'
        else:
            auth = f'{username}:{password}@{target}'
        
        result = subprocess.run(
            ['psexec.py', auth, 'cmd.exe', '/c', command],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def wmiexec(target, username, password, command):
    """Execute command via WMI."""
    try:
        result = subprocess.run(
            ['wmiexec.py', f'{username}:{password}@{target}', command],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def secretsdump(target, username, password):
    """Dump domain secrets and credentials."""
    try:
        result = subprocess.run(
            ['secretsdump.py', f'{username}:{password}@{target}'],
            capture_output=True,
            text=True,
            timeout=300
        )
        return {'status': 'success', 'output': result.stdout, 'hashes': result.stdout.split('\n')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def ticketer(domain, user_sid, krbtgt_hash, user='admin'):
    """Create forged Kerberos ticket."""
    return {
        'status': 'info',
        'method': 'Ticket generation via ticketer.py',
        'domain': domain,
        'user': user,
        'note': 'Requires KRBTGT hash for golden ticket creation'
    }


def utilities():
    """List all Impacket utilities."""
    return {
        'psexec.py': 'Execute commands via SMB/PSExec',
        'wmiexec.py': 'Execute commands via WMI',
        'secretsdump.py': 'Dump domain credentials and secrets',
        'ticketer.py': 'Create forged Kerberos tickets',
        'getArch.py': 'Determine system architecture',
        'rpcclient.py': 'RPC protocol client'
    }


def cli(args):
    """CLI: impacket_tools [utilities]"""
    if args and args[0] == 'utilities':
        result = utilities()
    else:
        result = {'status': 'info',
                  'note': 'Impacket exploitation tools - psexec, wmiexec, secretsdump. '
                          'Use "utilities" to list them.'}
    text, code = render(result)
    print(text)
    return code
