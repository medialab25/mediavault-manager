#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start the FastAPI server
uvicorn app.main:app --reload 