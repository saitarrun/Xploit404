"""Chisel — Fast TCP/UDP tunnel over HTTP.

Lightweight network tunneling for encapsulating traffic and bypassing firewalls.

The name `chisel` collides with an unrelated tool: Foundry's Solidity REPL
debugger also installs a binary literally called `chisel` (`brew install
chisel` gets you *that* one, not the network tunnel). The correct Homebrew
formula for this tool - jpillora/chisel - is `chisel-tunnel`, which exists
specifically because both formulas want to install a `chisel` binary and
can't coexist. Whichever one is actually on PATH depends on which formula
was installed last, so this module verifies behavior (does `chisel server
--help` actually describe a server?) rather than trusting the binary name.
"""

import shutil
import socket
import subprocess

from modules.tools import render

DESCRIPTION = 'Fast TCP/UDP tunnel over HTTP for network pivoting'


def _is_real_chisel(binary):
    """jpillora/chisel's `server --help` documents --host/--port; Foundry's
    same-named chisel has no `server` subcommand at all and errors out
    ("unrecognized subcommand") instead of printing anything like it."""
    try:
        result = subprocess.run([binary, 'server', '--help'],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    combined = result.stdout + result.stderr
    return '--port' in combined and '--host' in combined


def _binary():
    found = shutil.which('chisel')
    if found and _is_real_chisel(found):
        return found
    return None


def is_installed():
    return _binary() is not None


def ready():
    binary = _binary()
    if binary:
        try:
            result = subprocess.run([binary, '--version'], capture_output=True,
                                    text=True, timeout=5)
            version = (result.stdout or result.stderr).strip()
            return True, "installed (%s)" % version if version else "installed"
        except (OSError, subprocess.SubprocessError):
            return True, "installed"
    if shutil.which('chisel'):
        return False, ("a `chisel` is on PATH but it's not jpillora/chisel (network "
                       "tunnel) - looks like Foundry's Solidity debugger, which "
                       "installs a binary with the same name. Fix: brew uninstall "
                       "chisel && brew install chisel-tunnel")
    return False, "not installed (brew install chisel-tunnel, or go install github.com/jpillora/chisel@latest)"


def _port_in_use(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0


def start_server(listen_port=8080, auth=None, reverse=False):
    """Start a real Chisel server in the background.

    subprocess.Popen is fire-and-forget - checking the port first (the same
    approach used for Gophish elsewhere in this toolkit) turns "something's
    already listening" into a clean message instead of a doomed launch whose
    bind failure prints straight to this terminal moments later.
    """
    binary = _binary()
    if not binary:
        ok, detail = ready()
        return {'status': 'error', 'message': detail}
    if _port_in_use(listen_port):
        return {
            'status': 'error',
            'message': 'Something is already listening on port %d' % listen_port,
            'note': 'Stop it first (e.g. pkill -f "chisel server") or choose a '
                    'different port.',
        }
    cmd = [binary, 'server', '--host', '0.0.0.0', '--port', str(listen_port)]
    if auth:
        cmd.extend(['--auth', auth])
    if reverse:
        cmd.append('--reverse')
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        return {'status': 'error', 'message': str(e)}
    return {
        'status': 'launching',
        'pid': proc.pid,
        'server_url': 'http://0.0.0.0:%d' % listen_port,
        'note': 'Chisel server started (pid %d) - stop it with: kill %d'
                % (proc.pid, proc.pid),
    }


def connect_client(server_url, remote_port, local_port=None):
    """Connect a real Chisel client to a running server.

    Remote spec syntax (jpillora/chisel): up to
    <local-host>:<local-port>:<remote-host>:<remote-port>/<protocol>,
    filled in from the right when segments are omitted - two segments
    ("<local-port>:<remote-port>") means local-host and remote-host both
    default (remote-host defaults to the server's own localhost).
    """
    binary = _binary()
    if not binary:
        ok, detail = ready()
        return {'status': 'error', 'message': detail}
    local_port = local_port or remote_port
    remote_spec = '%s:%s' % (local_port, remote_port)
    cmd = [binary, 'client', server_url, remote_spec]
    try:
        proc = subprocess.Popen(cmd)
    except OSError as e:
        return {'status': 'error', 'message': str(e)}
    return {
        'status': 'launching',
        'pid': proc.pid,
        'server': server_url,
        'remote_port': remote_port,
        'local_port': local_port,
        'note': 'Chisel client started (pid %d) - stop it with: kill %d'
                % (proc.pid, proc.pid),
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
    text, code = render(result)
    print(text)
    return code
