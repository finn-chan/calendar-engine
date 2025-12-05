# Calendar Engine Documentation

Welcome to the Calendar Engine documentation. This directory contains detailed guides and technical specifications.

## Documentation Index

### User Guides
- **[README.md](../README.md)**: Main project documentation with quick start guide
- **[contacts.md](contacts.md)**: Detailed guide for Google Contacts synchronization
- **[tasks.md](tasks.md)**: Detailed guide for Google Tasks synchronization
- **[requirements.md](requirements.md)**: Technical requirements and API specifications

### Configuration
- **[config/README.md](../config/README.md)**: Configuration file documentation
- **[config/config.sample.yaml](../config/config.sample.yaml)**: Annotated configuration template

### Development
- **[CHANGELOG.md](../CHANGELOG.md)**: Version history and release notes
- **[LICENSE](../LICENSE)**: Project license

## Quick Links

### Getting Started
1. [Google API Setup](requirements.md#google-api-setup)
2. [Configuration Guide](../config/README.md)
3. [Installation Options](../README.md#installation)
4. [Usage Examples](../README.md#usage)

### Feature Documentation
- [Contacts Features](contacts.md)
  - Birthday events (Gregorian and Lunar)
  - Anniversary events
  - Age calculation
  - Reminder configuration
- [Tasks Features](tasks.md)
  - Task status tracking
  - Recurring tasks
  - Overdue task handling
  - Parent-child relationships

### Advanced Topics
- [Docker Deployment](../README.md#docker-execution)
- [Calendar Subscription](../README.md#calendar-subscription)
- [Troubleshooting](../README.md#troubleshooting)
- [Contributing Guidelines](../README.md#contributing)

## Architecture Overview

Calendar Engine uses a modular architecture:

```
app/
├── common/          # Shared utilities (auth, config)
├── contacts/        # Google Contacts module
│   ├── client.py    # API client
│   └── converter.py # ICS converter
└── tasks/           # Google Tasks module
    ├── client.py    # API client
    ├── converter.py # ICS converter
    └── recurrence.py # Recurring task parser
```

### Design Principles
1. **Modularity**: Each Google service is a separate module
2. **Extensibility**: Easy to add new Google services
3. **Configuration-Driven**: All behavior controlled via config file
4. **Shared Components**: Common authentication and utilities
5. **Standards Compliance**: RFC5545-compliant ICS output

## Support

### Common Issues
- **Authentication Problems**: Check [Troubleshooting](../README.md#troubleshooting)
- **Missing Events**: Review [Configuration Guide](../config/README.md)
- **Docker Issues**: See [Docker Section](../README.md#docker-execution)

### Getting Help
- Check existing documentation first
- Review configuration samples
- Check log files for error messages
- Report issues with detailed context

## Contributing

We welcome contributions! Please:
1. Follow Google Python Style Guide
2. Add tests for new features
3. Update documentation
4. Submit pull requests with clear descriptions

See [Contributing Guidelines](../README.md#contributing) for details.
