"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.config import Config


def test_config_initialization() -> None:
    """Test config initialization."""
    config = Config()
    assert config.config_dir is not None
    assert config.config_file is not None


def test_get_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting API key from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    config = Config()
    assert config.get_api_key() == "test-key-123"


def test_default_model() -> None:
    """Test default model."""
    config = Config()
    assert config.get_default_model() == "gpt-4"


def test_default_filter_level() -> None:
    """Test default filter level."""
    config = Config()
    assert config.get_default_filter_level() == "error"


def test_default_time_window() -> None:
    """Test default time window."""
    config = Config()
    assert config.get_default_time_window() == 3600
