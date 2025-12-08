"""Tests for unified configuration module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from app.config import Config


@pytest.fixture
def sample_config():
    """Create a sample configuration dictionary."""
    return {
        "google_api": {
            "credentials_file": "/config/credentials.json",
            "contacts": {
                "enabled": True,
                "token_file": "/data/token_contacts.json",
                "scopes": ["https://www.googleapis.com/auth/contacts.readonly"],
            },
            "tasks": {
                "enabled": True,
                "token_file": "/data/token_tasks.json",
                "scopes": ["https://www.googleapis.com/auth/tasks.readonly"],
            },
        },
        "sync": {
            "timezone": "UTC",
            "contacts": {"years_past": 5, "years_future": 5},
            "tasks": {
                "include_completed": True,
                "overdue_show_today": True,
                "repeat_future_instances": 10,
            },
        },
        "ics": {
            "contacts": {
                "enabled": True,
                "output_path": "/data/contacts.ics",
                "calendar_name": "Test Contacts",
            },
            "tasks": {
                "enabled": True,
                "output_path": "/data/tasks.ics",
                "calendar_name": "Test Tasks",
            },
            "common": {
                "apple_language": "en",
                "apple_region": "US",
            },
        },
        "logging": {"level": "INFO", "file": "/data/app.log"},
    }


@pytest.fixture
def config_file(sample_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


def test_config_loading(config_file):
    """Test configuration file loading."""
    config = Config(config_file)
    assert config.credentials_file == "/config/credentials.json"
    assert config.timezone == "America/New_York"


def test_contacts_config(config_file):
    """Test Contacts-specific configuration."""
    config = Config(config_file)
    assert config.contacts_enabled is True
    assert config.contacts_token_file == "/data/token_contacts.json"
    assert config.contacts_years_past == 5
    assert config.contacts_output_path == "/data/contacts.ics"


def test_tasks_config(config_file):
    """Test Tasks-specific configuration."""
    config = Config(config_file)
    assert config.tasks_enabled is True
    assert config.tasks_token_file == "/data/token_tasks.json"
    assert config.tasks_include_completed is True
    assert config.tasks_output_path == "/data/tasks.ics"


def test_common_config(config_file):
    """Test common configuration."""
    config = Config(config_file)
    assert config.apple_language == "en"
    assert config.apple_region == "US"
    assert config.log_level == "INFO"


def test_missing_config_file():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        Config("/nonexistent/config.yaml")


def test_default_values(config_file):
    """Test default values for missing config keys."""
    # Create minimal config
    minimal_config = {"google_api": {}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(minimal_config, f)
        temp_path = f.name

    try:
        config = Config(temp_path)
        # Test defaults
        assert config.contacts_enabled is True  # Default
        assert config.tasks_enabled is True  # Default
        assert config.timezone == "UTC"  # Default
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
