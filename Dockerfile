# Through Line: one container serves the API and the built website.
# Used by Render (render.yaml); also runs locally with:
#   docker build -t through-line . && docker run -p 8000:8000 --env-file .env through-line

# ---- 1. build the React frontend
FROM node:24-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 2. the Python app
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Open fonts with the same metrics as Calibri / Arial / Times, so PDF flyers look right on Linux.
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-crosextra-carlito fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ backend/
COPY scripts/operator_tools.py scripts/
COPY scripts/demo/ scripts/demo/
COPY --from=web /app/frontend/dist frontend/dist

# Data (database, sessions, logos, audit log) lives on the persistent disk mounted at /var/data; see render.yaml.
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
