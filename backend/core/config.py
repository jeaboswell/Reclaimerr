from pathlib import Path
from typing import Any

import tomlkit
from dotenv import load_dotenv
from tomlkit.toml_document import TOMLDocument

from backend.core.__version__ import __version__
from backend.core.logger import LogLevel
from backend.core.utils.working_dir import CONFIG_DIR

load_dotenv()


class Config:
    """Configuration manager using TOML for persistence"""

    # increment when breaking changes are made
    CONFIG_VERSION = 1

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_DIR / "config.toml"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config: TOMLDocument = self._load()

        # instance variables for easy access
        self.version = str(__version__)

    def _load(self) -> TOMLDocument:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                doc = tomlkit.load(f)

            # check config version compatibility
            config_version = doc.get("general", {}).get("config_version", 0)
            if config_version != self.CONFIG_VERSION:
                # version mismatch - backup old config and create new one
                backup_path = self.config_path.with_suffix(
                    f".toml.v{config_version}.bak"
                )
                self.config_path.rename(backup_path)
                return self._create_default()

            return doc
        return self._create_default()

    def _create_default(self) -> TOMLDocument:
        """Create default configuration"""
        doc = tomlkit.document()
        doc.add(tomlkit.comment("Vacuumarr Configuration"))
        doc.add(tomlkit.nl())

        # general settings
        general = tomlkit.table()
        general.add("config_version", self.CONFIG_VERSION)
        general.add("log_level", "INFO")

        doc.add("general", general)

        return doc

    def save(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            tomlkit.dump(self._config, f)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value from specified section

        Args:
            section: Config section
            key: Configuration key to retrieve
            default: Default value if key not found
        """
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value in specified section

        Args:
            section: Config section
            key: Configuration key to set
            value: Value to set
        """
        if section not in self._config:
            self._config[section] = tomlkit.table()
        self._config[section][key] = value  # pyright: ignore[reportIndexIssue]

    @property
    def log_level(self) -> LogLevel:
        """Get log level as enum"""
        level_str = self.get("general", "log_level", "INFO")
        try:
            return LogLevel[level_str.upper()]
        except KeyError:
            return LogLevel.INFO

    @log_level.setter
    def log_level(self, value: LogLevel) -> None:
        """Set log level from enum"""
        self.set("general", "log_level", str(value))


Conf = Config()
