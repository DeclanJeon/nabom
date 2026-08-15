# NABOM backend (facade + engines) — python multi-process image
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 의존성 (Pillow, psycopg 빌드)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    "Pillow>=10" "psycopg[binary]>=3.1" "redis>=5"

COPY backend/ /app/backend/
WORKDIR /app/backend

EXPOSE 8001 8002 8080
CMD ["sh", "-c", "\
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --app-dir saju-engine & \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --app-dir iching-engine & \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir nabom-api \
"]
