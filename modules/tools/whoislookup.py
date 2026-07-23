"""WHOIS registration lookup for a domain.

Prefers the system ``whois`` client (it handles every registry's referral
quirks); when it is absent, falls back to a dependency-free RFC 3912 socket
query that follows the IANA referral to the authoritative WHOIS server.
"""

import os
import shutil
import socket
import subprocess


def _clean(domain):
    domain = domain.strip().lower()
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    return domain.split('/', 1)[0].strip()


def _query(server, query, timeout=20):
    with socket.create_connection((server, 43), timeout=timeout) as sock:
        sock.sendall((query + '\r\n').encode('utf-8'))
        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b''.join(chunks).decode('utf-8', errors='replace')


def whois_socket(domain):
    """RFC 3912 lookup: ask IANA which server is authoritative, then query it."""
    domain = _clean(domain)
    referral_body = _query('whois.iana.org', domain)
    server = None
    for line in referral_body.splitlines():
        if line.lower().startswith('refer:'):
            server = line.split(':', 1)[1].strip()
            break
    if not server:
        return referral_body
    return _query(server, domain)


def run(domain, out_dir=None):
    domain = _clean(domain)
    print('[whois] Looking up %s ...' % domain)
    binary = shutil.which('whois')
    try:
        if binary:
            proc = subprocess.run([binary, domain], capture_output=True, text=True)
            text = (proc.stdout or '') + (proc.stderr or '')
        else:
            text = whois_socket(domain)
    except OSError as exc:
        print('[error] WHOIS lookup failed: %s' % exc)
        return 1
    text = text.strip()
    if not text:
        print('No WHOIS data returned.')
        return 0
    print(text)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, 'whois_%s.txt' % domain.replace('/', '_').replace(':', '_'))
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(text + '\n')
            print('\n[+] Saved to %s' % path)
        except OSError as exc:
            print('[error] Could not save: %s' % exc)
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1
                      else print('usage: whoislookup.py <domain>') or 2)
