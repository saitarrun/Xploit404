import io
import os
import re
import sys
import contextlib

# Sublist3r is vendored inside the repo (thirdparty/) so Osint_Tools stays
# self-contained; make that copy importable without a pip install.
_vendor = os.path.join(os.path.dirname(__file__), '..', '..', 'thirdparty')
if _vendor not in sys.path:
    sys.path.append(_vendor)

# hostname label chars only; anchors out any stray banner/log text
valid_hostname = re.compile(r'^[a-z0-9._-]+$')

try:
    import sublist3r
    _import_error = None
except ImportError as e:
    sublist3r = None
    _import_error = e


def sublister(host):
    # dnspython is the only extra requirement; report it clearly if missing
    # instead of silently returning no results.
    if sublist3r is None:
        print('[-] Sublist3r unavailable: %s' % _import_error)
        print('    Install its dependency with: pip3 install dnspython')
        return []
    host = host.lower()
    suffix = '.' + host
    try:
        # Sublist3r is chatty; swallow its stdout so Osint_Tools output stays clean.
        with contextlib.redirect_stdout(io.StringIO()):
            found = sublist3r.main(
                host,
                40,               # threads
                savefile=None,
                ports=None,
                silent=True,
                verbose=False,
                enable_bruteforce=False,
                engines=None,
            )
    except Exception:
        return []
    subdomains = set()
    for name in found or []:
        name = name.strip().lstrip('*.').lower()
        if name.endswith(suffix) and valid_hostname.match(name):
            subdomains.add(name)
    return list(subdomains)
