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

COPY internal_requirements.txt .
RUN pip install --no-cache-dir -r internal_requirements.txt

COPY . internal_module/

COPY --from=frontend-builder /app/frontend/dist internal_module/frontend/dist

EXPOSE 8000

CMD ["uvicorn", "internal_module.internal_main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker build -t internal_module:latest .

#docker run -d --name internal_module -v /mnt/allshare_fileserver/barometer_vacancies:/app/data -v vacancies_folder:/app/work internal_module:latest
