#!/bin/bash

# Portainer and Kubernetes Complete Setup Script
# Run with: sudo bash setup-portainer.sh

set -e

echo "======================================"
echo "Portainer & Kubernetes Setup Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Configuration
read -p "Enter your domain for Portainer (e.g., portainer.example.com) or press Enter to skip: " DOMAIN
read -p "Enter your email for SSL certificate (or press Enter to skip): " EMAIL

# Step 1: Install K3s if not installed
if ! command -v k3s &> /dev/null; then
    echo -e "${YELLOW}Installing K3s...${NC}"
    curl -sfL https://get.k3s.io | sh -
    sleep 10
    echo -e "${GREEN}K3s installed successfully${NC}"
else
    echo -e "${GREEN}K3s already installed${NC}"
fi

# Setup kubeconfig
mkdir -p ~/.kube
cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
export KUBECONFIG=~/.kube/config

# Step 2: Install Helm if not installed
if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}Installing Helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    echo -e "${GREEN}Helm installed successfully${NC}"
else
    echo -e "${GREEN}Helm already installed${NC}"
fi

# Step 3: Install Portainer
echo -e "${YELLOW}Installing Portainer...${NC}"

# Add Portainer Helm repo
helm repo add portainer https://portainer.github.io/k8s/
helm repo update

# Create namespace
kubectl create namespace portainer --dry-run=client -o yaml | kubectl apply -f -

# Install Portainer with NodePort
helm upgrade --install --create-namespace -n portainer portainer portainer/portainer \
  --set service.type=NodePort \
  --set service.nodePort=30777 \
  --set service.httpsNodePort=30779

echo -e "${GREEN}Portainer installed successfully${NC}"

# Wait for Portainer to be ready
echo -e "${YELLOW}Waiting for Portainer to be ready...${NC}"
kubectl wait --namespace portainer \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=portainer \
  --timeout=300s

# Step 4: Configure firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
ufw allow 30777/tcp comment 'Portainer HTTP'
ufw allow 30779/tcp comment 'Portainer HTTPS'
ufw allow 30776/tcp comment 'Portainer Edge'

# Step 5: Setup Nginx reverse proxy if domain provided
if [ ! -z "$DOMAIN" ]; then
    echo -e "${YELLOW}Setting up Nginx reverse proxy...${NC}"
    
    # Install Nginx and Certbot
    apt update
    apt install -y nginx certbot python3-certbot-nginx
    
    # Create Nginx config
    cat > /etc/nginx/sites-available/portainer << EOF
server {
    listen 80;
    server_name ${DOMAIN};
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    
    # SSL config will be added by certbot
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass https://localhost:30779;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/portainer /etc/nginx/sites-enabled/
    
    # Test Nginx config
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
    
    # Get SSL certificate if email provided
    if [ ! -z "$EMAIL" ]; then
        echo -e "${YELLOW}Obtaining SSL certificate...${NC}"
        certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos -m ${EMAIL}
        echo -e "${GREEN}SSL certificate obtained${NC}"
    else
        echo -e "${YELLOW}Skipping SSL certificate (no email provided)${NC}"
    fi
    
    # Open HTTP/HTTPS ports
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    
    echo -e "${GREEN}Nginx reverse proxy configured${NC}"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

# Print access information
echo ""
echo -e "${GREEN}======================================"
echo "Setup Complete!"
echo "======================================${NC}"
echo ""
echo "Portainer Access URLs:"
echo "----------------------"

if [ ! -z "$DOMAIN" ]; then
    echo -e "Primary: ${GREEN}https://${DOMAIN}${NC}"
fi

echo -e "Direct HTTPS: ${GREEN}https://${SERVER_IP}:30779${NC}"
echo -e "Direct HTTP:  ${GREEN}http://${SERVER_IP}:30777${NC}"
echo ""
echo "Initial Setup:"
echo "--------------"
echo "1. Open Portainer in your browser"
echo "2. Create admin user (first time only)"
echo "3. Select 'Kubernetes' environment"
echo "4. Start managing your cluster!"
echo ""
echo "Useful Commands:"
echo "----------------"
echo "Check Portainer status: kubectl get pods -n portainer"
echo "View Portainer logs:    kubectl logs -n portainer -l app.kubernetes.io/name=portainer"
echo "Restart Portainer:      kubectl rollout restart deployment/portainer -n portainer"
echo ""
echo -e "${YELLOW}Note: You may need to accept the self-signed certificate warning${NC}"
echo -e "${YELLOW}on first access if not using a domain with SSL.${NC}"
echo ""