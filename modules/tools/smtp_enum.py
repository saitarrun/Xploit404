"""SMTP email validation — check if emails are deliverable via SMTP probing.

Queries mail servers to test if an email address exists (without sending mail).
Note: Some mail servers block or rate-limit SMTP enumeration; use responsibly.
"""

import os
import socket

def is_installed():
    # No external dependency; uses Python's socket module.
    return True

def ready():
    return True, 'built-in (Python socket)'

def _get_mx_records(domain):
    """Fetch MX records for a domain using DNS."""
    try:
        import dns.resolver
        try:
            records = dns.resolver.resolve(domain, 'MX')
            return sorted([(r.preference, str(r.exchange)) for r in records])
        except Exception:
            return []
    except ImportError:
        # Fallback: nslookup / dig
        import subprocess
        try:
            result = subprocess.run(['dig', '+short', 'MX', domain],
                                  capture_output=True, text=True, timeout=5)
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return [(int(line.split()[0]), line.split()[1]) for line in lines if len(line.split()) >= 2]
        except (OSError, subprocess.SubprocessError):
            return []

def check_email(email, timeout=10):
    """Check if an email exists via SMTP."""
    if '@' not in email:
        return False, 'invalid email'
    local, domain = email.rsplit('@', 1)
    mx_records = _get_mx_records(domain)
    if not mx_records:
        return False, 'no MX records found'
    for pref, mx_host in mx_records:
        try:
            sock = socket.create_connection((mx_host, 25), timeout=timeout)
            sock.recv(1024)  # banner
            sock.send(b'EHLO checker\r\n')
            sock.recv(1024)
            sock.send(('MAIL FROM:<test@%s>\r\n' % domain).encode())
            sock.recv(1024)
            sock.send(('RCPT TO:<%s>\r\n' % email).encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.send(b'QUIT\r\n')
            sock.close()
            if '250' in response or '251' in response:
                return True, 'deliverable (SMTP 250/251)'
            elif '550' in response or '551' in response or '553' in response:
                return False, 'does not exist (SMTP 550/553)'
            elif '452' in response:
                return None, 'mailbox full (SMTP 452)'
            else:
                return None, 'uncertain (%s)' % response.split('\r\n')[0][:50]
        except socket.timeout:
            continue
        except Exception:
            continue
    return None, 'could not reach any MX server'

def run(email, out_dir=None):
    """Check one or more emails from a file or single email."""
    if os.path.isfile(email):
        # File of emails
        print('[*] Checking emails from %s' % email)
        results_found = []
        results_notfound = []
        with open(email) as f:
            for line in f:
                e = line.strip()
                if not e or e.startswith('#'):
                    continue
                ok, msg = check_email(e)
                if ok:
                    print('[+] %s: %s' % (e, msg))
                    results_found.append(e)
                elif ok is False:
                    print('[-] %s: %s' % (e, msg))
                    results_notfound.append(e)
                else:
                    print('[?] %s: %s' % (e, msg))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, 'smtp_enum.txt'), 'w') as f:
                f.write('FOUND:\n' + '\n'.join(results_found) + '\n\n')
                f.write('NOT FOUND:\n' + '\n'.join(results_notfound) + '\n')
        return 0
    else:
        # Single email
        ok, msg = check_email(email)
        if ok:
            print('[+] %s: %s' % (email, msg))
        elif ok is False:
            print('[-] %s: %s' % (email, msg))
        else:
            print('[?] %s: %s' % (email, msg))
        return 0 if ok else (1 if ok is False else 2)
