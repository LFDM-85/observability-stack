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

# Function to check directory for matching files (generic)
check_dir_with_files() {
    local dir="$1"
    local ext="$2"
    if [ -d "$dir" ] && ls "$dir"/*."$ext" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $dir/*.$ext"
        return 0
    else
        echo -e "${RED}✗${NC} $dir/*.$ext ${RED}(MISSING or EMPTY)${NC}"
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
check_dir_with_files "prometheus/alerts" "yml" || ((missing_count++))

# Loki
check_file "loki/loki-config.yml" || ((missing_count++))

# Tempo
check_file "tempo/tempo.yaml" || ((missing_count++))

# Alloy
check_file "alloy/config.alloy" || ((missing_count++))

# Grafana
check_file "grafana/provisioning/datasources/datasources.yml" || ((missing_count++))

# Alertmanager
check_file "alertmanager/alertmanager.yml" || ((missing_count++))

# Webhook Adapter
check_file "webhook-adapter/Dockerfile" || ((missing_count++))
check_file "webhook-adapter/teams-webhook-adapter.py" || ((missing_count++))

# --- DASHBOARD LOGIC UPDATE START ---
# Verificar se existem dashboards JSON (dinâmico)
if [ -d "grafana/dashboards" ] && ls grafana/dashboards/*.json >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Grafana Dashboards detected:"
    for db in grafana/dashboards/*.json; do
        echo -e "    - $(basename "$db")"
    done
else
    # Se a diretoria estiver vazia ou não existir, tentamos fazer download (se o script existir)
    echo -e "${YELLOW}⚠️  No dashboards found locally.${NC}"
    
    if command -v python3 &> /dev/null && [ -f "scripts/download_dashboard.py" ]; then
         echo -e "${BLUE}📥 Attempting to download dashboards...${NC}"
         python3 scripts/download_dashboard.py
         
         # Re-verificar após download
         if ls grafana/dashboards/*.json >/dev/null 2>&1; then
             echo -e "${GREEN}✓ Dashboards downloaded successfully.${NC}"
         else
             echo -e "${RED}✗ Failed to acquire dashboards.${NC}"
             ((missing_count++))
         fi
    else
        # Se não houver script de download e não houver ficheiros, é erro
        echo -e "${RED}✗ grafana/dashboards/*.json (MISSING)${NC}"
        ((missing_count++))
    fi
fi
# --- DASHBOARD LOGIC UPDATE END ---

check_file "hosts.txt" || ((missing_count++))
check_file "prometheus/targets.json" || ((missing_count++))

# Fix dashboards datasource variable
if [ -f "scripts/fix_dashboards.py" ]; then
    echo -e "${BLUE}🔧 Normalizing dashboard datasource UIDs...${NC}"
    # Verifica se há ficheiros json antes de correr o script para evitar erros
    if ls grafana/dashboards/*.json >/dev/null 2>&1; then
        python3 scripts/fix_dashboards.py
    fi
fi

echo ""

# If files are missing
if [ $missing_count -ne 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  ERROR: $missing_count file(s) missing!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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
DISCORD_WEBHOOK_URL=
TEAMS_WEBHOOK_URL=
EOF
    echo -e "${YELLOW}⚠️  .env file created.${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Check if Docker is running
echo -e "${BLUE}🐳 Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check docker-compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

# Check existing containers
running_containers=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
if [ $running_containers -gt 0 ]; then
    echo -e "${YELLOW}⚠️  There are $running_containers container(s) already running${NC}"
    echo -e "${BLUE}Do you want to stop and recreate them? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([sS]|[yY])$ ]]; then
        $DOCKER_COMPOSE down
    fi
fi

# Start stack
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
    echo -e "${GREEN}✨ Observability stack ready!${NC}"
    echo -e "${BLUE}📍 Grafana: http://localhost:3000${NC}"
fi