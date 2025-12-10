# Holidays Synchronization

## Overview

The Holidays module downloads and synchronizes Chinese statutory holidays and traditional festivals from Apple iCloud into two separate ICS calendar files with customized reminder settings.

## Features

- **Automatic Download**: Fetches latest holiday data from Apple iCloud
- **Smart Classification**: 
  - Statutory holidays and workdays (放假/调休) → `cn_zh_hol.ics`
  - Traditional festivals and solar terms (传统节日/节气) → `cn_zh_fest.ics`
- **Historical Data Preservation**: Optionally preserves previous events by reading existing ICS files (configurable)
- **Configurable Reminders**: Fully customizable reminder times for different holiday types
- **Smart Formatting**: 
  - Converts "清明" to "清明节"
  - Standardizes parentheses format (e.g., "春节（休）" → "春节 (休)")

## Configuration

### Basic Setup

```yaml
holidays:
  china:
    enabled: true
    source: icloud
    icloud:
      url: https://calendars.icloud.com/holidays/cn_zh.ics

ics:
  holidays:
    enabled: true
    holiday_output_path: /data/cn_zh_hol.ics     # Statutory holidays
    festival_output_path: /data/cn_zh_fest.ics   # Traditional festivals
    holiday_calendar_name: "中国法定假日"
    festival_calendar_name: "中国传统节日"
    
    # Reminder settings for different holiday types
    reminders:
      holiday:                           # Statutory holidays and workdays
        - "-2 09:00"                     # 3 days before at 09:00
        - "-14 09:00"                    # 15 days before at 09:00
      festival:                          # Traditional festivals
        - "09:00"                        # Same day at 09:00
```

### Configuration Options

#### holidays.china

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable holidays synchronization |
| `source` | string | `icloud` | Data source (currently only icloud) |
| `icloud.url` | string | Apple iCloud URL | Source URL for holiday data |

#### ics.holidays

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable ICS file generation |
| `holiday_output_path` | string | `/data/cn_zh_hol.ics` | Output path for statutory holidays |
| `festival_output_path` | string | `/data/cn_zh_fest.ics` | Output path for traditional festivals |
| `holiday_calendar_name` | string | `"中国法定假日"` | Calendar name for holidays |
| `festival_calendar_name` | string | `"中国传统节日"` | Calendar name for festivals |
| `reminders.holiday` | list | `["-2 09:00", "-14 09:00"]` | Reminder times for holidays |
| `reminders.festival` | list | `["09:00"]` | Reminder times for festivals |

**Reminder Format:**
- `"HH:MM"`: Same-day reminder at specified time (e.g., `"09:00"`)
- `"-N HH:MM"`: N days before at specified time (e.g., `"-2 09:00"` = 3 days before at 09:00)

## How It Works

### 1. Download Phase

The system downloads the ICS file from Apple iCloud:

```
https://calendars.icloud.com/holidays/cn_zh.ics
```

### 2. Classification

Events are classified based on:

- **Statutory Holidays** (`holiday`):
  - Has `X-APPLE-SPECIAL-DAY:WORK-HOLIDAY` marker (放假)
  - Has `X-APPLE-SPECIAL-DAY:ALTERNATE-WORKDAY` marker (调休)
  - Summary contains "（休）" or "（班）"
  - Major holidays: 元旦, 春节, 清明, 劳动节, 端午, 中秋, 国庆

- **Traditional Festivals** (`festival`):
  - All other events (traditional festivals, solar terms, etc.)

### 3. Formatting

Summary text is automatically formatted:

- `清明` → `清明节` (special case)
- `春节（休）` → `春节 (休)` (parentheses standardization)
- `元旦(1天)` → `元旦 (1天)` (add space before parentheses)

### 4. Reminder Generation

Reminders are fully configurable via `ics.holidays.reminders` in config.yaml.

#### Statutory Holidays (cn_zh_hol.ics)

Default reminders (configurable):
- 3 days before at 09:00 (TRIGGER: -P2DT15H)
- 15 days before at 09:00 (TRIGGER: -P14DT15H)

Example:
```ics
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:03天后是春节
TRIGGER:-P2DT15H
END:VALARM
```

#### Traditional Festivals (cn_zh_fest.ics)

Default reminder (configurable):
- Same day at 09:00 (TRIGGER: PT9H)

Example:
```ics
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:今天是立春
TRIGGER:PT9H
END:VALARM
```

### 5. Historical Data Preservation

**Problem**: Apple iCloud only provides recent holidays. Past events disappear over time.

**Solution**: The system reads existing output files to preserve historical data:

1. **First Run**: Download from Apple → Generate ICS files
2. **Subsequent Runs**: 
   - Load existing events from output ICS files (cn_zh_hol.ics, cn_zh_fest.ics)
   - Download new data from Apple
   - Merge (deduplicate by date + summary)
   - Generate updated ICS files

