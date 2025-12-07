# Configuration Directory

This directory contains configuration files for the Calendar Engine.

## Files

### `credentials.json`
Google API OAuth 2.0 client credentials. Obtain this file from [Google Cloud Console](https://console.cloud.google.com/):

1. Create or select a project
2. Enable required APIs:
   - Google People API (for Contacts)
   - Google Tasks API (for Tasks)
3. Create OAuth 2.0 Client ID (Application type: Desktop app)
4. Download credentials and save as `credentials.json`

### `config.yaml`
Main configuration file. Copy from `config.sample.yaml` and customize:

```bash
cp config.sample.yaml config.yaml
```

Key configuration sections:
- **google_api**: API credentials and scopes for each service
- **sync**: Synchronization behavior and timezone settings
- **ics**: Calendar output paths and formatting options
- **logging**: Logging level and output file

### Token Files
After first OAuth authentication, token files are automatically created in this directory:
- `token_contacts.json`: Contacts API token
- `token_tasks.json`: Tasks API token

These files store refresh tokens for automatic authentication renewal.

**Note:** Token files are now stored in the `config/` directory (not `data/`) for better security separation.

## Configuration Tips

1. **Enable/Disable Services**: Set `enabled: false` in `google_api.contacts` or `google_api.tasks` to disable specific services
2. **Timezone**: Use IANA timezone names (e.g., `America/New_York`, `Asia/Shanghai`)
3. **Reminders**: Configure notification times for different event types
4. **Output Paths**: Customize ICS file locations for different calendar subscriptions

## Security

⚠️ **Never commit these files to version control:**
- `credentials.json`
- `config.yaml` (may contain sensitive paths)
- Token files

Add them to `.gitignore` to prevent accidental commits.
