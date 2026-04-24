FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app:/shared-libraries/python"
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY services/websocket-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared-libraries/ /shared-libraries/
COPY services/websocket-service/app/ ./app/
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
