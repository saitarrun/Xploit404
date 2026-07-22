import re
import json

from core.requester import requester

# hostname label chars only; anchors out emails, CN descriptions and spaces
valid_hostname = re.compile(r'^[a-z0-9._-]+$')

def findsubdomains(host):
    # findsubdomains.com is now behind a paywall, so subdomains are
    # sourced from crt.sh certificate transparency logs instead.
    try:
        response = requester('https://crt.sh/', {'q': '%.' + host, 'output': 'json'}).text
    except Exception:
        return []
    try:
        entries = json.loads(response)
    except (ValueError, json.JSONDecodeError):
        return []
    host = host.lower()
    suffix = '.' + host
    subdomains = set()
    for entry in entries:
        # name_value may hold several newline-separated names per record
        for name in entry.get('name_value', '').split('\n'):
            name = name.strip().lstrip('*.').lower()
            # keep genuine subdomains of host, drop emails/CN text/unrelated hosts
            if name.endswith(suffix) and valid_hostname.match(name):
                subdomains.add(name)
    return list(subdomains)
