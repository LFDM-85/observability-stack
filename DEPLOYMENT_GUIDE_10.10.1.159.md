# Guia de Deployment - Observability Stack (10.10.1.159)

Este guia detalha o deployment da stack de observabilidade no ambiente Proxmox específico, com a máquina de monitorização no IP **10.10.1.159**.

## 📋 Topologia de Rede

```
┌─────────────────────────────────────────────────────────────┐
│  WAN Network: 192.168.90.x                                  │
│                                                             │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │ OPNsense     │         │ Proxmox Host    │              │
│  │ WAN: .105    │◄────────┤ 192.168.90.104  │              │
│  │ LAN: 10.10.1.1│        │ (pve)           │              │
│  └──────┬───────┘         └─────────────────┘              │
└─────────┼──────────────────────────────────────────────────┘
          │
          │ Routing & Firewall
          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAN Network: 10.10.1.x                                     │
│                                                             │
│  ┌─────────────────┐      ┌──────────────────┐             │
│  │ Monitoring Stack│─────►│ n8n (Terry)      │             │
│  │ 10.10.1.159     │      │ 10.10.1.172      │             │
│  │                 │      │ (LXC 202)        │             │
│  │ - Prometheus    │      └──────────────────┘             │
│  │ - Grafana       │                                       │
│  │ - Loki/Tempo    │      ┌──────────────────┐             │
│  │ - Alertmanager  │      │ Outros LXCs/VMs  │             │
│  └─────────────────┘      │ 10.10.1.xxx      │             │
│                           └──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Pré-requisitos

### Na Máquina de Monitorização (10.10.1.159)

**Software necessário:**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker e Docker Compose
sudo apt install -y docker.io docker-compose

# Instalar Python 3 e ferramentas
sudo apt install -y python3 python3-pip git

# Adicionar utilizador ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalação
docker --version
docker-compose --version
python3 --version
```

**Recursos mínimos recomendados:**

- CPU: 2 cores
- RAM: 4 GB (recomendado 8 GB)
- Disco: 50 GB (para retenção de 30 dias de métricas)

### Configuração de Rede e Firewall

#### No OPNsense (10.10.1.1)

**Regras de Firewall necessárias:**

**LAN → WAN (10.10.1.159 → 192.168.90.104):**

```
Protocolo: TCP
Origem: 10.10.1.159
Destino: 192.168.90.104
Portas: 22 (SSH), 9100 (Node Exporter), 9221 (Proxmox Exporter)
Ação: Permitir
```

**WAN → LAN (opcional, se Proxmox precisar aceder ao Prometheus):**

```
Protocolo: TCP
Origem: 192.168.90.104
Destino: 10.10.1.159
Portas: 9990 (Prometheus)
Ação: Permitir
```

#### Verificar Conectividade

```bash
# Na máquina 10.10.1.159, testar acesso ao Proxmox host
ping -c 3 192.168.90.104

# Testar porta SSH
nc -zv 192.168.90.104 22

# Testar acesso ao n8n
curl -I http://10.10.1.172:5678
```

## 🚀 Instalação

### 1. Clonar o Repositório

```bash
# Criar diretório de trabalho
mkdir -p ~/observability
cd ~/observability

# Clonar repositório
git clone <repository-url> observability-stack
cd observability-stack
```

### 2. Configurar Acesso SSH

**Setup de chaves SSH para acesso passwordless:**

```bash
# Gerar chave SSH (se não existir)
ssh-keygen -t rsa -b 4096 -C "monitoring@10.10.1.159"

# Distribuir chave para todos os hosts
python3 scripts/setup_ssh_key.py --all

# Verificar acesso
ssh root@192.168.90.104 'echo "SSH OK"'
```

**Se encontrares problemas:**

