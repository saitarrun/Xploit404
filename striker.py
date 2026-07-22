#!/usr/bin/env python3
"""Striker Toolkit entry point.

Thin wrapper around menu.py's CLI/interactive logic, so `python3 striker.py`
behaves identically to `python3 menu.py` (both are documented usages).
"""

import sys

from menu import main

if __name__ == '__main__':
    sys.exit(main())
