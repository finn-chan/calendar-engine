# Logs Directory

This directory stores application log files.

## Files

### `app.log` (generated)

Application log file containing:
- Synchronization activities
- API requests and responses
- Error messages and warnings
- Debug information (if enabled)

**Log Level Configuration** (in `config/config.yaml`):
```yaml
logging:
  level: INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: /logs/app.log   # Log file path
```

## Viewing Logs

### Docker Compose
```bash
# Tail application logs
docker-compose exec calendar-engine tail -f /logs/app.log

# View cron job logs
docker-compose exec calendar-engine tail -f /var/log/cron/contacts.log
docker-compose exec calendar-engine tail -f /var/log/cron/tasks.log
```

### Local Installation
```bash
# Tail log file
tail -f logs/app.log

# View last 100 lines
tail -n 100 logs/app.log

# Search for errors
grep ERROR logs/app.log
```

## Log Rotation

For production deployments, consider implementing log rotation to prevent disk space issues:

### Using logrotate (Linux)

Create `/etc/logrotate.d/calendar-engine`:
```
/path/to/calendar-engine/logs/app.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```

### Docker Compose

Add log rotation configuration:
```yaml
volumes:
  - ./logs:/logs
  - ./logrotate.conf:/etc/logrotate.d/calendar-engine:ro
```

## Security

🔒 **Keep this directory private** - Log files may contain:
- API request details
- Configuration information
- Debug information

Do not expose this directory via web server.

## Cleanup

Manual cleanup example:
```bash
# Remove old logs
rm logs/app.log

# Or truncate the file
truncate -s 0 logs/app.log
```

Logs will be regenerated automatically on next run.
