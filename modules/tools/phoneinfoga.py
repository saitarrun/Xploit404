import os
import sys
import shutil
import platform
import subprocess

_BIN_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'bin')
_KEYS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'keys.env')


def _load_keys():
    """Read KEY=VALUE pairs from config/keys.env. Real environment variables
    take precedence over the file."""
    keys = {}
    try:
        with open(_KEYS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                name, _, value = line.partition('=')
                keys[name.strip()] = value.strip()
    except OSError:
        pass
    return keys


def _platform_binary_name():
    """Map the current OS/arch to the vendored binary filename."""
    system = platform.system().lower()          # linux / darwin / windows
    machine = platform.machine().lower()         # x86_64 / amd64 / arm64 / aarch64
    if machine in ('x86_64', 'amd64'):
        arch = 'amd64'
    elif machine in ('arm64', 'aarch64'):
        arch = 'arm64'
    else:
        arch = machine
    name = 'phoneinfoga-%s-%s' % (system, arch)
    if system == 'windows':
        name += '.exe'
    return name


def _binary():
    # Prefer the binary matching this platform; fall back to one on PATH.
    bundled = os.path.join(_BIN_DIR, _platform_binary_name())
    if os.path.isfile(bundled):
        if platform.system().lower() != 'windows':
            os.access(bundled, os.X_OK) or os.chmod(bundled, 0o755)
        return bundled
    return shutil.which('phoneinfoga')


def phoneinfoga(number):
    """Run a PhoneInfoga scan for `number`, streaming its output to the
    terminal. Returns True on success, False if the tool is unavailable or
    the scan fails."""
    keys = _load_keys()
    # Environment wins over the config file so a user can override the key.
    numverify_key = os.environ.get('NUMVERIFY_API_KEY') or keys.get('NUMVERIFY_API_KEY')

    # numverify gives real carrier / line-type / location data. This build of
    # PhoneInfoga queries the newer api.apilayer.com endpoint, which rejects
    # classic numverify.com keys, so we run the lookup ourselves against the
    # legacy endpoint the key authenticates with.
    if numverify_key:
        from modules.tools.numverify import lookup
        print('Results for numverify')
        data = lookup(number, numverify_key)
        if data is None:
            pass
        elif 'error' in data:
            print('\t[-] numverify lookup failed: %s\n' % data['error'])
        else:
            print('\tValid:        %s' % data.get('valid'))
            print('\tCarrier:      %s' % (data.get('carrier') or 'n/a'))
            print('\tLine type:    %s' % (data.get('line_type') or 'n/a'))
            print('\tLocation:     %s' % (data.get('location') or 'n/a'))
            print('\tCountry:      %s (%s)' % (data.get('country_name') or 'n/a',
                                               data.get('country_code') or '?'))
            print('\tInternational: %s\n' % (data.get('international_format') or 'n/a'))

    binary = _binary()
    if not binary:
        print('[-] PhoneInfoga binary not found for this platform '
              '(expected bin/%s or a `phoneinfoga` on PATH).'
              % _platform_binary_name())
        return False
    # The vendored binaries are dev builds, which default their logger to
    # DEBUG and flood the scan with noise (.env-not-found, "scanner ignored"
    # for scanners that need API keys). Pin the level to INFO so the user sees
    # results and real errors only; honour an explicit LOG_LEVEL override so
    # debugging is still possible.
    env = os.environ.copy()
    env.setdefault('LOG_LEVEL', 'info')
    # Deliberately do NOT pass NUMVERIFY_API_KEY to the binary: its numverify
    # scanner uses the api.apilayer.com endpoint, which 401s on classic
    # numverify.com keys and would just print an error. We already ran the
    # lookup above against the endpoint the key works with.

    # Flush so the numverify section (buffered when piped) prints before the
    # binary writes straight to the terminal fd.
    sys.stdout.flush()
    try:
        result = subprocess.run([binary, 'scan', '-n', number], env=env)
    except OSError as e:
        print('[-] Failed to run PhoneInfoga: %s' % e)
        return False
    return result.returncode == 0
