# Calendar Engine - Quick Start Guide

## Project Successfully Merged! 🎉

The `google-contacts-calendar` and `google-tasks-calendar` projects have been unified into `calendar-engine`.

## What's New

### Unified Structure
```
calendar-engine/
├── app/
│   ├── common/       # Shared authentication & utilities
│   ├── contacts/     # Google Contacts module
│   ├── tasks/        # Google Tasks module
│   ├── config.py     # Unified configuration
│   ├── sync.py       # Main synchronization logic
│   └── cli.py        # Command-line interface
├── config/
│   └── config.sample.yaml  # Unified configuration template
├── data/             # Output directory
├── docs/             # Comprehensive documentation
└── tests/            # Test suite
```

### Key Improvements
1. **Modular Architecture**: Separate modules for each Google service
2. **Extensible Configuration**: Single YAML file supporting multiple services
3. **Unified Authentication**: Shared OAuth2 implementation
4. **Service Control**: Enable/disable services independently
5. **CLI Interface**: Command-line options for flexible execution

## Getting Started

### 1. Setup Configuration

```bash
cd calendar-engine
cp config/config.sample.yaml config/config.yaml
```

Edit `config/config.yaml`:
- Place `credentials.json` in `config/` directory
- Adjust timezone and other settings as needed
- Enable/disable services via `enabled` flags

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Synchronization

```bash
# Sync all enabled services
python -m app

# Sync only contacts
python -m app --only contacts

# Sync only tasks
python -m app --only tasks
```

### 4. First Run Authentication

On first run, a browser will open for OAuth2 authentication:
- Authorize the application
- Token files will be created automatically:
  - `data/token_contacts.json` (for Contacts)
  - `data/token_tasks.json` (for Tasks)

### 5. Check Output

Generated ICS files:
- `data/contacts.ics` - Birthday and anniversary events
- `data/tasks.ics` - Task events

## Docker Usage

### Build Image

```bash
docker build -t calendar-engine .
```

### First Run (Interactive for Auth)

```bash
docker run -it --rm \
  -v ${PWD}/config:/config \
  -v ${PWD}/data:/data \
  calendar-engine
```

### Subsequent Runs

```bash
docker run --rm \
  -v ${PWD}/config:/config \
  -v ${PWD}/data:/data \
  calendar-engine
```

## Migration Notes

### From google-contacts-calendar

**Configuration Changes:**
```yaml
# Old:
google_api:
  token_file: /data/token.json

# New:
google_api:
  contacts:
    token_file: /data/token_contacts.json
```

**Token File:**
- Rename `token.json` → `token_contacts.json`
- Or delete and re-authenticate

### From google-tasks-calendar

**Configuration Changes:**
```yaml
# Old:
google_api:
  token_file: /data/token.json

# New:
google_api:
  tasks:
    token_file: /data/token_tasks.json
```

**Token File:**
- Rename `token.json` → `token_tasks.json`
- Or delete and re-authenticate

## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=app

# Specific module
pytest tests/test_config.py -v
```

## Documentation

- **README.md**: Complete feature documentation
- **docs/contacts.md**: Contacts synchronization guide
- **docs/tasks.md**: Tasks synchronization guide
- **docs/requirements.md**: Technical requirements
- **CHANGELOG.md**: Version history

## Troubleshooting

### Configuration Issues

Check config file syntax:
```bash
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

### Authentication Issues

Delete token files and re-authenticate:
```bash
rm data/token_*.json
python -m app
```

### Import Errors

Ensure you're in the project root:
```bash
cd calendar-engine
python -m app
```

## Next Steps

1. **Configure Services**: Edit `config/config.yaml` to enable desired services
2. **Set Up Calendars**: Subscribe to generated ICS files in your calendar app
3. **Schedule Sync**: Set up cron job or scheduled task for automatic updates
4. **Customize**: Adjust emoji, reminders, and other settings

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Check logs in `data/app.log`
- **Configuration**: Review `config/config.sample.yaml`

## Contributing

Follow Google Python Style Guide:
- Type hints for all functions
- Docstrings in Google format
- Code formatting with `black`
- Import sorting with `isort`

---

**Project Status**: ✅ Ready for use

**Version**: 1.0.0

**License**: MIT
