FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей Python
COPY external_requirements.txt ./
RUN pip install --no-cache-dir -r external_requirements.txt

# Копирование исходного файла
COPY external_main.py ./

# Создание директории для данных
RUN mkdir -p /app/data

CMD ["python3", "external_main.py"]

# Build command (run from external_module directory):
# docker build -t external_module:latest .

# Run command:
# docker run -d --name external_module \
#   -v /mnt/bi_sandbox/barometer_vacancies:/app/data \
#   external_module:latest