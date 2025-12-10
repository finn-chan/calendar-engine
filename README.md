# Calendar Engine

A unified Python application that synchronizes various calendar sources (Google Contacts, Google Tasks, Holidays) into iCalendar (ICS) format, enabling seamless calendar subscription across mainstream calendar applications.

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

### Holidays
- ✅ Download China holiday data from Apple iCloud
- ✅ Automatic classification into statutory holidays and traditional festivals
- ✅ Generate two separate calendars (cn_zh_hol.ics, cn_zh_fest.ics)
- ✅ Configurable reminder system for different holiday types
- ✅ Historical data preservation by reading existing output files
- ✅ Smart summary formatting (清明 → 清明节, parentheses standardization)
- ✅ No authentication required (public data source)

### Common Features
- ✅ Unified configuration system with service-specific settings
- ✅ Unified retry mechanism with exponential backoff for all errors
- ✅ Automatic error recovery for network failures, API rate limits, and timeouts
- ✅ Configurable HTTP timeout and retry parameters
- ✅ Customizable reminder system with notification times
- ✅ Full timezone conversion support
- ✅ Docker containerization with cron scheduling
- ✅ Automated builds via GitHub Actions
- ✅ Command-line interface with service selection
- ✅ Extensible architecture for adding more Google services

## Quick Start

### 1. Prepare Google API Credentials (For Contacts and Tasks Only)

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable required APIs:
   - **Google People API** (for Contacts)
   - **Google Tasks API** (for Tasks)
4. Create OAuth 2.0 Client ID (Application type: Desktop app)
5. Download the credentials file and save it as `config/credentials.json`

**Note**: Holidays synchronization does not require Google API credentials as it uses a public data source from Apple iCloud.

### 2. Prepare Configuration File

Copy the sample configuration file and modify as needed:

```bash
cp config/config.sample.yaml config/config.yaml
```

Key configuration sections:
- **google_api**: Enable/disable Google services and configure API credentials
- **holidays**: Enable/disable holidays sync and configure data source
- **sync**: Synchronization behavior and timezone settings
- **ics**: Calendar output paths, names, and formatting options
- **logging**: Logging level and output file

See `config/config.sample.yaml` for detailed configuration options.

### 3. Installation & Deployment

#### Option A: Docker Compose (Recommended for Production)

Use Docker Compose for automated scheduled synchronization:

```bash
# Clone the repository
git clone https://github.com/finn-chan/calendar-engine.git
cd calendar-engine

# Configure your settings
cp config/config.sample.yaml config/config.yaml
# Edit config/config.yaml and add your credentials.json

# Configure sync schedules in docker-compose.yml
# Edit environment variables: CONTACTS_SCHEDULE and TASKS_SCHEDULE

# Start the container (runs continuously with cron)
docker-compose up -d

# View logs
docker-compose logs -f

# One-time sync (if SYNC_ON_START=false)
docker-compose run --rm calendar-engine once
```

See [Docker Deployment Guide](docs/docker-deployment.md) for detailed instructions on:
- Configuring sync schedules via environment variables
- Environment variable reference
- GitHub Actions for automated builds
- Monitoring and troubleshooting

#### Option B: Local Installation

```bash
# Clone the repository
git clone https://github.com/finn-chan/calendar-engine.git
cd calendar-engine

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

#### Option C: Manual Docker Build

```bash
# Build the image
docker build -t calendar-engine .

# Run once
docker run -it --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine once
```

### 4. Usage

#### Docker Compose (Automated Scheduling)

```bash
# Start container with cron daemon (runs continuously)
docker-compose up -d

# View real-time logs
docker-compose logs -f

# Run sync immediately (one-time)
docker-compose run --rm calendar-engine once

# Sync only contacts
docker-compose run --rm calendar-engine once --only contacts

# Check cron schedule
docker-compose exec calendar-engine cat /etc/cron.d/calendar-engine

# View sync logs
docker-compose exec calendar-engine tail -f /var/log/cron/contacts.log
```

#### Local Execution

```bash
# Sync all enabled services
python -m app

# Sync only contacts
python -m app --only contacts

# Sync only tasks
python -m app --only tasks

# Sync only holidays
python -m app --only holidays

# Use custom config file
python -m app --config /path/to/config.yaml

# Enable debug logging
python -m app --log-level DEBUG
```

**Note:** For automated scheduling with local Python, use system cron (Linux/macOS) or Task Scheduler (Windows).

#### Manual Docker Execution (Without Compose)

**First Run (Authorization Required):**

```bash
docker run -it --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine once
```

On first run, follow the authorization URL in the output to complete OAuth2 authorization. Token files will be saved to `data/`.

**Subsequent Runs:**

```bash
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine once
```

**Sync only specific service:**

```bash
docker run --rm \
  -v $(pwd)/config:/config \
  -v $(pwd)/data:/data \
  calendar-engine once --only contacts
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

holidays:
  china:
    enabled: true  # Set to false to disable Holidays sync
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
      overdue: "⚠️"                 # Shown on today's reminder for overdue tasks
