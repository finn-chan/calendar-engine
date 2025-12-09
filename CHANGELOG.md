# Changelog

All notable changes to Calendar Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-09

### Added
- **Unified Retry Mechanism**: Intelligent error handling with exponential backoff
  - Added `tenacity` library for comprehensive retry logic
  - **Retries ALL errors**: Network timeouts, connection failures, API errors, rate limits
  - Exponential backoff strategy: 4s → 8s → 16s → 32s → 60s between retries
  - Configurable retry attempts, wait times, and backoff multiplier
- **Extended HTTP Timeout**: Increased default timeout to 120 seconds
  - Handles slow network conditions and large contact lists
  - Prevents premature timeout errors
- **Configurable Retry Settings**: New configuration options in `config.yaml`
  ```yaml
  google_api:
    retry:
      max_attempts: 5              # Maximum retry attempts (applies to all errors)
      max_wait_seconds: 60         # Maximum wait between retries
      min_wait_seconds: 4          # Initial wait between retries
      multiplier: 2                # Exponential backoff multiplier
    timeout:
      http_timeout_seconds: 120    # HTTP request timeout
  ```
- **Enhanced Logging**: Detailed retry attempt logging
  - Shows retry attempt number and total attempts
  - Logs the specific error that triggered the retry
  - Reports final success or failure after all retries

### Changed
- **API Client Architecture**: Refactored for unified resilience
  - Single retry mechanism handles all error types (no separate layers)
  - All timeout and retry parameters fully configurable
  - No hardcoded values or retry limits
  - Maintains backward compatibility with sensible defaults

### Fixed
- **Network Timeout Issues**: Resolved frequent `TimeoutError: timed out` failures
  - Previously failed immediately after single timeout
  - Now retries with exponential backoff for up to 5 attempts
  - Automatically recovers from temporary network issues
- **API Error Recovery**: Improved handling of transient API failures
  - Retries rate limit errors (429), server errors (500/503), and all exceptions
  - Exponential backoff prevents overwhelming the API during issues
- **Connection Stability**: Enhanced reliability for unstable networks
  - Retries all error types: `TimeoutError`, `ConnectionError`, `OSError`, `HttpError`
  - Better handling of intermittent connectivity issues

### Dependencies
- Added `tenacity>=8.2.0` for retry logic

## [1.1.1] - 2025-12-08

### Changed
- **Simplified Schedule Configuration**: Removed static crontab file requirement
  - Cron schedules are now **automatically generated from environment variables only**
  - Users only need to configure `CONTACTS_SCHEDULE` and `TASKS_SCHEDULE` in `docker-compose.yml`
  - No need to create or manage `crontab` file manually
  - Container regenerates crontab on every restart based on environment variables
- **Updated Documentation**: All docs now reflect environment-variable-only configuration
  - Removed references to manual crontab file creation
  - Simplified deployment instructions
  - Added clear examples of schedule configuration in docker-compose.yml

### Removed
- **Static crontab File**: Removed `crontab` file from repository
  - No longer needed as schedules are fully managed via environment variables
  - Eliminates confusion about which configuration takes precedence
- **Crontab Volume Mount**: Removed from `docker-compose.yml`
  - Cleaner configuration with fewer moving parts

### Fixed
- **Cron Schedule Application**: Fixed issue where environment variables weren't being applied
  - Container now always generates fresh crontab from `CONTACTS_SCHEDULE` and `TASKS_SCHEDULE`
  - Eliminates stale configuration from previous runs
  - Ensures user's schedule preferences are always respected

## [1.1.0] - 2025-12-07

### Added
- **Separated Log Directory**: Created dedicated `/logs` directory for application logs
  - Moved `app.log` from `/data` to `/logs` for better security
  - Added `logs/README.md` with logging documentation
  - Updated `.gitignore` to ignore `logs/*.log`
- **Enhanced Directory Structure**: Implemented three-directory separation
  - `/config` - Private: credentials, tokens, configuration files
  - `/data` - Public: ICS calendar files only (safe for HTTP exposure)
  - `/logs` - Private: application logs and debug information
- **Improved Documentation**: Updated all documentation to reflect new directory structure
  - Updated `README.md` project structure section
  - Updated `docs/docker-deployment.md` with security best practices
  - Updated `data/README.md` to clarify contents
  - Updated `QUICKSTART.md` with correct log paths
  - Fixed `config/README.md` token file paths

### Changed
- **Token File Location**: Moved OAuth tokens from `/data` to `/config` directory
  - Updated `config.sample.yaml`: token paths changed to `/config/token_*.json`
  - Better security isolation: tokens no longer in same directory as public ICS files
- **Logging Configuration**: Updated log file path in sample configuration
  - Changed from `/data/app.log` to `/logs/app.log`
- **Docker Configuration**: Enhanced Docker setup for better directory management
  - `Dockerfile`: Added `/logs` directory creation and `procps` package for monitoring
  - `docker-compose.yml`: Added `./logs:/logs` volume mount
  - `docker-entrypoint.sh`: Creates all necessary directories on startup
- **Default Behavior**: `SYNC_ON_START` now defaults to `true`
  - Container runs initial sync on startup by default
  - Can be disabled by setting `SYNC_ON_START=false`
- **Schedule Configuration**: Environment variables are now the recommended method
  - Simpler than managing separate crontab file
  - `CONTACTS_SCHEDULE` and `TASKS_SCHEDULE` in docker-compose.yml

