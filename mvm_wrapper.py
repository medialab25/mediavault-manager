#!/home/mortd/mediavault-manager/.venv/bin/python
import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app.cli import app

if __name__ == "__main__":
    app()
