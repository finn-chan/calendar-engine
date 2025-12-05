FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY setup.cfg .

# Create necessary directories
RUN mkdir -p /config /data

# Set environment variables
ENV CONFIG_PATH=/config/config.yaml
ENV PYTHONUNBUFFERED=1

# Run the application
ENTRYPOINT ["python", "-m", "app"]
CMD []
