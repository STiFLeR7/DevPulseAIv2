# Backend-only: UI is deployed separately on Vercel
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# v3 server entry point (WebSocket + all v3 endpoints)
CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
