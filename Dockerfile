# ---- Stage 1: builder ----
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build deps for some Python wheels (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into a local vendor directory to copy into runtime
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install --no-cache-dir --target /app/vendor -r requirements.txt

# Copy application code and scripts
COPY app ./app
COPY student_private.pem student_public.pem instructor_public.pem ./
COPY scripts ./scripts
COPY cron/totp_cron /etc/cron.d/totp_cron

# ---- Stage 2: runtime ----
FROM python:3.11-slim AS runtime
LABEL maintainer="student"
ENV TZ=UTC
ENV DATA_DIR=/data
WORKDIR /srv/app

# Install runtime system deps (cron, tzdata); keep image small and clean caches
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    cron tzdata ca-certificates \
  && ln -snf /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone \
  && rm -rf /var/lib/apt/lists/*

# Create directories for persistent volumes and logs
RUN mkdir -p /data /cron /srv/app && chmod 0755 /data /cron

# Copy python packages installed in builder
COPY --from=builder /app/vendor /srv/app/vendor
ENV PYTHONPATH=/srv/app/vendor

# Copy app code, keys, scripts and cron config
COPY --from=builder /app/app ./app
COPY --from=builder /app/student_private.pem ./student_private.pem
COPY --from=builder /app/student_public.pem ./student_public.pem
COPY --from=builder /app/instructor_public.pem ./instructor_public.pem
COPY --from=builder /app/scripts ./scripts
# Cron file copied into /etc/cron.d to be picked up by cron
COPY --from=builder /etc/cron.d/totp_cron /etc/cron.d/totp_cron

# Ensure cron file has correct permissions
RUN chmod 0644 /etc/cron.d/totp_cron

# Strip any CRLF characters that may have been introduced on Windows hosts
# and make the runtime scripts executable. This prevents errors like:
# env: 'bash\r': No such file or directory when cron executes scripts.
# Make runtime scripts executable and strip CRLFs (ensure entrypoint cleaned too)
RUN sed -i 's/\r$//' /srv/app/scripts/* /etc/cron.d/totp_cron || true \
    && sed -i 's/\r$//' /srv/app/scripts/entrypoint.sh || true \
    && chmod +x ./scripts/run_cron.sh ./scripts/run_uvicorn.sh ./scripts/entrypoint.sh

# Expose API port
EXPOSE 8080

# Volumes (documented mount points)
VOLUME ["/data", "/cron"]

# Start cron (background) and then start uvicorn (foreground)
# The run script writes last_code to /cron/last_code.txt
CMD ["bash", "-lc", "./scripts/entrypoint.sh"]

# Docker healthcheck: ensure the HTTP API responds before container is considered healthy
# Use a Python-based healthcheck script (more portable than relying on curl)
COPY --from=builder /app/scripts/check_health.py ./scripts/check_health.py
RUN sed -i 's/\r$//' /srv/app/scripts/check_health.py || true \
    && chmod +x ./scripts/check_health.py
HEALTHCHECK --interval=5s --timeout=5s --start-period=30s --retries=6 \
  CMD python ./scripts/check_health.py || exit 1
