import warnings

import requests

warnings.filterwarnings('ignore')

# numverify's legacy validate endpoint (access_key based). This is the API
# that classic numverify.com keys authenticate against - the newer
# api.apilayer.com endpoint rejects those keys.
ENDPOINT = 'https://apilayer.net/api/validate'


def lookup(number, api_key, timeout=15):
    """Query numverify for carrier / line type / location of a phone number.

    Returns the parsed dict on success, {'error': msg} on failure, or None
    if no API key was supplied."""
    if not api_key:
        return None
    try:
        resp = requests.get(
            ENDPOINT,
            params={'access_key': api_key, 'number': number},
            timeout=timeout,
        )
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return {'error': str(exc)}
    # numverify signals failure with {"success": false, "error": {...}}.
    if 'valid' not in data:
        err = data.get('error', {})
        return {'error': err.get('info', 'lookup failed').strip()}
    return data
