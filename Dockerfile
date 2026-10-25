FROM python:3.12-slim-bookworm

ARG TARGETARCH
ARG TOOLS_VERSION=100.10.0

# mongodump / mongorestore (MongoDB Database Tools)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && case "${TARGETARCH:-amd64}" in arm64) ARCH=arm64;; *) ARCH=x86_64;; esac \
    && curl -fsSL "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-${ARCH}-${TOOLS_VERSION}.deb" -o /tmp/tools.deb \
    && apt-get install -y /tmp/tools.deb \
    && rm /tmp/tools.deb && apt-get purge -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY templates templates
COPY scripts scripts

ENV BACKUP_DIR=/data/backups PORT=8000
RUN useradd -m appuser && mkdir -p /data/backups && chown -R appuser /data
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "gunicorn app.wsgi:app --bind 0.0.0.0:${PORT} --workers 2"]
