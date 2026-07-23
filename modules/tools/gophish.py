"""Gophish — Open-source phishing simulation framework.

Professional phishing testing platform for security awareness programs.
"""

import shutil
import socket
import subprocess
import os

from modules.tools import render

DESCRIPTION = 'Professional phishing simulation framework'

# Vendored copy: needs config.json/static/templates alongside the binary,
# so it's kept as its own directory rather than a bare bin/ binary.
_VENDOR_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'thirdparty', 'gophish')
_VENDOR_BIN = os.path.join(_VENDOR_DIR, 'gophish')


def _binary():
    if os.path.isfile(_VENDOR_BIN):
        os.access(_VENDOR_BIN, os.X_OK) or os.chmod(_VENDOR_BIN, 0o755)
        return _VENDOR_BIN
    return shutil.which('gophish')


def is_installed():
    return _binary() is not None


def ready():
    if is_installed():
        return True, "installed (phishing framework)"
    return False, "not installed (https://github.com/gophish/gophish or brew install gophish)"


def _port_in_use(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0


def start_server(config_file=None, admin_port=3333, phish_port=80):
    """Start Gophish server (runs from its vendored directory so relative
    paths to config.json/static/templates resolve).

    subprocess.Popen is fire-and-forget: if the binary fails to bind its
    ports it dies moments later and dumps a fatal log straight to this
    terminal, while this function has already returned 'status: launching'.
    Checking the ports first turns "already running" into a clean message
    instead of a confusing async crash.
    """
    binary = _binary()
    if not binary:
        return {'status': 'error', 'message': 'Gophish not installed'}
    busy = [p for p in (admin_port, phish_port) if _port_in_use(p)]
    if busy:
        return {
            'status': 'error',
            'message': 'Gophish (or something else) is already listening on port(s) %s'
                       % ', '.join(str(p) for p in busy),
            'note': 'Use the admin URL below if that\'s your own already-running '
                    'server, or stop it first (e.g. pkill gophish) and try again.',
            'admin_url': f'https://localhost:{admin_port}',
        }
    try:
        cmd = [binary]
        if config_file and os.path.exists(config_file):
            cmd.extend(['--config', config_file])
        cwd = _VENDOR_DIR if binary == _VENDOR_BIN else None
        subprocess.Popen(cmd, cwd=cwd)
        return {
            'status': 'launching',
            'admin_url': f'https://localhost:{admin_port}',
            'phish_port': phish_port,
            'note': 'Gophish server starting - access admin panel at admin URL '
                    '(default creds are printed to the console on first run)'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def create_campaign(name, template, landing_page, target_list):
    """Create phishing campaign."""
    return {
        'status': 'info',
        'campaign_name': name,
        'template': template,
        'landing_page': landing_page,
        'targets': len(target_list) if isinstance(target_list, list) else 'N/A',
        'note': 'Create campaigns via Gophish web interface'
    }


def cli(args):
    """CLI: gophish [start]"""
    if args and args[0] == 'start':
        result = start_server()
    else:
        result = {'status': 'info',
                  'note': 'Gophish phishing simulation framework. '
                          'Use "start" to launch the server.'}
    text, code = render(result)
    print(text)
    return code
