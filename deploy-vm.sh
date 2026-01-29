#!/bin/bash

# wxmeow Weather Application - Linux VM Deployment Script
# This script deploys the wxmeow application to a Linux VM using Docker Compose
#
# Usage:
#   ./deploy-vm.sh [OPTIONS]
#
# Options:
#   --host HOST         Target host/IP address (required)
#   --user USER         SSH username (default: ubuntu)
#   --key PATH          Path to SSH private key
#   --port PORT         SSH port (default: 22)
#   --app-port PORT     Application port (default: 8000)
#   --domain DOMAIN     Domain name for reverse proxy setup
#   --ssl               Enable SSL/TLS with Let's Encrypt
#   --backup            Create backup before deployment
#   --rollback          Rollback to previous deployment
#   --health-check      Perform health check after deployment
#   --verbose           Enable verbose output
#   --dry-run           Show commands without executing
#   --help              Show this help message

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="wxmeow"
DEFAULT_USER="ubuntu"
DEFAULT_PORT="22"
DEFAULT_APP_PORT="8000"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
DOCKER_IMAGE="ghcr.io/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')/${PROJECT_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET_HOST=""
SSH_USER="${DEFAULT_USER}"
SSH_KEY=""
SSH_PORT="${DEFAULT_PORT}"
APP_PORT="${DEFAULT_APP_PORT}"
DOMAIN=""
ENABLE_SSL=false
CREATE_BACKUP=false
ROLLBACK=false
HEALTH_CHECK=true
VERBOSE=false
DRY_RUN=false

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}!  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

verbose() {
    if [[ "${VERBOSE}" == "true" ]]; then
        echo -e "${BLUE}🔧 $1${NC}"
    fi
}

show_help() {
    sed -n '3,25p' "${BASH_SOURCE[0]}" | sed 's/^# //'
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            TARGET_HOST="$2"
            shift 2
            ;;
        --user)
            SSH_USER="$2"
            shift 2
            ;;
        --key)
            SSH_KEY="$2"
            shift 2
            ;;
        --port)
            SSH_PORT="$2"
            shift 2
            ;;
        --app-port)
            APP_PORT="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --ssl)
            ENABLE_SSL=true
            shift
            ;;
        --backup)
            CREATE_BACKUP=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --health-check)
            HEALTH_CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validation
if [[ -z "${TARGET_HOST}" ]]; then
    error "Target host is required. Use --host HOST"
fi

if [[ -n "${SSH_KEY}" && ! -f "${SSH_KEY}" ]]; then
    error "SSH key file not found: ${SSH_KEY}"
fi

# SSH command builder
build_ssh_cmd() {
    local cmd="ssh"
    if [[ -n "${SSH_KEY}" ]]; then
        cmd="${cmd} -i ${SSH_KEY}"
    fi
    cmd="${cmd} -p ${SSH_PORT}"
    cmd="${cmd} -o StrictHostKeyChecking=no"
    cmd="${cmd} -o UserKnownHostsFile=/dev/null"
    cmd="${cmd} ${SSH_USER}@${TARGET_HOST}"
    echo "${cmd}"
}

# SCP command builder
build_scp_cmd() {
    local cmd="scp"
    if [[ -n "${SSH_KEY}" ]]; then
        cmd="${cmd} -i ${SSH_KEY}"
    fi
    cmd="${cmd} -P ${SSH_PORT}"
    cmd="${cmd} -o StrictHostKeyChecking=no"
    cmd="${cmd} -o UserKnownHostsFile=/dev/null"
    echo "${cmd}"
}

# Execute command (with dry-run support)
execute() {
    local cmd="$1"
    verbose "Executing: ${cmd}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "[DRY RUN] ${cmd}"
    else
        eval "${cmd}"
    fi
}

# Execute remote command
execute_remote() {
    local remote_cmd="$1"
    local ssh_cmd=$(build_ssh_cmd)
    execute "${ssh_cmd} '${remote_cmd}'"
}

# Copy file to remote
copy_to_remote() {
    local local_path="$1"
    local remote_path="$2"
    local scp_cmd=$(build_scp_cmd)
    execute "${scp_cmd} ${local_path} ${SSH_USER}@${TARGET_HOST}:${remote_path}"
}

