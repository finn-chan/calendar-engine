# Technical Requirements

## System Requirements

- Python 3.8 or higher
- Internet connection for Google API access
- Web browser for OAuth authentication

## Python Dependencies

### Core Dependencies
- `google-api-python-client>=2.100.0` - Google API client
- `google-auth-httplib2>=0.1.1` - HTTP library for auth
- `google-auth-oauthlib>=1.1.0` - OAuth2 flow implementation
- `icalendar>=5.0.0` - ICS file generation
- `pytz>=2023.3` - Timezone support
- `PyYAML>=6.0` - Configuration file parsing

### Module-Specific
- `lunarcalendar>=3.0.0` - Lunar calendar conversion (Contacts only)

### Development Dependencies
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `flake8>=6.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Google API Setup

### Required APIs
1. **Google People API** (for Contacts)
   - Endpoint: `https://people.googleapis.com/`
   - Scope: `https://www.googleapis.com/auth/contacts.readonly`

2. **Google Tasks API** (for Tasks)
   - Endpoint: `https://tasks.googleapis.com/`
   - Scope: `https://www.googleapis.com/auth/tasks.readonly`

### API Quotas
- Standard Google API quotas apply
- OAuth2 token refresh handled automatically
- Rate limiting should not affect normal usage

## Docker Requirements

- Docker Engine 20.10+
- Docker Compose (optional, for orchestration)
- Sufficient disk space for volumes

## Installation

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Standards Compliance

- **iCalendar**: RFC5545 compliant
- **OAuth2**: RFC6749 compliant
- **Timezone**: IANA timezone database
- **Python**: PEP 8 style guide (with modifications per Google style)

## Platform Support

- **Linux**: Full support
- **macOS**: Full support
- **Windows**: Full support with PowerShell
- **Docker**: Cross-platform via containers