- Verificar se o Proxmox permite autenticação por chave
- Confirmar que `/root/.ssh/authorized_keys` tem as permissões corretas (600)
- Ver troubleshooting no [README.md](README.md#ssh-key-troubleshooting)

### 3. Configurar Webhooks (Opcional)

```bash
# Editar ficheiro .env
nano .env
```

**Adicionar webhooks:**

```env
# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Teams (se aplicável)
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# n8n (já configurado para este ambiente)
N8N_WEBHOOK_URL=http://10.10.1.172:5678/webhook/homelab-alert
```

### 4. Iniciar a Stack

```bash
# Executar script de setup
./setup.sh
```

**O script irá:**

- ✅ Verificar configurações
- ✅ Criar ficheiros necessários
- ✅ Baixar dashboards do Grafana
- ✅ Iniciar todos os containers

**Verificar containers:**

```bash
docker compose ps
```

**Resultado esperado:**

```
NAME                STATUS              PORTS
prometheus          Up (healthy)        0.0.0.0:9990->9090/tcp
grafana             Up                  0.0.0.0:3000->3000/tcp
loki                Up                  0.0.0.0:3100->3100/tcp
tempo               Up                  0.0.0.0:3200->3200/tcp
alloy               Up                  0.0.0.0:12345->12345/tcp
alertmanager        Up                  0.0.0.0:9093->9093/tcp
n8n-adapter         Up                  0.0.0.0:8081->8081/tcp
node-exporter       Up
cadvisor            Up
```

### 5. Instalar Proxmox VE Exporter

**No host Proxmox (192.168.90.104):**

```bash
# Executar script de instalação
./scripts/install_proxmox_exporter.sh 192.168.90.104
```

**Configurar API Token:**

O script irá pedir para criar um token de API. Seguir as instruções:

1. Aceder à interface web do Proxmox: https://192.168.90.104:8006
2. Ir para **Datacenter → Permissions → API Tokens**
3. Criar token para utilizador `prometheus@pve`
4. Copiar o token e adicionar ao ficheiro `/etc/prometheus/pve.yml` no Proxmox host

**Verificar instalação:**

```bash
# Testar endpoint do exporter
curl http://192.168.90.104:9221/metrics | head -20

# Verificar serviço
ssh root@192.168.90.104 'systemctl status prometheus-pve-exporter'
```

### 6. Deploy de Exporters em Todos os Hosts

```bash
# Deploy automático de Node Exporter e cAdvisor
python3 scripts/deploy_monitor.py
```

**O script irá:**

- ✅ Ler todos os IPs do `hosts.txt`
- ✅ Detectar tipo de cada host (Proxmox, VM, LXC)
- ✅ Instalar Node Exporter em todos
- ✅ Instalar cAdvisor nos hosts com Docker
- ✅ Atualizar `prometheus/targets.json` e `prometheus/docker_targets.json`
- ✅ Verificar que Prometheus consegue fazer scrape

**Progresso esperado:**

```
[INFO] Deploying monitoring to 9 hosts...
[OK] 192.168.90.104 - Node Exporter installed
[OK] 192.168.90.105 - Node Exporter installed
[OK] 10.10.1.152 - Node Exporter + cAdvisor installed (Docker detected)
...
[SUCCESS] All hosts configured successfully!
```

## ✅ Verificação

### 1. Aceder ao Grafana

```bash
# Abrir no browser
http://10.10.1.159:3000
```

**Credenciais padrão:**

- Username: `admin`
- Password: `admin` (será pedido para alterar no primeiro login)

**Dashboards disponíveis:**

- **Proxmox Cluster Overview** - Status de VMs/LXCs, CPU, memória
- **Proxmox Hosts Overview** - Métricas de sistema de todos os hosts
- **Docker Containers** - Métricas de containers Docker

### 2. Verificar Targets no Prometheus

```bash
# Via browser
http://10.10.1.159:9990/targets

# Via script
python3 scripts/verify_prometheus_targets.py
```

**Targets esperados:**

- `monitoring_stack` - 6 targets (Prometheus, Grafana, Loki, Alloy, Node Exporter, cAdvisor)
- `remote_hosts` - 9 targets (todos os IPs do hosts.txt)
- `remote_docker` - 1+ targets (LXCs com Docker, ex: 10.10.1.152)
- `proxmox` - 1 target (192.168.90.104:9221)

### 3. Health Check Geral

```bash
python3 scripts/check_health.py
```

**Resultado esperado:**

```
=== Observability Stack Health Check ===

Docker Containers:
  ✅ prometheus - Up (healthy)
  ✅ grafana - Up
  ✅ loki - Up
  ...

Prometheus Targets:
  ✅ monitoring_stack: 6/6 up
  ✅ remote_hosts: 9/9 up
  ✅ remote_docker: 1/1 up
  ✅ proxmox: 1/1 up

Active Alerts: 0 critical, 0 warning

Overall Status: ✅ HEALTHY
```

### 4. Testar Alertas

```bash
# Enviar alerta de teste
./scripts/test_alerts.sh
```

**Verificar:**

- Alerta aparece no Alertmanager: http://10.10.1.159:9093
- Se n8n configurado, recebe notificação no Discord

## 🔧 Troubleshooting

### Problema: Target "down" no Prometheus

**Diagnóstico:**

```bash
# Verificar conectividade
ping -c 3 <IP_DO_HOST>

# Testar porta do exporter
nc -zv <IP_DO_HOST> 9100

# Verificar serviço no host remoto
ssh root@<IP_DO_HOST> 'systemctl status node_exporter'
```

**Soluções:**

1. Reiniciar serviço: `ssh root@<IP> 'systemctl restart node_exporter'`
2. Verificar firewall no host
3. Executar diagnóstico: `python3 scripts/diagnose_monitoring.py <IP>`

### Problema: Prometheus não consegue aceder ao Proxmox host (192.168.90.104)

**Causa provável:** Firewall OPNsense bloqueando tráfego entre redes.

**Solução:**

1. Aceder ao OPNsense (https://192.168.90.105 ou http://10.10.1.1)
2. Ir para **Firewall → Rules → LAN**
3. Adicionar regra:
   - Source: 10.10.1.159
   - Destination: 192.168.90.104
   - Port: 9100, 9221
   - Action: Pass

### Problema: n8n não recebe alertas

**Diagnóstico:**

```bash
# Testar conectividade ao n8n
curl -X POST http://10.10.1.172:5678/webhook/homelab-alert \
  -H "Content-Type: application/json" \
  -d '{"test": "alert"}'

# Verificar logs do n8n-adapter
docker logs n8n-adapter
```

**Soluções:**

1. Verificar se n8n está a correr: `ssh root@10.10.1.172 'docker ps | grep n8n'`
2. Confirmar URL do webhook no `.env`
3. Verificar workflow "Terry" está ativo no n8n

### Problema: Containers não iniciam

**Diagnóstico:**

```bash
# Ver logs de um container específico
docker logs prometheus

# Ver todos os logs
docker compose logs
```

**Soluções:**

1. Verificar espaço em disco: `df -h`
2. Verificar permissões dos volumes
3. Reiniciar stack: `docker compose down && docker compose up -d`

## 📊 Acesso aos Serviços

| Serviço          | URL                      | Credenciais   |
| ---------------- | ------------------------ | ------------- |
| **Grafana**      | http://10.10.1.159:3000  | admin / admin |
| **Prometheus**   | http://10.10.1.159:9990  | -             |
| **Alertmanager** | http://10.10.1.159:9093  | -             |
| **Loki**         | http://10.10.1.159:3100  | -             |
| **Tempo**        | http://10.10.1.159:3200  | -             |
| **Alloy UI**     | http://10.10.1.159:12345 | -             |

## 🔄 Manutenção

### Adicionar Novo Host

1. Editar `hosts.txt`:

   ```bash
   echo "10.10.1.200" >> hosts.txt
   ```

2. Deploy monitoring:

   ```bash
   python3 scripts/deploy_monitor.py
   ```

3. Aguardar 15-30 segundos para Prometheus detetar

### Atualizar Stack

```bash
# Pull de novas imagens
docker compose pull

# Reiniciar stack
docker compose down
docker compose up -d
```

### Backup de Configurações

```bash
# Backup completo
tar -czf observability_backup_$(date +%Y%m%d).tar.gz \
    hosts.txt \
    .env \
    prometheus/ \
    grafana/ \
    docker-compose.yml
```

## 📚 Recursos Adicionais

- [README.md](README.md) - Documentação geral
- [PROXMOX_SETUP_GUIDE.md](PROXMOX_SETUP_GUIDE.md) - Guia detalhado Proxmox
- [ALERTS.md](ALERTS.md) - Referência de alertas
- [N8N_INTEGRATION.md](N8N_INTEGRATION.md) - Integração com n8n Terry

## 🆘 Suporte

Para problemas:

1. Executar diagnóstico: `./diagnose.sh`
2. Verificar logs: `docker compose logs -f [serviço]`
3. Health check: `python3 scripts/check_health.py`
