"""Metasploit Framework — msfconsole integration.

The Metasploit Framework is the world's most used penetration testing framework
and helps security professionals access, verify, prevent, and remediate security
vulnerabilities. msfconsole is the command-line interface to Metasploit.
"""

import os
import shutil
import subprocess
import tempfile

from modules.tools import profiles


def msfconsole_bin():
    """Locate msfconsole binary."""
    found = shutil.which('msfconsole')
    if found:
        return found
    common_paths = [
        '/usr/bin/msfconsole',
        '/usr/local/bin/msfconsole',
        '/opt/metasploit-framework/bin/msfconsole',
        os.path.expanduser('~/.local/bin/msfconsole'),
    ]
    for candidate in common_paths:
        if os.path.isfile(candidate):
            return candidate
    return None


def is_installed():
    """Check if Metasploit Framework is installed."""
    return msfconsole_bin() is not None


def install_hint():
    """Return installation instructions for Metasploit Framework."""
    return 'https://docs.metasploit.com/docs/using-metasploit/getting-started.html or apt install metasploit-framework'


def ready():
    """Check if msfconsole is ready."""
    binary = msfconsole_bin()
    if not binary:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([binary, '--version'], capture_output=True,
                                text=True, timeout=10)
        version = result.stdout.splitlines()[0].strip() if result.stdout else 'installed'
    except (OSError, subprocess.SubprocessError):
        version = 'installed'
    return True, version


def run_interactive(out_dir=None):
    """Launch msfconsole in interactive mode."""
    binary = msfconsole_bin()
    if not binary:
        raise RuntimeError('msfconsole is not installed')
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    return subprocess.call([binary])


def run_module(module_path, payload='', lhost='', lport='', out_dir=None, profile=profiles.STANDARD):
    """Execute a specific Metasploit module."""
    binary = msfconsole_bin()
    if not binary:
        raise RuntimeError('msfconsole is not installed')

    rc_file = tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False)
    try:
        rc_file.write('use %s\n' % module_path)
        if payload:
            rc_file.write('set PAYLOAD %s\n' % payload)
        if lhost:
            rc_file.write('set LHOST %s\n' % lhost)
        if lport:
            rc_file.write('set LPORT %s\n' % lport)
        rc_file.write('run\n')
        rc_file.close()

        command = [binary, '-r', rc_file.name] + profiles.args_for('metasploit', profile)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)
    finally:
        if os.path.exists(rc_file.name):
            os.unlink(rc_file.name)


def search_exploit(query, out_dir=None):
    """Search for exploits matching a query."""
    binary = msfconsole_bin()
    if not binary:
        raise RuntimeError('msfconsole is not installed')

    command = [binary, '-c', 'search %s; exit' % query]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command)
