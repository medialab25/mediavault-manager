#!/bin/bash

# Enable error handling
set -e
set -o pipefail

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SCRIPT_DIR/service.log"
}

log "Starting service script"
log "Script directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    log "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    exit 1
fi

# Check if uvicorn exists
if [ ! -f "$SCRIPT_DIR/venv/bin/uvicorn" ]; then
    log "Error: uvicorn not found at $SCRIPT_DIR/venv/bin/uvicorn"
    exit 1
fi

# Activate virtual environment
log "Activating virtual environment"
source "$SCRIPT_DIR/venv/bin/activate"

# Set the working directory to the project root
log "Setting working directory to $SCRIPT_DIR"
cd "$SCRIPT_DIR"

# Run the FastAPI application using uvicorn with full path
log "Starting uvicorn server"
exec "$SCRIPT_DIR/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --workers 1 