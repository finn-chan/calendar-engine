"""ICS converter module for contacts birthdays and anniversaries."""

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytz
from icalendar import Alarm, Calendar, Event
from lunarcalendar import Converter, DateNotExist, Lunar

logger = logging.getLogger(__name__)


class ContactsConverter:
    """Convert Google Contacts data to ICS format."""

    def __init__(
        self,
        timezone: str,
        calendar_name: str,
        apple_language: str,
        apple_region: str,
        summary_language: str,
        add_empty_line: bool,
        emoji_birthday: str,
        emoji_anniversary: str,
        event_marker_gregorian: str,
        event_marker_lunar: str,
        event_marker_anniversary: str,
        reminders_birthday: List[str],
        reminders_lunar_birthday: List[str],
        reminders_anniversary: List[str],
    ):
        """Initialize ICS converter.

        Args:
            timezone: Target timezone (e.g., 'America/New_York')
            calendar_name: Calendar name for X-WR-CALNAME
            apple_language: Language code for Apple Calendar
            apple_region: Region code for Apple Calendar
            summary_language: Language parameter for SUMMARY field
            add_empty_line: Whether to add empty lines between events
            emoji_birthday: Emoji for birthday events
            emoji_anniversary: Emoji for anniversary events
            event_marker_gregorian: Marker for gregorian birthdays
            event_marker_lunar: Marker for lunar birthdays
            event_marker_anniversary: Marker for anniversaries
            reminders_birthday: List of reminder times for birthday events
            reminders_lunar_birthday: List of reminder times for lunar birthday events
            reminders_anniversary: List of reminder times for anniversary events
        """
        self.timezone = pytz.timezone(timezone)
        self.calendar_name = calendar_name
        self.apple_language = apple_language
        self.apple_region = apple_region
        self.summary_language = summary_language
        self.add_empty_line = add_empty_line
        self.emoji_birthday = emoji_birthday
        self.emoji_anniversary = emoji_anniversary
        self.event_marker_gregorian = event_marker_gregorian
        self.event_marker_lunar = event_marker_lunar
        self.event_marker_anniversary = event_marker_anniversary
        self.reminders_birthday = reminders_birthday
        self.reminders_lunar_birthday = reminders_lunar_birthday
        self.reminders_anniversary = reminders_anniversary

    def convert_contacts_to_ics(
        self,
        contacts: List[Dict[str, Any]],
        output_path: str,
        years_past: int,
        years_future: int,
    ) -> None:
        """Convert contacts to ICS format and save to file.

        Args:
            contacts: List of contact dictionaries from Google API
            output_path: Path to save ICS file
            years_past: Number of past years to generate events for
            years_future: Number of future years to generate events for
        """
        logger.info(f"Converting {len(contacts)} contacts to ICS format")

        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Calendar Engine - Contacts//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", self.calendar_name)
        cal.add("x-apple-language", self.apple_language)
        cal.add("x-apple-region", self.apple_region)

        current_year = datetime.now().year
        event_count = 0

        for contact in contacts:
            events_added = self._process_contact(
                contact, cal, current_year, years_past, years_future
            )
            event_count += events_added

        logger.info(f"Generated {event_count} events from {len(contacts)} contacts")

        # Save to file
        self._save_calendar(cal, output_path)

    def _process_contact(
        self,
        contact: Dict[str, Any],
        calendar: Calendar,
        current_year: int,
        years_past: int,
        years_future: int,
    ) -> int:
        """Process a single contact and add events to calendar.

        Args:
            contact: Contact dictionary from API
            calendar: Calendar object to add events to
            current_year: Current year
            years_past: Number of past years to generate
            years_future: Number of future years to generate

        Returns:
            Number of events added
        """
        event_count = 0

        # Extract contact info
        name = self._get_contact_name(contact)
        nickname = self._get_contact_nickname(contact)
        phone = self._get_contact_phone(contact)

        # Generate events for the year range
        start_year = current_year - years_past
        end_year = current_year + years_future + 1

        # Process birthday
        if "birthdays" in contact and contact["birthdays"]:
            birthday_info = contact["birthdays"][0]["date"]
            for year in range(start_year, end_year):
                self._add_gregorian_birthday_event(
                    calendar, name, nickname, phone, birthday_info, year
                )
                event_count += 1

        # Process custom events
        if "events" in contact and contact["events"]:
            for event in contact["events"]:
                event_type = event.get("type", "").lower()
                event_date = event["date"]

                if self.event_marker_lunar in event_type:
                    for year in range(start_year, end_year):
                        self._add_lunar_birthday_event(
                            calendar, name, nickname, phone, event_date, year
                        )
                        event_count += 1

                elif self.event_marker_anniversary in event_type:
                    # Extract anniversary name from event type
                    anniv_name = self._extract_anniversary_name(event_type)
                    for year in range(start_year, end_year):
                        self._add_anniversary_event(
                            calendar, name, anniv_name, event_date, year
                        )
                        event_count += 1

        return event_count

    def _add_gregorian_birthday_event(
        self,
        calendar: Calendar,
        name: str,
        nickname: Optional[str],
        phone: Optional[str],
        birth_date: Dict[str, int],
        year: int,
    ) -> None:
        """Add gregorian birthday event to calendar.

        Args:
            calendar: Calendar object
            name: Contact name
            nickname: Contact nickname (optional)
            phone: Contact phone (optional)
            birth_date: Birth date dictionary with year/month/day
            year: Year to generate event for
        """
        event = Event()

        month = birth_date["month"]
        day = birth_date["day"]
        birth_year = birth_date.get("year")

        # Calculate age if birth year is known
        if birth_year:
            age = year - birth_year
            summary = f"{name}'s {age}th Birthday {self.emoji_birthday}"
            description = (
                f"Today is {nickname if nickname else name}'s {age}th birthday!"
            )
        else:
            summary = f"{name}'s Birthday {self.emoji_birthday}"
            description = f"Today is {nickname if nickname else name}'s birthday!"

        if phone:
            description += f"\nTel: {phone}"

        event_date = datetime(year, month, day)
        uid = self._generate_uid(name, year, month, day, "gregorian-birthday")

        self._add_event_properties(
            event,
            uid,
            summary,
            description,
            event_date,
            "BIRTHDAY",
            self.reminders_birthday,
        )
        calendar.add_component(event)

    def _add_lunar_birthday_event(
        self,
        calendar: Calendar,
        name: str,
        nickname: Optional[str],
        phone: Optional[str],
        lunar_date: Dict[str, int],
        year: int,
    ) -> None:
        """Add lunar birthday event to calendar.

        Args:
            calendar: Calendar object
            name: Contact name
            nickname: Contact nickname (optional)
            phone: Contact phone (optional)
            lunar_date: Lunar date dictionary with year/month/day
            year: Year to generate event for
        """
        event = Event()

        month = lunar_date["month"]
        day = lunar_date["day"]
        lunar_year = lunar_date.get("year")

        # Convert lunar to solar date
        try:
            solar_date = self._convert_lunar_to_solar(year, month, day)
        except (DateNotExist, ValueError) as e:
            logger.warning(
                f"Failed to convert lunar date for {name} "
                f"({year}-{month}-{day}): {e}"
            )
            return

        # Calculate age if birth year is known
        if lunar_year:
            age = year - lunar_year
            summary = f"{name}'s {age}th Lunar Birthday {self.emoji_birthday}"
            description = (
                f"Today is {nickname if nickname else name}'s {age}th lunar birthday!"
            )
        else:
            summary = f"{name}'s Lunar Birthday {self.emoji_birthday}"
            description = f"Today is {nickname if nickname else name}'s lunar birthday!"

        if phone:
            description += f"\nTel: {phone}"

        uid = self._generate_uid(
            name, solar_date.year, solar_date.month, solar_date.day, "lunar-birthday"
        )

        self._add_event_properties(
            event,
            uid,
            summary,
            description,
            solar_date,
            "BIRTHDAY",
            self.reminders_lunar_birthday,
        )
        calendar.add_component(event)

    def _add_anniversary_event(
        self,
        calendar: Calendar,
        contact_name: str,
        event_name: str,
        event_date: Dict[str, int],
        year: int,
    ) -> None:
        """Add anniversary event to calendar.

        Args:
            calendar: Calendar object
            contact_name: Contact name
            event_name: Anniversary event name
            event_date: Event date dictionary with year/month/day
            year: Year to generate event for
        """
        event = Event()

        month = event_date["month"]
        day = event_date["day"]
        start_year = event_date.get("year")

        # Calculate years if start year is known
        if start_year:
            years = year - start_year
            summary = f"{event_name} {years}th Anniversary {self.emoji_anniversary}"
            description = f"Today is the {years}th anniversary of {event_name}!"
        else:
            summary = f"{event_name} Anniversary {self.emoji_anniversary}"
            description = f"Today is the anniversary of {event_name}!"

        anniv_date = datetime(year, month, day)
        uid = self._generate_uid(
            contact_name, year, month, day, f"anniversary-{event_name}"
        )

        self._add_event_properties(
            event,
            uid,
            summary,
            description,
            anniv_date,
            "ANNIVERSARY",
            self.reminders_anniversary,
        )
        calendar.add_component(event)

    def _add_event_properties(
        self,
        event: Event,
        uid: str,
        summary: str,
        description: str,
        event_date: datetime,
        category: str,
        reminders: List[str],
    ) -> None:
        """Add common properties to an event.

        Args:
            event: Event object
            uid: Unique identifier
            summary: Event summary/title
            description: Event description
            event_date: Event date
            category: Event category (BIRTHDAY, ANNIVERSARY)
            reminders: List of reminder time strings
        """
        now = datetime.now()

        event.add("uid", uid)
        event.add("dtstamp", now)
        event.add("dtstart", event_date.date())
        event.add("dtend", (event_date + timedelta(days=1)).date())
        event.add("summary", summary)
        event.add("description", description)
        event.add("status", "CONFIRMED")
        event.add("categories", category)
        event.add("class", "PUBLIC")
        event.add("transp", "TRANSPARENT")
        event.add("last-modified", now)

        # Add reminders
        self._add_reminders(event, event_date, reminders)

    def _add_reminders(
        self, event: Event, event_date: datetime, reminders: List[str]
    ) -> None:
        """Add reminder alarms to an event.

        Args:
            event: Event object
            event_date: Event date
            reminders: List of reminder time strings (e.g., "09:00" or "-1 09:00")
        """
        for reminder in reminders:
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", f"Reminder: {event.get('summary')}")

            # Parse reminder time
            if " " in reminder:
                # Multi-day advance reminder (e.g., "-1 09:00")
                parts = reminder.split()
                days_before = int(parts[0])
                time_str = parts[1]
            else:
                # Same-day reminder (e.g., "09:00")
                days_before = 0
                time_str = reminder

            # Parse time
            try:
                hour, minute = map(int, time_str.split(":"))

                # Calculate trigger datetime
                trigger_date = event_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                if days_before < 0:
                    trigger_date += timedelta(days=days_before)

                # Calculate duration from event start to trigger time
                # For all-day events, the event starts at 00:00
                event_start = datetime.combine(event_date.date(), datetime.min.time())
                trigger_delta = trigger_date - event_start

                alarm.add("trigger", trigger_delta)
                event.add_component(alarm)
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid reminder format '{reminder}': {e}")

    def _convert_lunar_to_solar(self, year: int, month: int, day: int) -> datetime:
        """Convert lunar date to solar date.

        Args:
            year: Lunar year
            month: Lunar month
            day: Lunar day

        Returns:
            Solar datetime object

        Raises:
            DateNotExist: If lunar date doesn't exist
            ValueError: If conversion fails
        """
        original_day = day
        max_attempts = 5

        # Try to convert, adjusting day if needed
        for attempt in range(max_attempts):
            try:
                lunar = Lunar(year, month, day)
                solar = Converter.Lunar2Solar(lunar)

                if attempt > 0:
                    logger.info(
                        f"Successfully converted lunar date after adjusting day "
                        f"from {original_day} to {day}"
                    )

                return datetime(solar.year, solar.month, solar.day)

            except DateNotExist:
                if day > 1:
                    day -= 1  # Try previous day
                else:
                    raise ValueError(
                        f"Lunar date adjustment failed for {year}-{month}-{original_day}"
                    )

        raise ValueError(
            f"Failed to convert lunar date {year}-{month}-{original_day} "
            f"after {max_attempts} attempts"
        )

    def _generate_uid(
        self, name: str, year: int, month: int, day: int, event_type: str
    ) -> str:
        """Generate unique identifier for event.

        Args:
            name: Contact name
            year: Event year
            month: Event month
            day: Event day
            event_type: Type of event

        Returns:
            Unique identifier string
        """
        uid_string = f"{name}-{year}-{month:02d}-{day:02d}-{event_type}"
        uid_hash = hashlib.sha256(uid_string.encode()).hexdigest()[:16]
        return f"{uid_hash}@calendar-engine-contacts"

    @staticmethod
    def _get_contact_name(contact: Dict[str, Any]) -> str:
        """Extract contact name from contact dictionary.

        Args:
            contact: Contact dictionary from API

        Returns:
            Display name or 'Unknown' if not found
        """
        if "names" in contact and contact["names"]:
            return contact["names"][0].get("displayName", "Unknown")
        return "Unknown"

    @staticmethod
    def _get_contact_nickname(contact: Dict[str, Any]) -> Optional[str]:
        """Extract contact nickname from contact dictionary.

        Args:
            contact: Contact dictionary from API

        Returns:
            Nickname value or None if not found
        """
        if "nicknames" in contact and contact["nicknames"]:
            return contact["nicknames"][0].get("value")
        return None

    @staticmethod
    def _get_contact_phone(contact: Dict[str, Any]) -> Optional[str]:
        """Extract contact phone number from contact dictionary.

        Args:
            contact: Contact dictionary from API

        Returns:
            Phone number or None if not found
        """
        if "phoneNumbers" in contact and contact["phoneNumbers"]:
            return contact["phoneNumbers"][0].get("canonicalForm") or contact[
                "phoneNumbers"
            ][0].get("value")
        return None

    @staticmethod
    def _extract_anniversary_name(event_type: str) -> str:
        """Extract anniversary name from event type string.

        Args:
            event_type: Event type string (may contain hashtags and markers)

        Returns:
            Cleaned anniversary name
        """
        # Remove common markers and clean up
        event_type = event_type.replace("anniversary", "").strip()
        event_type = event_type.replace("#", "").strip()

        # Split by common separators and take last meaningful part
        parts = [p.strip() for p in event_type.split() if p.strip()]

        if parts:
            return parts[-1]
        return "Anniversary"

    def _save_calendar(self, calendar: Calendar, output_path: str) -> None:
        """Save calendar to ICS file.

        Args:
            calendar: Calendar object
            output_path: Path to save file
        """
        # Create output directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Generate ICS content
        ics_content = calendar.to_ical().decode("utf-8")

        # Add empty lines between events if configured
        if self.add_empty_line:
            ics_content = self._format_with_empty_lines(ics_content)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ics_content)

        logger.info(f"ICS file saved to {output_path}")

    @staticmethod
    def _format_with_empty_lines(ics_content: str) -> str:
        """Format ICS content with empty lines between events.

        Args:
            ics_content: Original ICS content string

        Returns:
            Formatted ICS content with empty lines between events only
        """
        ics_content = ics_content.replace("\r\n", "\n")
        lines = ics_content.split("\n")
        formatted_lines = []

        for line in lines:
            if line.strip():
                formatted_lines.append(line)
                if line.strip() == "END:VEVENT":
                    formatted_lines.append("")

        if formatted_lines and not formatted_lines[-1].strip():
            formatted_lines.pop()

        return "\n".join(formatted_lines)
