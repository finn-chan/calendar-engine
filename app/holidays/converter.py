"""Holidays ICS converter module."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List

from app.holidays.client import HolidayEvent

logger = logging.getLogger(__name__)


class HolidaysConverter:
    """Converter for holidays to ICS format with custom alarms."""

    def __init__(
        self,
        holiday_output_path: str,
        festival_output_path: str,
        holiday_reminders: List[str],
        festival_reminders: List[str],
        holiday_calendar_name: str = "中国法定假日",
        festival_calendar_name: str = "中国传统节日",
    ):
        """Initialize holidays converter.

        Args:
            holiday_output_path: Output path for statutory holidays ICS file
            festival_output_path: Output path for traditional festivals ICS file
            holiday_reminders: List of reminder times for holidays (e.g., ["-2 09:00", "-14 09:00"])
            festival_reminders: List of reminder times for festivals (e.g., ["09:00"])
            holiday_calendar_name: Calendar name for statutory holidays
            festival_calendar_name: Calendar name for traditional festivals
        """
        self.holiday_output_path = Path(holiday_output_path)
        self.festival_output_path = Path(festival_output_path)
        self.holiday_reminders = holiday_reminders
        self.festival_reminders = festival_reminders
        self.holiday_calendar_name = holiday_calendar_name
        self.festival_calendar_name = festival_calendar_name

        # Create output directories if needed
        self.holiday_output_path.parent.mkdir(parents=True, exist_ok=True)
        self.festival_output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Holidays converter initialized "
            f"(holiday reminders: {len(holiday_reminders)}, "
            f"festival reminders: {len(festival_reminders)})"
        )

    def convert_and_save(self, events: List[HolidayEvent]) -> None:
        """Convert events and save to separate ICS files.

        Args:
            events: List of HolidayEvent objects
        """
        logger.info(f"Converting {len(events)} events to ICS format")

        # Separate events by category
        holiday_events = [e for e in events if e.category == "holiday"]
        festival_events = [e for e in events if e.category == "festival"]

        # Sort by date
        holiday_events.sort(key=lambda x: x.date)
        festival_events.sort(key=lambda x: x.date)

        logger.info(
            f"Split into {len(holiday_events)} statutory holidays "
            f"and {len(festival_events)} traditional festivals"
        )

        # Generate ICS content
        holiday_ics = self._generate_ics(
            holiday_events, self.holiday_calendar_name, "holiday"
        )
        festival_ics = self._generate_ics(
            festival_events, self.festival_calendar_name, "festival"
        )

        # Save files
        self._save_ics_file(self.holiday_output_path, holiday_ics)
        self._save_ics_file(self.festival_output_path, festival_ics)

        logger.info(
            f"Generated ICS files:\n"
            f"  - {self.holiday_output_path} ({len(holiday_events)} events)\n"
            f"  - {self.festival_output_path} ({len(festival_events)} events)"
        )

    def _generate_ics(
        self, events: List[HolidayEvent], calendar_name: str, event_type: str
    ) -> str:
        """Generate ICS file content.

        Args:
            events: List of HolidayEvent objects
            calendar_name: Name of the calendar
            event_type: 'holiday' or 'festival'

        Returns:
            Complete ICS file content
        """
        # Create header
        ics_content = self._create_ics_header(calendar_name)

        # Add events with alarms
        for event in events:
            event_with_alarms = self._add_alarms_to_event(
                event.raw_content, event.summary, event_type
            )
            ics_content += "\n" + event_with_alarms

        # Add footer
        ics_content += "\n" + self._create_ics_footer()

        return ics_content

    def _add_alarms_to_event(
        self, event_content: str, event_summary: str, event_type: str
    ) -> str:
        """Add alarm(s) to event.

        Args:
            event_content: Original event content
            event_summary: Event summary text
            event_type: 'holiday' or 'festival'

        Returns:
            Event content with alarms added
        """
        # Find END:VEVENT position
        end_event_pos = event_content.find("END:VEVENT")
        if end_event_pos == -1:
            return event_content

        # Select reminder times based on event type
        reminder_times = (
            self.holiday_reminders
            if event_type == "holiday"
            else self.festival_reminders
        )

        alarms = []
        for reminder in reminder_times:
            trigger, description = self._parse_reminder_time(reminder, event_summary)
            if trigger:
                alarms.append(
                    f"""BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:{description}
