#!/bin/bash

# Automatic observability stack setup script
# Usage: ./setup.sh

set -e

echo "🚀 Starting observability stack setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check files
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 ${RED}(MISSING)${NC}"
        return 1
    fi
}

# Check mandatory files
echo -e "${BLUE}📄 Checking configuration files...${NC}"
echo ""

missing_count=0

# Root
check_file "docker-compose.yml" || ((missing_count++))

# Prometheus
check_file "prometheus/prometheus.yml" || ((missing_count++))
check_file "prometheus/alerts/alerts.yml" || ((missing_count++))

# Loki
check_file "loki/loki-config.yml" || ((missing_count++))

# Alloy
check_file "alloy/config.alloy" || ((missing_count++))

# Grafana
check_file "grafana/provisioning/datasources/datasources.yml" || ((missing_count++))

# Alertmanager
check_file "alertmanager/alertmanager.yml" || ((missing_count++))

# Webhook Adapter
check_file "webhook-adapter/Dockerfile" || ((missing_count++))
check_file "webhook-adapter/teams-webhook-adapter.py" || ((missing_count++))

# Automation Scripts & Configs
if [ ! -d "grafana/dashboards" ] || [ -z "$(ls -A grafana/dashboards)" ]; then
    echo -e "${BLUE}📥 Downloading Grafana dashboards...${NC}"
    # Use python if available, otherwise warn
    if command -v python3 &> /dev/null; then
        python3 scripts/download_dashboard.py
    elif command -v python &> /dev/null; then
        python scripts/download_dashboard.py
    else
        echo -e "${YELLOW}⚠️  Python not found. Skipping dashboard download.${NC}"
        ((missing_count++))
    fi
fi
check_file "grafana/dashboards/node_exporter_full.json" || ((missing_count++))
check_file "hosts.txt" || ((missing_count++))
check_file "prometheus/targets.json" || ((missing_count++))

# Fix dashboards datasource variable
if [ -f "scripts/fix_dashboards.py" ]; then
    echo -e "${BLUE}🔧 Normalizing dashboard datasource UIDs...${NC}"
    python3 scripts/fix_dashboards.py
fi

echo ""

