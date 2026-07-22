"""Amass — Advanced subdomain enumeration & network mapping.

Industry-leading DNS namespace mapper for comprehensive attack surface discovery.
"""

import subprocess
import json

from modules.tools import render

DESCRIPTION = 'Subdomain enumeration & attack surface mapping'


def is_installed():
    """Check if Amass is installed."""
    try:
        result = subprocess.run(['amass', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ready():
    """Check if Amass is ready."""
    if is_installed():
        try:
            result = subprocess.run(['amass', '-version'], capture_output=True, text=True)
            version_line = result.stdout.split('\n')[0] if result.stdout else 'unknown'
            return True, f"installed ({version_line.strip()})"
        except:
            return True, "installed"
    return False, "not installed (https://github.com/owasp-amass/amass or brew install amass)"


def enum_passive(domain):
    """Passive enumeration of subdomains."""
    try:
        result = subprocess.run(
            ['amass', 'enum', '-passive', '-d', domain],
            capture_output=True,
            text=True,
            timeout=300
        )
        return {'status': 'success', 'output': result.stdout, 'domains': result.stdout.split('\n')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def enum_active(domain):
    """Active enumeration with DNS brute-forcing."""
    try:
        result = subprocess.run(
            ['amass', 'enum', '-d', domain],
            capture_output=True,
            text=True,
            timeout=600
        )
        return {'status': 'success', 'output': result.stdout, 'domains': result.stdout.split('\n')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def intel_collect(domain):
    """Collect intelligence about domain."""
    try:
        result = subprocess.run(
            ['amass', 'intel', '-d', domain],
            capture_output=True,
            text=True,
            timeout=300
        )
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def cli(args):
    """CLI: amass <domain> | amass -passive <domain> | amass intel <domain>"""
    if not args:
        print('Usage: amass <domain> | amass -passive <domain> | amass intel <domain>')
        return 2
    if args[0] == '-passive' and len(args) > 1:
        result = enum_passive(args[1])
    elif args[0] == 'intel' and len(args) > 1:
        result = intel_collect(args[1])
    else:
        result = enum_active(args[0])
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
