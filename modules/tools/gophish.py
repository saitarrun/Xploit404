"""Gophish — Open-source phishing simulation framework.

Professional phishing testing platform for security awareness programs.
"""

import shutil
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


def start_server(config_file=None, admin_port=3333, phish_port=80):
    """Start Gophish server (runs from its vendored directory so relative
    paths to config.json/static/templates resolve)."""
    binary = _binary()
    if not binary:
        return {'status': 'error', 'message': 'Gophish not installed'}
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
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
