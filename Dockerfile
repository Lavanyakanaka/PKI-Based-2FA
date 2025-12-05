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

# Ensure cron file has correct permissions and LF line endings
RUN chmod 0644 /etc/cron.d/totp_cron

# Make run script executable
RUN chmod +x ./scripts/run_cron.sh

# Expose API port
EXPOSE 8080

# Volumes (documented mount points)
VOLUME ["/data", "/cron"]

# Start cron (background) and then start uvicorn (foreground)
# The run script writes last_code to /cron/last_code.txt
CMD ["bash", "-lc", "service cron start || cron || true; ./scripts/run_uvicorn.sh"]
