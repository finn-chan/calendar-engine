"""Recurring task parser for extracting repeat patterns from task notes/title."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class RecurrenceType(Enum):
    """Types of recurrence patterns."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM_DAYS = "custom_days"


@dataclass
class RecurrenceRule:
    """Represents a parsed recurrence rule."""
    type: RecurrenceType
    interval: int = 1  # e.g., "every 2 days" has interval=2
    
    def __str__(self):
        return f"{self.type.value} (interval: {self.interval})"


class RecurrenceParser:
    """Parser for extracting recurrence patterns from task text."""
    
    # Patterns to match various recurrence formats
    PATTERNS = [
        # Daily patterns
        (re.compile(r'\bevery\s+day\b', re.IGNORECASE), RecurrenceType.DAILY, 1),
        (re.compile(r'\bdaily\b', re.IGNORECASE), RecurrenceType.DAILY, 1),
        (re.compile(r'\bevery\s+(\d+)\s+days?\b', re.IGNORECASE), RecurrenceType.DAILY, None),
        (re.compile(r'\brepeat:\s*daily\b', re.IGNORECASE), RecurrenceType.DAILY, 1),
        (re.compile(r'\brepeat\s+(\d+)\s+days?\b', re.IGNORECASE), RecurrenceType.DAILY, None),
        
        # Weekly patterns
        (re.compile(r'\bevery\s+week\b', re.IGNORECASE), RecurrenceType.WEEKLY, 1),
        (re.compile(r'\bweekly\b', re.IGNORECASE), RecurrenceType.WEEKLY, 1),
        (re.compile(r'\bevery\s+(\d+)\s+weeks?\b', re.IGNORECASE), RecurrenceType.WEEKLY, None),
        (re.compile(r'\brepeat:\s*weekly\b', re.IGNORECASE), RecurrenceType.WEEKLY, 1),
        
        # Monthly patterns
        (re.compile(r'\bevery\s+month\b', re.IGNORECASE), RecurrenceType.MONTHLY, 1),
        (re.compile(r'\bmonthly\b', re.IGNORECASE), RecurrenceType.MONTHLY, 1),
        (re.compile(r'\bevery\s+(\d+)\s+months?\b', re.IGNORECASE), RecurrenceType.MONTHLY, None),
        (re.compile(r'\brepeat:\s*monthly\b', re.IGNORECASE), RecurrenceType.MONTHLY, 1),
        
        # Yearly patterns
        (re.compile(r'\bevery\s+year\b', re.IGNORECASE), RecurrenceType.YEARLY, 1),
        (re.compile(r'\byearly\b', re.IGNORECASE), RecurrenceType.YEARLY, 1),
        (re.compile(r'\bannually\b', re.IGNORECASE), RecurrenceType.YEARLY, 1),
        (re.compile(r'\brepeat:\s*yearly\b', re.IGNORECASE), RecurrenceType.YEARLY, 1),
    ]
    
    @classmethod
    def parse(cls, text: str) -> Optional[RecurrenceRule]:
        """Parse recurrence rule from text.
        
        Args:
            text: Task title or notes containing recurrence pattern
        
        Returns:
            RecurrenceRule if pattern found, None otherwise
        """
        if not text:
            return None
        
        for pattern, rec_type, default_interval in cls.PATTERNS:
            match = pattern.search(text)
            if match:
                # Extract interval if it's a capturing group
                if match.groups():
                    interval = int(match.group(1))
                else:
                    interval = default_interval
                
                rule = RecurrenceRule(type=rec_type, interval=interval)
                logger.debug(f"Parsed recurrence rule from '{text}': {rule}")
                return rule
        
        logger.debug(f"No recurrence pattern found in '{text}'")
        return None
    
    @classmethod
    def generate_instances(cls, rule: RecurrenceRule, base_date: datetime,
                          past_days: int, future_count: int) -> List[datetime]:
        """Generate recurring task instances.
        
        Args:
            rule: The recurrence rule
            base_date: The original task due date
            past_days: Number of days in the past to generate instances
            future_count: Number of future instances to generate
        
        Returns:
            List of datetime instances
        """
        instances = []
        
        # Always include the base_date
        instances.append(base_date)
        
        # Determine if base_date is timezone-aware
        if base_date.tzinfo is not None:
            now = datetime.now(base_date.tzinfo)
        else:
            now = datetime.now()
        
        past_limit = now - timedelta(days=past_days)
        
        # Generate past instances (before base_date)
        current = cls._subtract_interval(base_date, rule)
        while current >= past_limit:
            instances.append(current)
            current = cls._subtract_interval(current, rule)
        
        # Generate future instances (after base_date)
        current = cls._add_interval(base_date, rule)
        for _ in range(future_count):
            instances.append(current)
            current = cls._add_interval(current, rule)
        
        # Sort instances chronologically
        instances.sort()
        
        logger.debug(f"Generated {len(instances)} instances for rule {rule}")
        return instances
    
    @staticmethod
    def _add_interval(dt: datetime, rule: RecurrenceRule) -> datetime:
        """Add one interval to a datetime based on recurrence rule."""
        if rule.type == RecurrenceType.DAILY:
            return dt + timedelta(days=rule.interval)
        elif rule.type == RecurrenceType.WEEKLY:
            return dt + timedelta(weeks=rule.interval)
        elif rule.type == RecurrenceType.MONTHLY:
            # Handle month addition (approximate)
            month = dt.month + rule.interval
            year = dt.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            try:
                return dt.replace(year=year, month=month)
            except ValueError:
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                if month == 2:
                    return dt.replace(year=year, month=month, day=28)
                else:
                    return dt.replace(year=year, month=month, day=30)
        elif rule.type == RecurrenceType.YEARLY:
            return dt.replace(year=dt.year + rule.interval)
        else:
            return dt
    
    @staticmethod
    def _subtract_interval(dt: datetime, rule: RecurrenceRule) -> datetime:
        """Subtract one interval from a datetime based on recurrence rule."""
        if rule.type == RecurrenceType.DAILY:
            return dt - timedelta(days=rule.interval)
        elif rule.type == RecurrenceType.WEEKLY:
            return dt - timedelta(weeks=rule.interval)
        elif rule.type == RecurrenceType.MONTHLY:
            # Handle month subtraction (approximate)
            month = dt.month - rule.interval
            year = dt.year
            while month < 1:
                month += 12
                year -= 1
            try:
                return dt.replace(year=year, month=month)
            except ValueError:
                # Handle day overflow
                if month == 2:
                    return dt.replace(year=year, month=month, day=28)
                else:
                    return dt.replace(year=year, month=month, day=30)
        elif rule.type == RecurrenceType.YEARLY:
            return dt.replace(year=dt.year - rule.interval)
        else:
            return dt
