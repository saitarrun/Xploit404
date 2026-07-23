"""Passive subdomain discovery via crt.sh certificate transparency logs.

No API key and no external tool: crt.sh exposes a JSON endpoint that returns
every certificate seen for a domain, which leaks the subdomains those certs
were issued for.  Complements the active subdomain enumeration in Sublist3r.
"""

import time
import os

import requests

_HEADERS = {'User-Agent': 'Mozilla/5.0 (OSINT recon; crt.sh lookup)'}


def _clean(domain):
    domain = domain.strip().lower()
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    return domain.split('/', 1)[0].strip().lstrip('*.')


def lookup(domain, timeout=40, attempts=3):
    """Return a sorted list of unique subdomains of `domain` seen in CT logs.

    crt.sh is frequently overloaded and returns a 502/empty body on the first
    hit, so retry a few times before giving up."""
    domain = _clean(domain)
    last_error = None
    data = None
    for attempt in range(attempts):
        try:
            resp = requests.get('https://crt.sh/',
                                params={'q': '%.' + domain, 'output': 'json'},
                                headers=_HEADERS, timeout=timeout)
            if resp.status_code == 200 and resp.text.strip():
                data = resp.json()
                break
            last_error = 'HTTP %s' % resp.status_code
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(2 * (attempt + 1))
    if data is None:
        raise requests.RequestException('crt.sh unavailable (%s)' % last_error)
    found = set()
    for entry in data:
        for name in (entry.get('name_value') or '').splitlines():
            name = name.strip().lower().lstrip('*.')
            if name and name.endswith(domain):
                found.add(name)
    return sorted(found)


def run(domain, out_dir=None):
    domain = _clean(domain)
    print('[crt.sh] Querying certificate transparency logs for %s ...' % domain)
    try:
        subs = lookup(domain)
    except requests.RequestException as exc:
        print('[error] crt.sh request failed: %s' % exc)
        return 1
    except ValueError:
        print('[error] crt.sh returned an unparseable response (try again).')
        return 1
    if not subs:
        print('No subdomains found in CT logs.')
        return 0
    print('\n'.join(subs))
    print('\n[+] %d unique subdomain(s) from certificate transparency.' % len(subs))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, 'crtsh_%s.txt' % domain.replace('/', '_').replace(':', '_'))
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('\n'.join(subs) + '\n')
            print('[+] Saved to %s' % path)
        except OSError as exc:
            print('[error] Could not save: %s' % exc)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1
                      else print('usage: crtsh.py <domain>') or 2)
