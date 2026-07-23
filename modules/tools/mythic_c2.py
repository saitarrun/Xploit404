"""Mythic — Collaborative, modular command and control framework.

Cross-platform C2 with pluggable agents for macOS, Linux, and Windows.
"""

import subprocess
import os

from modules.tools import render

DESCRIPTION = 'Collaborative C2 framework with pluggable cross-platform agents'


def is_installed():
    try:
        result = subprocess.run(['mythic', '--version'], capture_output=True, text=True)
        return result.returncode == 0 or os.path.exists('/opt/Mythic')
    except FileNotFoundError:
        return os.path.exists('/opt/Mythic')


def ready():
    if is_installed():
        return True, "installed (modular C2 framework)"
    return False, "not installed (https://github.com/its-a-feature/Mythic - requires Docker)"


def start_mythic(docker=True):
    """Start Mythic C2 server."""
    if docker:
        return {
            'status': 'info',
            'deployment': 'Docker-based',
            'command': 'cd /opt/Mythic && ./start.sh',
            'web_interface': 'https://localhost:7443',
            'note': 'Requires Docker and Docker Compose'
        }
    else:
        return {
            'status': 'info',
            'deployment': 'Direct installation',
            'note': 'Manual installation path available'
        }


def supported_agents():
    """List supported Mythic agents."""
    return {
        'apfell': 'macOS agent',
        'apollo': 'Windows agent with advanced evasion',
        'poseidon': 'Linux agent',
        'merlin': 'Go-based cross-platform agent',
        'python_agent': 'Lightweight Python implant',
        'note': 'Pluggable architecture allows custom agents'
    }


def agent_features():
    """Mythic agent capabilities."""
    return {
        'persistence': 'Multi-method persistence techniques',
        'privilege_escalation': 'UAC bypass, sudo bypass, kernel exploits',
        'lateral_movement': 'Pass-the-hash, pass-the-ticket, lateral execution',
        'data_exfiltration': 'Encrypted, stealth data collection',
        'anti_forensics': 'Event log clearing, artifact removal'
    }


def cli(args):
    """CLI: mythic_c2 [agents]"""
    if args and args[0] == 'agents':
        result = supported_agents()
    else:
        result = agent_features()
    text, code = render(result)
    print(text)
    return code
