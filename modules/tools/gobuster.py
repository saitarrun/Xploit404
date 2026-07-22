"""Gobuster — URI/DNS/VHOST and subdomain busting tool.

Gobuster is a tool used to brute-force URIs (directories and files) in web
sites, DNS subdomains (ideally for use outside the scope of a pentest), and
virtual host names on target web servers.
"""

import os
import shutil
import subprocess

from modules.tools import profiles


def gobuster_bin():
    """Locate gobuster binary."""
    found = shutil.which('gobuster')
    if found:
        return found
    common_paths = ['/usr/bin/gobuster', '/usr/local/bin/gobuster']
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if gobuster is installed."""
    return gobuster_bin() is not None


def install_hint():
    """Return installation instructions."""
    return 'go install github.com/OJ/gobuster/v3@latest or apt install gobuster'


def ready():
    """Check if gobuster is ready."""
    binary = gobuster_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, 'version'], capture_output=True,
                                text=True, timeout=5)
        version = result.stdout.strip() if result.stdout else 'installed'
        return True, version
    except (OSError, subprocess.SubprocessError):
        return False, 'installation corrupted'


def dir_bust(url, wordlist=None, extensions=None, out_dir=None, profile=profiles.STANDARD):
    """Brute force directories and files.

    Args:
        url: Target URL
        wordlist: Wordlist file (default common.txt)
        extensions: File extensions to search (e.g., 'php,html,txt')
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = gobuster_bin()
    if not binary:
        raise RuntimeError('gobuster is not installed')

    command = [binary, 'dir', '-u', url]

    if wordlist:
        command.extend(['-w', wordlist])

    if extensions:
        command.extend(['-x', extensions])

    command.extend(['-q'])
    command.extend(profiles.args_for('gobuster', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe_url = url.replace('/', '_').replace(':', '_').replace('?', '_')
        output_file = os.path.join(out_dir, 'gobuster_dir_%s.txt' % safe_url)
        command.extend(['-o', output_file])
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)


def dns_bust(domain, wordlist=None, out_dir=None, profile=profiles.STANDARD):
    """Brute force DNS subdomains.

    Args:
        domain: Target domain
        wordlist: Subdomain wordlist
        out_dir: Output directory
        profile: Standard or intensive profile
    """
    binary = gobuster_bin()
    if not binary:
        raise RuntimeError('gobuster is not installed')

    command = [binary, 'dns', '-d', domain]

    if wordlist:
        command.extend(['-w', wordlist])

    command.extend(['-q'])
    command.extend(profiles.args_for('gobuster', profile))

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        output_file = os.path.join(out_dir, 'gobuster_dns_%s.txt' % domain)
        command.extend(['-o', output_file])
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)

    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
