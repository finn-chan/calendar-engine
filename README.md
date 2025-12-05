# Calendar Engine

A unified Python application that synchronizes Google services (Contacts, Tasks) into iCalendar (ICS) format, enabling seamless calendar subscription across mainstream calendar applications.

## Features

### Google Contacts
- ✅ Fetch contact data using Google People API
- ✅ OAuth2 authentication with automatic token refresh
- ✅ Convert birthdays and anniversaries to RFC5545-compliant ICS format
- ✅ Support for Gregorian birthdays (with or without birth year)
- ✅ Support for Lunar calendar birthdays with automatic solar date conversion
- ✅ Support for custom anniversary events
- ✅ All-day event support with proper date formatting
- ✅ Automatic age calculation for events with known start years
- ✅ Contact nickname and phone number display in descriptions
- ✅ Customizable calendar metadata and formatting

### Google Tasks
- ✅ Fetch all task data using Google Tasks API
- ✅ Convert tasks to RFC5545-compliant ICS format
- ✅ Support for both completed and incomplete tasks
- ✅ Support for tasks with and without due dates
- ✅ All-day event support (Google Tasks only supports dates, not specific times)
- ✅ Smart task status visualization with emoji (✔️ completed/⭕️ incomplete/⚠️ overdue)
- ✅ Intelligent date handling for undated tasks
- ✅ Automatic today reminder events for overdue incomplete tasks
- ✅ Dual event strategy for overdue tasks (original date + today)
- ✅ Parse recurring task patterns from task title/notes (e.g., "every day", "weekly")
- ✅ Smart recurring task instances (completed: single event, incomplete: future instances)
- ✅ Automatically generate multiple instances for recurring tasks
- ✅ Parent-child task relationship support

### Common Features
- ✅ Unified configuration system with service-specific settings
- ✅ Customizable reminder system with notification times
- ✅ Full timezone conversion support
- ✅ Docker containerization
- ✅ Command-line interface with service selection
- ✅ Extensible architecture for adding more Google services

## Quick Start

### 1. Prepare Google API Credentials

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable required APIs:
   - **Google People API** (for Contacts)
   - **Google Tasks API** (for Tasks)
4. Create OAuth 2.0 Client ID (Application type: Desktop app)
5. Download the credentials file and save it as `config/credentials.json`

### 2. Prepare Configuration File

Copy the sample configuration file and modify as needed:

```bash
cp config/config.sample.yaml config/config.yaml
```

Key configuration sections:
- **google_api**: Enable/disable services and configure API credentials
- **sync**: Synchronization behavior and timezone settings
- **ics**: Calendar output paths, names, and formatting options
- **logging**: Logging level and output file

See `config/config.sample.yaml` for detailed configuration options.

### 3. Installation

#### Option A: Local Installation

```bash
# Clone the repository
git clone https://github.com/finn-chan/calendar-engine.git
cd calendar-engine

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

#### Option B: Docker

```bash
# Build the image
docker build -t calendar-engine .
```

### 4. Usage

#### Local Execution

```bash
# Sync all enabled services
python -m app

# Sync only contacts
python -m app --only contacts

# Sync only tasks
python -m app --only tasks

# Use custom config file
python -m app --config /path/to/config.yaml

# Enable debug logging
python -m app --log-level DEBUG
```

#### Docker Execution

**First Run (Authorization Required):**

```bash
docker run -it --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine
```

On first run, a browser will open to complete OAuth2 authorization. After authorization, token files will be generated.

**Subsequent Runs:**

```bash
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine
```

**Sync only specific service:**

```bash
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine --only contacts
```

### 5. Calendar Subscription

After generating ICS files in the `data/` directory:

#### Local File Subscription
- **macOS Calendar**: File → New Calendar Subscription → file:///path/to/contacts.ics
- **Google Calendar**: Import via Settings → Import & Export

#### HTTP Subscription (Recommended for Auto-Updates)

Host the files via HTTP server:

```bash
cd data
python -m http.server 8000
```

Then subscribe using: `http://localhost:8000/contacts.ics`

For production, use a proper web server (nginx, Apache, etc.) or cloud storage with HTTP access.

## Configuration

### Service Control

Enable or disable services in `config.yaml`:

```yaml
google_api:
  contacts:
    enabled: true  # Set to false to disable Contacts sync
  tasks:
    enabled: true  # Set to false to disable Tasks sync
```

### Contacts Configuration

Configure birthday and anniversary event generation:

```yaml
sync:
  contacts:
    years_past: 5      # Generate events for past 5 years
    years_future: 5    # Generate events for next 5 years

ics:
  contacts:
    emoji:
      birthday: "🎂"
      anniversary: "💝"
    reminders:
      birthday:
        - "09:00"      # Same day at 9 AM
        - "-1 09:00"   # 1 day before at 9 AM
```

### Tasks Configuration

Configure task event generation and recurring task behavior:

```yaml
sync:
  tasks:
    include_completed: true         # Include completed tasks
    overdue_show_today: true        # Show overdue tasks as today's reminders
    repeat_future_instances: 10     # Generate 10 future instances for recurring tasks

ics:
  tasks:
    emoji:
      completed: "✔️"
      incomplete: "⭕️"
      overdue: "⚠️"           # Shown on today's reminder for overdue tasks
```

### Recurring Tasks

Tasks with these patterns in title or notes are treated as recurring:
- Daily: "every day", "daily", "every 2 days"
- Weekly: "every week", "weekly", "every 2 weeks"
- Monthly: "every month", "monthly"
- Yearly: "every year", "yearly", "annually"

## Project Structure

```
calendar-engine/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point for module execution
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Unified configuration management
│   ├── sync.py               # Main synchronization logic
│   ├── common/               # Shared utilities
│   │   ├── auth.py           # OAuth2 authentication
│   │   └── ...
│   ├── contacts/             # Contacts module
│   │   ├── client.py         # Google People API client
│   │   └── converter.py      # ICS converter for contacts
│   └── tasks/                # Tasks module
│       ├── client.py         # Google Tasks API client
│       ├── converter.py      # ICS converter for tasks
│       └── recurrence.py     # Recurring task parser
├── config/
│   ├── config.sample.yaml    # Sample configuration
│   ├── config.yaml           # User configuration (gitignored)
│   └── credentials.json      # Google API credentials (gitignored)
├── data/                     # Output directory
│   ├── *.ics                 # Generated calendars
│   └── *.json                # OAuth tokens (gitignored)
├── tests/                    # Test suite
├── docs/                     # Documentation
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
# Format code with black
black app/

# Sort imports
isort app/

# Lint with flake8
flake8 app/
```

### Type Checking

```bash
mypy app/
```

## Troubleshooting

### Authentication Issues
- Ensure `credentials.json` is in the `config/` directory
- Delete token files and re-authenticate if you change API scopes
- Check that required APIs are enabled in Google Cloud Console

### Missing Events
- Verify configuration: check `enabled` flags and date ranges
- Review log output for errors or warnings
- Ensure contacts have properly formatted birthday/event fields

### Docker Permission Issues
On Linux, ensure proper permissions for mounted volumes:

```bash
chmod 777 config data
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow Google Python Style Guide
4. Add tests for new features
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

This project merges and enhances functionality from:
- google-contacts-calendar
- google-tasks-calendar

Special thanks to all contributors of the original projects.

## Related Documentation

- [Configuration Guide](docs/README.md)
- [Contacts Features](docs/contacts.md)
- [Tasks Features](docs/tasks.md)
- [Requirements](docs/requirements.md)
