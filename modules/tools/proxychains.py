"""Proxychains — Network proxy chaining for anonymous traffic routing.

Route traffic through SOCKS proxies to mask attack source and bypass network restrictions.
"""

import shutil
import subprocess

from modules.tools import render

DESCRIPTION = 'Traffic routing through SOCKS proxies for anonymity'


def _binary():
    """proxychains-ng (brew) ships as 'proxychains4'; Linux packages ship 'proxychains'."""
    return shutil.which('proxychains4') or shutil.which('proxychains')


def is_installed():
    return _binary() is not None


def ready():
    binary = _binary()
    if binary:
        return True, "installed (%s)" % binary
    return False, "not installed (apt install proxychains or brew install proxychains-ng)"


def route_through_proxy(command, proxy_config=None):
    """Execute command through proxychains."""
    try:
        cmd = [_binary()]
        if proxy_config:
            cmd.extend(['-c', proxy_config])
        cmd.extend(command.split())
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {'status': 'success', 'output': result.stdout, 'errors': result.stderr}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def configure_proxy(socks_host='127.0.0.1', socks_port=9050):
    """Generate proxychains configuration."""
    config = f"""
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000
socks5 {socks_host} {socks_port}
"""
    return {'status': 'success', 'config': config.strip()}


def cli(args):
    """CLI: proxychains [command...] (blank generates a default config)"""
    if not args:
        result = configure_proxy()
    else:
        result = route_through_proxy(' '.join(args))
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
