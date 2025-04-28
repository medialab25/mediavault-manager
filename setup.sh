#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create media directory
mkdir -p media

echo "Setup complete! To activate the virtual environment, run:"
echo "source venv/bin/activate" 