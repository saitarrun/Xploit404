"""PureDNS — Rapid DNS subdomain enumeration & resolver.

Modern Go-based DNS resolver for comprehensive subdomain discovery.
"""

import subprocess

from modules.tools import render

DESCRIPTION = 'Rapid DNS resolution & subdomain bruteforce'


def is_installed():
    try:
        result = subprocess.run(['puredns', '-h'], capture_output=True, text=True)
        return result.returncode == 0 or 'puredns' in result.stdout
    except FileNotFoundError:
        return False


def ready():
    if is_installed():
        return True, "installed (Go-based DNS resolver)"
    return False, "not installed (https://github.com/d3mondev/puredns or brew install puredns)"


def resolve_dns(target):
    """Resolve DNS records for target."""
    try:
        result = subprocess.run(
            ['puredns', 'resolve', target],
            capture_output=True,
            text=True,
            timeout=60
        )
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def bruteforce_domains(domain, wordlist=None):
    """Bruteforce subdomains."""
    try:
        cmd = ['puredns', 'bruteforce', domain]
        if wordlist:
            cmd.extend(['-w', wordlist])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return {'status': 'success', 'output': result.stdout}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def cli(args):
    """CLI: puredns <domain> [wordlist]"""
    if not args:
        print('Usage: puredns <domain> [wordlist]')
        return 2
    if len(args) > 1:
        result = bruteforce_domains(args[0], wordlist=args[1])
    else:
        result = resolve_dns(args[0])
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
