# mediavault-manager

## Docker Instructions

### Building and Running with Docker

1. Build the Docker image:
```bash
docker build -t mediavault-manager .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 --name mediavault mediavault-manager
```

3. Test the health endpoint:
```bash
curl http://localhost:8000/system/health
```

### Container Management

To stop the container:
```bash
docker stop mediavault
```

To remove the container:
```bash
docker rm mediavault
```

The application will be available at `http://localhost:8000` when running.

## CLI Usage

The application provides a command-line interface for managing your media library. The CLI supports auto-completion for easier command usage.

### Installing Auto-completion

To enable command auto-completion, run one of the following commands based on your shell:

```bash
# For Bash
python -m app.cli --install-completion bash

# For Zsh
python -m app.cli --install-completion zsh

# For Fish
python -m app.cli --install-completion fish

# For PowerShell
python -m app.cli --install-completion powershell
```

After installation, restart your terminal for the changes to take effect.

### Using Auto-completion

Once installed, you can use TAB completion to:
- See all available commands
- Complete command names
- See available options for each command
- Complete option names

Example usage:
```bash
# List all commands
python -m app.cli [TAB]

# List all media commands
python -m app.cli media [TAB]

# See options for media search
python -m app.cli media search --[TAB]
```
