"""Configuration and API key management."""

import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Configuration manager for Windows Error Analyzer."""

    def __init__(self) -> None:
        """Initialize configuration manager."""
        self.config_dir = Path.home() / ".windows-error-analyzer"
        self.config_file = self.config_dir / "config.json"
        self.cache_dir = self.config_dir / "cache"
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self._config = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._config = {}
        else:
            self._config = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self._config, f, indent=2)

    def get_api_key(self) -> str | None:
        """Get OpenAI API key from environment or config file.

        Returns:
            API key if found, None otherwise
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return api_key
        return self._config.get("api_key")

    def set_api_key(self, api_key: str) -> None:
        """Set OpenAI API key in config file.

        Args:
            api_key: OpenAI API key to save
        """
        self._config["api_key"] = api_key
        self._save_config()

    def get_default_model(self) -> str:
        """Get default OpenAI model.

        Returns:
            Model name (default: gpt-4)
        """
        return self._config.get("default_model", "gpt-4")

    def set_default_model(self, model: str) -> None:
        """Set default OpenAI model.

        Args:
            model: Model name (e.g., gpt-4, gpt-3.5-turbo)
        """
        self._config["default_model"] = model
        self._save_config()

    def get_default_filter_level(self) -> str:
        """Get default event filter level.

        Returns:
            Filter level (default: error)
        """
        return self._config.get("default_filter_level", "error")

    def set_default_filter_level(self, level: str) -> None:
        """Set default event filter level.

        Args:
            level: Filter level (all, critical, error, warning, info)
        """
        self._config["default_filter_level"] = level
        self._save_config()

    def get_default_time_window(self) -> int:
        """Get default time window in seconds.

        Returns:
            Time window in seconds (default: 3600)
        """
        return self._config.get("default_time_window", 3600)

    def set_default_time_window(self, seconds: int) -> None:
        """Set default time window in seconds.

        Args:
            seconds: Time window in seconds
        """
        self._config["default_time_window"] = seconds
        self._save_config()

    def get_all_config(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary of all configuration values
        """
        return self._config.copy()

    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()

    def ensure_cache_dir(self) -> Path:
        """Ensure cache directory exists and return path.

        Returns:
            Path to cache directory
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir
