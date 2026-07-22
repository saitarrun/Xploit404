#!/usr/bin/env python3
"""Install or verify the terminal-native dark-web integrations."""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.tools.darkweb_tools import (  # noqa: E402
    TOOLS,
    install_bundled_onionsearch,
    install_tool,
    is_installed,
    verify_bundled_onionsearch,
    verify_site,
    verify_tool,
    verify_tor_transport,
    website_entries,
)


def selected_tools(values):
    if not values or values == ['all']:
        return list(TOOLS)
    unknown = [value for value in values if value not in TOOLS]
    if unknown:
        raise SystemExit('Unknown tool(s): %s' % ', '.join(unknown))
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'verify', 'status'])
    parser.add_argument('tools', nargs='*', metavar='TOOL')
    args = parser.parse_args()
    manage_every_entry = not args.tools or args.tools == ['all']
    verify_every_entry = args.action == 'verify' and manage_every_entry
    failures = 0
    if verify_every_entry:
        # Start and validate Tor before checking Tor-dependent CLI entries.
        ok, detail = verify_tor_transport()
        print('%s %-18s %s' % ('PASS' if ok else 'FAIL', 'tor-transport', detail))
        failures += int(not ok)

    for slug in selected_tools(args.tools):
        try:
            if args.action == 'install':
                install_tool(slug)
            elif args.action == 'verify':
                ok, detail = verify_tool(slug)
                print('%s %-18s %s' % ('PASS' if ok else 'FAIL', slug, detail))
                failures += int(not ok)
            else:
                print('%-18s %s' % (slug, 'installed' if is_installed(slug) else 'missing'))
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            print('FAIL %-18s %s' % (slug, exc))
            failures += 1
    if manage_every_entry:
        if args.action == 'install':
            try:
                install_bundled_onionsearch()
            except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
                print('FAIL %-18s %s' % ('onionsearch', exc))
                failures += 1
        else:
            ok, detail = verify_bundled_onionsearch()
            if args.action == 'verify':
                print('%s %-18s %s' % ('PASS' if ok else 'FAIL', 'onionsearch', detail))
                failures += int(not ok)
            else:
                print('%-18s %s' % ('onionsearch', 'installed' if ok else 'missing'))

    if verify_every_entry:
        sites = website_entries()
        with ThreadPoolExecutor(max_workers=min(6, len(sites))) as executor:
            results = list(executor.map(lambda item: verify_site(*item), sites))
        for (name, _), (ok, detail) in zip(sites, results):
            # A remote directory outage is not a failed local installation.
            # Keep it visible without masking failures in tools we control.
            print('%s site:%-13s %s' % ('PASS' if ok else 'WARN', name, detail))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
