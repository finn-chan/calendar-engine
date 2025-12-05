FROM debian:12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Python and cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python/pip commands
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY setup.cfg .

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /config /data /var/log/cron

# Set environment variables
ENV CONFIG_PATH=/config/config.yaml
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Run the entrypoint script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["cron"]
