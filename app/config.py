"""Configuration management module for Calendar Engine.

This module provides a unified configuration interface for all services
(Contacts, Tasks) with extensible structure and sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class Config:
    """Unified configuration loader and accessor for all services."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to YAML configuration file.
                        If None, looks for CONFIG_PATH environment variable.
        """
        if config_path is None:
            config_path = os.environ.get("CONFIG_PATH", "./config/config.yaml")

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file.

        Raises:
            FileNotFoundError: If configuration file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    # =========================================================================
    # Common Google API Configuration
    # =========================================================================

    @property
    def credentials_file(self) -> str:
        """Get Google API credentials file path."""
        return self._config.get("google_api", {}).get(
            "credentials_file", "/config/credentials.json"
        )

    @property
    def api_retry_max_attempts(self) -> int:
        """Get maximum number of retry attempts for API calls."""
        return (
            self._config.get("google_api", {}).get("retry", {}).get("max_attempts", 5)
        )

    @property
    def api_retry_max_wait_seconds(self) -> int:
        """Get maximum wait time between retries in seconds."""
        return (
            self._config.get("google_api", {})
            .get("retry", {})
            .get("max_wait_seconds", 60)
        )

    @property
    def api_retry_min_wait_seconds(self) -> int:
        """Get minimum wait time between retries in seconds."""
        return (
            self._config.get("google_api", {})
            .get("retry", {})
            .get("min_wait_seconds", 4)
        )

    @property
    def api_retry_multiplier(self) -> int:
        """Get exponential backoff multiplier for retries."""
        return self._config.get("google_api", {}).get("retry", {}).get("multiplier", 2)

    @property
    def api_http_timeout_seconds(self) -> int:
        """Get HTTP request timeout in seconds."""
        return (
            self._config.get("google_api", {})
            .get("timeout", {})
            .get("http_timeout_seconds", 120)
        )

    # =========================================================================
    # Contacts API Configuration
    # =========================================================================

    @property
    def contacts_enabled(self) -> bool:
        """Check if Contacts sync is enabled."""
        return (
            self._config.get("google_api", {}).get("contacts", {}).get("enabled", True)
        )

    @property
    def contacts_token_file(self) -> str:
        """Get Contacts API token file path."""
        return (
            self._config.get("google_api", {})
            .get("contacts", {})
            .get("token_file", "/data/token_contacts.json")
        )

    @property
    def contacts_scopes(self) -> List[str]:
        """Get Contacts API scopes."""
        return (
            self._config.get("google_api", {})
            .get("contacts", {})
            .get("scopes", ["https://www.googleapis.com/auth/contacts.readonly"])
        )

    @property
    def contacts_years_past(self) -> int:
        """Get number of past years to generate birthday/anniversary events."""
        return self._config.get("sync", {}).get("contacts", {}).get("years_past", 5)

    @property
    def contacts_years_future(self) -> int:
        """Get number of future years to generate birthday/anniversary events."""
        return self._config.get("sync", {}).get("contacts", {}).get("years_future", 5)

    # =========================================================================
    # Tasks API Configuration
    # =========================================================================

    @property
    def tasks_enabled(self) -> bool:
        """Check if Tasks sync is enabled."""
        return self._config.get("google_api", {}).get("tasks", {}).get("enabled", True)

    @property
    def tasks_token_file(self) -> str:
        """Get Tasks API token file path."""
        return (
            self._config.get("google_api", {})
            .get("tasks", {})
            .get("token_file", "/data/token_tasks.json")
        )

    @property
    def tasks_scopes(self) -> List[str]:
        """Get Tasks API scopes."""
        return (
            self._config.get("google_api", {})
            .get("tasks", {})
            .get("scopes", ["https://www.googleapis.com/auth/tasks.readonly"])
        )

    @property
    def tasks_include_completed(self) -> bool:
        """Whether to include completed tasks."""
        return (
            self._config.get("sync", {}).get("tasks", {}).get("include_completed", True)
        )

    @property
    def tasks_include_without_due(self) -> bool:
        """Whether to include tasks without due date."""
        return (
            self._config.get("sync", {})
            .get("tasks", {})
            .get("include_without_due", True)
        )

    @property
    def tasks_overdue_show_today(self) -> bool:
        """Whether to show overdue tasks as today's events."""
        return (
            self._config.get("sync", {})
            .get("tasks", {})
            .get("overdue_show_today", True)
        )

    @property
    def tasks_repeat_past_instances_days(self) -> int:
        """Number of days to generate past instances for recurring tasks."""
        return (
            self._config.get("sync", {})
            .get("tasks", {})
            .get("repeat_past_instances_days", 30)
        )

    @property
    def tasks_repeat_future_instances(self) -> int:
        """Number of future instances to generate for recurring tasks."""
        return (
            self._config.get("sync", {})
            .get("tasks", {})
            .get("repeat_future_instances", 10)
        )

    # =========================================================================
    # Common Sync Configuration
    # =========================================================================

    @property
    def timezone(self) -> str:
        """Get timezone for ICS conversion."""
        return self._config.get("sync", {}).get("timezone", "UTC")

    # =========================================================================
    # Contacts ICS Output Configuration
    # =========================================================================

    @property
    def contacts_ics_enabled(self) -> bool:
        """Check if Contacts ICS output is enabled."""
        return self._config.get("ics", {}).get("contacts", {}).get("enabled", True)

    @property
    def contacts_output_path(self) -> str:
        """Get Contacts ICS output file path."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("output_path", "/data/contacts.ics")
        )

    @property
    def contacts_calendar_name(self) -> str:
        """Get Contacts calendar name."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("calendar_name", "Google Contacts")
        )

    @property
    def contacts_add_empty_line(self) -> bool:
        """Whether to add empty lines between Contacts events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("add_empty_line_between_events", True)
        )

    @property
    def contacts_event_marker_gregorian(self) -> str:
        """Get gregorian birthday event marker."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("event_markers", {})
            .get("gregorian_birthday", "gregorian-birthday")
        )

    @property
    def contacts_event_marker_lunar(self) -> str:
        """Get lunar birthday event marker."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("event_markers", {})
            .get("lunar_birthday", "lunar-birthday")
        )

    @property
    def contacts_event_marker_anniversary(self) -> str:
        """Get anniversary event marker."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("event_markers", {})
            .get("anniversary", "anniversary")
        )

    @property
    def contacts_emoji_birthday(self) -> str:
        """Get emoji for birthday events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("emoji", {})
            .get("birthday", "🎂")
        )

    @property
    def contacts_emoji_anniversary(self) -> str:
        """Get emoji for anniversary events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("emoji", {})
            .get("anniversary", "💝")
        )

    @property
    def contacts_reminders_birthday(self) -> List[str]:
        """Get reminder times for birthday events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("reminders", {})
            .get("birthday", ["09:00", "19:00"])
        )

    @property
    def contacts_reminders_lunar_birthday(self) -> List[str]:
        """Get reminder times for lunar birthday events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("reminders", {})
            .get("lunar_birthday", ["09:00", "19:00"])
        )

    @property
    def contacts_reminders_anniversary(self) -> List[str]:
        """Get reminder times for anniversary events."""
        return (
            self._config.get("ics", {})
            .get("contacts", {})
            .get("reminders", {})
            .get("anniversary", ["09:00", "19:00"])
        )

    # =========================================================================
    # Tasks ICS Output Configuration
    # =========================================================================

    @property
    def tasks_ics_enabled(self) -> bool:
        """Check if Tasks ICS output is enabled."""
        return self._config.get("ics", {}).get("tasks", {}).get("enabled", True)

    @property
    def tasks_output_path(self) -> str:
        """Get Tasks ICS output file path."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("output_path", "/data/tasks.ics")
        )

    @property
    def tasks_calendar_name(self) -> str:
        """Get Tasks calendar name."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("calendar_name", "Google Tasks")
        )

    @property
    def tasks_add_tasklist_to_summary(self) -> bool:
        """Whether to add task list name to summary."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("add_tasklist_to_summary", False)
        )

    @property
    def tasks_add_status_to_description(self) -> bool:
        """Whether to add status to description."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("add_status_to_description", True)
        )

    @property
    def tasks_add_empty_line(self) -> bool:
        """Whether to add empty lines between Tasks events."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("add_empty_line_between_events", True)
        )

    @property
    def tasks_timed_event_duration_hours(self) -> int:
        """Get default duration for timed events in hours."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("timed_event_duration_hours", 1)
        )

    @property
    def tasks_emoji_completed(self) -> str:
        """Get emoji for completed tasks."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("emoji", {})
            .get("completed", "✔️")
        )

    @property
    def tasks_emoji_incomplete(self) -> str:
        """Get emoji for incomplete tasks."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("emoji", {})
            .get("incomplete", "⭕️")
        )

    @property
    def tasks_emoji_overdue(self) -> str:
        """Get emoji for overdue tasks."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("emoji", {})
            .get("overdue", "⚠️")
        )

    @property
    def tasks_reminders(self) -> List[str]:
        """Get reminder times for tasks."""
        return (
            self._config.get("ics", {})
            .get("tasks", {})
            .get("reminders", ["09:00", "19:00"])
        )

    # =========================================================================
    # Common ICS Configuration
    # =========================================================================

    @property
    def apple_language(self) -> str:
        """Get Apple calendar language."""
        return self._config.get("ics", {}).get("common", {}).get("apple_language", "en")

    @property
    def apple_region(self) -> str:
        """Get Apple calendar region."""
        return self._config.get("ics", {}).get("common", {}).get("apple_region", "US")

    @property
    def summary_language(self) -> str:
        """Get summary language parameter."""
        return (
            self._config.get("ics", {})
            .get("common", {})
            .get("summary_language", "en_US")
        )

    # =========================================================================
    # Holidays Configuration
    # =========================================================================

    @property
    def holidays_enabled(self) -> bool:
        """Check if Holidays sync is enabled."""
        return self._config.get("holidays", {}).get("china", {}).get("enabled", True)

    @property
    def holidays_preserve_history(self) -> bool:
        """Check if historical holiday data should be preserved."""
        return (
            self._config.get("holidays", {})
            .get("china", {})
            .get("preserve_history", True)
        )

    @property
    def holidays_source_url(self) -> str:
        """Get holidays source URL from iCloud."""
        return (
            self._config.get("holidays", {})
            .get("china", {})
            .get("icloud", {})
            .get("url", "https://calendars.icloud.com/holidays/cn_zh.ics")
        )

    # Holidays ICS Configuration

    @property
    def holidays_ics_enabled(self) -> bool:
        """Check if holidays ICS output is enabled."""
        return self._config.get("ics", {}).get("holidays", {}).get("enabled", True)

    @property
    def holidays_output_path(self) -> str:
        """Get holidays ICS output path (statutory holidays)."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("holiday_output_path", "/data/cn_zh_hol.ics")
        )

    @property
    def festivals_output_path(self) -> str:
        """Get festivals ICS output path (traditional festivals)."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("festival_output_path", "/data/cn_zh_fest.ics")
        )

    @property
    def holiday_calendar_name(self) -> str:
        """Get holiday calendar name."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("holiday_calendar_name", "中国法定假日")
        )

    @property
    def festival_calendar_name(self) -> str:
        """Get festival calendar name."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("festival_calendar_name", "中国传统节日")
        )

    @property
    def holiday_reminders(self) -> List[str]:
        """Get reminder times for statutory holidays."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("reminders", {})
            .get("holiday", ["-2 09:00", "-14 09:00"])
        )

    @property
    def festival_reminders(self) -> List[str]:
        """Get reminder times for traditional festivals."""
        return (
            self._config.get("ics", {})
            .get("holidays", {})
            .get("reminders", {})
            .get("festival", ["09:00"])
        )

    # =========================================================================
    # Logging Configuration
    # =========================================================================

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._config.get("logging", {}).get("level", "INFO")

    @property
    def log_file(self) -> Optional[str]:
        """Get log file path."""
        return self._config.get("logging", {}).get("file", "/data/app.log")
