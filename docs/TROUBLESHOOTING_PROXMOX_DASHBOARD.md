# Troubleshooting: Proxmox Dashboard Sem Dados

## Diagnóstico Rápido

```bash
# No servidor de monitorização (10.10.1.159)
cd /root/observability-stack
bash scripts/diagnose_proxmox_dashboard.sh
```

## Causa Mais Provável

O **Proxmox VE Exporter** não está instalado no host Proxmox (192.168.90.104).

## Solução Rápida

### 1. Instalar Proxmox VE Exporter

```bash
# No servidor de monitorização (10.10.1.159)
cd /root/observability-stack
./scripts/install_proxmox_exporter.sh 192.168.90.104
```

O script irá:

1. SSH para o Proxmox host
2. Instalar Proxmox VE Exporter
3. Configurar como serviço systemd
4. Criar API token no Proxmox
5. Iniciar o exporter

### 2. Criar API Token no Proxmox (Manual)

Se o script pedir, criar token manualmente:

1. **Aceder ao Proxmox Web UI**: https://192.168.90.104:8006
2. **Datacenter → Permissions → API Tokens**
3. **Add**:
   - User: `root@pam`
   - Token ID: `monitoring`
   - Privilege Separation: **Desmarcar** (sem privilege separation)
4. **Copiar o token** (só aparece uma vez!)

### 3. Configurar Exporter

```bash
# SSH para Proxmox host
ssh root@192.168.90.104

# Editar configuração
nano /etc/default/prometheus-pve-exporter

# Adicionar:
PVE_USER=root@pam
PVE_TOKEN_NAME=monitoring
PVE_TOKEN_VALUE=SEU_TOKEN_AQUI
PVE_VERIFY_SSL=false

# Reiniciar serviço
systemctl restart prometheus-pve-exporter
systemctl status prometheus-pve-exporter
```

### 4. Verificar Exporter

```bash
# Testar se exporter está a responder
curl http://192.168.90.104:9221/metrics | grep pve_up

# Deve retornar:
# pve_up{node="pve"} 1
```

### 5. Verificar Prometheus

```bash
# No servidor de monitorização
# Aceder: http://10.10.1.159:9990/targets

# Procurar job "proxmox"
# Status deve ser "UP"
```

### 6. Verificar Dashboard

1. Aceder Grafana: http://10.10.1.159:3000
2. Abrir dashboard "Proxmox Cluster Overview"
3. Verificar time range (últimas 6 horas)
4. Aguardar 1-2 minutos para dados aparecerem

## Outras Causas Possíveis

### Firewall Bloqueando

```bash
# Verificar se porta 9221 está acessível
nc -zv 192.168.90.104 9221

# Se falhar, adicionar regra no OPNsense:
# Source: 10.10.1.159
# Destination: 192.168.90.104
# Port: 9221
# Action: Pass
```

### Prometheus Não Está a Fazer Scrape

```bash
# Verificar logs do Prometheus
docker compose logs prometheus | grep proxmox

# Reiniciar Prometheus
docker compose restart prometheus
```

### Dashboard com Time Range Errado

1. No Grafana, clicar no time picker (canto superior direito)
2. Selecionar "Last 6 hours"
3. Clicar "Apply"

## Verificação Completa

```bash
# 1. Exporter a responder
curl http://192.168.90.104:9221/metrics | head -20

# 2. Prometheus a fazer scrape
curl http://10.10.1.159:9990/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="proxmox")'

# 3. Query retorna dados
curl 'http://10.10.1.159:9990/api/v1/query?query=pve_up' | jq .

# 4. Health check
cd /root/observability-stack
python3 scripts/check_health.py
```

## Instalação Manual do Exporter

Se o script automático falhar:

```bash
# SSH para Proxmox
ssh root@192.168.90.104

# Instalar dependências
apt update
apt install -y python3 python3-pip

# Instalar exporter
pip3 install prometheus-pve-exporter

# Criar ficheiro de serviço
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

[Install]
WantedBy=multi-user.target
EOF

# Criar configuração
cat > /etc/default/prometheus-pve-exporter << 'EOF'
PVE_USER=root@pam
PVE_TOKEN_NAME=monitoring
PVE_TOKEN_VALUE=SEU_TOKEN_AQUI
PVE_VERIFY_SSL=false
EOF

# Iniciar serviço
systemctl daemon-reload
systemctl enable prometheus-pve-exporter
systemctl start prometheus-pve-exporter
systemctl status prometheus-pve-exporter
```

## Métricas Esperadas

Quando funcionar, deves ver métricas como:

```
pve_up{node="pve"} 1
pve_node_info{...} 1
pve_cpu_usage_ratio{...} 0.15
pve_memory_usage_bytes{...} 8589934592
pve_guest_info{...} 1
pve_disk_usage_bytes{...} 107374182400
```
