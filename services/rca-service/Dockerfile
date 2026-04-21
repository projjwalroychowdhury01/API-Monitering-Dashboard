FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH="/app:/shared_libraries/python"

COPY services/rca-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/rca-service /app
COPY shared_libraries/python /shared_libraries/python

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
