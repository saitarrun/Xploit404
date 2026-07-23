"""theHarvester integration - emails, subdomains, hosts and names from public
sources.

The upstream project is not published as a usable wheel and does not support
the newest Python, so it is vendored under ``thirdparty/theHarvester`` and run
from its own isolated interpreter (built with a compatible Python located the
same way the dark-web tools locate theirs).
"""

import os
import subprocess
from pathlib import Path

from modules.tools.darkweb_tools import find_python

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'thirdparty' / 'theHarvester'
REPO = 'https://github.com/laramies/theHarvester'

# Passive, key-free sources that work out of the box (no API credentials).
# bing/anubis/threatminer were dropped upstream (theHarvester 4.11.1 rejects
# them outright with "Invalid source" rather than skipping just those three).
DEFAULT_SOURCES = 'crtsh,duckduckgo,otx,hackertarget,rapiddns,urlscan,certspotter'


def venv_python():
    directory = SRC / '.venv'
    windows = directory / 'Scripts' / 'python.exe'
    return windows if windows.is_file() else directory / 'bin' / 'python'


def is_installed():
    return venv_python().is_file()


def ready():
    python = venv_python()
    if not python.is_file():
        return False, 'not installed (select it once to set up)'
    result = subprocess.run(
        [str(python), '-c', 'import theHarvester; print("ok")'],
        capture_output=True, text=True)
    if result.returncode == 0:
        return True, 'ready'
    return False, 'installed but not importable (re-run to repair)'


def install():
    """Clone the project (once) and build its isolated environment."""
    if not SRC.is_dir():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        print('[install] cloning theHarvester ...', flush=True)
        subprocess.check_call(['git', 'clone', '--depth', '1', REPO, str(SRC)])
    python = venv_python()
    if not python.is_file():
        # theHarvester requires Python >= 3.12; build the isolated env with a
        # compatible interpreter located the same way the dark-web tools do.
        subprocess.check_call([find_python('3.12'), '-m', 'venv',
                               str(SRC / '.venv')])
    subprocess.check_call([str(python), '-m', 'pip', 'install', '--upgrade',
                           'pip'])
    print('[install] installing theHarvester and its dependencies ...', flush=True)
    subprocess.check_call([str(python), '-m', 'pip', 'install', '.'], cwd=str(SRC))


def run(domain, sources=DEFAULT_SOURCES, out_dir=None):
    python = venv_python()
    # `python -m theHarvester` runs theHarvester/__main__.py, which (this is
    # upstream's own design, not a packaging accident - it has no
    # `if __name__ == '__main__'` guard either) only defines entry_point()
    # without calling it, so it silently does nothing. The real entry point
    # is theHarvester.theHarvester:main (see its [project.scripts] in
    # pyproject.toml); call it directly rather than via the installed
    # `theHarvester` console-script, whose shebang bakes in this venv's
    # absolute path at creation time and breaks if the project folder is
    # ever moved or renamed (as happened here).
    command = [str(python), '-c',
              'import sys; sys.argv[0] = "theHarvester"; '
              'from theHarvester.theHarvester import main; sys.exit(main())',
              '-d', domain, '-b', sources]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        command.extend(['-f', os.path.join(out_dir,
                                            'theharvester_%s' % domain.replace('/', '_').replace(':', '_'))])
    print('[run] %s' % ' '.join(command), flush=True)
    return subprocess.call(command, cwd=str(SRC))
