"""Main synchronization module with unified logic for all services."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from app.cli import parse_args, validate_args
from app.config import Config
from app.contacts.client import ContactsClient
from app.contacts.converter import ContactsConverter
from app.tasks.client import TasksClient
from app.tasks.converter import TasksConverter


def setup_logging(config: Config, log_level_override: Optional[str] = None) -> None:
    """Setup logging configuration.

    Args:
        config: Configuration object
        log_level_override: Optional log level to override config setting
    """
    log_level_str = log_level_override or config.log_level
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_file = config.log_file

    # Create log directory if needed
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)


def sync_contacts(config: Config) -> bool:
    """Synchronize Google Contacts to ICS.

    Args:
        config: Configuration object

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not config.contacts_enabled:
        logger.info("Contacts sync is disabled in configuration")
        return True

    if not config.contacts_ics_enabled:
        logger.info("Contacts ICS output is disabled in configuration")
        return True

    try:
        logger.info("=" * 60)
        logger.info("Starting Google Contacts synchronization")
        logger.info("=" * 60)

        # Initialize Google Contacts client
        logger.info("Initializing Google Contacts client")
        client = ContactsClient(
            credentials_file=config.credentials_file,
            token_file=config.contacts_token_file,
            scopes=config.contacts_scopes,
        )

        # Fetch all contacts
        logger.info("Fetching contacts from Google People API")
        contacts = client.get_all_contacts()

        # Convert to ICS
        logger.info("Converting contacts to ICS format")
        converter = ContactsConverter(
            timezone=config.timezone,
            calendar_name=config.contacts_calendar_name,
            apple_language=config.apple_language,
            apple_region=config.apple_region,
            summary_language=config.summary_language,
            add_empty_line=config.contacts_add_empty_line,
            emoji_birthday=config.contacts_emoji_birthday,
            emoji_anniversary=config.contacts_emoji_anniversary,
            event_marker_gregorian=config.contacts_event_marker_gregorian,
            event_marker_lunar=config.contacts_event_marker_lunar,
            event_marker_anniversary=config.contacts_event_marker_anniversary,
            reminders_birthday=config.contacts_reminders_birthday,
            reminders_lunar_birthday=config.contacts_reminders_lunar_birthday,
            reminders_anniversary=config.contacts_reminders_anniversary,
        )

        converter.convert_contacts_to_ics(
            contacts,
            config.contacts_output_path,
            config.contacts_years_past,
            config.contacts_years_future,
        )

        logger.info("=" * 60)
        logger.info("Contacts synchronization completed successfully")
        logger.info(f"Output file: {config.contacts_output_path}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Contacts synchronization failed: {e}", exc_info=True)
        return False


def sync_tasks(config: Config) -> bool:
    """Synchronize Google Tasks to ICS.

    Args:
        config: Configuration object

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not config.tasks_enabled:
        logger.info("Tasks sync is disabled in configuration")
        return True

    if not config.tasks_ics_enabled:
        logger.info("Tasks ICS output is disabled in configuration")
        return True

    try:
        logger.info("=" * 60)
        logger.info("Starting Google Tasks synchronization")
        logger.info("=" * 60)

        # Initialize Google Tasks client
        logger.info("Initializing Google Tasks client")
        client = TasksClient(
            credentials_file=config.credentials_file,
            token_file=config.tasks_token_file,
            scopes=config.tasks_scopes,
        )

        # Fetch all tasks
        logger.info("Fetching tasks from Google Tasks API")
        all_tasks = client.get_all_tasks(
            show_completed=config.tasks_include_completed, show_hidden=True
        )

        # Convert to ICS
        logger.info("Converting tasks to ICS format")
        converter = TasksConverter(
            timezone=config.timezone,
            calendar_name=config.tasks_calendar_name,
            apple_language=config.apple_language,
            apple_region=config.apple_region,
            summary_language=config.summary_language,
            add_tasklist_to_summary=config.tasks_add_tasklist_to_summary,
            add_status_to_description=config.tasks_add_status_to_description,
            add_empty_line=config.tasks_add_empty_line,
            timed_event_duration_hours=config.tasks_timed_event_duration_hours,
            emoji_completed=config.tasks_emoji_completed,
            emoji_incomplete=config.tasks_emoji_incomplete,
            emoji_overdue=config.tasks_emoji_overdue,
            reminders=config.tasks_reminders,
            overdue_show_today=config.tasks_overdue_show_today,
            repeat_past_days=config.tasks_repeat_past_instances_days,
            repeat_future_count=config.tasks_repeat_future_instances,
        )

        converter.convert_tasks_to_ics(all_tasks, config.tasks_output_path)

        logger.info("=" * 60)
        logger.info("Tasks synchronization completed successfully")
        logger.info(f"Output file: {config.tasks_output_path}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Tasks synchronization failed: {e}", exc_info=True)
        return False


def main() -> int:
    """Main entry point for Calendar Engine.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_args()

    # Validate arguments
    if not validate_args(args):
        return 1

    try:
        # Set config path from args if provided
        if args.config:
            os.environ["CONFIG_PATH"] = args.config

        # Load configuration
        config = Config()

        # Setup logging
        setup_logging(config, args.log_level)
        logger = logging.getLogger(__name__)

        logger.info("=" * 60)
        logger.info("Calendar Engine - Starting Synchronization")
        logger.info("=" * 60)

        # Determine which services to sync
        sync_all = args.only is None
        sync_contacts_flag = sync_all or args.only == "contacts"
        sync_tasks_flag = sync_all or args.only == "tasks"

        success = True

        # Sync contacts if requested
        if sync_contacts_flag:
            contacts_success = sync_contacts(config)
            success = success and contacts_success

        # Sync tasks if requested
        if sync_tasks_flag:
            tasks_success = sync_tasks(config)
            success = success and tasks_success

        if success:
            logger.info("=" * 60)
            logger.info("All synchronization tasks completed successfully")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("=" * 60)
            logger.error("Some synchronization tasks failed")
            logger.error("=" * 60)
            return 1

    except FileNotFoundError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"File not found: {e}")
        return 1

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
