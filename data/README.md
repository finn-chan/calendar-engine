# Data Directory

This directory stores generated ICS calendar files.

## Files

### Output Files
- `contacts.ics`: Calendar events from Google Contacts (birthdays, anniversaries)
- `tasks.ics`: Calendar events from Google Tasks

**Note:** Authentication tokens and application logs are now stored in separate directories:
- Tokens: `config/token_*.json` (OAuth tokens)
- Logs: `logs/app.log` (application logs)

## Calendar Subscription

After generating ICS files, you can subscribe to them in your calendar application:

### Local File Access
- **macOS Calendar**: File → New Calendar Subscription → file:///path/to/contacts.ics
- **Google Calendar**: Import the ICS file via Settings → Import & Export

### HTTP Server (Recommended)
For automatic updates, host these files via HTTP and subscribe using the URL:

```bash
# Simple HTTP server example
cd /path/to/calendar-engine/data
python -m http.server 8000
```

Then subscribe to: `http://localhost:8000/contacts.ics`

### Docker Volume
When using Docker, this directory is mounted as a volume for persistence:

```bash
docker run -v $(pwd)/config:/config -v $(pwd)/data:/data -v $(pwd)/logs:/logs calendar-engine
```

## Security

This directory contains only generated ICS calendar files, which are safe to expose via HTTP for calendar subscription.

**Sensitive files are stored elsewhere:**
- 🔒 **Credentials & Tokens**: `config/` directory (keep private)
- 🔒 **Application Logs**: `logs/` directory (keep private)
- 🌐 **ICS Files**: `data/` directory (safe to serve via HTTP)

## Cleanup

ICS files are regenerated on each sync, so old files are automatically replaced.
