"""Atomic Red Team — Tightly scoped security tests mapped to MITRE ATT&CK.

Library of simple, executable tests for validating defensive capabilities.
"""

import subprocess
import os

from modules.tools import render

DESCRIPTION = 'Tightly scoped ATT&CK-mapped security tests'


def is_installed():
    try:
        result = subprocess.run(['Invoke-AtomicTest', '-ListAtomics'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ready():
    if is_installed():
        return True, "installed (ATT&CK test library)"
    return False, "not installed (https://github.com/redcanaryco/atomic-red-team)"


def list_tests(technique_id=None):
    """List available Atomic Red Team tests."""
    return {
        'status': 'info',
        'technique': technique_id or 'all',
        'note': 'Use T-code (e.g., T1566.002 for Phishing: Spearphishing Link)',
        'framework': 'MITRE ATT&CK mapped'
    }


def run_test(technique_id, test_number=None):
    """Execute Atomic Red Team test."""
    try:
        cmd = ['Invoke-AtomicTest', technique_id]
        if test_number:
            cmd.extend(['-TestNumbers', str(test_number)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def execution_techniques():
    """Common execution techniques."""
    return {
        'T1059': 'Command and Scripting Interpreter',
        'T1203': 'Exploitation for Client Execution',
        'T1559': 'Inter-Process Communication',
        'T1053': 'Scheduled Task/Job',
        'T1648': 'Serverless Execution',
        'T1204': 'User Execution'
    }


def persistence_techniques():
    """Common persistence techniques."""
    return {
        'T1547': 'Boot or Logon Autostart Execution',
        'T1547.001': 'Registry Run Keys / Startup Folder',
        'T1547.010': 'Port Monitors',
        'T1547.013': 'XDG Autostart Entries',
        'T1547.014': 'Rc.common',
        'T1547.015': 'Startup Items'
    }


def test_categories():
    """Atomic Red Team test categories."""
    return {
        'execution': 'Execute commands, scripts, code',
        'persistence': 'Maintain access across reboots',
        'privilege_escalation': 'Gain higher privileges',
        'defense_evasion': 'Avoid security detection',
        'credential_access': 'Extract credentials',
        'discovery': 'Gather system information',
        'lateral_movement': 'Move between systems',
        'collection': 'Gather data from target',
        'exfiltration': 'Move data out of network',
        'impact': 'Disrupt or destroy data/systems'
    }


def cli(args):
    """CLI: atomic_red_team [tests]"""
    if args and args[0] == 'tests':
        result = test_categories()
    else:
        result = {'status': 'info',
                  'note': 'Atomic Red Team - ATT&CK-mapped security tests. '
                          'Use "tests" to list categories.'}
    text, code = render(result)
    print(text)
    return code
