"""Amass — Advanced subdomain enumeration & network mapping.

Industry-leading DNS namespace mapper for comprehensive attack surface discovery.

Amass v5 rearchitected around a client/server split: `amass engine` runs a
persistent background service that populates a local asset database, and
`amass enum` (and its sibling subcommands) are clients that connect to it -
there is no more standalone `amass enum -passive -d ...` like v3/v4 had.
This module manages that engine the same way Gophish's server is managed
elsewhere in this toolkit: start it once, track its PID, health-check
before reuse, and expose a way to stop it so it doesn't run forever in the
background unnoticed.

Known limitation (not fixable here): Amass v5.1.1's engine does a BGPTools
ASN lookup during startup and refuses to start at all if that lookup fails
- an open upstream bug with no documented workaround as of this writing
(https://github.com/owasp-amass/amass/issues/1082). When that happens,
start_engine() surfaces amass's own error with a pointer to that issue
rather than the generic "did not respond" timeout enum would otherwise give.
"""

import os
import shutil
import signal
import subprocess
import time

from modules.tools import render

DESCRIPTION = 'Subdomain enumeration & attack surface mapping'

_STATE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'output')
_PID_FILE = os.path.join(_STATE_DIR, '.amass_engine.pid')
_LOG_FILE = os.path.join(_STATE_DIR, 'amass_engine.log')
_STARTUP_TIMEOUT = 45  # seconds - the BGPTools ASN lookup at startup can be slow
_UPSTREAM_BUG_NOTE = ('Known upstream issue in Amass v5 when its startup BGPTools '
                      'ASN lookup fails - see github.com/owasp-amass/amass/issues/1082. '
                      'Not something this wrapper can work around; retry later, or '
                      'downgrade to an Amass version before the engine/enum split.')


def _binary():
    return shutil.which('amass')


def is_installed():
    """Check if Amass is installed."""
    return _binary() is not None


def ready():
    """Check if Amass is ready."""
    binary = _binary()
    if not binary:
        return False, "not installed (https://github.com/owasp-amass/amass or brew install amass)"
    try:
        result = subprocess.run([binary, '-version'], capture_output=True, text=True, timeout=10)
        version_line = result.stdout.strip().splitlines()[0] if result.stdout else 'unknown'
        return True, "installed (%s)" % version_line
    except (OSError, subprocess.SubprocessError):
        return True, "installed"


# --- Engine lifecycle -------------------------------------------------------

def _read_pid():
    try:
        with open(_PID_FILE) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _clear_pid_file():
    try:
        os.remove(_PID_FILE)
    except OSError:
        pass


def engine_status():
    """Return (running, detail) for the engine process this module started
    (does not detect an engine started outside this wrapper)."""
    pid = _read_pid()
    if pid and _pid_alive(pid):
        return True, 'running (pid %d)' % pid
    if pid:
        _clear_pid_file()  # stale file from a process that's no longer alive
    return False, 'not running'


def _tail(path, lines=3):
    try:
        with open(path, 'r', errors='replace') as f:
            content = f.read().strip().splitlines()
        return ' | '.join(content[-lines:]) if content else '(no output)'
    except OSError:
        return '(log unavailable)'


def _probe_ready(binary):
    """`amass enum -h` talks to the engine before printing help, and fails
    fast with a message containing "did not respond" if it can't reach it -
    a side-effect-free way to check the engine is actually accepting
    connections yet (the process existing isn't enough; startup takes a
    few seconds)."""
    try:
        result = subprocess.run([binary, 'enum', '-h'], capture_output=True,
                                text=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return False
    return 'did not respond' not in (result.stdout + result.stderr)


def start_engine(timeout=_STARTUP_TIMEOUT):
    """Start `amass engine` in the background if it isn't already running,
    and wait for it to become ready. Returns (ok, detail)."""
    running, detail = engine_status()
    if running:
        return True, detail
    binary = _binary()
    if not binary:
        return False, 'amass is not installed'

    os.makedirs(_STATE_DIR, exist_ok=True)
    try:
        logfile = open(_LOG_FILE, 'wb')
        proc = subprocess.Popen([binary, 'engine'], stdout=logfile, stderr=subprocess.STDOUT)
    except OSError as exc:
        return False, 'failed to launch: %s' % exc
    with open(_PID_FILE, 'w') as f:
        f.write(str(proc.pid))

    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            _clear_pid_file()  # it already exited - startup failed
            return False, 'engine exited during startup: %s' % _tail(_LOG_FILE)
        if _probe_ready(binary):
            return True, 'engine ready (pid %d)' % proc.pid
        time.sleep(1)

    return False, ('engine did not become ready within %ds (see %s): %s'
                   % (timeout, os.path.relpath(_LOG_FILE), _tail(_LOG_FILE)))


def stop_engine():
    """Stop the engine this module started, if any. Returns (ok, detail)."""
    pid = _read_pid()
    if not pid:
        return True, 'not running'
    if not _pid_alive(pid):
        _clear_pid_file()
        return True, 'not running'
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return False, str(exc)
    for _ in range(10):
        if not _pid_alive(pid):
            break
        time.sleep(0.5)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    _clear_pid_file()
    return True, 'stopped (pid %d)' % pid


# --- Enumeration -------------------------------------------------------------

def _run_client(args, timeout):
    binary = _binary()
    ok, detail = start_engine()
    if not ok:
        return {'status': 'error', 'message': 'amass engine unavailable: %s' % detail,
                'note': _UPSTREAM_BUG_NOTE}
    try:
        result = subprocess.run([binary] + args, capture_output=True, text=True,
                                timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'message': 'amass %s timed out after %ds'
                                              % (' '.join(args), timeout)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    if result.returncode != 0:
        return {'status': 'error',
               'message': (result.stderr or result.stdout).strip()
                          or 'amass exited with code %d' % result.returncode}
    return {'status': 'success', 'output': result.stdout, 'domains': result.stdout.split('\n')}


def enum_passive(domain):
    """Passive enumeration of subdomains."""
    return _run_client(['enum', '-passive', '-d', domain], timeout=300)


def enum_active(domain):
    """Active enumeration with DNS brute-forcing."""
    return _run_client(['enum', '-d', domain], timeout=600)


def intel_collect(domain):
    """Collect intelligence about domain."""
    return _run_client(['intel', '-d', domain], timeout=300)


def cli(args):
    """CLI: amass <domain> | amass -passive <domain> | amass intel <domain>
    | amass engine <status|stop>"""
    if not args:
        print('Usage: amass <domain> | amass -passive <domain> | amass intel <domain> '
              '| amass engine <status|stop>')
        return 2

    if args[0] == 'engine':
        action = args[1] if len(args) > 1 else 'status'
        if action == 'status':
            # Not running is a valid state, not a failure of the check itself.
            running, detail = engine_status()
            print('[+] %s' % detail)
            return 0
        if action == 'stop':
            ok, detail = stop_engine()
            print('%s %s' % ('[+]' if ok else '[error]', detail))
            return 0 if ok else 1
        print('Usage: amass engine <status|stop>')
        return 2

    if args[0] == '-passive' and len(args) > 1:
        result = enum_passive(args[1])
    elif args[0] == 'intel' and len(args) > 1:
        result = intel_collect(args[1])
    else:
        result = enum_active(args[0])
    text, code = render(result)
    print(text)
    return code
