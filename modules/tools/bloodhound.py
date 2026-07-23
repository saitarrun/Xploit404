"""BloodHound — Active Directory attack path visualization.

Maps trust relationships and privilege escalation paths in AD environments.
"""

import shutil
import subprocess
import json
import os

from modules.tools import render

DESCRIPTION = 'Active Directory trust relationships & privilege escalation paths'
MACOS_APP = '/Applications/BloodHound.app'


def is_installed():
    if shutil.which('bloodhound'):
        return True
    return os.path.exists(MACOS_APP)


def ready():
    if is_installed():
        return True, "installed (AD enumeration tool)"
    return False, "not installed (https://github.com/BloodHoundAD/BloodHound or brew install bloodhound)"


def collect_data(output_file=None):
    """Launch BloodHound (GUI on macOS) or run the SharpHound CLI collector if on PATH."""
    try:
        if shutil.which('bloodhound'):
            cmd = ['bloodhound']
            if output_file:
                cmd.extend(['-o', output_file])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            return {'status': 'success', 'output': result.stdout}
        if os.path.exists(MACOS_APP):
            subprocess.run(['open', '-a', 'BloodHound'], check=True)
            return {'status': 'success', 'output': 'Launched BloodHound.app (requires Neo4j running)'}
        return {'status': 'error', 'message': 'BloodHound not installed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def query_paths(source, target):
    """Query shortest paths between two AD objects."""
    return {
        'status': 'info',
        'note': 'BloodHound API queries require database connection',
        'source': source,
        'target': target
    }


def list_admin_users():
    """Identify domain admin accounts."""
    return {
        'status': 'info',
        'note': 'Requires SharpHound collection data in database',
        'query': 'MATCH (u:User)-[:MemberOf*1..]->(g:Group) WHERE g.name CONTAINS "ADMIN" RETURN u'
    }


def cli(args):
    """CLI: bloodhound [collect | query_paths <source> <target> | list_admins]"""
    if args and args[0] == 'collect':
        result = collect_data()
    elif args and args[0] == 'query_paths' and len(args) >= 3:
        result = query_paths(args[1], args[2])
    else:
        result = list_admin_users()
    text, code = render(result)
    print(text)
    return code
