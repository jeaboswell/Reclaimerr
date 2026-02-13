from pathlib import Path

import tomllib
from semver import VersionInfo

program_name = "Reclaimerr"
program_url = "https://github.com/jessielw/reclaimerr"

# read version from pyproject.toml
_pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
with open(_pyproject_file, "rb") as f:
    _pyproject_data = tomllib.load(f)

__version__ = VersionInfo.parse(_pyproject_data["project"]["version"])
