FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python -m venv /opt/venv \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chmod +x /app/docker-entrypoint.sh

WORKDIR /app/MTDC

ENTRYPOINT ["/app/docker-entrypoint.sh"]
