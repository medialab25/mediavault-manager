#!/bin/bash

# Get the absolute path of the current directory
CURRENT_DIR=$(pwd)

# Get the path to the virtual environment's Python interpreter
VENV_PYTHON="$CURRENT_DIR/.venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PYTHON"
    echo "Please create a virtual environment first:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Check if requirements are installed
echo "Checking requirements..."
if ! "$VENV_PYTHON" -c "import typer, rich" 2>/dev/null; then
    echo "Installing requirements..."
    "$VENV_PYTHON" -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements"
        exit 1
    fi
    echo "Requirements installed successfully"
else
    echo "Requirements already installed"
fi

# Make the script executable
chmod +x mvm.py

# Create the symbolic link
echo "Creating symbolic link for mvm command..."
sudo ln -sf "$CURRENT_DIR/mvm.py" /usr/local/bin/mvm

echo "Setup complete! You can now use the 'mvm' command from anywhere."
echo "Try it out with: mvm --help" 