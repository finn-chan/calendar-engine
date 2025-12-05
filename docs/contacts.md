# Google Contacts Synchronization Guide

This guide covers the Google Contacts synchronization features in Calendar Engine.

## Overview

The Contacts module converts Google Contacts birthdays and anniversaries into iCalendar (ICS) format. It supports Gregorian calendars, Lunar calendars, and custom anniversary events with automatic age calculation.

## Features

### Birthday Events
- **Gregorian Birthdays**: Birthdays from the contact's birthday field
- **Lunar Birthdays**: Lunar calendar birthdays with automatic solar date conversion
- **Age Calculation**: Automatic age display when birth year is known
- **Multiple Years**: Generate events for configurable past and future years

### Anniversary Events
- **Custom Events**: Support for any anniversary type (wedding, first date, etc.)
- **Year Counting**: Automatic calculation of anniversary years
- **Flexible Naming**: Extract anniversary name from event type

### Contact Information
- **Nickname Display**: Show contact nickname in event description
- **Phone Number**: Include phone number in event description
- **Configurable Emoji**: Customize emoji for different event types

## Configuration

### Basic Setup

Enable Contacts synchronization in `config/config.yaml`:

```yaml
google_api:
  contacts:
    enabled: true
    token_file: /data/token_contacts.json
    scopes:
      - https://www.googleapis.com/auth/contacts.readonly
```

### Sync Settings

Configure event generation range:

```yaml
sync:
  timezone: America/New_York
  contacts:
    years_past: 5      # Generate events for past 5 years
    years_future: 5    # Generate events for next 5 years
```

### Output Configuration

Customize calendar output:

```yaml
ics:
  contacts:
    enabled: true
    output_path: /data/contacts.ics
    calendar_name: Google Contacts
    add_empty_line_between_events: true
```

### Event Markers

Configure how to identify event types in contacts:

```yaml
ics:
  contacts:
    event_markers:
      gregorian_birthday: "gregorian-birthday"  # Default for birthday field
      lunar_birthday: "lunar-birthday"          # Marker in custom events
      anniversary: "anniversary"                # Marker in custom events
```

### Emoji Configuration

Customize emoji for different event types:

```yaml
ics:
  contacts:
    emoji:
      birthday: "🎂"
      anniversary: "💝"
```

### Reminder Configuration

Set up reminders for each event type:

```yaml
ics:
  contacts:
    reminders:
      birthday:
        - "09:00"      # Same day at 9:00 AM
        - "19:00"      # Same day at 7:00 PM
        - "-1 09:00"   # 1 day before at 9:00 AM
      lunar_birthday:
        - "09:00"
        - "19:00"
      anniversary:
        - "09:00"
        - "-1 09:00"   # Remind 1 day in advance
```

**Reminder Format:**
- `"HH:MM"`: Same-day reminder at specified time
- `"-N HH:MM"`: Reminder N days before at specified time

## Setting Up Contact Events

### Gregorian Birthdays

Birthdays are automatically detected from the contact's birthday field in Google Contacts:

1. Open Google Contacts
2. Edit contact
3. Add birthday in the "Birthday" field
4. Include year for age calculation (optional)

### Lunar Birthdays

To add lunar birthdays:

1. Open Google Contacts
2. Edit contact
3. Add a custom event:
   - **Date**: Lunar birthday date (will be converted to solar)
   - **Type**: Include "lunar-birthday" (e.g., "Custom: lunar-birthday")
4. Include year for age calculation (optional)

### Anniversaries

To add anniversaries:

1. Open Google Contacts
2. Edit contact
3. Add a custom event:
   - **Date**: Anniversary date
   - **Type**: Include "anniversary" + name (e.g., "Custom: anniversary Wedding")
4. Include start year for year counting (optional)

## Event Generation

### Event Format

**Birthday Example:**
```
SUMMARY: John Doe's 30th Birthday 🎂
DESCRIPTION: Today is John's 30th birthday!
              Tel: +1234567890
DTSTART: 2025-12-03 (all-day)
```

**Lunar Birthday Example:**
```
SUMMARY: Jane Smith's 25th Lunar Birthday 🎂
DESCRIPTION: Today is Jane's 25th lunar birthday!
              Tel: +9876543210
DTSTART: 2025-12-15 (all-day, converted from lunar date)
```

**Anniversary Example:**
```
SUMMARY: Wedding 5th Anniversary 💝
DESCRIPTION: Today is the 5th anniversary of Wedding!
DTSTART: 2025-06-20 (all-day)
```

### Multi-Year Generation

