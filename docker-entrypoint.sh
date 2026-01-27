#!/bin/bash
set -e

echo "=========================================="
echo "Calendar Engine - Starting"
echo "=========================================="
echo "Time: $(date)"
echo "Timezone: ${TZ:-UTC}"
echo "=========================================="

# Set timezone from environment variable
if [ -n "$TZ" ]; then
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo $TZ > /etc/timezone
    echo "Timezone set to: $TZ"
fi

# Create necessary directories
mkdir -p /config /data /logs /var/log/cron

# Always generate fresh crontab from environment variables
echo "Configuring cron schedules from environment variables..."

# Use environment variables or fall back to defaults
CONTACTS_CRON="${CONTACTS_SCHEDULE:-0 8 * * *}"
TASKS_CRON="${TASKS_SCHEDULE:-0 */6 * * *}"

# Generate crontab file
cat > /etc/crontabs/root << EOF
# Calendar Engine Cron Schedule (Auto-generated from Environment Variables)
# Contacts sync schedule: $CONTACTS_CRON
$CONTACTS_CRON cd /app && CONFIG_PATH=/config/config.yaml python -m app --only contacts >> /var/log/cron/contacts.log 2>&1
# Tasks sync schedule: $TASKS_CRON
$TASKS_CRON cd /app && CONFIG_PATH=/config/config.yaml python -m app --only tasks >> /var/log/cron/tasks.log 2>&1

EOF

# Set proper permissions
chmod 0600 /etc/crontabs/root

echo "Crontab configured:"
echo "  Contacts: $CONTACTS_CRON"
echo "  Tasks: $TASKS_CRON"
echo "=========================================="
echo "Full crontab configuration:"
cat /etc/crontabs/root
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
if [ "${SYNC_ON_START:-true}" = "true" ]; then
    echo "Running initial synchronization..."
    cd /app && python -m app || echo "Initial sync failed (this is normal on first run before OAuth)"
    echo "=========================================="
fi

# Start cron daemon
echo "Starting cron daemon..."
crond -f -l 2 &

# Verify cron is running
sleep 2
if pgrep crond >/dev/null 2>&1 || pgrep cron >/dev/null 2>&1; then
    echo "Cron daemon started successfully"
else
    echo "WARNING: Cron daemon may not be running"
fi

# Keep container running
echo "Container is ready."
echo "=========================================="

# Create log files
touch /var/log/cron/contacts.log /var/log/cron/tasks.log /var/log/cron/full-sync.log

# Keep container alive
sleep infinity
