FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app:/shared_libraries/python"
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY services/metrics-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared_libraries/python /shared_libraries/python
COPY services/metrics-api/app/ ./app/
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
