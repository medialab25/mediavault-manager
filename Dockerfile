# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Set environment to production mode
# This ensures the application uses config.json as base
# and doesn't load development overrides from config.dev.json
ENV ENV=prod

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 