#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_NAME="mediavault-manager"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root (use sudo)"
        exit 1
    fi
}

# Function to check if service file exists
check_service_file() {
    if [ ! -f "$SERVICE_FILE" ]; then
        echo "Service file not found at $SERVICE_FILE"
        echo "Please install the service first using: sudo $0 install"
        exit 1
    fi
}

# Function to install the service
install_service() {
    check_root
    
    # Set default user/group to 1000 if SUDO_USER is not set
    SERVICE_USER=${SUDO_USER:-1000}
    
    # Create service file
    cat > "$SERVICE_FILE" << EOL
[Unit]
Description=MediaVault Manager Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/run_service.sh
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

    # Make run_service.sh executable
    chmod +x "$SCRIPT_DIR/run_service.sh"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable and start the service
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    
    # Ensure the log directory exists with correct permissions
    log_dir="/var/log/mediavault-manager"
    mkdir -p "$log_dir"
    chown -R 1000:1000 "$log_dir"
    chmod 755 "$log_dir"

    echo "Service installed and started successfully"
}

# Function to uninstall the service
uninstall_service() {
    check_root
    check_service_file
    
    # Stop and disable the service
    systemctl stop "$SERVICE_NAME"
    systemctl disable "$SERVICE_NAME"
    
    # Remove the service file
    rm "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    echo "Service uninstalled successfully"
}

# Function to start the service
start_service() {
    check_root
    check_service_file
    systemctl start "$SERVICE_NAME"
    echo "Service started"
}

# Function to stop the service
stop_service() {
    check_root
    check_service_file
    systemctl stop "$SERVICE_NAME"
    echo "Service stopped"
}

# Function to restart the service
restart_service() {
    check_root
    check_service_file
    systemctl restart "$SERVICE_NAME"
    echo "Service restarted"
}

# Function to show service status
status_service() {
    check_root
    check_service_file
    systemctl status "$SERVICE_NAME"
}

# Function to show service logs
logs_service() {
    check_root
    check_service_file
    journalctl -u "$SERVICE_NAME" -f
}

# Main script logic
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    *)
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs}"
        exit 1
        ;;
esac

exit 0 