#!/bin/bash
# Auto-deployment script para servidor 10.10.1.159
# Este script corre NO SERVIDOR e faz pull do GitHub

set -e

# Configuração
REPO_URL="https://github.com/YOUR_USERNAME/observability-stack.git"
DEPLOY_PATH="/root/observability-stack"
BRANCH="main"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  Auto-Deployment - Observability Stack"
echo "==========================================${NC}"
echo ""

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git não instalado${NC}"
    echo "Instalar: apt install -y git"
    exit 1
fi

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não instalado${NC}"
    echo "Instalar: apt install -y docker.io docker-compose"
    exit 1
fi

# Criar backup se deployment existir
if [ -d "$DEPLOY_PATH" ]; then
    echo -e "${YELLOW}Criando backup...${NC}"
    BACKUP_NAME="observability-stack-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$DEPLOY_PATH" "/root/$BACKUP_NAME"
    echo -e "${GREEN}✅ Backup criado: /root/$BACKUP_NAME${NC}"
    
    # Entrar no diretório e fazer pull
    cd "$DEPLOY_PATH"
    
    # Verificar se é um repositório git
    if [ -d ".git" ]; then
        echo -e "${BLUE}Atualizando código...${NC}"
        git fetch origin
        git reset --hard origin/$BRANCH
        echo -e "${GREEN}✅ Código atualizado${NC}"
    else
        echo -e "${YELLOW}⚠️  Não é um repositório git, fazendo clone...${NC}"
        cd /root
        rm -rf "$DEPLOY_PATH"
        git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_PATH"
        cd "$DEPLOY_PATH"
    fi
else
    # Primeiro deployment - clonar repositório
    echo -e "${BLUE}Primeiro deployment - clonando repositório...${NC}"
    git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_PATH"
    cd "$DEPLOY_PATH"
    echo -e "${GREEN}✅ Repositório clonado${NC}"
fi

# Verificar ficheiros de configuração
echo ""
echo -e "${BLUE}Verificando configuração...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env não encontrado${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${RED}❌ Configure .env antes de continuar!${NC}"
        echo "Execute: nano $DEPLOY_PATH/.env"
        exit 1
    fi
fi

if [ ! -f hosts.txt ]; then
    echo -e "${YELLOW}⚠️  hosts.txt não encontrado${NC}"
    if [ -f hosts.txt.example ]; then
        cp hosts.txt.example hosts.txt
        echo -e "${RED}❌ Configure hosts.txt antes de continuar!${NC}"
        echo "Execute: nano $DEPLOY_PATH/hosts.txt"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Configuração OK${NC}"

# Dar permissões de execução
chmod +x setup.sh diagnose.sh scripts/*.sh 2>/dev/null || true

# Reiniciar stack Docker
echo ""
echo -e "${BLUE}Reiniciando Docker stack...${NC}"

# Parar stack atual
echo "Parando containers..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

# Pull de novas imagens
echo "Atualizando imagens..."
docker compose pull 2>/dev/null || docker-compose pull 2>/dev/null

# Iniciar stack
echo "Iniciando containers..."
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null

# Aguardar containers iniciarem
echo "Aguardando containers iniciarem..."
sleep 15

# Verificar status
echo ""
echo -e "${GREEN}Status dos containers:${NC}"
docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null

# Health check
echo ""
if command -v python3 &> /dev/null && [ -f scripts/check_health.py ]; then
    echo -e "${BLUE}Executando health check...${NC}"
    python3 scripts/check_health.py 2>/dev/null || echo -e "${YELLOW}⚠️  Health check falhou${NC}"
fi

# Resumo
echo ""
echo -e "${GREEN}=========================================="
echo "  Deployment Concluído!"
echo "==========================================${NC}"
echo ""
echo "Serviços disponíveis:"
echo "  🎨 Grafana:      http://10.10.1.159:3000"
echo "  📊 Prometheus:   http://10.10.1.159:9990"
echo "  🔔 Alertmanager: http://10.10.1.159:9093"
echo ""
echo "Backup anterior: /root/$BACKUP_NAME"
echo ""
