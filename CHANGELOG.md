# Changelog

All notable changes to Calendar Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
