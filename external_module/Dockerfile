FROM python:3.10-slim

WORKDIR /app

COPY external_requirements.txt .

RUN pip install --no-cache-dir -r external_requirements.txt

COPY external_main.py .

CMD ["python3", "external_main.py"]