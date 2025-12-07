#!/bin/bash
set -e

echo "=========================================="
echo "Calendar Engine - Starting"
echo "=========================================="
echo "Time: $(date)"
echo "Timezone: ${TZ:-UTC}"
echo "=========================================="

# Create necessary directories
mkdir -p /config /data /logs /var/log/cron

# Always generate fresh crontab from environment variables
echo "Configuring cron schedules from environment variables..."

# Use environment variables or fall back to defaults
CONTACTS_CRON="${CONTACTS_SCHEDULE:-0 8 * * *}"
TASKS_CRON="${TASKS_SCHEDULE:-0 */6 * * *}"

# Generate crontab file
cat > /etc/cron.d/calendar-engine << EOF
# Calendar Engine Cron Schedule (Auto-generated from Environment Variables)
# Contacts sync schedule: $CONTACTS_CRON
$CONTACTS_CRON root cd /app && CONFIG_PATH=/config/config.yaml python -m app --only contacts >> /var/log/cron/contacts.log 2>&1
# Tasks sync schedule: $TASKS_CRON
$TASKS_CRON root cd /app && CONFIG_PATH=/config/config.yaml python -m app --only tasks >> /var/log/cron/tasks.log 2>&1

EOF

# Set proper permissions
chmod 0644 /etc/cron.d/calendar-engine

echo "Crontab configured:"
echo "  Contacts: $CONTACTS_CRON"
echo "  Tasks: $TASKS_CRON"
echo "=========================================="
echo "Full crontab configuration:"
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

# Run initial sync on container start (default: true)
if [ "${SYNC_ON_START:-true}" = "true" ]; then
    echo "Running initial synchronization..."
    cd /app && python -m app || echo "Initial sync failed (this is normal on first run before OAuth)"
    echo "=========================================="
fi

# Start cron daemon
echo "Starting cron daemon..."
cron

# Verify cron is running (non-fatal check)
sleep 2
if command -v ps >/dev/null 2>&1; then
    if ps aux | grep -q '[c]ron'; then
        echo "Cron daemon started successfully"
    else
        echo "WARNING: Cron daemon may not be running"
    fi
else
    echo "WARNING: 'ps' command not available, skipping cron verification"
    echo "Assuming cron started successfully..."
fi

# Keep container running and tail logs
echo "Container is ready. Tailing log files..."
echo "=========================================="

# Create log files if they don't exist
touch /var/log/cron/contacts.log /var/log/cron/tasks.log /var/log/cron/full-sync.log

# Tail all cron logs
tail -f /var/log/cron/*.log