### Fixed
- **Cron Configuration**: Added missing `CONFIG_PATH` environment variable to static `crontab` file
  - All cron jobs now explicitly set `CONFIG_PATH=/config/config.yaml`
  - Ensures configuration file is found during scheduled execution
  - Fixes issue where cron jobs would fail to locate config after initial run
- **Directory Creation**: Ensured all required directories are created on container startup
  - `docker-entrypoint.sh` now creates `/config`, `/data`, `/logs`, `/var/log/cron`
  - Prevents "directory not found" errors
- **Missing ps Command**: Added `procps` package to Dockerfile
  - Fixes "ps: command not found" error during cron verification
  - Prevents container restart loop
- **Cron Verification**: Made cron daemon check non-fatal
  - Container continues even if ps command unavailable
  - Logs warning instead of exiting on verification failure

### Security
- **Improved Security Model**: Clear separation of public and private files
  - Public exposure via HTTP: Only `/data` directory (ICS files)
  - Private storage: `/config` (credentials/tokens) and `/logs` (application logs)
  - Documented security best practices in deployment guide
- **Nginx Configuration Examples**: Added location filtering examples
  - Serve only `.ics` files from `/data` directory
  - Explicitly deny access to other file types

### Documentation
- Created comprehensive `logs/README.md` with:
  - Log viewing commands for Docker and local installations
  - Log rotation configuration examples
  - Security warnings about log content
- Updated deployment guide with:
  - Three-directory structure explanation
  - Security considerations for each directory
  - Nginx configuration for safe ICS file serving
  - Migration instructions with path updates

## [1.0.0] - 2025-12-05

### Added - Project Merger
- **Unified Architecture**: Merged google-contacts-calendar and google-tasks-calendar into single Calendar Engine project
- **Modular Design**: Separated codebase into `app/contacts/` and `app/tasks/` modules with shared `app/common/` utilities
- **Unified Configuration**: Single extensible YAML configuration file supporting multiple services
- **Command-Line Interface**: Added CLI with service selection (`--only contacts|tasks`)
- **Shared Authentication**: Extracted OAuth2 authentication to common module for reuse
- **Service Control**: Independent enable/disable flags for each service in configuration
- **Separate Token Files**: Each service uses its own token file for better isolation
- **Unified Entry Point**: Single `app/__main__.py` and `app/sync.py` for all services
- **Docker Support**: Single Dockerfile supporting both services

### Features - Google Contacts
- OAuth2 authentication with automatic token refresh
- Convert birthdays and anniversaries to RFC5545-compliant ICS format
- Support for Gregorian birthdays (with or without birth year)
- Support for Lunar calendar birthdays with automatic solar date conversion
- Support for custom anniversary events
- All-day event support with proper date formatting
- Automatic age calculation for events with known start years
- Contact nickname and phone number display in descriptions
- Configurable event type markers for custom events
- Customizable emoji for different event types (🎂 for birthdays, 💝 for anniversaries)
- Configurable reminder system with advance and same-day notifications
- Multi-year event generation (configurable past/future years)

### Features - Google Tasks
- OAuth2 authentication with automatic token refresh
- Convert tasks to RFC5545-compliant ICS format
- Support for both completed and incomplete tasks
- Support for tasks with and without due dates
- All-day event support (Google Tasks API limitation: dates only, no times)
- Smart task status visualization with emoji (✔️ completed, ⭕️ incomplete)
- Intelligent date handling for undated tasks
- Automatic today reminder events for overdue incomplete tasks
- Dual event strategy for overdue tasks (original date + today)
- Parse recurring task patterns from task title/notes
- Automatically generate multiple instances for recurring tasks
- Parent-child task relationship support
- Configurable reminder system with customizable notification times
- Task web link in event description

### Common Features
- Full timezone conversion support
- Customizable calendar metadata (name, language, region)
- Configurable empty lines between events for readability
- RFC5545-compliant ICS format
- Comprehensive logging with file and console output
- Docker containerization
- Unified project documentation
- Extensible architecture for future Google services

### Technical Details
- Python 3.8+ support
- Google API Python Client for API interactions
- iCalendar library for ICS generation
- PyYAML for configuration management
- pytz for timezone handling
- lunarcalendar for lunar date conversion (Contacts only)

### Migration Notes
This release merges two separate projects into a unified codebase:
- **From google-contacts-calendar**: All Contacts features from v1.1.0
- **From google-tasks-calendar**: All Tasks features from v1.2.0
- **Configuration**: Existing config files need migration to new unified format
- **Token Files**: Separate token files for each service (token_contacts.json, token_tasks.json)
- **Module Structure**: Code reorganized into modular structure
- **Import Paths**: Updated for new package structure

### Developer Notes
- Follows Google Python Style Guide
- Type hints throughout codebase
- Modular architecture for maintainability
- Shared authentication and common utilities
- Extensible design for adding more Google services

---

## Historical Releases (Pre-Merger)

### google-contacts-calendar v1.1.0 - 2025-12-02
- Added event reminder support with configurable times
- Split years configuration into years_past and years_future

### google-contacts-calendar v1.0.0 - 2025-11-19
- Initial release with birthday and anniversary support
- Gregorian and lunar calendar support
- Docker containerization

### google-tasks-calendar v1.2.0 - 2025-12-03
- Simplified reminder system
- Fixed timezone handling in reminders

### google-tasks-calendar v1.1.0 - 2025-11-18
- Smart status visualization with emoji
- Dual event strategy for overdue tasks
- Recurring task support
- Parent-child relationship support

### google-tasks-calendar v1.0.0 - 2025-11-12
- Initial release with Google Tasks API integration
- Basic task to ICS conversion
- Docker support

[Full historical changelogs available in original repositories]
