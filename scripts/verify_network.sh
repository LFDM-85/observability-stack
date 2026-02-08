#!/bin/bash
# Script de Verificação de Rede para Deployment em 10.10.1.159
# Verifica conectividade entre a máquina de monitorização e os targets

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Verificação de Rede - Proxmox Stack"
echo "=========================================="
echo ""

# Verificar se está a correr na máquina correta
CURRENT_IP=$(hostname -I | awk '{print $1}')
echo "IP atual da máquina: $CURRENT_IP"

if [ "$CURRENT_IP" != "10.10.1.159" ]; then
    echo -e "${YELLOW}⚠️  AVISO: Esta máquina não tem o IP 10.10.1.159${NC}"
    echo "   Esperado: 10.10.1.159"
    echo "   Atual: $CURRENT_IP"
    echo ""
fi

# Função para testar conectividade
test_connection() {
    local host=$1
    local port=$2
    local service=$3
    
    echo -n "Testando $service ($host:$port)... "
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU${NC}"
        return 1
    fi
}

# Função para testar ping
test_ping() {
    local host=$1
    local name=$2
    
    echo -n "Ping para $name ($host)... "
    
    if ping -c 1 -W 2 $host > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU${NC}"
        return 1
    fi
}

echo "1. Testando conectividade básica (ICMP)"
echo "----------------------------------------"
test_ping "192.168.90.104" "Proxmox Host"
test_ping "192.168.90.105" "OPNsense WAN"
test_ping "10.10.1.1" "OPNsense LAN"
test_ping "10.10.1.172" "n8n LXC"
echo ""

echo "2. Testando portas do Proxmox Host (192.168.90.104)"
echo "----------------------------------------------------"
test_connection "192.168.90.104" "22" "SSH"
test_connection "192.168.90.104" "9100" "Node Exporter"
test_connection "192.168.90.104" "9221" "Proxmox Exporter"
echo ""

echo "3. Testando acesso ao n8n (10.10.1.172)"
echo "----------------------------------------"
test_connection "10.10.1.172" "5678" "n8n Webhook"
echo ""

echo "4. Testando hosts do hosts.txt"
echo "-------------------------------"
if [ -f "hosts.txt" ]; then
    while IFS= read -r line; do
        # Ignorar comentários e linhas vazias
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        
        # Extrair IP (remover user@ se existir)
        ip=$(echo "$line" | sed 's/.*@//')
        
        test_ping "$ip" "Host"
    done < hosts.txt
else
    echo -e "${YELLOW}⚠️  Ficheiro hosts.txt não encontrado${NC}"
fi
echo ""

echo "5. Verificar regras de firewall necessárias"
echo "--------------------------------------------"
echo "Para o OPNsense permitir tráfego, precisa de regras para:"
echo ""
echo "  LAN → WAN (10.10.1.159 → 192.168.90.104):"
echo "    - Porta 22 (SSH)"
echo "    - Porta 9100 (Node Exporter)"
echo "    - Porta 9221 (Proxmox Exporter)"
echo ""
echo "  Aceder ao OPNsense:"
echo "    - WAN: https://192.168.90.105"
echo "    - LAN: http://10.10.1.1"
echo ""

# Testar se consegue fazer SSH ao Proxmox
echo "6. Testar acesso SSH ao Proxmox"
echo "--------------------------------"
echo -n "SSH para root@192.168.90.104... "
if timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=3 root@192.168.90.104 'echo OK' 2>/dev/null | grep -q OK; then
    echo -e "${GREEN}✅ OK (chave SSH configurada)${NC}"
else
    echo -e "${YELLOW}⚠️  Sem acesso (precisa configurar chave SSH)${NC}"
    echo "   Execute: python3 scripts/setup_ssh_key.py --all"
fi
echo ""

echo "=========================================="
echo "  Verificação Concluída"
echo "=========================================="
