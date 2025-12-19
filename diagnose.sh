#!/bin/bash

# Observability stack diagnostic script
# Usage: ./diagnose.sh

echo "🔍 Observability Stack Diagnostic"
echo "================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect docker compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif docker compose version &> /dev/null; then
    DC="docker compose"
else
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Container Status:${NC}"
echo ""
$DC ps
echo ""

echo -e "${BLUE}🔍 Checking each service:${NC}"
echo ""

# Check Prometheus
echo -e "${YELLOW}[Prometheus]${NC}"
if docker ps | grep -q prometheus; then
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Prometheus is running and healthy${NC}"
    else
        echo -e "${RED}✗ Prometheus is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=20 prometheus
    fi
else
    echo -e "${RED}✗ Prometheus is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=20 prometheus
fi
echo ""

# Check Loki
echo -e "${YELLOW}[Loki]${NC}"
if docker ps | grep -q loki; then
    if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Loki is running and ready${NC}"
    else
        echo -e "${RED}✗ Loki is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=30 loki
    fi
else
    echo -e "${RED}✗ Loki is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=30 loki
fi
echo ""

# Check Alertmanager
echo -e "${YELLOW}[Alertmanager]${NC}"
if docker ps | grep -q alertmanager; then
    if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Alertmanager is running and healthy${NC}"
    else
        echo -e "${RED}✗ Alertmanager is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=30 alertmanager
    fi
else
    echo -e "${RED}✗ Alertmanager is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=30 alertmanager
fi
echo ""

# Check Alloy
echo -e "${YELLOW}[Alloy]${NC}"
if docker ps | grep -q alloy; then
    if curl -s http://localhost:12345/-/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Alloy is running${NC}"
    else
        echo -e "${RED}✗ Alloy is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=20 alloy
    fi
else
    echo -e "${RED}✗ Alloy is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=20 alloy
fi
echo ""

# Check Grafana
echo -e "${YELLOW}[Grafana]${NC}"
if docker ps | grep -q grafana; then
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Grafana is running${NC}"
    else
        echo -e "${RED}✗ Grafana is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=20 grafana
    fi
else
    echo -e "${RED}✗ Grafana is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=20 grafana
fi
echo ""

# Check Webhook Adapter
echo -e "${YELLOW}[Webhook Adapter]${NC}"
if docker ps | grep -q webhook-adapter; then
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Webhook Adapter is running${NC}"
    else
        echo -e "${RED}✗ Webhook Adapter is not responding${NC}"
        echo "Last log lines:"
        $DC logs --tail=20 webhook-adapter
    fi
else
    echo -e "${RED}✗ Webhook Adapter is not running${NC}"
    echo "Last log lines:"
    $DC logs --tail=20 webhook-adapter
fi
echo ""

echo -e "${BLUE}📊 Resource usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep observability || echo "No containers found"
echo ""

echo -e "${BLUE}💾 Volumes:${NC}"
docker volume ls | grep observability
echo ""

echo -e "${BLUE}🌐 Ports in use:${NC}"
echo "9090: Prometheus"
echo "3100: Loki"
echo "9093: Alertmanager"
echo "3000: Grafana"
echo "12345: Alloy"
echo "8080: Webhook Adapter"
echo ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 Useful debug commands:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "View logs in real-time:"
echo "  $DC logs -f loki"
echo "  $DC logs -f alertmanager"
echo ""
echo "Restart specific service:"
echo "  $DC restart loki"
echo "  $DC restart alertmanager"
echo ""
echo "Recreate specific service:"
echo "  $DC up -d --force-recreate loki"
echo "  $DC up -d --force-recreate alertmanager"
echo ""
echo "View applied configuration:"
echo "  $DC exec loki cat /etc/loki/local-config.yaml"
echo "  $DC exec alertmanager cat /etc/alertmanager/alertmanager.yml"
echo ""
