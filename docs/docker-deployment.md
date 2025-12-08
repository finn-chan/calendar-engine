# Docker Deployment Guide

This guide covers deploying Calendar Engine using Docker and Docker Compose with automated scheduled synchronization.

## Overview

Calendar Engine is packaged as a Docker image based on Debian 12 (slim) with built-in cron support for automated synchronization. The container runs continuously and executes sync jobs on your configured schedule.

## Quick Start

### 1. Prepare Directory Structure

```bash
calendar-engine/
├── config/                   # Private: configuration and credentials
│   ├── config.yaml           # Application configuration
│   ├── credentials.json      # Google API credentials (OAuth client)
│   ├── token_contacts.json   # Google Contacts token (auto-generated)
│   └── token_tasks.json      # Google Tasks token (auto-generated)
├── data/                     # Public: ICS calendar files
│   ├── contacts.ics          # Generated contacts calendar (auto-created)
│   └── tasks.ics             # Generated tasks calendar (auto-created)
├── logs/                     # Private: application logs
│   └── app.log               # Application log file
└── docker-compose.yml        # Docker Compose configuration
```

**Directory Security:**
- 🔒 **`config/`** - Keep private, contains credentials and tokens
- 🌐 **`data/`** - Safe to expose via web server (only ICS files)
- 🔒 **`logs/`** - Keep private, contains application logs

### 2. Configure Schedule

Configure sync frequency by editing environment variables in `docker-compose.yml`:

```yaml
environment:
  - CONTACTS_SCHEDULE=0 8 * * *      # Contacts: daily at 8:00 AM
  - TASKS_SCHEDULE=0 */6 * * *       # Tasks: every 6 hours
```

**Cron Format:** `minute hour day month weekday`

**Common Examples:**
- `0 8 * * *` - Daily at 8:00 AM
- `0 */6 * * *` - Every 6 hours (0:00, 6:00, 12:00, 18:00)
- `*/30 * * * *` - Every 30 minutes
- `0 8,20 * * *` - Daily at 8:00 AM and 8:00 PM
- `0 2 * * 0` - Weekly on Sunday at 2:00 AM

**Default Values (if not specified):**
- Contacts: `0 8 * * *` (daily at 8:00 AM)
- Tasks: `0 */6 * * *` (every 6 hours)

### 3. Deploy with Docker Compose

```bash
# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Check configured cron schedule
docker-compose exec calendar-engine cat /etc/cron.d/calendar-engine

# View sync logs
docker-compose exec calendar-engine tail -f /var/log/cron/contacts.log
docker-compose exec calendar-engine tail -f /var/log/cron/tasks.log

# Stop the container
docker-compose down
```

## Configuration Options

### Environment Variables

Configure schedules and behavior in `docker-compose.yml`:

```yaml
environment:
  # Timezone setting (use your local timezone)
  - TZ=UTC
  
  # Sync schedules (cron format: minute hour day month weekday)
  - CONTACTS_SCHEDULE=0 8 * * *      # Daily at 8:00 AM (default)
  - TASKS_SCHEDULE=0 */6 * * *       # Every 6 hours (default)
  
  # Initial sync on container start
  - SYNC_ON_START=true               # true (default) or false
```

**Available Variables:**

| Variable | Description | Default | Example |
### Volume Mounts

```yaml
volumes:
  # Configuration directory (private: credentials, tokens, config)
  - ./config:/config
  # Data directory (public: ICS calendar files)
  - ./data:/data
  # Logs directory (private: application logs)
  - ./logs:/logs
```
```yaml
volumes:
  # Configuration directory (private: credentials, tokens, config)
  - ./config:/config
  # Data directory (public: ICS calendar files)
  - ./data:/data
  # Logs directory (private: application logs)
  - ./logs:/logs
```

**Security Best Practices:**

1. **Keep `config/` directory private** - Contains sensitive credentials and tokens
2. **`config/` needs write access** - For token file creation during OAuth
3. **Expose ICS files carefully** - Use nginx location filtering or separate mount:

```yaml
# Option 1: Filter in nginx (recommended)
volumes:
  - ./data:/usr/share/nginx/html/calendar:ro

# Nginx config to only serve .ics files
location /calendar/ {
    location ~ \.ics$ { allow all; }
    location ~ . { deny all; }
}

# Or mount entire data directory (nginx filters to .ics only via location directive)
volumes:
  - ./data:/usr/share/nginx/html/calendar:ro
```

## Building from Source

### Using GitHub Actions (Recommended)

Push to your repository and GitHub Actions will automatically build and push the image to GitHub Container Registry:

```bash
git push origin main
```

Image will be available at: `ghcr.io/<username>/calendar-engine:latest`

Update `docker-compose.yml` to use your image:

```yaml
services:
  calendar-engine:
    image: ghcr.io/<username>/calendar-engine:latest
```

### Local Build

If you need to build locally on Windows:

```bash
# Build the image
docker build -t calendar-engine:latest .

# Or use docker-compose to build
docker-compose build
```

**Note:** GitHub Actions is recommended as it ensures consistent builds on Linux (x86_64) regardless of your local platform.

## One-Shot Execution

Run sync once without starting cron daemon:

```bash
# Sync all services once
docker-compose run --rm calendar-engine once

# Sync only contacts once
docker-compose run --rm calendar-engine once --only contacts

# Sync only tasks once
docker-compose run --rm calendar-engine once --only tasks
```

