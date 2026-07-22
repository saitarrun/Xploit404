import os
import sys

# dnspython is vendored under thirdparty/ so this works without a pip install.
_vendor = os.path.join(os.path.dirname(__file__), '..', '..', 'thirdparty')
if _vendor not in sys.path:
    sys.path.append(_vendor)

try:
    import dns.resolver
except ImportError:
    dns = None

RECORD_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']


def enumerate_dns(domain):
    """Resolve the common DNS record types for a host. Returns a dict of
    {record_type: [values]} for the types that exist."""
    if dns is None:
        return {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5
    records = {}
    for rtype in RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, rtype)
            records[rtype] = sorted(r.to_text() for r in answers)
        except Exception:
            # NXDOMAIN, NoAnswer, timeout, etc. - just skip that type.
            pass
    return records
