#!/bin/bash

# Script de diagnóstico da stack de observabilidade
# Uso: ./diagnose.sh

echo "🔍 Diagnóstico da Stack de Observabilidade"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detectar docker compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
elif docker compose version &> /dev/null; then
    DC="docker compose"
else
    echo -e "${RED}✗ Docker Compose não encontrado${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Status dos Containers:${NC}"
echo ""
$DC ps
echo ""

echo -e "${BLUE}🔍 Verificando cada serviço:${NC}"
echo ""

# Verificar Prometheus
echo -e "${YELLOW}[Prometheus]${NC}"
if docker ps | grep -q prometheus; then
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Prometheus está rodando e saudável${NC}"
    else
        echo -e "${RED}✗ Prometheus não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=20 prometheus
    fi
else
    echo -e "${RED}✗ Prometheus não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=20 prometheus
fi
echo ""

# Verificar Loki
echo -e "${YELLOW}[Loki]${NC}"
if docker ps | grep -q loki; then
    if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Loki está rodando e pronto${NC}"
    else
        echo -e "${RED}✗ Loki não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=30 loki
    fi
else
    echo -e "${RED}✗ Loki não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=30 loki
fi
echo ""

# Verificar Alertmanager
echo -e "${YELLOW}[Alertmanager]${NC}"
if docker ps | grep -q alertmanager; then
    if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Alertmanager está rodando e saudável${NC}"
    else
        echo -e "${RED}✗ Alertmanager não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=30 alertmanager
    fi
else
    echo -e "${RED}✗ Alertmanager não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=30 alertmanager
fi
echo ""

# Verificar Alloy
echo -e "${YELLOW}[Alloy]${NC}"
if docker ps | grep -q alloy; then
    if curl -s http://localhost:12345/-/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Alloy está rodando${NC}"
    else
        echo -e "${RED}✗ Alloy não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=20 alloy
    fi
else
    echo -e "${RED}✗ Alloy não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=20 alloy
fi
echo ""

# Verificar Grafana
echo -e "${YELLOW}[Grafana]${NC}"
if docker ps | grep -q grafana; then
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Grafana está rodando${NC}"
    else
        echo -e "${RED}✗ Grafana não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=20 grafana
    fi
else
    echo -e "${RED}✗ Grafana não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=20 grafana
fi
echo ""

# Verificar Webhook Adapter
echo -e "${YELLOW}[Webhook Adapter]${NC}"
if docker ps | grep -q webhook-adapter; then
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Webhook Adapter está rodando${NC}"
    else
        echo -e "${RED}✗ Webhook Adapter não responde${NC}"
        echo "Últimas linhas do log:"
        $DC logs --tail=20 webhook-adapter
    fi
else
    echo -e "${RED}✗ Webhook Adapter não está rodando${NC}"
    echo "Últimas linhas do log:"
    $DC logs --tail=20 webhook-adapter
fi
echo ""

echo -e "${BLUE}📊 Uso de recursos:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep observability || echo "Nenhum container encontrado"
echo ""

echo -e "${BLUE}💾 Volumes:${NC}"
docker volume ls | grep observability
echo ""

echo -e "${BLUE}🌐 Portas em uso:${NC}"
echo "9090: Prometheus"
echo "3100: Loki"
echo "9093: Alertmanager"
echo "3000: Grafana"
echo "12345: Alloy"
echo "8080: Webhook Adapter"
echo ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 Comandos úteis para debug:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Ver logs em tempo real:"
echo "  $DC logs -f loki"
echo "  $DC logs -f alertmanager"
echo ""
echo "Reiniciar serviço específico:"
echo "  $DC restart loki"
echo "  $DC restart alertmanager"
echo ""
echo "Recriar serviço específico:"
echo "  $DC up -d --force-recreate loki"
echo "  $DC up -d --force-recreate alertmanager"
echo ""
echo "Ver configuração aplicada:"
echo "  $DC exec loki cat /etc/loki/local-config.yaml"
echo "  $DC exec alertmanager cat /etc/alertmanager/alertmanager.yml"
echo ""