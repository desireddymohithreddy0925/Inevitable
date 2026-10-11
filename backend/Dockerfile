FROM python:3.11-slim

WORKDIR /app

# Install git and other required system dependencies for repo inspection
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run uvicorn
EXPOSE 8000
CMD ["uvicorn", "inevitable.app:app", "--host", "0.0.0.0", "--port", "8000"]