```

### Recurring Tasks

Tasks with these patterns in title or notes are treated as recurring:
- Daily: "every day", "daily", "every 2 days"
- Weekly: "every week", "weekly", "every 2 weeks"
- Monthly: "every month", "monthly"
- Yearly: "every year", "yearly", "annually"

### Holidays Configuration

Configure holiday synchronization and reminders:

```yaml
holidays:
  china:
    enabled: true
    preserve_history: true     # Preserve historical events from existing ICS files

ics:
  holidays:
    reminders:
      holiday:                 # Statutory holidays
        - "-3 09:00"           # 3 days before at 09:00
        - "-15 09:00"          # 15 days before at 09:00
      festival:                # Traditional festivals
        - "09:00"              # Same day at 09:00
```

**Options:**
- `preserve_history: true` (default): Merge with existing ICS files to preserve historical events
- `preserve_history: false`: Only use latest data from source (useful for clean start)

### Retry & Timeout Configuration

Configure automatic retry behavior for handling transient errors:

```yaml
google_api:
  retry:
    max_attempts: 5            # Maximum retry attempts (including initial try)
    min_wait_seconds: 4        # Initial wait time before first retry
    max_wait_seconds: 60       # Maximum wait time between retries
    multiplier: 2              # Exponential backoff multiplier (4s→8s→16s→32s→60s)
  timeout:
    http_timeout_seconds: 120  # HTTP request timeout
```

The retry mechanism uses exponential backoff and automatically retries all types of errors:
- Network connectivity issues
- Google API rate limits (HTTP 429)
- Server errors (HTTP 5xx)
- Timeout errors
- Other transient failures

For detailed information, see [Retry Configuration Guide](docs/retry-configuration.md).

## Project Structure

```
calendar-engine/
├── .github/
│   └── workflows/
│       └── docker-build.yml  # GitHub Actions CI/CD
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
│   ├── tasks/                # Tasks module
│   │   ├── client.py         # Google Tasks API client
│   │   ├── converter.py      # ICS converter for tasks
│   │   └── recurrence.py     # Recurring task parser
│   └── holidays/             # Holidays module
│       ├── client.py         # Holidays download and parsing client
│       └── converter.py      # ICS converter for holidays
├── config/
│   ├── config.sample.yaml    # Sample configuration
│   ├── config.yaml           # User configuration (gitignored)
│   ├── credentials.json      # Google API credentials (gitignored)
│   └── token_*.json          # OAuth tokens (gitignored, auto-generated)
├── data/                     # Data directory
│   └── *.ics                 # Generated calendar files (gitignored)
├── logs/                     # Logs directory
│   └── app.log               # Application log file (gitignored)
├── tests/                    # Test suite
├── docs/                     # Documentation
│   ├── docker-deployment.md  # Docker deployment guide
│   └── ...
├── Dockerfile                # Docker image configuration
├── docker-compose.yml        # Docker Compose configuration
├── docker-entrypoint.sh      # Container startup script
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

### Network Timeout & API Errors

The application includes automatic retry with exponential backoff for transient errors:

**Symptoms:**
- Log shows "TimeoutError: timed out" or "ConnectionError"
- Intermittent sync failures during specific times
- "Rate limit exceeded" or HTTP 429 errors

**Automatic Handling:**
- Network errors are automatically retried up to 5 times (configurable)
- Wait time increases exponentially: 4s → 8s → 16s → 32s → 60s
- All error types are retried (network, timeout, rate limits, server errors)

**Manual Actions:**
- Check logs for retry attempts: `grep "Retry attempt" logs/app.log`
- Adjust retry parameters in `config/config.yaml` if needed
- Increase `http_timeout_seconds` for slow networks (default: 120s)
- Reduce `max_attempts` if you want faster failures

**Configuration Example:**
```yaml
google_api:
  retry:
    max_attempts: 5            # Increase for unreliable networks
    max_wait_seconds: 60       # Increase for severe rate limiting
  timeout:
    http_timeout_seconds: 180  # Increase for slow connections
```

See [Retry Configuration Guide](docs/retry-configuration.md) for detailed troubleshooting.

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
chmod -R 755 config data
```

### Cron Not Running
Check if cron daemon is running:

```bash
docker-compose exec calendar-engine ps aux | grep cron
docker-compose restart
```

For more troubleshooting, see [Docker Deployment Guide](docs/docker-deployment.md).

## Deployment Options

### Option 1: GitHub Container Registry (Recommended)

Push to GitHub and use automated builds:

```yaml
services:
  calendar-engine:
    image: ghcr.io/<username>/calendar-engine:latest
```

GitHub Actions automatically builds and publishes images on push to main branch.

### Option 2: Self-Hosted

Build and run locally with Docker Compose:

```bash
docker-compose up -d
```

### Option 3: Cloud Hosting

Deploy to any cloud provider supporting Docker:
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

See [Docker Deployment Guide](docs/docker-deployment.md) for detailed instructions.

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

- [Docker Deployment Guide](docs/docker-deployment.md)
- [Configuration Guide](docs/README.md)
- [Contacts Features](docs/contacts.md)
- [Tasks Features](docs/tasks.md)
- [Holidays Guide](docs/holidays.md)
- [Retry Configuration](docs/retry-configuration.md)
- [Requirements](docs/requirements.md)