# Check SSH connectivity
check_ssh_connectivity() {
    log "Checking SSH connectivity to ${TARGET_HOST}..."

    local ssh_cmd=$(build_ssh_cmd)
    if execute "${ssh_cmd} 'echo \"SSH connection successful\"'"; then
        success "SSH connectivity verified"
    else
        error "Failed to connect to ${TARGET_HOST}"
    fi
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."

    execute_remote "sudo apt-get update"
    execute_remote "sudo apt-get install -y docker.io docker-compose git curl wget unzip"
    execute_remote "sudo systemctl enable docker"
    execute_remote "sudo systemctl start docker"
    execute_remote "sudo usermod -aG docker ${SSH_USER}"

    success "System dependencies installed"
}

# Create backup
create_backup() {
    if [[ "${CREATE_BACKUP}" != "true" ]]; then
        return 0
    fi

    log "Creating backup of existing deployment..."

    local backup_dir="/opt/backups/${PROJECT_NAME}-$(date +%Y%m%d-%H%M%S)"

    execute_remote "sudo mkdir -p /opt/backups"
    execute_remote "if [ -d '${DEPLOY_DIR}' ]; then sudo cp -r ${DEPLOY_DIR} ${backup_dir}; fi"

    success "Backup created at ${backup_dir}"
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."

    execute_remote "sudo mkdir -p ${DEPLOY_DIR}"
    execute_remote "sudo chown ${SSH_USER}:${SSH_USER} ${DEPLOY_DIR}"

    success "Application directory created"
}

# Deploy application files
deploy_application() {
    log "Deploying application files..."

    # Copy docker-compose.yml
    copy_to_remote "${SCRIPT_DIR}/docker-compose.yml" "${DEPLOY_DIR}/docker-compose.yml"

    # Copy environment file if it exists
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        copy_to_remote "${SCRIPT_DIR}/.env" "${DEPLOY_DIR}/.env"
    fi

    # Create production docker-compose override
    local override_content="version: '3.8'
services:
  wxmeow:
    ports:
      - \"${APP_PORT}:5000\"
    environment:
      - FLASK_ENV=production"

    if [[ "${DRY_RUN}" != "true" ]]; then
        echo "${override_content}" | $(build_ssh_cmd) "cat > ${DEPLOY_DIR}/docker-compose.override.yml"
    fi

    success "Application files deployed"
}

# Setup reverse proxy (Nginx)
setup_reverse_proxy() {
    if [[ -z "${DOMAIN}" ]]; then
        verbose "No domain specified, skipping reverse proxy setup"
        return 0
    fi

    log "Setting up reverse proxy for ${DOMAIN}..."

    execute_remote "sudo apt-get install -y nginx"

    local nginx_config="server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://localhost:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}"

    if [[ "${DRY_RUN}" != "true" ]]; then
        echo "${nginx_config}" | $(build_ssh_cmd) "sudo tee /etc/nginx/sites-available/${PROJECT_NAME}"
        execute_remote "sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/"
        execute_remote "sudo nginx -t"
        execute_remote "sudo systemctl reload nginx"
    fi

    success "Reverse proxy configured"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    if [[ "${ENABLE_SSL}" != "true" || -z "${DOMAIN}" ]]; then
        verbose "SSL not requested or no domain specified"
        return 0
    fi

    log "Setting up SSL with Let's Encrypt..."

    execute_remote "sudo apt-get install -y certbot python3-certbot-nginx"
    execute_remote "sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN}"

    success "SSL certificate installed"
}

# Login to Docker registry
docker_login() {
    log "Logging in to Docker registry..."

    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        execute_remote "echo ${GITHUB_TOKEN} | docker login ghcr.io -u ${GITHUB_ACTOR:-$USER} --password-stdin"
        success "Docker registry login successful"
    else
        warning "GITHUB_TOKEN not set, assuming public image"
    fi
}

# Pull and start application
start_application() {
    log "Starting application..."

    execute_remote "cd ${DEPLOY_DIR} && docker-compose pull"
    execute_remote "cd ${DEPLOY_DIR} && docker-compose down || true"
    execute_remote "cd ${DEPLOY_DIR} && docker-compose up -d"

    # Wait for application to start
    sleep 30

    success "Application started"
}

