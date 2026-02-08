#!/bin/bash
# Script de Setup para CI/CD - GitHub Actions
# Configura chave SSH e secrets necessários para deployment automático

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  Setup CI/CD - GitHub Actions"
echo "==========================================${NC}"
echo ""

# Variáveis
DEPLOY_HOST="10.10.1.159"
DEPLOY_USER="root"
SSH_KEY_PATH="$HOME/.ssh/deploy_key_github"

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependências
echo "1. Verificando dependências..."
if ! command_exists ssh-keygen; then
    echo -e "${RED}❌ ssh-keygen não encontrado${NC}"
    exit 1
fi

if ! command_exists ssh-copy-id; then
    echo -e "${RED}❌ ssh-copy-id não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependências OK${NC}"
echo ""

# Gerar chave SSH
echo "2. Gerando chave SSH para CI/CD..."
if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️  Chave SSH já existe em $SSH_KEY_PATH${NC}"
    read -p "Deseja sobrescrever? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Usando chave existente..."
    else
        rm -f "$SSH_KEY_PATH" "$SSH_KEY_PATH.pub"
        ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -C "github-actions@observability" -N ""
        echo -e "${GREEN}✅ Nova chave gerada${NC}"
    fi
else
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -C "github-actions@observability" -N ""
    echo -e "${GREEN}✅ Chave SSH gerada${NC}"
fi
echo ""

# Copiar chave para servidor
echo "3. Copiando chave SSH para servidor ($DEPLOY_HOST)..."
echo "   Será pedida a password do servidor..."
if ssh-copy-id -i "$SSH_KEY_PATH.pub" "$DEPLOY_USER@$DEPLOY_HOST"; then
    echo -e "${GREEN}✅ Chave copiada com sucesso${NC}"
else
    echo -e "${RED}❌ Falha ao copiar chave${NC}"
    echo "   Verifique se o servidor está acessível e se a password está correta"
    exit 1
fi
echo ""

# Testar conexão SSH
echo "4. Testando conexão SSH..."
if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$DEPLOY_USER@$DEPLOY_HOST" 'echo "SSH OK"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Conexão SSH funcionando${NC}"
else
    echo -e "${RED}❌ Falha na conexão SSH${NC}"
    exit 1
fi
echo ""

# Mostrar chave privada para GitHub Secret
echo "5. Configurar GitHub Secret..."
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}COPIE O CONTEÚDO ABAIXO PARA O GITHUB SECRET:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
cat "$SSH_KEY_PATH"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Passos para adicionar no GitHub:"
echo "  1. Ir para: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo "  2. Clicar em 'New repository secret'"
echo "  3. Nome: DEPLOY_SSH_KEY"
echo "  4. Valor: Copiar TODO o conteúdo acima (incluindo BEGIN e END)"
echo "  5. Clicar 'Add secret'"
echo ""

# Verificar servidor
echo "6. Verificando servidor de deployment..."
ssh -i "$SSH_KEY_PATH" "$DEPLOY_USER@$DEPLOY_HOST" << 'EOF'
    echo "Verificando dependências no servidor..."
    
    # Verificar Docker
    if command -v docker &> /dev/null; then
        echo "✅ Docker instalado: $(docker --version)"
    else
        echo "❌ Docker NÃO instalado"
        echo "   Execute: apt install -y docker.io docker-compose"
    fi
    
    # Verificar Docker Compose
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose instalado: $(docker-compose --version)"
    else
        echo "❌ Docker Compose NÃO instalado"
    fi
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        echo "✅ Python3 instalado: $(python3 --version)"
    else
        echo "⚠️  Python3 NÃO instalado (opcional para health checks)"
    fi
    
    # Verificar diretório de deployment
    if [ -d "/root/observability-stack" ]; then
        echo "✅ Diretório de deployment existe"
    else
        echo "⚠️  Diretório de deployment não existe (será criado no primeiro deploy)"
    fi
EOF
echo ""

# Resumo
echo -e "${GREEN}=========================================="
echo "  Setup Concluído!"
echo "==========================================${NC}"
echo ""
echo "Próximos passos:"
echo "  1. ✅ Adicionar secret DEPLOY_SSH_KEY no GitHub (instruções acima)"
echo "  2. ✅ Fazer commit e push para testar:"
echo "       git add ."
echo "       git commit -m 'ci: setup GitHub Actions deployment'"
echo "       git push origin main"
echo "  3. ✅ Verificar workflow em: https://github.com/YOUR_REPO/actions"
echo ""
echo "Documentação completa: docs/CICD.md"
echo ""
