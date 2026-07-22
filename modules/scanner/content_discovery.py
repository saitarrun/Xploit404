import random
import string
import warnings
import concurrent.futures

import requests

warnings.filterwarnings('ignore')  # silence SSL warnings (verify=False)

# Sensitive files / paths worth probing on any web host.
PATHS = [
    'robots.txt', 'sitemap.xml', 'crossdomain.xml', 'clientaccesspolicy.xml',
    '.well-known/security.txt', '.git/config', '.git/HEAD', '.svn/entries',
    '.env', '.htaccess', '.htpasswd', 'web.config', '.DS_Store',
    'admin/', 'administrator/', 'login', 'wp-admin/', 'wp-login.php',
    'phpinfo.php', 'info.php', 'test.php', 'server-status', 'server-info',
    'config.php', 'configuration.php', 'backup.zip', 'backup.tar.gz',
    'backup.sql', 'db.sql', 'dump.sql', 'database.sql',
    'actuator', 'actuator/health', 'actuator/env', 'api/', 'api/v1/',
    'swagger.json', 'swagger-ui.html', 'openapi.json', 'graphql',
    '.aws/credentials', 'id_rsa', 'debug', 'status', 'metrics',
]

# Status codes that are worth surfacing.
INTERESTING = {200, 201, 204, 301, 302, 307, 401, 403, 405, 500}


def _baseline(base, timeout):
    """Fetch a random non-existent path to learn how the server answers
    for things that don't exist (soft-404 detection)."""
    rnd = ''.join(random.choice(string.ascii_lowercase) for _ in range(16))
    try:
        r = requests.get(base + rnd, timeout=timeout, verify=False,
                         allow_redirects=False)
        return r.status_code, len(r.content)
    except requests.RequestException:
        return None, None


def discover(base_url, timeout=6, workers=20):
    """Aggressively probe common sensitive paths. Uses a soft-404 baseline
    so hosts that answer 200 for everything don't produce noise."""
    base = base_url.rstrip('/') + '/'
    base_code, base_len = _baseline(base, timeout)

    def probe(path):
        url = base + path
        try:
            r = requests.get(url, timeout=timeout, verify=False,
                            allow_redirects=False)
        except requests.RequestException:
            return None
        if r.status_code not in INTERESTING:
            return None
        # Discard responses that look like the soft-404 baseline: a server
        # that answers 200 for everything. Use a relative tolerance so SPA
        # 404 pages (which vary slightly in length) are also filtered.
        if base_code == r.status_code == 200 and base_len:
            largest = max(len(r.content), base_len)
            if abs(len(r.content) - base_len) / largest < 0.20:
                return None
        return {'path': '/' + path, 'status': r.status_code,
                'length': len(r.content)}

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for res in pool.map(probe, PATHS):
            if res:
                found.append(res)
    found.sort(key=lambda x: (x['status'], x['path']))
    return found
