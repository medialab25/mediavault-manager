#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Set the working directory to the project root
cd "$SCRIPT_DIR"

# Run the FastAPI application using uvicorn with full path
exec "$SCRIPT_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --workers 1 