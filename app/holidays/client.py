"""Holidays API client module."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httplib2

logger = logging.getLogger(__name__)


@dataclass
class HolidayEvent:
    """Holiday event information."""

    raw_content: str
    date: datetime
    summary: str
    category: str  # 'holiday' or 'festival'


class HolidaysClient:
    """Client for downloading and parsing holidays from Apple iCloud."""

    def __init__(
        self,
        source_url: str,
        http_timeout: int = 120,
        holiday_output_path: Optional[str] = None,
        festival_output_path: Optional[str] = None,
        preserve_history: bool = True,
    ):
        """Initialize Holidays client.

        Args:
            source_url: URL to download holidays ICS file
            http_timeout: HTTP request timeout in seconds
            holiday_output_path: Path to statutory holidays ICS file (for loading history)
            festival_output_path: Path to traditional festivals ICS file (for loading history)
            preserve_history: Whether to preserve historical events from existing files
        """
        self.source_url = source_url
        self.http_timeout = http_timeout
        self.holiday_output_path = (
            Path(holiday_output_path) if holiday_output_path else None
        )
        self.festival_output_path = (
            Path(festival_output_path) if festival_output_path else None
        )
        self.preserve_history = preserve_history

        logger.info(
            f"Holidays client initialized "
            f"(timeout={http_timeout}s, preserve_history={preserve_history})"
        )

    def download_ics(self) -> str:
        """Download ICS file content from source URL.

        Returns:
            ICS file content as string

        Raises:
            Exception: If download fails
        """
        logger.info(f"Downloading holidays from {self.source_url}")

        try:
            http = httplib2.Http(timeout=self.http_timeout)
            response, content = http.request(self.source_url, "GET")

            if response.status != 200:
                raise Exception(f"HTTP request failed with status {response.status}")

            # Decode content
            ics_content = content.decode("utf-8")
            logger.info(f"Downloaded {len(ics_content)} bytes of ICS data")

            return ics_content

        except Exception as e:
            logger.error(f"Failed to download holidays: {e}")
            raise

    def parse_events(self, ics_content: str) -> List[HolidayEvent]:
        """Parse ICS file and extract holiday events.

        Args:
            ics_content: ICS file content

        Returns:
            List of HolidayEvent objects
        """
        logger.info("Parsing holiday events from ICS content")

        events = []
        lines = ics_content.split("\n")
        current_event = []
        in_event = False

        for line in lines:
            line = line.strip()

            if line == "BEGIN:VEVENT":
                in_event = True
                current_event = [line]

            elif line == "END:VEVENT":
                current_event.append(line)
                raw_content = "\n".join(current_event)

                # Extract date
                date = self._extract_date(raw_content)
                if date is None:
                    logger.warning("Skipping event with unparseable date")
                    current_event = []
                    in_event = False
                    continue

                # Extract and format summary
                summary = self._extract_summary(raw_content)
                summary = self._format_summary(summary)

                # Update event content with formatted summary
                raw_content = self._update_event_summary(raw_content, summary)

                # Classify event
                category = self._classify_event(raw_content)

                events.append(
                    HolidayEvent(
                        raw_content=raw_content,
                        date=date,
                        summary=summary,
                        category=category,
                    )
                )

                current_event = []
                in_event = False

            elif in_event:
                current_event.append(line)

        logger.info(
            f"Parsed {len(events)} events "
            f"({len([e for e in events if e.category == 'holiday'])} holidays, "
            f"{len([e for e in events if e.category == 'festival'])} festivals)"
        )

        return events

    def get_all_events(self) -> List[HolidayEvent]:
        """Download and parse all holiday events, merging with existing ICS files.

        Returns:
            List of all holiday events (new + existing from output files if preserve_history=True)
        """
        # Download new data
        ics_content = self.download_ics()
        new_events = self.parse_events(ics_content)

        # Load existing events from output files if history preservation is enabled
        if self.preserve_history:
            existing_events = self._load_existing_events()
            # Merge events (deduplicate by date+summary)
            merged_events = self._merge_events(new_events, existing_events)
            logger.info(
                f"Total events after merge: {len(merged_events)} "
                f"(new: {len(new_events)}, existing: {len(existing_events)})"
            )
            return merged_events
        else:
            logger.info(
                f"History preservation disabled, using only new events: {len(new_events)}"
            )
            return new_events

    def _load_existing_events(self) -> List[HolidayEvent]:
        """Load existing events from output ICS files.

        Returns:
            List of existing HolidayEvent objects from both output files
        """
        events = []

        # Load from holiday output file
        if self.holiday_output_path and self.holiday_output_path.exists():
            events.extend(self._load_events_from_file(self.holiday_output_path))

        # Load from festival output file
        if self.festival_output_path and self.festival_output_path.exists():
            events.extend(self._load_events_from_file(self.festival_output_path))

        logger.info(f"Loaded {len(events)} existing events from output files")
        return events

    def _load_events_from_file(self, file_path: Path) -> List[HolidayEvent]:
        """Load events from a single ICS file.

        Args:
            file_path: Path to ICS file

        Returns:
            List of HolidayEvent objects
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            events = []
            lines = content.split("\n")
            current_event = []
            in_event = False

            for line in lines:
                line = line.strip()
                if line == "BEGIN:VEVENT":
                    in_event = True
                    current_event = [line]
                elif line == "END:VEVENT":
                    current_event.append(line)
                    raw_content = "\n".join(current_event)

                    date = self._extract_date(raw_content)
                    summary = self._extract_summary(raw_content)
                    category = self._classify_event(raw_content)

                    if date:
                        events.append(
                            HolidayEvent(
                                raw_content=raw_content,
                                date=date,
                                summary=summary,
                                category=category,
                            )
                        )

                    current_event = []
                    in_event = False
                elif in_event:
                    current_event.append(line)

            logger.debug(f"Loaded {len(events)} events from {file_path}")
            return events

        except Exception as e:
            logger.warning(f"Failed to load events from {file_path}: {e}")
            return []

    def _merge_events(
        self, new_events: List[HolidayEvent], existing_events: List[HolidayEvent]
    ) -> List[HolidayEvent]:
        """Merge new and existing events, removing duplicates.

        Args:
            new_events: Newly downloaded events
            existing_events: Previously saved events from output files

        Returns:
            Merged list with duplicates removed, sorted by date
        """
        # Create a dictionary keyed by (date, summary) to deduplicate
        event_dict: Dict[tuple, HolidayEvent] = {}

        # Add existing events first
        for event in existing_events:
            key = (event.date.strftime("%Y%m%d"), event.summary)
            event_dict[key] = event

        # Add new events (overwrite if exists)
        for event in new_events:
            key = (event.date.strftime("%Y%m%d"), event.summary)
            event_dict[key] = event

        # Convert back to list and sort by date
        merged = sorted(event_dict.values(), key=lambda e: e.date)

        return merged

    @staticmethod
    def _extract_date(event: str) -> Optional[datetime]:
        """Extract date from event content.

        Args:
            event: Event content string

        Returns:
            Datetime object or None if parsing fails
        """
        patterns = [
            r"DTSTART;VALUE=DATE:(\d{8})",
            r"DTSTART:(\d{8})",
            r"DTSTART;VALUE=DATE:(\d{4})(\d{2})(\d{2})",
            r"DTSTART:(\d{4})(\d{2})(\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, event)
            if match:
                if len(match.groups()) == 1:
                    date_str = match.group(1)
                    if len(date_str) == 8:
                        try:
                            return datetime.strptime(date_str, "%Y%m%d")
                        except ValueError:
                            continue
                elif len(match.groups()) == 3:
                    try:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    except ValueError:
                        continue

        return None

    @staticmethod
    def _extract_summary(event: str) -> str:
        """Extract summary from event content.

        Args:
            event: Event content string

        Returns:
            Summary text
        """
        summary_match = re.search(r"SUMMARY.*?:(.*?)(?:\n|$)", event)
        if summary_match:
            summary = summary_match.group(1).strip()
            # Remove language identifier
            summary = re.sub(r";LANGUAGE=zh_CN", "", summary)
            return summary
        return "未知事件"

    @staticmethod
    def _format_summary(summary: str) -> str:
        """Format summary text according to special rules.

        Args:
            summary: Original summary text

        Returns:
            Formatted summary text
        """
        # Special case: 清明 -> 清明节
        if summary.startswith("清明"):
            summary = summary.replace("清明", "清明节", 1)

        # Convert Chinese parentheses to English, ensure space before
        pattern = r"([^（(]+?)(\s*)（([^）]+)）"

        def replace_brackets(match):
            name = match.group(1).rstrip()
            content = match.group(3)
            return f"{name} ({content})"

        summary = re.sub(pattern, replace_brackets, summary)

        # Add space before English parentheses if missing
        pattern2 = r"([^( ]+)\(([^)]+)\)"

        def add_space_before_bracket(match):
            name = match.group(1)
            content = match.group(2)
            return f"{name} ({content})"

        summary = re.sub(pattern2, add_space_before_bracket, summary)

        return summary

    @staticmethod
    def _update_event_summary(event_content: str, new_summary: str) -> str:
        """Update summary in event content.

        Args:
            event_content: Original event content
            new_summary: New summary text

        Returns:
            Updated event content
        """
        pattern = r"(SUMMARY.*?:)(.*?)(\n|$)"

        def replace_summary(match):
            return match.group(1) + new_summary + match.group(3)

        return re.sub(pattern, replace_summary, event_content)

    @staticmethod
    def _classify_event(event: str) -> str:
        """Classify event as 'holiday' or 'festival'.

        Args:
            event: Event content string

        Returns:
            'holiday' for statutory holidays/workdays, 'festival' for others
        """
        # Check for statutory holiday marker
        if "X-APPLE-SPECIAL-DAY:WORK-HOLIDAY" in event:
            return "holiday"

        # Check for alternate workday marker
        if "X-APPLE-SPECIAL-DAY:ALTERNATE-WORKDAY" in event:
            return "holiday"

        # Check summary for休/班 markers
        summary_match = re.search(r"SUMMARY.*?:(.*?)(?:\n|$)", event)
        if summary_match:
            summary = summary_match.group(1)

            if "（休）" in summary or "（班）" in summary:
                return "holiday"

            # Check for major holidays
            major_holidays = [
                "元旦",
                "春节",
                "清明",
                "劳动",
                "端午",
                "中秋",
                "国庆",
            ]
            for holiday in major_holidays:
                if holiday in summary and "（" not in summary:
                    return "holiday"

        return "festival"
