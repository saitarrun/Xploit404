"""Bounded execution profiles for terminal tool integrations.

The intensive profile increases coverage and diagnostic detail without enabling
denial-of-service, fuzzing, evasion, or unbounded concurrency features.
"""

STANDARD = 'standard'
INTENSIVE = 'intensive'
NAMES = (STANDARD, INTENSIVE)

_ARGS = {
    STANDARD: {},
    INTENSIVE: {
        'sublist3r': ['-b', '-t', '40'],
        'sherlock': [
            '--timeout', '30', '--print-found', '--nsfw',
            '--ignore-exclusions',
        ],
        'subfinder': [
            '-all', '-rl', '15', '-timeout', '45', '-max-time', '20',
            '-stats',
        ],
        'httpx': [
            '-status-code', '-content-length', '-content-type', '-location',
            '-title', '-server', '-tech-detect', '-cpe', '-ip', '-cname',
            '-asn', '-cdn', '-response-time', '-follow-host-redirects',
            '-tls-grab', '-http2', '-threads', '60', '-rate-limit', '175',
            '-retries', '2', '-stats',
        ],
        'nuclei': [
            '-exclude-tags', 'dos,fuzz', '-rate-limit', '175',
            '-bulk-size', '30', '-concurrency', '30', '-retries', '2',
            '-stats',
        ],
        'gau': ['--subs', '--threads', '5', '--retries', '3'],
    },
}

_SETTINGS = {
    STANDARD: {
        'wayback_limit': 10000,
        'nmap_profile': '2',
        'nuclei_severity': 'medium',
    },
    INTENSIVE: {
        'wayback_limit': 50000,
        'nmap_profile': '6',
        'nuclei_severity': 'info,low,medium,high,critical',
    },
}

_PROTECTED_ARGS = {
    'httpx': {
        't', 'threads', 'rl', 'rate-limit', 'rlm',
        'rate-limit-minute', 'config', 'unsafe',
    },
}


def normalize(name):
    """Return a valid profile name or raise ``ValueError``."""
    value = (name or STANDARD).strip().lower()
    if value not in NAMES:
        raise ValueError('unknown profile: %s' % value)
    return value


def args_for(tool, profile=STANDARD):
    """Return a copy of the bounded extra arguments for ``tool``."""
    return list(_ARGS[normalize(profile)].get(tool, ()))


def setting(name, profile=STANDARD):
    """Return a profile-owned per-tool default."""
    return _SETTINGS[normalize(profile)][name]


def validate_user_args(tool, args, profile=STANDARD):
    """Reject custom arguments that can override intensive safety bounds."""
    values = list(args or ())
    if not is_intensive(profile):
        return values
    protected = _PROTECTED_ARGS.get(tool, set())
    blocked = [value for value in values
               if value.split('=', 1)[0].lstrip('-') in protected]
    if blocked:
        raise ValueError(
            '%s cannot override intensive profile controls: %s'
            % (tool, ', '.join(blocked)))
    return values


def is_intensive(profile):
    return normalize(profile) == INTENSIVE
