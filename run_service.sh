#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Set the working directory to the project root
cd "$(dirname "$0")"

# Run the FastAPI application using uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 