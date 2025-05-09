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
curl http://localhost:8000/api/system/health
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

## Systemd Service Management

The application can be run as a systemd service for better process management and automatic startup. A management script is provided to handle all service operations.

### Installing the Service

1. Make the management script executable:
```bash
chmod +x manage_service.sh
```

2. Install and start the service:
```bash
sudo ./manage_service.sh install
```

### Managing the Service

The following commands are available for managing the service:

- Start the service:
```bash
sudo ./manage_service.sh start
```

- Stop the service:
```bash
sudo ./manage_service.sh stop
```

- Restart the service:
```bash
sudo ./manage_service.sh restart
```

- Check service status:
```bash
sudo ./manage_service.sh status
```

- View service logs:
```bash
sudo ./manage_service.sh logs
```

- Uninstall the service:
```bash
sudo ./manage_service.sh uninstall
```

The service will automatically:
- Start on system boot
- Restart if it crashes
- Log output to syslog
- Run with proper user permissions

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
