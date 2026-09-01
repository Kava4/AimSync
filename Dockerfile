# AimSync CS2 Makcu — recoil-only image for Raspberry Pi 4/5 (linux/arm64)
# Build on Pi:  docker compose build
# Cross-build:  docker buildx build --platform linux/arm64 -t aimsync-cs2-makcu .

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIMSYNC_DOCKER=1 \
    AIMSYNC_HEADLESS=1 \
    AIMSYNC_RECOIL_ONLY=1 \
    AIMSYNC_CONFIG_DIR=/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-pi.txt /app/requirements-pi.txt
RUN pip install --no-cache-dir -r /app/requirements-pi.txt

# App source (recoil sealed blobs + web UI)
COPY main.py /app/main.py
COPY app /app/app
COPY web /app/web

COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && mkdir -p /data

EXPOSE 5000
VOLUME ["/data"]

ENTRYPOINT ["/entrypoint.sh"]
