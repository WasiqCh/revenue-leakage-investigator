# Minimal scaffold. TICKET-001 and TICKET-002 own the final version of this file.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir fastapi uvicorn

COPY . .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
