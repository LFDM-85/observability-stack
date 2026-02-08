#!/bin/bash
# Instalação Manual Simplificada do Proxmox VE Exporter
# Executar no Proxmox host (192.168.90.104)

set -e

echo "=========================================="
echo "  Proxmox VE Exporter - Instalação"
echo "=========================================="
echo ""

# 1. Instalar dependências
echo "1. Instalando dependências..."
apt update
apt install -y python3 python3-pip

# 2. Instalar exporter
echo ""
echo "2. Instalando prometheus-pve-exporter..."
pip3 install prometheus-pve-exporter

# Verificar instalação
if ! command -v pve_exporter &> /dev/null; then
    echo "❌ Erro: pve_exporter não foi instalado"
    echo "Tentando caminho alternativo..."
    export PATH=$PATH:/usr/local/bin
fi

# 3. Criar configuração
echo ""
echo "3. Criando configuração..."
cat > /etc/default/prometheus-pve-exporter << 'EOF'
PVE_USER=prometheus@pve
PVE_TOKEN_NAME=monitoring
PVE_TOKEN_VALUE=PLACEHOLDER_TOKEN
PVE_VERIFY_SSL=false
EOF

echo "✅ Ficheiro criado: /etc/default/prometheus-pve-exporter"

# 4. Criar serviço systemd
echo ""
echo "4. Criando serviço systemd..."
cat > /etc/systemd/system/prometheus-pve-exporter.service << 'EOF'
[Unit]
Description=Prometheus Proxmox VE Exporter
After=network.target

[Service]
Type=simple
User=root
EnvironmentFile=/etc/default/prometheus-pve-exporter
ExecStart=/usr/local/bin/pve_exporter --address 0.0.0.0 --port 9221
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Serviço criado"

# 5. Recarregar systemd
echo ""
echo "5. Recarregando systemd..."
systemctl daemon-reload

echo ""
echo "=========================================="
echo "  ⚠️  CONFIGURAÇÃO NECESSÁRIA"
echo "=========================================="
echo ""
echo "Antes de iniciar o serviço, precisas de:"
echo ""
echo "1. Criar API Token no Proxmox Web UI:"
echo "   - Aceder: https://192.168.90.104:8006"
echo "   - Datacenter → Permissions → API Tokens"
echo "   - Add:"
echo "     • User: prometheus@pve"
echo "     • Token ID: monitoring"
echo "     • Privilege Separation: DESMARCAR"
echo "   - Copiar o token"
echo ""
echo "2. Adicionar token ao ficheiro de configuração:"
echo "   nano /etc/default/prometheus-pve-exporter"
echo "   (Substituir PLACEHOLDER_TOKEN pelo token real)"
echo ""
echo "3. Iniciar o serviço:"
echo "   systemctl enable prometheus-pve-exporter"
echo "   systemctl start prometheus-pve-exporter"
echo ""
echo "4. Verificar:"
echo "   systemctl status prometheus-pve-exporter"
echo "   curl http://localhost:9221/metrics | head -20"
echo ""
