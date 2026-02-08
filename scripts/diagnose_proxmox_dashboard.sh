#!/bin/bash
# Script de Diagnóstico - Proxmox Cluster Dashboard
# Verifica porque o dashboard não está a receber dados

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROXMOX_HOST="192.168.90.104"
PROXMOX_EXPORTER_PORT="9221"

echo -e "${BLUE}=========================================="
echo "  Diagnóstico - Proxmox Dashboard"
echo "==========================================${NC}"
echo ""

# 1. Verificar conectividade ao Proxmox
echo -e "${BLUE}1. Testando conectividade ao Proxmox host...${NC}"
if ping -c 2 $PROXMOX_HOST > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ping OK${NC}"
else
    echo -e "${RED}❌ Não consegue fazer ping ao Proxmox host${NC}"
    echo "   Verificar firewall OPNsense"
    exit 1
fi

# 2. Verificar se Proxmox Exporter está a responder
echo ""
echo -e "${BLUE}2. Verificando Proxmox VE Exporter...${NC}"
if timeout 3 curl -s http://$PROXMOX_HOST:$PROXMOX_EXPORTER_PORT/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Proxmox Exporter está a responder${NC}"
    
    # Verificar se tem métricas
    METRICS_COUNT=$(curl -s http://$PROXMOX_HOST:$PROXMOX_EXPORTER_PORT/metrics | grep -c "^pve_" || true)
    echo "   Métricas encontradas: $METRICS_COUNT"
    
    if [ "$METRICS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Exporter tem métricas${NC}"
    else
        echo -e "${YELLOW}⚠️  Exporter não tem métricas pve_*${NC}"
        echo "   Verificar configuração do token API"
    fi
else
    echo -e "${RED}❌ Proxmox Exporter NÃO está a responder${NC}"
    echo ""
    echo "Possíveis causas:"
    echo "  1. Exporter não está instalado"
    echo "  2. Serviço não está a correr"
    echo "  3. Firewall bloqueando porta $PROXMOX_EXPORTER_PORT"
    echo ""
    echo "Para instalar:"
    echo "  ./scripts/install_proxmox_exporter.sh $PROXMOX_HOST"
    exit 1
fi

# 3. Verificar se Prometheus está a fazer scrape
echo ""
echo -e "${BLUE}3. Verificando Prometheus targets...${NC}"

# Verificar se Prometheus está acessível
if ! curl -s http://localhost:9990/-/healthy > /dev/null 2>&1; then
    echo -e "${RED}❌ Prometheus não está acessível${NC}"
    echo "   Verificar se container está a correr: docker compose ps prometheus"
    exit 1
fi

# Verificar target do Proxmox
PROXMOX_TARGET_STATUS=$(curl -s http://localhost:9990/api/v1/targets | \
    jq -r '.data.activeTargets[] | select(.labels.job=="proxmox") | .health' 2>/dev/null || echo "unknown")

if [ "$PROXMOX_TARGET_STATUS" = "up" ]; then
    echo -e "${GREEN}✅ Prometheus está a fazer scrape do Proxmox${NC}"
elif [ "$PROXMOX_TARGET_STATUS" = "down" ]; then
    echo -e "${RED}❌ Target Proxmox está DOWN no Prometheus${NC}"
    
    # Mostrar erro
    ERROR_MSG=$(curl -s http://localhost:9990/api/v1/targets | \
        jq -r '.data.activeTargets[] | select(.labels.job=="proxmox") | .lastError' 2>/dev/null || echo "unknown")
    echo "   Erro: $ERROR_MSG"
else
    echo -e "${YELLOW}⚠️  Target Proxmox não encontrado no Prometheus${NC}"
    echo "   Verificar prometheus/prometheus.yml"
fi

# 4. Testar query de métricas
echo ""
echo -e "${BLUE}4. Testando queries do dashboard...${NC}"

# Query básica do Proxmox
QUERY="pve_up"
RESULT=$(curl -s "http://localhost:9990/api/v1/query?query=$QUERY" | jq -r '.data.result | length' 2>/dev/null || echo "0")

if [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ Query 'pve_up' retorna dados ($RESULT resultados)${NC}"
else
    echo -e "${RED}❌ Query 'pve_up' não retorna dados${NC}"
    echo "   Dashboard não terá dados"
fi

# 5. Verificar configuração do Prometheus
echo ""
echo -e "${BLUE}5. Verificando configuração do Prometheus...${NC}"

if grep -q "job_name: 'proxmox'" prometheus/prometheus.yml 2>/dev/null; then
    echo -e "${GREEN}✅ Job 'proxmox' configurado${NC}"
    
    # Mostrar configuração
    echo ""
    echo "Configuração atual:"
    grep -A 10 "job_name: 'proxmox'" prometheus/prometheus.yml | head -15
else
    echo -e "${RED}❌ Job 'proxmox' NÃO encontrado em prometheus.yml${NC}"
fi

# Resumo
echo ""
echo -e "${BLUE}=========================================="
echo "  Resumo do Diagnóstico"
echo "==========================================${NC}"
echo ""

if [ "$PROXMOX_TARGET_STATUS" = "up" ] && [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✅ Tudo OK - Dashboard deveria ter dados${NC}"
    echo ""
    echo "Se ainda não vês dados:"
    echo "  1. Aguardar 1-2 minutos para Prometheus coletar"
    echo "  2. Refrescar dashboard no Grafana"
    echo "  3. Verificar time range no Grafana (últimas 6h)"
else
    echo -e "${RED}❌ Problemas encontrados${NC}"
    echo ""
    echo "Próximos passos:"
    
    if timeout 3 curl -s http://$PROXMOX_HOST:$PROXMOX_EXPORTER_PORT/metrics > /dev/null 2>&1; then
        echo "  1. Verificar configuração do Prometheus"
        echo "  2. Reiniciar Prometheus: docker compose restart prometheus"
    else
        echo "  1. Instalar Proxmox VE Exporter:"
        echo "     ./scripts/install_proxmox_exporter.sh $PROXMOX_HOST"
        echo "  2. Configurar API token no Proxmox"
        echo "  3. Verificar firewall (porta $PROXMOX_EXPORTER_PORT)"
    fi
fi

echo ""
