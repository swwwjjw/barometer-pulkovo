FROM python:3.10-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Create the output directory for vacancy data
RUN mkdir -p /mnt/bi_sandbox/barometer_vacancies

# Copy the external module code
COPY external_main.py .

# Run the application
CMD ["python", "external_main.py"]