This ensures historical holidays remain in your calendar even after Apple removes them from the source. The output files themselves serve as the history cache.

## Usage

### Docker Compose (Recommended)

Schedule automatic synchronization:

```yaml
services:
  calendar-engine:
    environment:
      - HOLIDAYS_SCHEDULE=0 6 * * *  # Every day at 06:00
```

Run manually:
```bash
docker-compose run --rm calendar-engine once --only holidays
```

### Local Python

Sync all services:
```bash
python -m app
```

Sync only holidays:
```bash
python -m app --only holidays
```

With custom config:
```bash
python -m app --config /path/to/config.yaml --only holidays
```

## Output Files

### cn_zh_hol.ics (Statutory Holidays)

Contains:
- 元旦
- 春节及调休
- 清明节及调休
- 劳动节及调休
- 端午节及调休
- 中秋节及调休
- 国庆节及调休

Calendar name: **中国法定假日**

Reminders: **3 days** and **15 days** before at **09:00**

### cn_zh_fest.ics (Traditional Festivals)

Contains:
- 传统节日: 除夕, 元宵节, 端午节前夜, etc.
- 24 节气: 立春, 雨水, 惊蛰, 春分, etc.
- 其他节日: 腊八节, 中元节, 重阳节, etc.

Calendar name: **中国传统节日**

Reminder: **Same day** at **09:00**

## Calendar Subscription

After generating the ICS files, subscribe in your calendar app:

### Apple Calendar (macOS/iOS)

1. Copy ICS files to a web-accessible location
2. Calendar → File → New Calendar Subscription
3. Enter URL: `http://your-server/cn_zh_hol.ics`
4. Repeat for `cn_zh_fest.ics`

### Google Calendar

1. Settings → Import & Export
2. Import the ICS files
3. Or use a public URL if hosted

## Troubleshooting

### No Events Generated

**Symptoms**: ICS files are empty or have very few events

**Solutions**:
1. Check if source URL is accessible:
   ```bash
   curl -I https://calendars.icloud.com/holidays/cn_zh.ics
   ```
2. Verify `enabled` is `true` in config
3. Check logs for download errors

### Missing Historical Events

**Symptoms**: Old holidays disappear after sync

**Solutions**:
1. Ensure `preserve_history: true` in config (default)
2. Check that output ICS files exist and are readable
3. Verify that previous sync ran successfully and generated ICS files

### Wrong Classification

**Symptoms**: Event appears in wrong calendar

**Solutions**:
1. Check event summary for classification markers (休/班)
2. Review classification logic in `client.py`
3. Report specific event for manual adjustment

### Reminder Times Incorrect

**Symptoms**: Reminders appear at wrong time

**Solutions**:
1. Check `ics.holidays.reminders` configuration
2. Verify reminder format: "HH:MM" or "-N HH:MM"
3. Check timezone settings in `sync.timezone`
4. Test with calendar app's timezone settings

## Advanced Configuration

### Disabling History Preservation

If you want to start fresh without historical data:

```yaml
holidays:
  china:
    preserve_history: false  # Only use latest data from Apple
```

Use cases:
- Clean start after data corruption
- Only interested in current/future holidays
- Testing or debugging

### Customizing Reminder Times

Reminders are fully configurable:

```yaml
ics:
  holidays:
    reminders:
      holiday:              # Statutory holidays
        - "-7 08:00"        # 8 days before at 08:00
        - "-1 20:00"        # 2 days before at 20:00
      festival:             # Traditional festivals
        - "-1 09:00"        # 1 day before at 09:00
        - "12:00"           # Same day at 12:00
```

## Technical Details

### Data Flow

```
Apple iCloud
    ↓ (httplib2)
Download ICS
    ↓
Parse Events (client.py)
    ↓
Load Existing Events (if preserve_history=true)
    ↓
Merge & Deduplicate
    ↓
Classify (holiday/festival)
    ↓
Format Summary
    ↓
Add Configurable Reminders (converter.py)
    ↓
Generate & Save ICS Files
```

### History Storage

Historical events are preserved by reading existing output ICS files:
- `cn_zh_hol.ics`: Statutory holidays history
- `cn_zh_fest.ics`: Traditional festivals history

No separate cache file is needed. The output files themselves serve as the history source.

### Classification Rules

```python
if "X-APPLE-SPECIAL-DAY:WORK-HOLIDAY" in event:
    return "holiday"
elif "X-APPLE-SPECIAL-DAY:ALTERNATE-WORKDAY" in event:
    return "holiday"
elif "（休）" in summary or "（班）" in summary:
    return "holiday"
elif major_holiday in summary:
    return "holiday"
else:
    return "festival"
```

## Related Documentation

- [Configuration Guide](README.md)
- [Docker Deployment](docker-deployment.md)
- [Retry Configuration](retry-configuration.md)
