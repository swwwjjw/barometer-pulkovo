# Сборка фронтенда
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Сборка бэкенда
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей Python
COPY internal_requirements.txt ./
RUN pip install --no-cache-dir -r internal_requirements.txt

# Копирование исходников модуля
COPY __init__.py ./internal_module/__init__.py
COPY internal_main.py ./internal_module/internal_main.py
COPY parser.py ./internal_module/parser.py
COPY b1_data.json ./internal_module/b1_data.json

# Копирование собранного фронтенда
COPY --from=frontend-builder /app/frontend/dist ./internal_module/frontend/dist

# Создание директорий для данных
RUN mkdir -p /app/data /app/work

EXPOSE 8000

CMD ["uvicorn", "internal_module.internal_main:app", "--host", "0.0.0.0", "--port", "8000"]

# Build command (run from internal_module directory):
# docker build -t internal_module:latest .

# Run command:
# docker run -d --name internal_module \
#   -v /mnt/allshare_fileserver/barometer_vacancies:/app/data \
#   -v vacancies_folder:/app/work \
#   -p 8000:8000 \
#   internal_module:latest