# If files are missing
if [ $missing_count -ne 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  ERROR: $missing_count file(s) missing!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Please create the files listed above before continuing.${NC}"
    echo -e "${YELLOW}You can copy the content from the provided artifacts.${NC}"
    echo ""
    echo -e "${BLUE}💡 Hint: Expected directory structure:${NC}"
    echo "   observability-stack/"
    echo "   ├── docker-compose.yml"
    echo "   ├── prometheus/"
    echo "   │   ├── prometheus.yml"
    echo "   │   └── alerts/alerts.yml"
    echo "   ├── loki/loki-config.yml"
    echo "   ├── alloy/config.alloy"
    echo "   ├── grafana/provisioning/datasources/datasources.yml"
    echo "   ├── alertmanager/alertmanager.yml"
    echo "   └── webhook-adapter/"
    echo "       ├── Dockerfile"
    echo "       └── teams-webhook-adapter.py"
    echo "   ├── scripts/"
    echo "   │   ├── deploy_monitor.py"
    echo "   │   └── download_dashboard.py"
    echo "   ├── hosts.txt"
    echo "   └── prometheus/targets.json"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ All configuration files found!${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}🔧 Creating .env file...${NC}"
    cat > .env << 'EOF'
# Webhooks for alert notifications

# Discord Webhook URL
# How to get: Channel Settings > Integrations > Webhooks > New Webhook
DISCORD_WEBHOOK_URL=

# Microsoft Teams Webhook URL
# How to get: Channel > ... > Connectors > Incoming Webhook
TEAMS_WEBHOOK_URL=
EOF
    echo -e "${YELLOW}⚠️  .env file created.${NC}"
    echo -e "${YELLOW}    IMPORTANT: Configure webhooks before using alerts!${NC}"
    echo ""
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
    
    # Check if webhooks are configured
    if grep -q "DISCORD_WEBHOOK_URL=$" .env || grep -q "TEAMS_WEBHOOK_URL=$" .env; then
        echo -e "${YELLOW}⚠️  Webhooks not configured in .env file${NC}"
    else
        echo -e "${GREEN}✓ Webhooks configured in .env${NC}"
    fi
    echo ""
fi

# Check if Docker is running
echo -e "${BLUE}🐳 Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo -e "${YELLOW}Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if docker-compose is installed
echo -e "${BLUE}🔍 Checking docker-compose...${NC}"
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo -e "${GREEN}✓ docker-compose found${NC}"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo -e "${GREEN}✓ docker compose found${NC}"
else
    echo -e "${RED}✗ docker-compose not found${NC}"
    echo -e "${YELLOW}Please install docker-compose first.${NC}"
    exit 1
fi
echo ""

# Check if containers are already running
running_containers=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
if [ $running_containers -gt 0 ]; then
    echo -e "${YELLOW}⚠️  There are $running_containers container(s) already running${NC}"
    echo -e "${BLUE}Do you want to stop and recreate them? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([sS]|[yY])$ ]]; then
        echo -e "${BLUE}🛑 Stopping containers...${NC}"
        $DOCKER_COMPOSE down
        echo ""
    fi
fi

# Ask if user wants to start the stack
echo -e "${BLUE}🚀 Do you want to start the stack now? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([sS]|[yY])$ ]]; then
    echo ""
    echo -e "${BLUE}📦 Building images...${NC}"
    $DOCKER_COMPOSE build --no-cache webhook-adapter
    
    echo ""
    echo -e "${BLUE}🚀 Starting containers...${NC}"
    $DOCKER_COMPOSE up -d
    
    echo ""
    echo -e "${BLUE}📊 Waiting for services to become ready...${NC}"
    
    # Wait for services
    sleep 5
    
    # Check container status
    echo ""
    echo -e "${BLUE}📋 Container status:${NC}"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ Setup completed successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📍 Access URLs:${NC}"
    echo "   🎨 Grafana:       http://localhost:3000  (admin/admin)"
    echo "   📊 Prometheus:    http://localhost:9090"
    echo "   🔔 Alertmanager:  http://localhost:9093"
    echo "   📝 Loki:          http://localhost:3100"
    echo "   🤖 Alloy:         http://localhost:12345"
    echo "   🔗 Webhook:       http://localhost:8080/health"
    echo ""
    echo -e "${BLUE}📝 Useful commands:${NC}"
    echo "   View logs:        $DOCKER_COMPOSE logs -f"
    echo "   View logs (srv):  $DOCKER_COMPOSE logs -f <service>"
    echo "   View status:      $DOCKER_COMPOSE ps"
    echo "   Stop all:         $DOCKER_COMPOSE down"
    echo "   Restart:          $DOCKER_COMPOSE restart"
    echo "   Restart (srv):    $DOCKER_COMPOSE restart <service>"
    echo ""
    echo -e "${BLUE}🧪 Test alert:${NC}"
    echo "   curl -X POST http://localhost:9093/api/v2/alerts -H "Content-Type: application/json" -d '[{"labels":{"alertname":"TestAlert","severity":"warning","instance":"test-server"},"annotations":{"summary":"Discord Alert Test","description":"This is a test to verify if alerts are reaching Discord"},"startsAt":"2025-11-19T20:00:00.000Z"}]'"
    echo ""
    
    # Check webhooks
    if grep -q "DISCORD_WEBHOOK_URL=$" .env || grep -q "TEAMS_WEBHOOK_URL=$" .env; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}⚠️  WARNING: Webhooks not configured!${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}To receive alerts:${NC}"
        echo "   1. Edit the .env file"
        echo "   2. Configure DISCORD_WEBHOOK_URL and/or TEAMS_WEBHOOK_URL"
        echo "   3. Run: $DOCKER_COMPOSE restart webhook-adapter"
        echo ""
    fi
    
    echo -e "${GREEN}✨ Observability stack ready for use!${NC}"
    echo ""
    
else
    echo ""
    echo -e "${BLUE}ℹ️  Setup validated successfully!${NC}"
    echo ""
    echo -e "${BLUE}To start the stack manually, run:${NC}"
    echo "   $DOCKER_COMPOSE build"
    echo "   $DOCKER_COMPOSE up -d"
    echo ""
fi