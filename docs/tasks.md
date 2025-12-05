# Google Tasks Synchronization Guide

This guide covers the Google Tasks synchronization features in Calendar Engine.

## Overview

The Tasks module converts Google Tasks into iCalendar (ICS) format with support for task status, recurring tasks, parent-child relationships, and smart overdue handling.

## Key Features

- Convert tasks to RFC5545-compliant ICS format
- Smart status visualization with emoji (✔️ completed/⭕️ incomplete/⚠️ overdue)
- Recurring task support with pattern parsing
- Parent-child task relationships
- Overdue task handling with dual events
- Customizable reminders

## Configuration

### Basic Setup

```yaml
google_api:
  tasks:
    enabled: true
    token_file: /data/token_tasks.json
    scopes:
      - https://www.googleapis.com/auth/tasks.readonly

sync:
  tasks:
    include_completed: true
    include_without_due: true
    overdue_show_today: true
    repeat_past_instances_days: 30
    repeat_future_instances: 10

ics:
  tasks:
    enabled: true
    output_path: /data/tasks.ics
    calendar_name: Google Tasks
    emoji:
      completed: "✔️"
      incomplete: "⭕️"
      overdue: "⚠️"
    reminders:
      - "09:00"
      - "19:00"
```

## Recurring Tasks

Tasks with these patterns are treated as recurring:
- Daily: "every day", "daily", "every 2 days"
- Weekly: "every week", "weekly"
- Monthly: "every month", "monthly"
- Yearly: "every year", "yearly", "annually"

## Event Format

**Completed Task Example:**
```
SUMMARY: ✔️ Complete project documentation
DESCRIPTION: Status: Completed
              From: Project Tasks
              Link: https://tasks.google.com/...
```

**Incomplete Task Example:**
```
SUMMARY: ⭕️ Review pull request
DESCRIPTION: Status: To Do
              From: Project Tasks
              Link: https://tasks.google.com/...
```

**Overdue Task Example (Today's Reminder):**
```
SUMMARY: ⚠️ Submit report
DESCRIPTION: Status: Overdue 2025-11-30
              From: Project Tasks
              Link: https://tasks.google.com/...
```

## For More Details

See source project documentation at `google-tasks-calendar/README.md`