## First-Time OAuth Setup

On first run, you need to complete OAuth authorization:

```bash
# Run container in interactive mode
docker-compose run --rm calendar-engine once

# Follow the authorization URL in the output
# After authorization, token files will be saved to ./data/
```

Subsequent runs will use the saved tokens automatically.

## Monitoring

### Check Container Status

```bash
# Container status
docker-compose ps

# Resource usage
docker stats calendar-engine
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Specific service logs
docker-compose exec calendar-engine tail -f /var/log/cron/contacts.log
docker-compose exec calendar-engine tail -f /var/log/cron/tasks.log
docker-compose exec calendar-engine tail -f /var/log/cron/full-sync.log
```

### Health Check

```bash
# Manual health check - verify ICS files are generated
docker-compose exec calendar-engine ls -lh /data/*.ics

# Check all directories
docker-compose exec calendar-engine ls -lh /config/
docker-compose exec calendar-engine ls -lh /data/
```

## Troubleshooting

### Cron Not Running

```bash
# Check if cron daemon is running
docker-compose exec calendar-engine ps aux | grep cron

# Verify cron configuration
docker-compose exec calendar-engine cat /etc/cron.d/calendar-engine

# Check cron logs
docker-compose exec calendar-engine tail -f /var/log/cron/contacts.log
docker-compose exec calendar-engine tail -f /var/log/cron/tasks.log

# Restart container to regenerate cron config from environment variables
docker-compose restart
```

### Permission Issues

```bash
# Ensure proper permissions for directories
chmod -R 755 config data

# Config directory needs write access for token files
chmod 755 config
```

### Timezone Issues

Verify timezone is set correctly:

```bash
docker-compose exec calendar-engine date
docker-compose exec calendar-engine cat /etc/timezone
```

Update `TZ` environment variable in `docker-compose.yml` if needed.

### OAuth Token Expired

Delete token files and re-authenticate:

```bash
rm config/token_*.json
docker-compose run --rm calendar-engine once
```

## Advanced Configuration

### Modifying Sync Schedules

To change sync frequency:

```bash
# 1. Edit docker-compose.yml
vim docker-compose.yml

# Example: Change to hourly syncs
environment:
  - CONTACTS_SCHEDULE=0 * * * *    # Every hour
  - TASKS_SCHEDULE=0 * * * *       # Every hour

# 2. Restart container to apply new schedule
docker-compose up -d

# 3. Verify new schedule
docker-compose exec calendar-engine cat /etc/cron.d/calendar-engine
```

### Log Rotation

Add log rotation to prevent disk space issues:

```yaml
volumes:
  - ./logrotate.conf:/etc/logrotate.d/calendar-engine:ro
```

Create `logrotate.conf`:

```
/var/log/cron/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Production Deployment

### Using Pre-Built Image from GHCR

```yaml
services:
  calendar-engine:
    image: ghcr.io/finn-chan/calendar-engine:latest
    # ... rest of configuration
```

### Serving ICS Files via HTTP

**Method 1: Nginx with location filtering (Recommended)**

```yaml
services:
  calendar-engine:
    volumes:
      - ./config:/config
      - ./data:/data
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./data:/usr/share/nginx/html/calendar:ro
    ports:
      - "8080:80"
```

Nginx configuration for security (only serve .ics files):

```nginx
server {
    listen 80;
    server_name calendar.yourdomain.com;

    location /calendar/ {
        alias /usr/share/nginx/html/calendar/;
        autoindex off;
        
        # Only allow .ics files
        location ~ \.ics$ {
            add_header Access-Control-Allow-Origin *;
            add_header Cache-Control "no-cache, must-revalidate";
            types {
                text/calendar ics;
            }
        }
        
        # Deny all other files (including .log, .json)
        location ~ . {
            deny all;
            return 403;
        }
    }
}
```

**Method 2: Individual file mounts (Maximum security)**

```yaml
nginx:
  image: nginx:alpine
  volumes:
    # Only mount specific ICS files, not the whole data directory
    - ./data/contacts.ics:/usr/share/nginx/html/calendar/contacts.ics:ro
    - ./data/tasks.ics:/usr/share/nginx/html/calendar/tasks.ics:ro
  ports:
    - "8080:80"
```
      - "8080:80"
```

Access ICS files at: 
- `http://your-server:8080/calendar/contacts.ics`
- `http://your-server:8080/calendar/tasks.ics`

## Migration from Local Python

If migrating from local Python installation:

1. **Prepare directories:**
   ```bash
   mkdir -p calendar-engine/{config,data}
   ```

2. **Copy configuration files:**
   ```bash
   cp config/config.yaml calendar-engine/config/
   cp config/credentials.json calendar-engine/config/
   ```

3. **Copy token files** (if already authorized):
   ```bash
   # Tokens now go in config/ directory for better security
   cp data/token_*.json calendar-engine/config/
   ```

4. **Update config.yaml paths:**
   - Token files: `./data/token_*.json` → `/config/token_*.json`
   - ICS output: Keep as `/data/*.ics`
   - Log file: `/data/app.log` → `/logs/app.log`

5. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

**Directory Mapping:**
- Local `./config/` → Container `/config/` (credentials, tokens, config)
- Local `./data/` → Container `/data/` (ICS files, logs)

## Resources

- [Main README](../README.md)
- [Configuration Guide](README.md)
- [GitHub Container Registry](https://github.com/features/packages)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
