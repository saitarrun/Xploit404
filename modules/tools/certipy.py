"""Certipy — Active Directory Certificate Services exploitation.

Tool for exploiting ADCS misconfigurations to escalate to domain administrator.
"""

import subprocess

from modules.tools import render

DESCRIPTION = 'Active Directory Certificate Services exploitation'


def is_installed():
    try:
        result = subprocess.run(['certipy', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ready():
    if is_installed():
        try:
            result = subprocess.run(['certipy', '--version'], capture_output=True, text=True)
            version = result.stdout.strip()
            return True, f"installed ({version})"
        except:
            return True, "installed (ADCS exploitation)"
    return False, "not installed (pip install certipy-ad or https://github.com/ly4k/Certipy)"


def find_adcs(target, username=None, password=None):
    """Find ADCS endpoints in domain."""
    try:
        cmd = ['certipy', 'find', '-u', username or 'guest', '-p', password or '', '-target', target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def request_certificate(ca_name, template, username, domain):
    """Request vulnerable certificate template."""
    return {
        'status': 'info',
        'ca': ca_name,
        'template': template,
        'username': username,
        'domain': domain,
        'note': 'Use certreq.exe or certipy to request certificate'
    }


def escalate_to_admin(cert_file, key_file, domain):
    """Escalate to domain admin via ADCS."""
    return {
        'status': 'info',
        'method': 'ESC vulnerability exploitation',
        'certificate': cert_file,
        'private_key': key_file,
        'domain': domain,
        'note': 'Use cert to request domain admin certificate via PKINIT'
    }


def adcs_vulns():
    """Common ADCS vulnerabilities."""
    return {
        'ESC1': 'Low-privileged user can enroll with admin template',
        'ESC2': 'Any user can enroll in certificate with ClientAuth EKU',
        'ESC3': 'Enrollment agents abuse',
        'ESC4': 'ACL misconfigurations allowing arbitrary template modification',
        'ESC5': 'CA ACL allows low-privilege users to modify CA configuration',
        'ESC6': 'NTLM relay to HTTP endpoints',
        'ESC7': 'User account control abuse',
        'ESC8': 'HTTP to HTTPS relay'
    }


def cli(args):
    """CLI: certipy [vulns]"""
    if args and args[0] == 'vulns':
        result = adcs_vulns()
    else:
        result = {'status': 'info',
                  'note': 'Certipy - ADCS exploitation tool. '
                          'Use "vulns" to list known ADCS vulnerabilities.'}
    text, code = render(result)
    print(text)
    return code
