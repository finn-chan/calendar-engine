# Data Directory

This directory stores output files and authentication tokens.

## Files

### Output Files
- `contacts.ics`: Calendar events from Google Contacts (birthdays, anniversaries)
- `tasks.ics`: Calendar events from Google Tasks
- `app.log`: Application log file (if logging is enabled)

### Token Files
- `token_contacts.json`: OAuth token for Google Contacts API
- `token_tasks.json`: OAuth token for Google Tasks API

These tokens are automatically created after first authentication and refreshed as needed.

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
docker run -v $(pwd)/data:/data calendar-engine
```

## Security

⚠️ Token files contain sensitive authentication data. Protect them appropriately:
- Set restrictive file permissions (e.g., `chmod 600 token_*.json`)
- Never commit to version control
- Back up securely if needed

## Cleanup

ICS files are regenerated on each sync, so old files are automatically replaced. Log files may grow over time and can be rotated or deleted as needed.
