FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (excluding old queue directory)
COPY src/api /app/src/api/
COPY src/database /app/src/database/
COPY src/message_queue /app/src/message_queue/
COPY src/redis /app/src/redis/
COPY src/utils /app/src/utils/
COPY src/__init__.py /app/src/
COPY src/config.py /app/src/
COPY src/main.py /app/src/

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path
ENV PYTHONPATH=/app

# Health check endpoint
EXPOSE 8000

CMD ["python", "src/main.py"]