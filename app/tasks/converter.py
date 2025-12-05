"""ICS converter for transforming Google Tasks into iCalendar format."""

import hashlib
import logging
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytz
from icalendar import Calendar, Event

from app.tasks.recurrence import RecurrenceParser

logger = logging.getLogger(__name__)


class TasksConverter:
    """Converts Google Tasks to ICS format."""

    def __init__(
        self,
        timezone: str,
        calendar_name: str = "Google Tasks",
        apple_language: str = "en",
        apple_region: str = "US",
        summary_language: str = "en_US",
        add_tasklist_to_summary: bool = False,
        add_status_to_description: bool = True,
        add_empty_line: bool = True,
        timed_event_duration_hours: int = 1,
        emoji_completed: str = "✔️",
        emoji_incomplete: str = "⭕️",
        emoji_overdue: str = "⚠️",
        reminders: List[str] = None,
        overdue_show_today: bool = True,
        repeat_past_days: int = 30,
        repeat_future_count: int = 10,
    ):
        """Initialize ICS converter.

        Args:
            timezone: Target timezone for events
            calendar_name: Name of the calendar
            apple_language: Language for Apple Calendar
            apple_region: Region for Apple Calendar
            summary_language: Language parameter for SUMMARY field
            add_tasklist_to_summary: Whether to add task list name to summary
            add_status_to_description: Whether to add status to description
            add_empty_line: Whether to add empty lines between events
            timed_event_duration_hours: Default duration for timed events in hours
            emoji_completed: Emoji for completed tasks
            emoji_incomplete: Emoji for incomplete tasks
            emoji_overdue: Emoji for overdue tasks
            reminders: List of reminder times in "HH:MM" format (default: ["09:00", "19:00"])
            overdue_show_today: Whether to create today's event for overdue tasks
            repeat_past_days: Days to look back for recurring task instances
            repeat_future_count: Number of future instances for recurring tasks
        """
        self.timezone = pytz.timezone(timezone)
        self.calendar_name = calendar_name
        self.apple_language = apple_language
        self.apple_region = apple_region
        self.summary_language = summary_language
        self.add_tasklist_to_summary = add_tasklist_to_summary
        self.add_status_to_description = add_status_to_description
        self.add_empty_line = add_empty_line
        self.timed_event_duration_hours = timed_event_duration_hours
        self.emoji_completed = emoji_completed
        self.emoji_incomplete = emoji_incomplete
        self.emoji_overdue = emoji_overdue
        self.reminders = reminders if reminders is not None else ["09:00", "19:00"]
        self.overdue_show_today = overdue_show_today
        self.repeat_past_days = repeat_past_days
        self.repeat_future_count = repeat_future_count

    def convert_tasks_to_ics(
        self, all_tasks: Dict[str, Dict[str, Any]], output_path: str
    ) -> None:
        """Convert all tasks to ICS file.

        Args:
            all_tasks: Dictionary mapping task list IDs to task data with parent-child relationships
            output_path: Path to write the ICS file
        """
        logger.info(f"Converting tasks to ICS format")

        cal = Calendar()
        cal.add("prodid", "-//Calendar Engine - Tasks//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", self.calendar_name)
        cal.add("x-apple-language", self.apple_language)
        cal.add("x-apple-region", self.apple_region)

        event_count = 0

        for list_id, list_data in all_tasks.items():
            list_title = list_data["title"]
            tasks = list_data["tasks"]

            # Build parent-child map
            task_map = {task["id"]: task for task in tasks}

            for task in tasks:
                # Get subtasks for this task
                subtasks = self._get_subtasks(task, task_map)

                events = self._task_to_events(task, list_title, subtasks)
                for event in events:
                    cal.add_component(event)
                    event_count += 1

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        ics_content = cal.to_ical()

        # Add empty lines between events if configured
        if self.add_empty_line:
            ics_content = self._add_empty_lines_between_events(ics_content)

        with open(output_file, "wb") as f:
            f.write(ics_content)

        logger.info(f"Successfully wrote {event_count} events to {output_path}")

    def _add_empty_lines_between_events(self, ics_content: bytes) -> bytes:
        """Add empty lines between VEVENT blocks.

        Args:
            ics_content: Original ICS content

        Returns:
            Modified ICS content with empty lines
        """
        lines = ics_content.decode("utf-8").split("\r\n")
        result = []

        for i, line in enumerate(lines):
            result.append(line)
            # Add empty line after END:VEVENT (except for the last one)
            if line == "END:VEVENT" and i < len(lines) - 1:
                result.append("")

        return "\r\n".join(result).encode("utf-8")

    def _get_subtasks(
        self, task: Dict[str, Any], task_map: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Get subtask titles for a parent task.

        Args:
            task: Parent task
            task_map: Map of task IDs to task objects

        Returns:
            List of subtask titles
        """
        subtasks = []
        task_id = task.get("id", "")

        for other_task in task_map.values():
            if other_task.get("parent") == task_id:
                subtasks.append(other_task.get("title", "Untitled"))

        return subtasks

    def _task_to_events(
        self, task: Dict[str, Any], list_title: str, subtasks: List[str]
    ) -> List[Event]:
        """Convert a single task to one or more ICS events.

        Args:
            task: Task dictionary from Google Tasks API
            list_title: Name of the task list
            subtasks: List of subtask titles

        Returns:
            List of Event objects (may be multiple for recurring tasks)
        """
        events = []

        # Parse task data
        task_id = task.get("id", "")
        title = task.get("title", "Untitled Task")
        notes = task.get("notes", "")
        status = task.get("status", "needsAction")  # "completed" or "needsAction"
        due = task.get("due")  # ISO format datetime string
        completed = task.get("completed")  # Completion datetime
        web_view_link = task.get("webViewLink")  # Web link to task

        # Handle tasks without due date
        if not due:
            logger.debug(f"Task '{title}' has no due date")

            if status == "completed" and completed:
                # Completed task: use completion date
                completed_dt = self._parse_due_date(completed)
                if completed_dt:
                    event = self._create_event(
                        task_id,
                        title,
                        notes,
                        status,
                        list_title,
                        completed_dt,
                        subtasks,
                        is_all_day=True,
                        web_view_link=web_view_link,
                    )
                    if event:
                        events.append(event)
            else:
                # Incomplete task: use today
                today = datetime.now(self.timezone)
                event = self._create_event(
                    task_id,
                    title,
                    notes,
                    status,
                    list_title,
                    today,
                    subtasks,
                    is_all_day=True,
                    web_view_link=web_view_link,
                )
                if event:
                    events.append(event)

            return events

        # Parse due date
        due_dt = self._parse_due_date(due)
        if not due_dt:
            return events

        # Determine if it's all-day event (naive datetime without tzinfo)
        is_all_day = due_dt.tzinfo is None

        # Check for recurrence pattern
        recurrence_text = f"{title} {notes}"
        recurrence_rule = RecurrenceParser.parse(recurrence_text)

        if recurrence_rule:
            # Recurring task
            logger.debug(f"Task '{title}' has recurrence: {recurrence_rule}")

            if status == "completed":
                # Completed recurring task: create single event at original due date
                event = self._create_event(
                    task_id,
                    title,
                    notes,
                    status,
                    list_title,
                    due_dt,
                    subtasks,
                    is_all_day,
                    web_view_link=web_view_link,
                )
                if event:
                    events.append(event)
            else:
                # Incomplete recurring task: generate future instances
                instances = RecurrenceParser.generate_instances(
                    recurrence_rule,
                    due_dt,
                    past_days=0,  # Don't generate past instances for incomplete recurring
                    future_count=self.repeat_future_count,
                )

                for idx, instance_date in enumerate(instances):
                    instance_id = f"{task_id}-recur-{idx}"
                    event = self._create_event(
                        instance_id,
                        title,
                        notes,
                        status,
                        list_title,
                        instance_date,
                        subtasks,
                        is_all_day,
                        is_recurring=True,
                        web_view_link=web_view_link,
                    )
                    if event:
                        events.append(event)
        else:
            # Single event
            event = self._create_event(
                task_id,
                title,
                notes,
                status,
                list_title,
                due_dt,
                subtasks,
                is_all_day,
                web_view_link=web_view_link,
            )
            if event:
                events.append(event)

            # Check if overdue and incomplete
            if (
                status == "needsAction"
                and self.overdue_show_today
                and due_dt.date() < datetime.now(self.timezone).date()
            ):
                logger.debug(f"Task '{title}' is overdue, creating today's reminder")
                # Create original date event (already added above)
                # Create today's reminder
                today_event = self._create_overdue_reminder(
                    task_id,
                    title,
                    notes,
                    list_title,
                    subtasks,
                    due_dt,
                    web_view_link=web_view_link,
                )
                if today_event:
                    events.append(today_event)

        return events

    def _create_event(
        self,
        task_id: str,
        title: str,
        notes: str,
        status: str,
        list_title: str,
        due_dt: datetime,
        subtasks: List[str],
        is_all_day: bool,
        is_recurring: bool = False,
        web_view_link: Optional[str] = None,
    ) -> Optional[Event]:
        """Create an ICS event from task data.

        Args:
            task_id: Task ID for UID generation
            title: Task title
            notes: Task notes
            status: Task status ("completed" or "needsAction")
            list_title: Task list name
            due_dt: Due datetime
            subtasks: List of subtask titles
            is_all_day: Whether this is an all-day event
            is_recurring: Whether this is a recurring instance

        Returns:
            Event object or None
        """
        event = Event()

        # DTSTAMP must be first (use fixed date format for Apple compatibility)
        event.add("dtstamp", date(1976, 4, 1), parameters={"VALUE": "DATE"})

        # Generate stable UID
        uid = self._generate_uid(task_id)
        event.add("uid", uid)

        # Set date/time
        if is_all_day:
            # All-day event with VALUE=DATE
            event.add("dtstart", due_dt.date(), parameters={"VALUE": "DATE"})
        else:
            # Event with specific time
            event.add("dtstart", due_dt)
            # Add DTEND (end time) for timed events
            end_dt = due_dt + timedelta(hours=self.timed_event_duration_hours)
            event.add("dtend", end_dt)

        # Add CLASS (required by Apple)
        event.add("class", "PUBLIC")

        # Set summary with emoji prefix
        emoji = self.emoji_completed if status == "completed" else self.emoji_incomplete
        summary = f"{emoji} {title}"
        if self.add_tasklist_to_summary:
            summary = f"[{list_title}] {summary}"
        event.add("summary", summary, parameters={"LANGUAGE": self.summary_language})

        # Build description
        description_parts = []

        # Add notes
        if notes:
            description_parts.append(notes)
            description_parts.append("")

        # Add status (first)
        if self.add_status_to_description:
            status_text = "Completed" if status == "completed" else "To Do"
            description_parts.append(f"Status: {status_text}")

        # Add task list info (second)
        description_parts.append(f"From: {list_title}")

        # Add link (third)
        if web_view_link:
            description_parts.append(f"Link: {web_view_link}")

        # Add subtasks if any
        if subtasks:
            description_parts.append("")
            description_parts.append("Subtasks:")
            for subtask_title in subtasks:
                description_parts.append(f"  • {subtask_title}")

        event.add("description", "\n".join(description_parts))

        # Add TRANSP (required by Apple)
        event.add("transp", "TRANSPARENT")

        # Add category (use list title)
        event.add("categories", [list_title])

        # Add X-APPLE-UNIVERSAL-ID (required by Apple)
        apple_uid = str(uuid.uuid4())
        event.add("x-apple-universal-id", apple_uid)

        # Add reminders
        self._add_reminders(event, due_dt, title)

        return event

    def _create_overdue_reminder(
        self,
        task_id: str,
        title: str,
        notes: str,
        list_title: str,
        subtasks: List[str],
        original_due: datetime,
        web_view_link: Optional[str] = None,
    ) -> Event:
        """Create a today's reminder event for overdue tasks.

        Args:
            task_id: Original task ID
            title: Task title
            notes: Task notes
            list_title: Task list name
            subtasks: List of subtask titles
            original_due: Original due date

        Returns:
            Event object for today
        """
        event = Event()

        # DTSTAMP first
        event.add("dtstamp", date(1976, 4, 1), parameters={"VALUE": "DATE"})

        # Generate unique UID for overdue reminder
        today_str = datetime.now(self.timezone).date().isoformat()
        uid = self._generate_uid(f"{task_id}-overdue-{today_str}")
        event.add("uid", uid)

        # Set to today (all-day with VALUE=DATE)
        today = datetime.now(self.timezone).date()
        event.add("dtstart", today, parameters={"VALUE": "DATE"})

        # Add CLASS
        event.add("class", "PUBLIC")

        # Set summary with overdue indicator
        summary = f"{self.emoji_overdue} {title}"
        if self.add_tasklist_to_summary:
            summary = f"[{list_title}] {summary}"
        event.add("summary", summary, parameters={"LANGUAGE": self.summary_language})

        # Build description
        description_parts = []

        # Add notes
        if notes:
            description_parts.append(notes)
            description_parts.append("")

        # Add overdue status (first)
        original_date_str = original_due.strftime("%Y-%m-%d")
        description_parts.append(f"Status: Overdue {original_date_str}")

        # Add task list info (second)
        description_parts.append(f"From: {list_title}")

        # Add link (third)
        if web_view_link:
            description_parts.append(f"Link: {web_view_link}")

        # Add subtasks if any
        if subtasks:
            description_parts.append("")
            description_parts.append("Subtasks:")
            for subtask_title in subtasks:
                description_parts.append(f"  • {subtask_title}")

        event.add("description", "\n".join(description_parts))

        # Add TRANSP
        event.add("transp", "TRANSPARENT")

        # Add category
        event.add("categories", [list_title, "Overdue"])

        # Add X-APPLE-UNIVERSAL-ID
        apple_uid = str(uuid.uuid4())
        event.add("x-apple-universal-id", apple_uid)

        # Add reminders
        today_dt = datetime.now(self.timezone)
        self._add_reminders(event, today_dt, title)

        return event

    def _add_reminders(self, event: Event, event_date: datetime, title: str) -> None:
        """Add reminder alarms to an event.

        Args:
            event: Event object
            event_date: Event date
            title: Task title for alarm description
        """
        from icalendar import Alarm

        for reminder in self.reminders:
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", f"Reminder: {title}")

            # Parse reminder time (format: "HH:MM")
            try:
                hour, minute = map(int, reminder.split(":"))

                # Calculate trigger datetime
                # Remove timezone info if present to work with naive datetimes
                if event_date.tzinfo is not None:
                    event_date_naive = event_date.replace(tzinfo=None)
                else:
                    event_date_naive = event_date

                trigger_date = event_date_naive.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # Calculate duration from event start to trigger time
                # For all-day events, the event starts at 00:00
                event_start = datetime.combine(
                    event_date_naive.date(), datetime.min.time()
                )
                trigger_delta = trigger_date - event_start

                alarm.add("trigger", trigger_delta)
                event.add_component(alarm)
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid reminder format '{reminder}': {e}")

    def _parse_due_date(self, due_str: str) -> Optional[datetime]:
        """Parse Google Tasks due date string.

        Args:
            due_str: ISO format datetime string from Google Tasks

        Returns:
            Datetime object, or None if parsing fails.
            For all-day tasks (00:00:00Z), returns date without timezone.
            For timed tasks, returns datetime in target timezone.
        """
        try:
            # Google Tasks returns RFC3339 format: 2024-01-01T00:00:00.000Z
            # Remove microseconds if present and parse
            if "." in due_str:
                due_str = due_str.split(".")[0] + "Z"

            # Parse as UTC
            dt = datetime.strptime(due_str, "%Y-%m-%dT%H:%M:%SZ")

            # Google Tasks API only supports dates, not times
            # All tasks return T00:00:00.000Z, which should be treated as all-day events
            # Return as naive datetime (no timezone) to indicate all-day event
            return dt.replace(tzinfo=None)

        except Exception as e:
            logger.error(f"Failed to parse due date '{due_str}': {e}")
            return None

    @staticmethod
    def _generate_uid(task_id: str) -> str:
        """Generate a stable UID for an event.

        Args:
            task_id: Task ID or composite ID

        Returns:
            Stable UID string
        """
        # Use SHA256 hash to create stable UID
        hash_obj = hashlib.sha256(task_id.encode("utf-8"))
        return f"{hash_obj.hexdigest()[:16]}@calendar-engine-tasks"
