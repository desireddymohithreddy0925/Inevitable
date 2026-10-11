FROM python:3.11-slim

WORKDIR /app

# Install git and other required system dependencies for repo inspection
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application files
COPY backend/ /app/
COPY . /app/

ENV PYTHONPATH=/app:/app/backend
EXPOSE 8000

# Use $PORT environment variable if assigned by Render/cloud providers, default to 8000
CMD ["sh", "-c", "uvicorn inevitable.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
