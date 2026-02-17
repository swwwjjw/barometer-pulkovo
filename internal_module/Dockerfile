# Этап 1: Сборка фронтенда
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY internal_module/frontend/package*.json ./
RUN npm install

COPY internal_module/frontend/ .
RUN npm run build

# Этап 2: Сборка бэкенда
FROM python:3.10-slim

WORKDIR /app

COPY internal_requirements.txt .
RUN pip install --no-cache-dir -r internal_requirements.txt

COPY internal_module/ internal_module/

COPY final_folder/ final_folder/

COPY --from=frontend-builder /app/frontend/dist internal_module/frontend/dist

EXPOSE 8000

CMD ["uvicorn", "internal_module.internal_main:app", "--host", "0.0.0.0", "--port", "8000"]
