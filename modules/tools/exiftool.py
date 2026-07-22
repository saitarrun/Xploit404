"""exiftool — extract metadata from images, PDFs, documents.

Read EXIF, IPTC, XMP, and other embedded data from files.
"""

import os
import shutil
import subprocess

def binary():
    found = shutil.which('exiftool')
    if found:
        return found
    for candidate in ('/opt/homebrew/bin/exiftool', '/usr/local/bin/exiftool'):
        if os.path.isfile(candidate):
            return candidate
    return None

def is_installed():
    return binary() is not None

def install_hint():
    import platform
    hints = {
        'darwin': 'brew install exiftool',
        'linux': 'sudo apt install libimage-exiftool-perl   (or dnf/pacman equivalent)',
        'windows': 'choco install exiftool',
    }
    return hints.get(platform.system().lower(), 'see https://exiftool.org')

def ready():
    bin = binary()
    if not bin:
        return False, 'not installed (%s)' % install_hint()
    try:
        result = subprocess.run([bin, '-ver'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip().split()[0] if result.stdout else 'installed'
    except (OSError, subprocess.SubprocessError):
        version = 'installed'
    return True, version

def run(file_path, out_dir=None):
    """Extract metadata from a file."""
    bin = binary()
    if not bin:
        raise RuntimeError('exiftool is not installed')
    if not os.path.isfile(file_path):
        print('[!] File not found: %s' % file_path)
        return 1
    command = [bin, file_path]
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        safe = os.path.basename(file_path).replace('.', '_')
        out_file = os.path.join(out_dir, 'exiftool_%s.txt' % safe)
        print('[run] %s > %s' % (' '.join(command), out_file), flush=True)
        with open(out_file, 'w') as f:
            return subprocess.call(command, stdout=f, stderr=subprocess.DEVNULL)
    else:
        print('[run] %s' % ' '.join(command), flush=True)
        return subprocess.call(command)
