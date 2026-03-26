FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/
COPY public/ ./public/
COPY config/ ./config/

ENV CONFIG_PATH=/app/config/config.yaml

EXPOSE 8002

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8002"]
