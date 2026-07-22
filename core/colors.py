import os
import sys


def _supports_color():
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('FORCE_COLOR'):
        return True
    return sys.stdout.isatty()


if os.name == 'nt':
    os.system('')  # enable ANSI escape processing on Windows 10+

colors = _supports_color()  # Output should be colored

if not colors:
    end = bold = red = green = yellow = blue = magenta = cyan = white = ''
    back = info = que = bad = good = run = ''
else:
    end = '\033[0m'
    bold = '\033[1m'
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    blue = '\033[94m'
    magenta = '\033[95m'
    cyan = '\033[96m'
    white = '\033[97m'
    back = '\033[7;91m'
    info = '%s[!]%s' % (yellow, end)
    que = '%s[?]%s' % (cyan, end)
    bad = '%s[-]%s' % (red, end)
    good = '%s[+]%s' % (green, end)
    run = '%s[^]%s' % (white, end)

red_line = red + ('―' * 60) + end
