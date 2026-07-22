import os
import re
import time
import warnings

import requests

warnings.filterwarnings('ignore')

NVD_API = 'https://services.nvd.nist.gov/rest/json/cves/2.0'

# NVD rate limits: 5 requests / 30s without a key, 50 requests / 30s with one.
# An API key (free from https://nvd.nist.gov/developers/request-an-api-key) is
# read from the NVD_API_KEY environment variable when present.
DELAY_WITH_KEY = 0.7
DELAY_NO_KEY = 6


def _api_key():
    return os.environ.get('NVD_API_KEY', '').strip()

# (banner regex, display label, CPE vendor, CPE product). The version captured
# by the regex is fed into an NVD CPE match so results are version-accurate.
_PATTERNS = [
    (re.compile(r'OpenSSH[_/ ]([\d.]+)', re.I), 'OpenSSH', 'openbsd', 'openssh'),
    (re.compile(r'Apache/([\d.]+)', re.I), 'Apache httpd', 'apache', 'http_server'),
    (re.compile(r'nginx/([\d.]+)', re.I), 'nginx', 'f5', 'nginx'),
    (re.compile(r'Microsoft-IIS/([\d.]+)', re.I), 'Microsoft IIS', 'microsoft', 'internet_information_services'),
    (re.compile(r'lighttpd/([\d.]+)', re.I), 'lighttpd', 'lighttpd', 'lighttpd'),
    (re.compile(r'ProFTPD ([\d.]+)', re.I), 'ProFTPD', 'proftpd', 'proftpd'),
    (re.compile(r'PHP/([\d.]+)', re.I), 'PHP', 'php', 'php'),
    (re.compile(r'MySQL[ /-]?([\d.]+)', re.I), 'MySQL', 'oracle', 'mysql'),
    (re.compile(r'OpenSSL/([\d.]+[a-z]?)', re.I), 'OpenSSL', 'openssl', 'openssl'),
    (re.compile(r'Exim[ /]([\d.]+)', re.I), 'Exim', 'exim', 'exim'),
]


def _extract_software(banners):
    """Return {label: (cpe_vendor, cpe_product, version)} from banners."""
    software = {}
    for banner in banners.values():
        for regex, label, vendor, product in _PATTERNS:
            match = regex.search(banner)
            if match:
                version = match.group(1).rstrip('.')
                software['%s %s' % (label, version)] = (vendor, product, version)
    return software


def _best_score(cve):
    metrics = cve.get('metrics', {})
    for key in ('cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2'):
        if metrics.get(key):
            return metrics[key][0]['cvssData'].get('baseScore')
    return None


def correlate(banners, max_per_product=5, timeout=20, delay=None):
    """Look up version-specific CVEs for software found in banners, via the
    NVD 2.0 API using CPE match. Returns {label: {total, top:[...]}}.

    If NVD_API_KEY is set, it is sent with each request and the inter-request
    delay drops (higher rate limit). A delay is otherwise inserted between
    queries to respect NVD's keyless rate limit (5 requests / 30s)."""
    api_key = _api_key()
    headers = {'apiKey': api_key} if api_key else {}
    if delay is None:
        delay = DELAY_WITH_KEY if api_key else DELAY_NO_KEY

    software = _extract_software(banners)
    results = {}
    for i, (label, (vendor, product, version)) in enumerate(software.items()):
        if i:
            time.sleep(delay)
        cpe = 'cpe:2.3:a:%s:%s:%s' % (vendor, product, version)
        try:
            resp = requests.get(
                NVD_API,
                params={'virtualMatchString': cpe, 'resultsPerPage': 30},
                headers=headers, timeout=timeout, verify=False,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
        except (requests.RequestException, ValueError):
            continue

        cves = []
        for item in data.get('vulnerabilities', []):
            cve = item.get('cve', {})
            summary = ''
            for desc in cve.get('descriptions', []):
                if desc.get('lang') == 'en':
                    summary = desc.get('value', '')
                    break
            cves.append({
                'id': cve.get('id'),
                'cvss': _best_score(cve),
                'summary': summary[:160],
            })

        cves.sort(key=lambda c: c['cvss'] or 0, reverse=True)
        if cves:
            results[label] = {
                'total': data.get('totalResults', len(cves)),
                'top': cves[:max_per_product],
            }
    return results
