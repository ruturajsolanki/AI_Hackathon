# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only FIRST (much smaller - ~200MB vs 2GB+)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable for port (Railway provides this)
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Start command - use shell form to expand $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
