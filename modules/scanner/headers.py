# Security-relevant response headers and why each one matters.
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'HSTS missing - HTTPS not enforced',
    'Content-Security-Policy': 'No CSP - weaker XSS/injection defence',
    'X-Frame-Options': 'Clickjacking protection missing',
    'X-Content-Type-Options': 'MIME-sniffing protection missing',
    'Referrer-Policy': 'Referrer leakage possible',
    'Permissions-Policy': 'Feature/permissions policy not set',
}

# Headers that tend to leak stack/version information.
DISCLOSURE_HEADERS = [
    'Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version',
    'X-Generator', 'X-Runtime', 'X-Drupal-Cache', 'Via',
]


def analyze_headers(response):
    """Flag missing security headers and version-disclosing headers."""
    headers = response.headers
    missing = [
        '%s (%s)' % (name, reason)
        for name, reason in SECURITY_HEADERS.items()
        if name not in headers
    ]
    disclosure = {h: headers[h] for h in DISCLOSURE_HEADERS if h in headers}
    return {
        'missing_security_headers': missing,
        'information_disclosure': disclosure,
    }
