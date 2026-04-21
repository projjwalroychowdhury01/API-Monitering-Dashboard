FROM python:3.11-slim as builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:/shared_libraries/python" \
    PORT=8000
WORKDIR /app
COPY --from=builder /install /usr/local
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
COPY --chown=appuser:appuser shared_libraries/python /shared_libraries/python
COPY --chown=appuser:appuser services/api-gateway/app/ ./app/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
