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
        # `puredns resolve <file>` treats its positional argument as a file
        # of domains to read, not a domain itself - passing the domain
        # directly makes it look for (and silently find no) file by that
        # name and exit 0 with empty output. Its docs cover exactly this
        # case: "the <file> argument can be omitted if the domains to
        # resolve are read from stdin".
        result = subprocess.run(
            ['puredns', 'resolve'],
            input=target + '\n',
            capture_output=True,
            text=True,
            timeout=90
        )
        if result.returncode != 0:
            return {'status': 'error',
                   'message': result.stderr.strip() or
                              'puredns exited with code %d' % result.returncode}
        # Resolved results go to stdout, but ALL of puredns's progress and
        # "no valid domains remaining"-type diagnostics go to stderr - stdout
        # alone looks confusingly empty even on a real, completed run.
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        return {'status': 'success', 'output': output}
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
    text, code = render(result)
    print(text)
    return code
