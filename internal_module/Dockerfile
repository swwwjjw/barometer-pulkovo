FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY internal_requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r internal_requirements.txt

COPY internal_main.py parser.py b1_data.json ./
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

RUN mkdir -p hh_data

EXPOSE 8083

CMD ["uvicorn", "internal_main:app", "--host", "0.0.0.0", "--port", "8083"]
