#!/bin/bash

# Script de setup automático da stack de observabilidade
# Uso: ./setup.sh

set -e

echo "🚀 Iniciando setup da stack de observabilidade..."
echo ""

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para verificar arquivos
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 ${RED}(FALTANDO)${NC}"
        return 1
    fi
}

# Verificar arquivos obrigatórios
echo -e "${BLUE}📄 Verificando arquivos de configuração...${NC}"
echo ""

missing_count=0

# Raiz
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

echo ""

# Se houver arquivos faltando
if [ $missing_count -ne 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  ERRO: $missing_count arquivo(s) faltando!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Por favor, crie os arquivos listados acima antes de continuar.${NC}"
    echo -e "${YELLOW}Você pode copiar o conteúdo dos artifacts fornecidos.${NC}"
    echo ""
    echo -e "${BLUE}💡 Dica: Estrutura de diretórios esperada:${NC}"
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
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Todos os arquivos de configuração encontrados!${NC}"
echo ""

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo -e "${BLUE}🔧 Criando arquivo .env...${NC}"
    cat > .env << 'EOF'
# Webhooks para notificações de alertas

# Discord Webhook URL
# Como obter: Configurações do Canal > Integrações > Webhooks > Novo Webhook
DISCORD_WEBHOOK_URL=

# Microsoft Teams Webhook URL
# Como obter: Canal > ... > Conectores > Incoming Webhook
TEAMS_WEBHOOK_URL=
EOF
    echo -e "${YELLOW}⚠️  Arquivo .env criado.${NC}"
    echo -e "${YELLOW}    IMPORTANTE: Configure os webhooks antes de usar alertas!${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Arquivo .env já existe${NC}"
    
    # Verificar se webhooks estão configurados
    if grep -q "DISCORD_WEBHOOK_URL=$" .env || grep -q "TEAMS_WEBHOOK_URL=$" .env; then
        echo -e "${YELLOW}⚠️  Webhooks não configurados no arquivo .env${NC}"
    else
        echo -e "${GREEN}✓ Webhooks configurados no .env${NC}"
    fi
    echo ""
fi

# Verificar se Docker está rodando
echo -e "${BLUE}🐳 Verificando Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker não está rodando${NC}"
    echo -e "${YELLOW}Por favor, inicie o Docker primeiro.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker está rodando${NC}"
echo ""

# Verificar se docker-compose está instalado
echo -e "${BLUE}🔍 Verificando docker-compose...${NC}"
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo -e "${GREEN}✓ docker-compose encontrado${NC}"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo -e "${GREEN}✓ docker compose encontrado${NC}"
else
    echo -e "${RED}✗ docker-compose não encontrado${NC}"
    echo -e "${YELLOW}Por favor, instale docker-compose primeiro.${NC}"
    exit 1
fi
echo ""

# Verificar se há containers já rodando
running_containers=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
if [ $running_containers -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Há $running_containers container(s) já rodando${NC}"
    echo -e "${BLUE}Deseja parar e recriar? (s/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([sS]|[yY])$ ]]; then
        echo -e "${BLUE}🛑 Parando containers...${NC}"
        $DOCKER_COMPOSE down
        echo ""
    fi
fi

# Perguntar se quer iniciar os containers
echo -e "${BLUE}🚀 Deseja iniciar a stack agora? (s/n)${NC}"
read -r response

if [[ "$response" =~ ^([sS]|[yY])$ ]]; then
    echo ""
    echo -e "${BLUE}📦 Construindo imagens...${NC}"
    $DOCKER_COMPOSE build --no-cache webhook-adapter
    
    echo ""
    echo -e "${BLUE}🚀 Iniciando containers...${NC}"
    $DOCKER_COMPOSE up -d
    
    echo ""
    echo -e "${BLUE}📊 Aguardando serviços ficarem prontos...${NC}"
    
    # Aguardar serviços
    sleep 5
    
    # Verificar status dos containers
    echo ""
    echo -e "${BLUE}📋 Status dos containers:${NC}"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ Setup concluído com sucesso!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📍 URLs de Acesso:${NC}"
    echo "   🎨 Grafana:       http://localhost:3000  (admin/admin)"
    echo "   📊 Prometheus:    http://localhost:9090"
    echo "   🔔 Alertmanager:  http://localhost:9093"
    echo "   📝 Loki:          http://localhost:3100"
    echo "   🤖 Alloy:         http://localhost:12345"
    echo "   🔗 Webhook:       http://localhost:8080/health"
    echo ""
    echo -e "${BLUE}📝 Comandos úteis:${NC}"
    echo "   Ver logs:        $DOCKER_COMPOSE logs -f"
    echo "   Ver logs (srv):  $DOCKER_COMPOSE logs -f <serviço>"
    echo "   Ver status:      $DOCKER_COMPOSE ps"
    echo "   Parar tudo:      $DOCKER_COMPOSE down"
    echo "   Reiniciar:       $DOCKER_COMPOSE restart"
    echo "   Reiniciar (srv): $DOCKER_COMPOSE restart <serviço>"
    echo ""
    echo -e "${BLUE}🧪 Testar alerta:${NC}"
    echo "   curl -X POST http://localhost:9093/api/v2/alerts -H "Content-Type: application/json" -d '[{"labels":{"alertname":"TestAlert","severity":"warning","instance":"test-server"},"annotations":{"summary":"Teste de alerta do Discord","description":"Este é um teste para verificar se os alertas estão chegando no Discord"},"startsAt":"2025-11-19T20:00:00.000Z"}]'"
    echo ""
    
    # Verificar webhooks
    if grep -q "DISCORD_WEBHOOK_URL=$" .env || grep -q "TEAMS_WEBHOOK_URL=$" .env; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}⚠️  ATENÇÃO: Webhooks não configurados!${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}Para receber alertas:${NC}"
        echo "   1. Edite o arquivo .env"
        echo "   2. Configure DISCORD_WEBHOOK_URL e/ou TEAMS_WEBHOOK_URL"
        echo "   3. Execute: $DOCKER_COMPOSE restart webhook-adapter"
        echo ""
    fi
    
    echo -e "${GREEN}✨ Stack de observabilidade pronta para uso!${NC}"
    echo ""
    
else
    echo ""
    echo -e "${BLUE}ℹ️  Setup validado com sucesso!${NC}"
    echo ""
    echo -e "${BLUE}Para iniciar a stack manualmente, execute:${NC}"
    echo "   $DOCKER_COMPOSE build"
    echo "   $DOCKER_COMPOSE up -d"
    echo ""
fi
