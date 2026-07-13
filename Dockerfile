FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.14-slim-bookworm AS python-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.14-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY --from=python-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
