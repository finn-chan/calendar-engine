#!/bin/bash
set -e

echo "=========================================="
echo "Calendar Engine - Starting"
echo "=========================================="
echo "Time: $(date)"
echo "Timezone: ${TZ:-UTC}"
echo "=========================================="

# Create log directory if not exists
mkdir -p /var/log/cron

# Set proper permissions for crontab file
if [ -f /etc/cron.d/calendar-engine ]; then
    echo "Installing crontab from /etc/cron.d/calendar-engine"
    chmod 0644 /etc/cron.d/calendar-engine
    # Apply environment variables to crontab if provided
    if [ -n "$CONTACTS_SCHEDULE" ] || [ -n "$TASKS_SCHEDULE" ]; then
        echo "Applying custom schedule from environment variables"
        cat > /etc/cron.d/calendar-engine << EOF
# Calendar Engine Cron Schedule (Generated from environment variables)

EOF
        if [ -n "$CONTACTS_SCHEDULE" ]; then
            echo "${CONTACTS_SCHEDULE} root cd /app && python -m app --only contacts >> /var/log/cron/contacts.log 2>&1" >> /etc/cron.d/calendar-engine
            echo "  Contacts schedule: ${CONTACTS_SCHEDULE}"
        fi
        
        if [ -n "$TASKS_SCHEDULE" ]; then
            echo "${TASKS_SCHEDULE} root cd /app && python -m app --only tasks >> /var/log/cron/tasks.log 2>&1" >> /etc/cron.d/calendar-engine
            echo "  Tasks schedule: ${TASKS_SCHEDULE}"
        fi
        
        # Add empty line at the end
        echo "" >> /etc/cron.d/calendar-engine
        chmod 0644 /etc/cron.d/calendar-engine
    fi
else
    echo "WARNING: No crontab file found at /etc/cron.d/calendar-engine"
    echo "Creating default crontab..."
    cat > /etc/cron.d/calendar-engine << 'EOF'
# Calendar Engine Default Cron Schedule
# Contacts: daily at 8:00 AM
0 8 * * * root cd /app && python -m app --only contacts >> /var/log/cron/contacts.log 2>&1
# Tasks: every 6 hours
0 */6 * * * root cd /app && python -m app --only tasks >> /var/log/cron/tasks.log 2>&1

EOF
    chmod 0644 /etc/cron.d/calendar-engine
fi

echo "=========================================="
echo "Crontab configuration:"
cat /etc/cron.d/calendar-engine
echo "=========================================="

# Check if running in one-shot mode
if [ "$1" = "once" ]; then
    echo "Running in one-shot mode (no cron daemon)"
    echo "Executing synchronization now..."
    cd /app && python -m app "${@:2}"
    echo "Synchronization completed at $(date)"
    exit 0
fi

# Run initial sync on container start
if [ "${SYNC_ON_START:-true}" != "false" ]; then
    echo "Running initial synchronization..."
    cd /app && python -m app || echo "Initial sync failed (this is normal on first run before OAuth)"
    echo "=========================================="
fi

# Start cron daemon
echo "Starting cron daemon..."
cron

# Keep container running and tail logs
echo "Container is ready. Tailing log files..."
echo "=========================================="

# Create log files if they don't exist
touch /var/log/cron/contacts.log /var/log/cron/tasks.log /var/log/cron/full-sync.log

# Tail all cron logs
tail -f /var/log/cron/*.log
