# Multi-stage: build React UI then serve with FastAPI
FROM node:20-slim AS ui-build
WORKDIR /ui
COPY ui/devpulseai-ui-main/package*.json ./
RUN npm ci --prefer-offline
COPY ui/devpulseai-ui-main/ ./
RUN npm run build

# Python backend
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

# Copy built UI from the first stage
COPY --from=ui-build /ui/dist /app/ui/devpulseai-ui-main/dist

EXPOSE 8080

# Use v3 server entry point (has WebSocket + all v3 endpoints)
CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
