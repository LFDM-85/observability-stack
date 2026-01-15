#!/bin/bash

# Script to install custom Grafana dashboards
# This will copy the dashboards to the correct location and restart Grafana

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
DASHBOARDS_DIR="$BASE_DIR/grafana/dashboards"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📊 Installing Custom Grafana Dashboards${NC}"
echo ""

# Create dashboards directory if it doesn't exist
mkdir -p "$DASHBOARDS_DIR"

# Array of dashboards to install
declare -A DASHBOARDS=(
    ["unified-infrastructure-dashboard.json"]="Infrastructure Overview - Unified view of all hosts, Docker containers, and MySQL databases"
    ["docker-containers-dashboard.json"]="Docker Containers - Detailed monitoring of Docker containers"
    ["mysql-monitoring-dashboard.json"]="MySQL Monitoring - Detailed MySQL/MariaDB database metrics"
)

echo -e "${BLUE}Found ${#DASHBOARDS[@]} dashboard(s) to install:${NC}"
echo ""

installed=0
skipped=0
failed=0

for dashboard in "${!DASHBOARDS[@]}"; do
    description="${DASHBOARDS[$dashboard]}"
    target_file="$DASHBOARDS_DIR/$dashboard"
    
    echo -e "${BLUE}➜ $dashboard${NC}"
    echo -e "  Description: $description"
    
    if [ -f "$target_file" ]; then
        echo -e "  ${YELLOW}⚠️  Already exists. Overwrite? (y/n)${NC} "
        read -r response
        if [[ ! "$response" =~ ^([yY])$ ]]; then
            echo -e "  ${YELLOW}⏭️  Skipped${NC}"
            ((skipped++))
            echo ""
            continue
        fi
    fi
    
    # Check if source file exists in current directory
    if [ -f "$BASE_DIR/$dashboard" ]; then
        cp "$BASE_DIR/$dashboard" "$target_file"
        echo -e "  ${GREEN}✅ Installed${NC}"
        ((installed++))
    elif [ -f "$SCRIPT_DIR/$dashboard" ]; then
        cp "$SCRIPT_DIR/$dashboard" "$target_file"
        echo -e "  ${GREEN}✅ Installed${NC}"
        ((installed++))
    else
        echo -e "  ${RED}❌ Source file not found${NC}"
        echo -e "  ${YELLOW}💡 Place $dashboard in $BASE_DIR or $SCRIPT_DIR${NC}"
        ((failed++))
    fi
    
    echo ""
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 Installation Summary:${NC}"
echo -e "  ✅ Installed: $installed"
echo -e "  ⏭️  Skipped:   $skipped"
if [ $failed -gt 0 ]; then
    echo -e "  ${RED}❌ Failed:    $failed${NC}"
fi
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $installed -gt 0 ]; then
    # Fix datasource UIDs in dashboards
    if [ -f "$SCRIPT_DIR/fix_dashboards.py" ]; then
        echo -e "${BLUE}🔧 Fixing datasource UIDs...${NC}"
        python3 "$SCRIPT_DIR/fix_dashboards.py"
        echo ""
    fi
    
    # Check if docker-compose is running
    if docker-compose -f "$BASE_DIR/docker-compose.yml" ps grafana 2>/dev/null | grep -q "Up"; then
        echo -e "${BLUE}🔄 Restarting Grafana to load new dashboards...${NC}"
        docker-compose -f "$BASE_DIR/docker-compose.yml" restart grafana
        
        echo ""
        echo -e "${GREEN}✨ Dashboards installed successfully!${NC}"
        echo ""
        echo -e "${BLUE}📍 Access Grafana at: http://localhost:3000${NC}"
        echo -e "   Username: admin"
        echo -e "   Password: admin"
        echo ""
        echo -e "${BLUE}🎨 Your new dashboards:${NC}"
        for dashboard in "${!DASHBOARDS[@]}"; do
            description="${DASHBOARDS[$dashboard]}"
            dashboard_name="${dashboard%.json}"
            echo -e "   • $description"
        done
        echo ""
        echo -e "${YELLOW}💡 TIP: Dashboards will be available in ~10 seconds after Grafana restarts${NC}"
    else
        echo -e "${YELLOW}⚠️  Grafana is not running${NC}"
        echo -e "   Start the stack with: docker-compose up -d"
        echo -e "   Then dashboards will be automatically loaded"
    fi
else
    echo -e "${YELLOW}ℹ️  No dashboards were installed${NC}"
fi

echo ""