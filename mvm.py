#!/usr/bin/env python3
import os
import sys
import subprocess

def find_venv_python():
    """Find the Python interpreter in the virtual environment"""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for .venv in the script directory
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    
    # Look for .venv in the parent directory
    parent_dir = os.path.dirname(script_dir)
    venv_python = os.path.join(parent_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    
    # Look for .venv in the current working directory
    cwd = os.getcwd()
    venv_python = os.path.join(cwd, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    
    return None

def find_project_dir():
    """Find the project directory by looking for the app directory"""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If we're in /usr/local/bin, we need to find the actual project directory
    if script_dir == "/usr/local/bin":
        # Look in the current working directory
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "app")):
            return cwd
        
        # Look in the parent directory of the virtual environment
        venv_python = find_venv_python()
        if venv_python:
            venv_dir = os.path.dirname(os.path.dirname(venv_python))
            if os.path.exists(os.path.join(venv_dir, "app")):
                return venv_dir
    
    # If we're not in /usr/local/bin, use the script directory
    return script_dir

def main():
    # Find the virtual environment's Python interpreter
    venv_python = find_venv_python()
    if not venv_python:
        print("Error: Virtual environment not found. Please run 'python -m venv .venv' and 'pip install -r requirements.txt'")
        sys.exit(1)
    
    # Get the project directory
    project_dir = find_project_dir()
    
    # Run the command with the virtual environment's Python
    try:
        # Set up the environment for the subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_dir}:{env.get('PYTHONPATH', '')}"
        
        # Run the command with the virtual environment's Python
        cmd = [venv_python, "-m", "app.cli"] + sys.argv[1:]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Only show package-related error for actual package errors
        if result.returncode != 0 and "ModuleNotFoundError" in result.stderr:
            print("Please make sure you have installed all required packages:")
            print("pip install -r requirements.txt")
        
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 