"""Historical URL discovery via the Wayback Machine CDX API.

Pulls every URL the Internet Archive has ever captured for a domain - a rich,
passive source of old endpoints, parameters, and files that may no longer be
linked but are often still live.  Complements the scanner's content discovery.
"""

import time
import os

import requests

_HEADERS = {'User-Agent': 'Mozilla/5.0 (OSINT recon; wayback lookup)'}
_CDX = 'https://web.archive.org/cdx/search/cdx'


def _clean(domain):
    domain = domain.strip().lower()
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    return domain.split('/', 1)[0].strip()


def urls(domain, limit=10000, subdomains=True, timeout=90, attempts=2):
    """Return a de-duplicated list of archived URLs for `domain`.

    Uses the CDX API's explicit ``matchType`` (``domain`` covers subdomains,
    ``host`` is exact) rather than a ``*.domain/*`` wildcard: the wildcard form
    forces a full-index scan that routinely times out, while ``matchType``
    hits the server's index directly.  A generous timeout and one retry absorb
    the endpoint's usual slowness."""
    domain = _clean(domain)
    params = {'url': domain, 'matchType': 'domain' if subdomains else 'host',
              'output': 'json', 'fl': 'original', 'collapse': 'urlkey'}
    if limit:
        params['limit'] = str(limit)
    last_error = None
    for attempt in range(attempts):
        try:
            resp = requests.get(_CDX, params=params, headers=_HEADERS,
                                timeout=timeout)
            resp.raise_for_status()
            rows = resp.json() if resp.text.strip() else []
            # First row is the header (["original"]); rest are single-item rows.
            return [row[0] for row in rows[1:]]
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(3)
    raise requests.RequestException('Wayback unavailable (%s)' % last_error)


def run(domain, out_dir=None, limit=10000):
    domain = _clean(domain)
    print('[wayback] Fetching archived URLs for %s ...' % domain)
    try:
        found = urls(domain, limit=limit)
    except requests.RequestException as exc:
        print('[error] Wayback request failed: %s' % exc)
        return 1
    except ValueError:
        print('[error] Wayback returned an unparseable response.')
        return 1
    if not found:
        print('No archived URLs found.')
        return 0
    for url in found[:500]:
        print(url)
    if len(found) > 500:
        print('... (%d more; full list saved to file)' % (len(found) - 500))
    print('\n[+] %d archived URL(s) from the Wayback Machine.' % len(found))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, 'wayback_%s.txt' % domain.replace('/', '_'))
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('\n'.join(found) + '\n')
            print('[+] Saved to %s' % path)
        except OSError as exc:
            print('[error] Could not save: %s' % exc)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1
                      else print('usage: wayback.py <domain>') or 2)
