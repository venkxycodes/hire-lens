FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --upgrade pip \
    && pip install ".[dev]"

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000 8001

ENTRYPOINT ["docker/entrypoint.sh"]
