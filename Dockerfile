# Stage 1: Build Frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

COPY internal_module/frontend/package*.json ./
RUN npm install

COPY internal_module/frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY internal_module/ internal_module/

# Copy data folder
COPY final_folder/ final_folder/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist internal_module/frontend/dist

# Expose the port
EXPOSE 8000

# Run the application
# We use the module path syntax. Since we are in /app, internal_module.internal_main should be resolvable.
CMD ["uvicorn", "internal_module.internal_main:app", "--host", "0.0.0.0", "--port", "8000"]