Events are generated for a range of years:
- **Past Years**: Specified by `years_past` (default: 5)
- **Current Year**: Always included
- **Future Years**: Specified by `years_future` (default: 5)

Example with defaults: Events from 2020 to 2030 (total: 11 years)

### Age Calculation

When birth/start year is provided:
- **With Year**: "John Doe's 30th Birthday 🎂"
- **Without Year**: "John Doe's Birthday 🎂"

## Lunar Calendar Support

### How It Works

Lunar dates are automatically converted to solar (Gregorian) dates:

1. Parse lunar date from contact event
2. Convert to solar date for the target year
3. Generate ICS event with solar date
4. Handle edge cases (non-existent dates)

### Edge Case Handling

Some lunar dates don't exist in certain years (e.g., lunar Feb 30). Calendar Engine automatically:
- Tries the specified day
- Falls back to previous days if needed
- Logs the adjustment for transparency

### Supported Range

Lunar calendar conversion is supported for years:
- **Minimum**: 1900
- **Maximum**: 2100
- Outside this range: Events are skipped with warnings

## Calendar Subscription

After generating `data/contacts.ics`:

### macOS Calendar
1. Open Calendar app
2. File → New Calendar Subscription
3. Enter: `file:///path/to/calendar-engine/data/contacts.ics`
4. Set refresh interval (e.g., daily)

### Google Calendar
1. Open Google Calendar settings
2. Import & Export → Import
3. Select `contacts.ics` file
4. Choose destination calendar

### Auto-Sync via HTTP

For automatic updates, host the ICS file via HTTP:

```bash
# Simple HTTP server
cd data
python -m http.server 8000
```

Subscribe to: `http://localhost:8000/contacts.ics`

For production, use proper web hosting or cloud storage.

## Troubleshooting

### No Events Generated

**Possible Causes:**
- Contacts don't have birthday or event fields
- Event markers don't match configuration
- Date range excludes relevant years

**Solutions:**
- Check contact data in Google Contacts
- Review `event_markers` in config
- Adjust `years_past` and `years_future`

### Lunar Date Conversion Errors

**Symptoms:**
```
WARNING: Failed to convert lunar date for Jane (2025-1-30): Lunar date adjustment failed
```

**Solutions:**
- Verify lunar date exists (some dates like lunar Feb 30 may not exist in all years)
- Check year range (1900-2100 supported)
- Lunar date will be adjusted automatically if possible

### Missing Contact Information

**Symptoms:**
- No nickname or phone number in description

**Solutions:**
- Add nickname and phone fields in Google Contacts
- Contact information is optional and won't prevent event generation

### Authentication Issues

**Symptoms:**
```
ERROR: Credentials file not found: /config/credentials.json
```

**Solutions:**
- Download credentials from Google Cloud Console
- Place file at configured path
- Ensure Google People API is enabled

## Advanced Usage

### Custom Event Markers

Change event markers to match your contact organization:

```yaml
event_markers:
  lunar_birthday: "lunar"       # Shorter marker
  anniversary: "anniv"          # Custom abbreviation
```

### Timezone Considerations

All events are all-day events, but timezone affects:
- Reminder calculation
- Log timestamps

Set appropriate timezone in config:

```yaml
sync:
  timezone: Asia/Shanghai  # Your local timezone
```

### Performance Optimization

For large contact lists:
- Events are generated in batches
- Adjust date range to reduce event count
- Monitor log file size

## API Limitations

### Google People API

- **Rate Limits**: Standard Google API quotas apply
- **Batch Size**: Maximum 1000 contacts per request
- **Fields**: Limited to specified person fields
- **Updates**: Requires re-sync to get updated contact data

### Best Practices

1. Run sync periodically (e.g., daily via cron)
2. Monitor OAuth token expiration
3. Keep configuration backed up
4. Review logs for warnings

## Examples

### Configuration Examples

**Minimal Configuration:**
```yaml
google_api:
  contacts:
    enabled: true

sync:
  contacts:
    years_past: 3
    years_future: 3
```

**Maximum Features:**
```yaml
google_api:
  contacts:
    enabled: true

sync:
  timezone: Asia/Shanghai
  contacts:
    years_past: 10
    years_future: 10

ics:
  contacts:
    calendar_name: 联系人生日
    emoji:
      birthday: "🎁"
      anniversary: "❤️"
    reminders:
      birthday:
        - "-7 09:00"  # 1 week before
        - "-1 09:00"  # 1 day before
        - "09:00"     # Same day
```

### CLI Examples

```bash
# Sync only contacts
python -m app --only contacts

# Use custom config
python -m app --config /path/to/contacts.yaml

# Debug mode
python -m app --only contacts --log-level DEBUG
```
