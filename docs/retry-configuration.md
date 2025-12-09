# API Retry and Resilience Configuration

This document explains the unified retry and resilience mechanism implemented in Calendar Engine to handle network issues and API failures.

## Overview

Calendar Engine implements a **unified retry mechanism** with two components:

1. **HTTP Timeout**: Prevents requests from hanging indefinitely
2. **Intelligent Exponential Backoff**: Automatically retries ALL failures with increasing wait times

## Configuration

All retry and timeout settings are configurable in `config/config.yaml`:

```yaml
google_api:
  retry:
    max_attempts: 5              # Maximum retry attempts
    max_wait_seconds: 60         # Maximum wait between retries
    min_wait_seconds: 4          # Initial wait between retries
    multiplier: 2                # Exponential backoff multiplier
  
  timeout:
    http_timeout_seconds: 120    # HTTP request timeout in seconds
```

## How It Works

### 1. HTTP Timeout

- **Purpose**: Prevents requests from hanging forever
- **Default**: 120 seconds (2 minutes)
- **Applied to**: All HTTP requests to Google APIs
- **Benefit**: Fails fast on network issues instead of blocking indefinitely

### 2. Unified Exponential Backoff Retry

- **Purpose**: Intelligently retries ALL failures with exponential wait strategy
- **Default**: 5 attempts with exponential backoff
- **Wait times**: 4s → 8s → 16s → 32s → 60s (capped at max)
- **Retries ALL error types**:
  - **Network errors**: `TimeoutError`, `ConnectionError`, `OSError`
  - **API errors**: `HttpError` (rate limits, server errors)
  - **All exceptions**: Any `Exception` raised during API calls
- **Benefit**: Single unified mechanism handles all failure scenarios

### Example Retry Sequence

If errors occur during synchronization:

```
06:00:00 - Initial request → TimeoutError
06:00:04 - Retry 1/5 (wait 4s) → HttpError 429 (rate limit)
06:00:12 - Retry 2/5 (wait 8s) → ConnectionError
06:00:28 - Retry 3/5 (wait 16s) → HttpError 500 (server error)
06:01:00 - Retry 4/5 (wait 32s) → Success! ✓
```

Total recovery time: ~60 seconds (much better than waiting until next cron)

## Best Practices

### Production Settings

For production environments with reliable networks:

```yaml
google_api:
  retry:
    max_attempts: 3              # Fewer retries for faster failures
    max_wait_seconds: 30         # Shorter max wait
    min_wait_seconds: 2          # Shorter initial wait
    multiplier: 2
  timeout:
    http_timeout_seconds: 90     # Shorter timeout
```

### Unreliable Network Settings

For environments with poor connectivity:

```yaml
google_api:
  retry:
    max_attempts: 8              # More retries
    max_wait_seconds: 120        # Longer max wait
    min_wait_seconds: 5          # Longer initial wait
    multiplier: 1.5              # Slower backoff growth
  timeout:
    http_timeout_seconds: 180    # Longer timeout (3 minutes)
```

### Testing/Development Settings

For faster feedback during development:

```yaml
google_api:
  retry:
    max_attempts: 2              # Quick failure
    max_wait_seconds: 10
    min_wait_seconds: 2
    multiplier: 2
  timeout:
    http_timeout_seconds: 30     # Fail fast
```

## Monitoring

Retry attempts are logged with detailed information:

```
2025-12-09 06:00:02 - app.contacts.client - INFO - Fetching contacts from Google People API
2025-12-09 06:00:32 - app.contacts.client - WARNING - Retry attempt 1/5 after error: timed out
2025-12-09 06:00:40 - app.contacts.client - INFO - Retrieved 150 total contacts
```

Monitor your logs for:
- **Frequent retries**: May indicate network issues or need for timeout adjustment
- **All retries exhausted**: May need to increase `max_attempts` or investigate root cause
- **No retries**: Good! Your network is stable

## Troubleshooting

### Still Getting Timeout Errors?

1. **Increase timeout**: 
   ```yaml
   timeout:
     http_timeout_seconds: 180  # Try 3 minutes
   ```

2. **Increase max attempts**:
   ```yaml
   retry:
     max_attempts: 8
   ```

3. **Check network**: Test connectivity to Google APIs
   ```bash
   docker exec calendar-engine ping -c 3 www.googleapis.com
   ```

### Retries Taking Too Long?

1. **Reduce max wait**:
   ```yaml
   retry:
     max_wait_seconds: 30  # Cap at 30 seconds
   ```

2. **Reduce max attempts**:
   ```yaml
   retry:
     max_attempts: 3  # Fail faster
   ```

### API Rate Limiting?

The unified retry mechanism handles rate limits automatically with exponential backoff. If you see rate limit errors:

1. **Increase retry attempts**:
   ```yaml
   retry:
     max_attempts: 8  # More attempts for rate limit recovery
   ```

2. **Spread out your schedules**:
   ```yaml
   CONTACTS_SCHEDULE: "0 6 * * *"   # 6 AM
   TASKS_SCHEDULE: "0 */6 * * *"    # Every 6 hours
   ```

3. **Reduce fetch frequency** if syncing very frequently

## Technical Details

### Dependencies

- **tenacity** (`>=8.2.0`): Provides unified retry logic with exponential backoff
- **httplib2**: Handles HTTP timeout configuration
- **google-api-python-client**: Google API client library

### Retry Scope

- **Retries applied at**: Top-level aggregation methods (`get_all_contacts`, `get_all_tasks`)
- **Not retried individually**: Low-level methods (`get_task_lists`, `get_tasks`)
- **Reason**: Avoids nested retries and retry count multiplication
- **Behavior**: If any sub-operation fails, the entire sync operation is retried

### Code Structure

- **Config** (`app/config.py`): Loads and exposes retry/timeout settings
- **Clients** (`app/contacts/client.py`, `app/tasks/client.py`): Implement retry logic
- **Sync** (`app/sync.py`): Passes configuration to clients

### Docker Considerations

The retry configuration is loaded from `config/config.yaml` at runtime, so:

- ✅ No need to rebuild Docker image when changing settings
- ✅ Can override via environment variables (future enhancement)
- ✅ Different settings per deployment environment

## Future Enhancements

Potential improvements for future versions:

1. **Environment Variable Override**: Allow runtime config via env vars
2. **Per-Service Settings**: Different retry settings for Contacts vs Tasks
3. **Circuit Breaker**: Temporarily stop retries if API is consistently down
4. **Retry Queue**: Persist failed jobs for later retry
5. **Health Check**: Pre-flight API connectivity check before sync
