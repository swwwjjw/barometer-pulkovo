# Этап 1: Сборка фронтенда
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

COPY internal_module/frontend/package*.json ./
RUN npm install

COPY internal_module/frontend/ .
RUN npm run build

# Этап 2: Среда выполнения
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бэкенда
COPY internal_module/ internal_module/

# Копирование папки с данными
COPY final_folder/ final_folder/

# Копирование собранного фронтенда из Этапа 1
COPY --from=frontend-builder /app/frontend/dist internal_module/frontend/dist

# Открытие порта
EXPOSE 8000

# Запуск приложения
# Мы используем синтаксис пути модуля. Поскольку мы находимся в /app, internal_module.internal_main должен быть разрешим.
CMD ["uvicorn", "internal_module.internal_main:app", "--host", "0.0.0.0", "--port", "8000"]
