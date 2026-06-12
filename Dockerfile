# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Keep Python output unbuffered and avoid .pyc files in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/MTDC

# Runtime packages for PostgreSQL access and health/debug commands.
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to maximize Docker layer cache reuse.
COPY requirements.txt /app/MTDC/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/MTDC/requirements.txt

# Copy project source after dependency install.
COPY . /app/MTDC/
RUN chmod +x /app/MTDC/docker-entrypoint.sh

# Django project root (contains manage.py).
WORKDIR /app/MTDC/MTDC

# Gunicorn listens on internal app port 8003.
EXPOSE 8003

ENTRYPOINT ["/app/MTDC/docker-entrypoint.sh"]
