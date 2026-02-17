FROM python:3.10-slim

WORKDIR /app

COPY external_requirements.txt .

RUN pip install --no-cache-dir -r external_requirements.txt

COPY external_main.py .

CMD ["python3", "external_main.py"]

# docker build -t external_module:latest .

#docker run -d --name external_module -v /mnt/bi_sandbox/barometer_vacancies:app/data external_module:latest