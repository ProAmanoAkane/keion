#!/bin/bash
set -euo pipefail

# --- Helper Functions ---
info() {
    echo "[INFO] $1"
}

warn() {
    echo "[WARN] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

# --- Dependency Installation ---
install_debian_deps() {
    info "Detected Debian/Ubuntu based system. Using apt."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg git docker.io docker-compose-plugin
}

install_fedora_deps() {
    info "Detected Fedora/CentOS/RHEL based system. Using dnf/yum."
    if check_command dnf; then
        PKG_MANAGER="dnf"
    elif check_command yum; then
        PKG_MANAGER="yum"
    else
        error "Could not find dnf or yum package manager."
    fi
    sudo "$PKG_MANAGER" check-update || true # Allow non-zero exit code if no updates
    sudo "$PKG_MANAGER" install -y curl git docker docker-compose-plugin

    # Add Docker repository if docker isn't found directly (common on CentOS/RHEL)
    if ! check_command docker; then
         info "Docker not found directly, attempting to install from Docker repository..."
         sudo "$PKG_MANAGER" install -y yum-utils
         sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
         sudo "$PKG_MANAGER" install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi
}

# --- Docker Setup ---
setup_docker() {
    info "Setting up Docker..."
    if ! check_command docker; then
        error "Docker installation failed or not found in PATH."
    fi

    # Check if docker service exists and start/enable it
    if systemctl list-unit-files | grep -q docker.service; then
        if ! systemctl is-active --quiet docker; then
            info "Starting Docker service..."
            sudo systemctl start docker
        fi
        if ! systemctl is-enabled --quiet docker; then
            info "Enabling Docker service to start on boot..."
            sudo systemctl enable docker
        fi
    else
        warn "Could not detect Docker systemd service. Please ensure Docker daemon is running."
    fi

    # Add user to docker group (optional but recommended)
    if ! groups "$(whoami)" | grep -q '\bdocker\b'; then
        warn "Your user '$(whoami)' is not in the 'docker' group."
        warn "You might need to run Docker commands with 'sudo' or add your user to the group:"
        warn "  sudo usermod -aG docker $(whoami)"
        warn "You will need to log out and log back in for the group change to take effect."
    fi
}

# --- Project Setup ---
start_project() {
    info "Starting Keion bot..."

    # Check for .env file
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            info "Copying .env.example to .env..."
            cp .env.example .env
            warn "Please edit the '.env' file and add your Discord token and other credentials."
            warn "Setup cannot complete without a valid token in .env."
            read -p "Press Enter after editing .env to continue..."
        else
            error ".env file not found and .env.example is missing. Cannot proceed."
        fi
    fi

    # Check if DISCORD_TOKEN is set (basic check)
    if ! grep -q "DISCORD_TOKEN=.*" .env || grep -q "DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN" .env; then
         warn "DISCORD_TOKEN in .env seems to be missing or using the default example value."
         warn "The bot might not start correctly."
         read -p "Press Enter to attempt starting anyway, or Ctrl+C to abort and edit .env..."
    fi

    # Build and run docker compose
    info "Building and starting Docker containers..."
    if check_command docker compose; then
        sudo docker compose up -d --build
    elif check_command docker-compose; then # Fallback for older docker-compose
        sudo docker-compose up -d --build
    else
        error "Neither 'docker compose' nor 'docker-compose' command found. Cannot start project."
    fi

    info "Keion bot should be starting up in the background."
    info "You can check the logs using: sudo docker compose logs -f"
}

# --- Main Script ---
main() {
    info "Starting Keion bootstrap process..."

    # Check for root privileges if installing packages
    if [ "$(id -u)" -ne 0 ]; then
        info "Requesting sudo privileges for package installation..."
        sudo -v # Ask for password upfront
        if [ $? -ne 0 ]; then
            error "Sudo privileges required for package installation."
        fi
    fi

    # Detect OS and install dependencies
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        case "$ID_LIKE" in
            *debian*) install_debian_deps ;;
            *fedora* | *rhel*) install_fedora_deps ;;
            *)
                case "$ID" in
                    debian | ubuntu) install_debian_deps ;;
                    fedora | centos | rhel) install_fedora_deps ;;
                    *) error "Unsupported Linux distribution: $ID. Please install git, docker, and docker-compose-plugin manually." ;;
                esac
                ;;
        esac
    elif [ -f /etc/debian_version ]; then
        install_debian_deps
    elif [ -f /etc/redhat-release ]; then
        install_fedora_deps
    else
        error "Cannot detect Linux distribution. Please install git, docker, and docker-compose-plugin manually."
    fi

    # Setup Docker
    setup_docker

    # Start the project
    start_project

    info "Bootstrap process completed successfully!"
}

# --- Run Main ---
main