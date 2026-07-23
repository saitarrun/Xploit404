"""IP geolocation and ASN/ISP lookup via the free ip-api.com endpoint.

Accepts an IP address or a hostname (the API resolves hostnames server-side)
and reports country, city, coordinates, timezone, ISP, organisation, and the
autonomous system.  No API key required.
"""

import os

import requests

_HEADERS = {'User-Agent': 'Mozilla/5.0 (OSINT recon; ip geo lookup)'}
_FIELDS = ('status,message,query,country,countryCode,regionName,city,zip,lat,'
           'lon,timezone,isp,org,as,reverse,mobile,proxy,hosting')


def lookup(host, timeout=20):
    """Return the ip-api.com record for `host` (an IP or hostname)."""
    host = host.strip()
    if '://' in host:
        host = host.split('://', 1)[1].split('/', 1)[0]
    resp = requests.get('http://ip-api.com/json/%s' % host,
                        params={'fields': _FIELDS},
                        headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


_ROWS = [
    ('IP', 'query'), ('Country', 'country'), ('Country code', 'countryCode'),
    ('Region', 'regionName'), ('City', 'city'), ('Postal', 'zip'),
    ('Coordinates', None), ('Timezone', 'timezone'), ('ISP', 'isp'),
    ('Organisation', 'org'), ('AS', 'as'), ('Reverse DNS', 'reverse'),
]


def run(host, out_dir=None):
    print('[ip-api] Looking up %s ...' % host.strip())
    try:
        data = lookup(host)
    except requests.RequestException as exc:
        print('[error] ip-api request failed: %s' % exc)
        return 1
    except ValueError:
        print('[error] ip-api returned an unparseable response.')
        return 1
    if data.get('status') != 'success':
        print('[error] Lookup failed: %s' % data.get('message', 'unknown error'))
        return 1

    flags = [name for name in ('mobile', 'proxy', 'hosting') if data.get(name)]
    lines = []
    for label, key in _ROWS:
        if label == 'Coordinates':
            value = '%s, %s' % (data.get('lat'), data.get('lon'))
        else:
            value = data.get(key)
        if value not in (None, '', 'None, None'):
            lines.append('  %-13s %s' % (label + ':', value))
    if flags:
        lines.append('  %-13s %s' % ('Flags:', ', '.join(flags)))
    output = '\n'.join(lines)
    print(output)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe = (data.get('query') or host).replace('/', '_').replace(':', '_')
        path = os.path.join(out_dir, 'ipgeo_%s.txt' % safe)
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(output + '\n')
            print('[+] Saved to %s' % path)
        except OSError as exc:
            print('[error] Could not save: %s' % exc)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1
                      else print('usage: ipgeo.py <ip|host>') or 2)
