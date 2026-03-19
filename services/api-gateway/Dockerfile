# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install requirements to a temporary directory
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Final Runtime Image
FROM python:3.11-slim

# Security: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:/shared-libraries/python" \
    PORT=8000

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Create a non-privileged user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Copy shared libraries and service code
# (Assumes docker build is run from the monorepo root)
COPY --chown=appuser:appuser shared-libraries/ /shared-libraries/
COPY --chown=appuser:appuser services/api-gateway/app/ ./app/

# Switch to non-root user
USER appuser

# Expose the configured port
EXPOSE 8000

# Healthcheck to ensure the container is responsive
# Note: curl is not in slim images by default, usually we use a python script or wget if available
# For production, we'll keep it simple or use a python-based check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