TRIGGER:{trigger}
END:VALARM"""
                )

        if not alarms:
            logger.warning(
                f"No valid alarms generated for {event_type}: {event_summary}"
            )
            return event_content

        # Insert alarms before END:VEVENT
        alarm_text = "\n" + "\n".join(alarms) + "\n"
        modified_content = (
            event_content[:end_event_pos] + alarm_text + event_content[end_event_pos:]
        )

        return modified_content

    @staticmethod
    def _parse_reminder_time(reminder: str, event_summary: str) -> tuple:
        """Parse reminder time string to iCalendar TRIGGER format.

        Args:
            reminder: Reminder time string (e.g., "-2 09:00", "09:00")
            event_summary: Event summary for description

        Returns:
            Tuple of (trigger_string, description_string)
        """
        parts = reminder.strip().split()

        if len(parts) == 2:
            # Format: "-2 09:00" (days before + time)
            try:
                days = int(parts[0])
                time = parts[1]
                hours, minutes = map(int, time.split(":"))

                if days < 0:
                    # Before event
                    days_abs = abs(days)
                    # Calculate hours offset from midnight
                    hours_offset = 24 - hours
                    trigger = f"-P{days_abs - 1}DT{hours_offset}H"

                    if days_abs == 1:
                        description = f"明天是{event_summary}"
                    elif days_abs == 2:
                        description = f"03天后是{event_summary}"
                    elif days_abs <= 7:
                        description = f"0{days_abs + 1}天后是{event_summary}"
                    else:
                        description = f"{days_abs + 1}天后是{event_summary}"
                else:
                    # After event (unusual, but support it)
                    trigger = f"P{days}DT{hours}H"
                    description = f"{event_summary}已过{days}天"

                return trigger, description

            except (ValueError, IndexError):
                logger.warning(f"Invalid reminder format: {reminder}")
                return None, None

        elif len(parts) == 1:
            # Format: "09:00" (same day at specific time)
            try:
                time = parts[0]
                hours, minutes = map(int, time.split(":"))
                trigger = f"PT{hours}H"
                description = f"今天是{event_summary}"
                return trigger, description

            except (ValueError, IndexError):
                logger.warning(f"Invalid reminder format: {reminder}")
                return None, None

        else:
            logger.warning(f"Unsupported reminder format: {reminder}")
            return None, None

    @staticmethod
    def _create_ics_header(calendar_name: str) -> str:
        """Create ICS file header.

        Args:
            calendar_name: Name of the calendar

        Returns:
            ICS header content
        """
        return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Calendar Engine//Holidays//EN
CALSCALE:GREGORIAN
X-WR-CALNAME:{calendar_name}
X-APPLE-LANGUAGE:zh
X-APPLE-REGION:CN"""

    @staticmethod
    def _create_ics_footer() -> str:
        """Create ICS file footer.

        Returns:
            ICS footer content
        """
        return "END:VCALENDAR"

    def _save_ics_file(self, file_path: Path, content: str) -> None:
        """Save ICS content to file.

        Args:
            file_path: Path to save file
            content: ICS file content
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Saved ICS file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to save ICS file {file_path}: {e}")
            raise

    def print_summary(self, events: List[HolidayEvent]) -> None:
        """Print event summary grouped by year.

        Args:
            events: List of HolidayEvent objects
        """
        holiday_events = [e for e in events if e.category == "holiday"]
        festival_events = [e for e in events if e.category == "festival"]

        # Print statutory holidays
        logger.info("=" * 60)
        logger.info("Statutory Holidays and Workdays (法定节假日和调休)")
        logger.info("=" * 60)

        if holiday_events:
            current_year = None
            for event in sorted(holiday_events, key=lambda x: x.date):
                event_year = event.date.year
                if current_year != event_year:
                    current_year = event_year
                    logger.info(f"\n[{current_year}]")

                date_str = event.date.strftime("%Y-%m-%d")
                logger.info(f"  {date_str}  {event.summary}")
        else:
            logger.info("  No events found")

        logger.info(f"\nSubtotal: {len(holiday_events)} events")

        # Print traditional festivals
        logger.info("\n" + "=" * 60)
        logger.info("Traditional Festivals and Solar Terms (传统节日和节气)")
        logger.info("=" * 60)

        if festival_events:
            current_year = None
            for event in sorted(festival_events, key=lambda x: x.date):
                event_year = event.date.year
                if current_year != event_year:
                    current_year = event_year
                    logger.info(f"\n[{current_year}]")

                date_str = event.date.strftime("%Y-%m-%d")
                logger.info(f"  {date_str}  {event.summary}")
        else:
            logger.info("  No events found")

        logger.info(f"\nSubtotal: {len(festival_events)} events")
        logger.info(f"\nTotal: {len(holiday_events) + len(festival_events)} events")
