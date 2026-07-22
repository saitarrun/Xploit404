import re

from core.utils import var


def detect_waf(response):
    """Detect Web Application Firewalls / protective CDNs from an HTTP
    response, using the bundled sqlmap-derived signature database
    (db/waf_signatures.json). Returns a list of matched product names."""
    try:
        signatures = var('waf_signatures')
    except KeyError:
        return []

    headers_blob = '\n'.join('%s: %s' % (k, v)
                             for k, v in response.headers.items())
    body = response.text
    detected = []

    for name, sig in signatures.items():
        header_re = sig.get('headers', '')
        page_re = sig.get('page', '')
        matched = False
        # Header signatures are the most reliable; page signatures next.
        if header_re:
            try:
                if re.search(header_re, headers_blob, re.I):
                    matched = True
            except re.error:
                pass
        if not matched and page_re:
            try:
                if re.search(page_re, body, re.I):
                    matched = True
            except re.error:
                pass
        if matched:
            detected.append(name)

    return detected
