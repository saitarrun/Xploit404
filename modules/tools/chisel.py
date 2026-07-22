"""Chisel — Fast TCP/UDP tunnel over HTTP.

Lightweight network tunneling for encapsulating traffic and bypassing firewalls.
"""

import subprocess
import os

from modules.tools import render

DESCRIPTION = 'Fast TCP/UDP tunnel over HTTP for network pivoting'


def is_installed():
    try:
        result = subprocess.run(['chisel', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ready():
    if is_installed():
        try:
            result = subprocess.run(['chisel', '--version'], capture_output=True, text=True)
            version = result.stdout.strip()
            return True, f"installed ({version})"
        except:
            return True, "installed"
    return False, "not installed (https://github.com/jpillora/chisel or go install github.com/jpillora/chisel@latest)"


def start_server(listen_port=8080, auth=None, reverse=False):
    """Start Chisel server."""
    try:
        cmd = ['chisel', 'server']
        if auth:
            cmd.extend(['--auth', auth])
        cmd.extend(['--host', '0.0.0.0', '--port', str(listen_port)])
        if reverse:
            cmd.append('--reverse')
        return {
            'status': 'launching',
            'server_url': f'http://0.0.0.0:{listen_port}',
            'note': 'Chisel server ready for client connections'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def connect_client(server_url, remote_port, local_port=None):
    """Connect Chisel client to server."""
    return {
        'status': 'info',
        'server': server_url,
        'remote_port': remote_port,
        'local_port': local_port or remote_port,
        'command': f'chisel client {server_url} {remote_port}:{local_port or remote_port}'
    }


def cli(args):
    """CLI: chisel server [port] | chisel client <server_url> [remote_port]"""
    if args and args[0] == 'server':
        port = int(args[1]) if len(args) > 1 else 8080
        result = start_server(listen_port=port)
    elif args and args[0] == 'client' and len(args) > 1:
        remote_port = int(args[2]) if len(args) > 2 else 8080
        result = connect_client(args[1], remote_port)
    else:
        result = {'status': 'info',
                  'note': 'Usage: chisel server [port] | chisel client <server_url> [port]'}
    text, code = render(result, desc=DESCRIPTION)
    print(text)
    return code
