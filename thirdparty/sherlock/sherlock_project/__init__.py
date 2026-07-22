""" Sherlock Module

This module contains the main logic to search for usernames at social
networks.

"""

from importlib.metadata import version as pkg_version, PackageNotFoundError
import pathlib


def get_version() -> str:
    """Fetch the version number of the installed package."""
    try:
        return pkg_version("sherlock_project")
    except PackageNotFoundError:
        pass
    # Vendored copy: read the version from pyproject.toml when available,
    # preferring the stdlib toml parser so no extra dependency is required.
    try:
        try:
            import tomllib as _toml
        except ModuleNotFoundError:
            import tomli as _toml
        pyproject_path = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
        with pyproject_path.open("rb") as f:
            return _toml.load(f)["tool"]["poetry"]["version"]
    except (FileNotFoundError, ModuleNotFoundError, KeyError):
        return "0.0.0-vendored"

# This variable is only used to check for ImportErrors induced by users running as script rather than as module or package
import_error_test_var = None

__shortname__   = "Sherlock"
__longname__    = "Sherlock: Find Usernames Across Social Networks"
__version__     = get_version()

forge_api_latest_release = "https://api.github.com/repos/sherlock-project/sherlock/releases/latest"