# Health check
perform_health_check() {
    if [[ "${HEALTH_CHECK}" != "true" ]]; then
        return 0
    fi

    log "Performing health check..."

    local health_url="http://localhost:${APP_PORT}/"
    if [[ -n "${DOMAIN}" ]]; then
        health_url="http://${DOMAIN}/"
        if [[ "${ENABLE_SSL}" == "true" ]]; then
            health_url="https://${DOMAIN}/"
        fi
    fi

    execute_remote "curl -f ${health_url} || exit 1"

    success "Health check passed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."

    # Create simple monitoring script
    local monitor_script="#!/bin/bash
# Simple health check script for ${PROJECT_NAME}
curl -f http://localhost:${APP_PORT}/ > /dev/null 2>&1
if [ \$? -ne 0 ]; then
    echo \"$(date): ${PROJECT_NAME} health check failed\" >> /var/log/${PROJECT_NAME}-monitor.log
    # Restart the application
    cd ${DEPLOY_DIR} && docker-compose restart
fi"

    if [[ "${DRY_RUN}" != "true" ]]; then
        echo "${monitor_script}" | $(build_ssh_cmd) "sudo tee /usr/local/bin/${PROJECT_NAME}-monitor.sh"
        execute_remote "sudo chmod +x /usr/local/bin/${PROJECT_NAME}-monitor.sh"

        # Add cron job for monitoring (every 5 minutes)
        execute_remote "(crontab -l 2>/dev/null; echo '*/5 * * * * /usr/local/bin/${PROJECT_NAME}-monitor.sh') | crontab -"
    fi

    success "Basic monitoring configured"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."

    local logrotate_config="/var/log/${PROJECT_NAME}/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}"

    if [[ "${DRY_RUN}" != "true" ]]; then
        echo "${logrotate_config}" | $(build_ssh_cmd) "sudo tee /etc/logrotate.d/${PROJECT_NAME}"
    fi

    success "Log rotation configured"
}

# Rollback deployment
perform_rollback() {
    if [[ "${ROLLBACK}" != "true" ]]; then
        return 0
    fi

    log "Performing rollback..."

    # Find latest backup
    local latest_backup=$(execute_remote "ls -t /opt/backups/${PROJECT_NAME}-* 2>/dev/null | head -1" | tr -d '\n')

    if [[ -n "${latest_backup}" ]]; then
        execute_remote "sudo rm -rf ${DEPLOY_DIR}"
        execute_remote "sudo cp -r ${latest_backup} ${DEPLOY_DIR}"
        execute_remote "sudo chown -R ${SSH_USER}:${SSH_USER} ${DEPLOY_DIR}"
        execute_remote "cd ${DEPLOY_DIR} && docker-compose up -d"
        success "Rollback completed using backup: ${latest_backup}"
    else
        error "No backup found for rollback"
    fi
}

# Show deployment summary
show_summary() {
    log "Deployment Summary"
    echo "=================="
    echo "Target Host: ${TARGET_HOST}"
    echo "SSH User: ${SSH_USER}"
    echo "Application Port: ${APP_PORT}"
    if [[ -n "${DOMAIN}" ]]; then
        echo "Domain: ${DOMAIN}"
        if [[ "${ENABLE_SSL}" == "true" ]]; then
            echo "URL: https://${DOMAIN}"
        else
            echo "URL: http://${DOMAIN}"
        fi
    else
        echo "URL: http://${TARGET_HOST}:${APP_PORT}"
    fi
    echo "Deploy Directory: ${DEPLOY_DIR}"
    echo "=================="
}

# Main deployment function
main() {
    log "Starting deployment of ${PROJECT_NAME} to ${TARGET_HOST}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        warning "Running in DRY RUN mode - no changes will be made"
    fi

    # Pre-deployment checks
    check_ssh_connectivity

    if [[ "${ROLLBACK}" == "true" ]]; then
        perform_rollback
        show_summary
        return 0
    fi

    # Create backup if requested
    create_backup

    # System setup
    install_system_dependencies
    setup_app_directory

    # Application deployment
    deploy_application
    docker_login
    start_application

    # Infrastructure setup
    setup_reverse_proxy
    setup_ssl
    setup_monitoring
    setup_log_rotation

    # Post-deployment verification
    perform_health_check

    show_summary
    success "Deployment completed successfully!"
}

# Trap to handle script interruption
trap 'error "Deployment interrupted by user"' INT TERM

# Run main function
main "$@"
