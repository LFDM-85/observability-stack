# Guia de Setup - Monitorização Proxmox

Este guia explica como configurar o stack de observabilidade para monitorizar um ambiente Proxmox VE com LXCs e VMs.

## 📋 Visão Geral

**Ambiente Proxmox:**
- **Host Proxmox**: 192.168.90.104
- **VMs**: 2 (OPNsense, Zorin18)
- **LXCs**: 7 (adguard, immich, n8n, zabbix, passbolt, monit, ollama)

**Componentes de Monitorização:**
1. **Prometheus** - Coleta e armazena métricas
2. **Grafana** - Visualização de dashboards
3. **Node Exporter** - Métricas de sistema (CPU, RAM, disco, rede)
4. **cAdvisor** - Métricas de containers Docker
5. **Proxmox VE Exporter** - Métricas específicas do Proxmox (VMs, LXCs, storage)
6. **Loki** - Logs centralizados
7. **Alloy** - Coleta e processamento de logs

## 🚀 Quick Start

### 1. Pré-requisitos

No **servidor onde vai correr o stack** (pode ser um LXC ou máquina dedicada):

```bash
# Instalar dependências
sudo apt update
sudo apt install -y docker.io docker-compose python3 python3-pip git

# Clone o repositório
git clone https://github.com/LFDM-85/observability-stack.git
cd observability-stack
```

### 2. Configurar Acesso SSH

Configure acesso SSH passwordless para todos os hosts:

```bash
# Gerar chave SSH (se não existir)
ssh-keygen -t rsa -b 4096

# Distribuir a chave para todos os hosts (incluindo Proxmox host)
python3 scripts/setup_ssh_key.py --all

# Ou manualmente para cada host
ssh-copy-id root@192.168.90.104
ssh-copy-id root@192.168.90.105
# ... etc
```

### 3. Iniciar o Stack de Monitorização

```bash
# Subir os containers do stack
docker-compose up -d

# Verificar se todos os containers estão running
docker-compose ps
```

### 4. Instalar Proxmox VE Exporter

No **host Proxmox** (192.168.90.104):

```bash
# Executar script de instalação
./scripts/install_proxmox_exporter.sh 192.168.90.104
```

**Importante:** Após a instalação, precisa configurar o token de API:

```bash
# No host Proxmox, obter o token
ssh root@192.168.90.104 'pveum user token list prometheus@pve'

# Editar o ficheiro de configuração e adicionar o token
ssh root@192.168.90.104 'nano /etc/prometheus/pve.yml'

# Reiniciar o serviço
ssh root@192.168.90.104 'systemctl restart prometheus-pve-exporter'

# Verificar se está a funcionar
curl http://192.168.90.104:9221/metrics | head -20
```

### 5. Deploy de Exporters em LXCs/VMs

Este script vai instalar automaticamente Node Exporter em todos os hosts e cAdvisor onde houver Docker:

```bash
# Deploy automático em todos os hosts do hosts.txt
python3 scripts/deploy_monitor.py

# O script irá:
# 1. Detectar tipo de guest (LXC, VM, ou Proxmox host)
# 2. Instalar Node Exporter em todos
# 3. Instalar cAdvisor nos hosts com Docker
# 4. Verificar conectividade e scraping do Prometheus
# 5. Mostrar relatório detalhado
```

### 6. Aceder aos Dashboards

Aguarde 1-2 minutos para o Prometheus começar a coletar métricas, depois:

- **Grafana**: http://localhost:3000
  - User: `admin`
  - Password: `admin` (altere no primeiro login)

- **Prometheus**: http://localhost:9990
  - Ver targets: http://localhost:9990/targets

- **Dashboards disponíveis**:
  1. **Proxmox Cluster Overview** - Visão geral de VMs/LXCs, CPU, memória
  2. **Proxmox Hosts Overview** - Métricas de sistema de cada LXC/VM/Host
  3. **Docker Containers Overview** - Containers Docker (LXC immich)

## 📊 Arquitetura de Monitorização

```
┌─────────────────────────────────────────────────────────────────┐
│                    Proxmox VE Host (192.168.90.104)             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Node Exporter│  │Proxmox Exporter│  │  cAdvisor   │          │
│  │   :9100      │  │    :9221      │  │   :9991     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                 │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                      Prometheus :9990                           │
│              (Scrape interval: 15s)                            │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │      Grafana :3000            │
          │  - Proxmox Cluster Dashboard  │
          │  - Hosts Overview Dashboard   │
          │  - Docker Containers Dashboard│
          └───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         VMs                                     │
│                                                                 │
│  VM 100 (OPNsense)        VM 101 (Zorin18)                      │
│  192.168.90.105           10.10.1.156                           │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │Node Exporter │         │Node Exporter │                     │
│  │   :9100      │         │   :9100      │                     │
│  └──────────────┘         └──────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
          │                          │
          └──────────┬───────────────┘
                     ▼
              Prometheus :9990

┌─────────────────────────────────────────────────────────────────┐
│                         LXCs                                    │
│                                                                 │
│  LXC 200 (adguard)        LXC 201 (immich)                      │
│  192.168.90.106           10.10.1.152                           │
│  ┌──────────────┐         ┌──────────────┐  ┌──────────────┐   │
│  │Node Exporter │         │Node Exporter │  │  cAdvisor    │   │
│  │   :9100      │         │   :9100      │  │   :9991      │   │
│  └──────────────┘         └──────────────┘  └──────────────┘   │
│                                                                 │
│  LXC 202-206 (n8n, zabbix, passbolt, monit, ollama)            │
│  Cada um com Node Exporter :9100                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configurações Detalhadas

### Prometheus Jobs

O [prometheus/prometheus.yml](prometheus/prometheus.yml) está configurado com os seguintes jobs:

1. **`monitoring_stack`** - Serviços locais do stack
   - Prometheus, Grafana, Loki, Alloy, Node Exporter, cAdvisor locais

2. **`remote_hosts`** - Node Exporter nos LXCs/VMs/Host
   - Descoberta via `targets.json`
   - Porta 9100
   - Métricas: CPU, RAM, disco, rede, processos

3. **`remote_docker`** - cAdvisor nos hosts com Docker
   - Descoberta via `docker_targets.json`
   - Porta 9991
   - Métricas: Containers, CPU/RAM por container, rede

4. **`proxmox`** - Proxmox VE Exporter
   - Target estático: `192.168.90.104:9221`
   - Métricas: Status VMs/LXCs, storage, cluster

### Ficheiros de Targets

#### [prometheus/targets.json](prometheus/targets.json)
```json
[
  {
    "targets": [
      "192.168.90.104:9100",  // Proxmox Host
      "192.168.90.105:9100",  // VM 100 - OPNsense
      "10.10.1.156:9100",     // VM 101 - Zorin18
      "192.168.90.106:9100",  // LXC 200 - adguard
      "10.10.1.152:9100",     // LXC 201 - immich
      "10.10.1.172:9100",     // LXC 202 - n8n
      "10.10.1.116:9100",     // LXC 203 - zabbix
      "10.10.1.183:9100",     // LXC 204 - passbolt
      "10.10.1.148:9100",     // LXC 205 - monit
      "10.10.1.117:9100"      // LXC 206 - ollama
    ],
    "labels": {
      "job": "remote_hosts",
      "env": "proxmox"
    }
  }
]
```

#### [prometheus/docker_targets.json](prometheus/docker_targets.json)
```json
[
  {
    "targets": [
      "10.10.1.152:9991"  // LXC 201 - immich (tem Docker)
    ],
    "labels": {
      "env": "proxmox",
      "container": "immich"
    }
  }
]
```

### Hosts File

O [hosts.txt](hosts.txt) contém todos os IPs a monitorizar:

```
# Proxmox Host
192.168.90.104  # Proxmox VE Host (pve)

# Virtual Machines
192.168.90.105  # VM 100 - OPNsense-Firewall
10.10.1.156     # VM 101 - Zorin18

# LXC Containers
192.168.90.106  # LXC 200 - adguard
10.10.1.152     # LXC 201 - immich
10.10.1.172     # LXC 202 - n8n
10.10.1.116     # LXC 203 - zabbix
10.10.1.183     # LXC 204 - passbolt
10.10.1.148     # LXC 205 - monit
10.10.1.117     # LXC 206 - ollama
```

## 🐛 Troubleshooting

### Verificar Targets no Prometheus

```bash
# Ver todos os targets
curl http://localhost:9990/api/v1/targets | jq '.data.activeTargets[] | {instance: .labels.instance, job: .labels.job, health: .health}'

# Ou use o script
python3 scripts/verify_prometheus_targets.py
```

### Diagnóstico de Host Específico

```bash
# Diagnosticar problemas em um host
python3 scripts/diagnose_monitoring.py 192.168.90.106

# Auto-fix de problemas comuns
python3 scripts/diagnose_monitoring.py 192.168.90.106 --fix
```

### Health Check Geral

```bash
# Ver saúde geral do sistema
python3 scripts/check_health.py
```

### Problemas Comuns

#### 1. Node Exporter não responde

```bash
# Verificar serviço no host remoto
ssh root@<IP> 'systemctl status node_exporter'

# Verificar porta
ssh root@<IP> 'ss -tlnp | grep 9100'

# Reiniciar serviço
ssh root@<IP> 'systemctl restart node_exporter'
```

#### 2. cAdvisor não consegue aceder a containers

```bash
# Verificar permissões do Docker socket
ssh root@<IP> 'ls -l /var/run/docker.sock'

# Ver logs do cAdvisor
ssh root@<IP> 'journalctl -u cadvisor -n 50'

# Reiniciar cAdvisor
ssh root@<IP> 'systemctl restart cadvisor'
```

#### 3. Proxmox Exporter sem métricas

```bash
# Verificar configuração
ssh root@192.168.90.104 'cat /etc/prometheus/pve.yml'

# Verificar logs
ssh root@192.168.90.104 'journalctl -u prometheus-pve-exporter -n 50'

# Testar API token
ssh root@192.168.90.104 'pveum user token list prometheus@pve'

# Reiniciar serviço
ssh root@192.168.90.104 'systemctl restart prometheus-pve-exporter'
```

#### 4. Firewall bloqueando portas

```bash
# Abrir portas necessárias (executar em cada host)
sudo firewall-cmd --add-port=9100/tcp --permanent  # Node Exporter
sudo firewall-cmd --add-port=9991/tcp --permanent  # cAdvisor
sudo firewall-cmd --add-port=9221/tcp --permanent  # Proxmox Exporter (só no host)
sudo firewall-cmd --reload

# Ou desabilitar firewall temporariamente para teste
sudo systemctl stop firewalld
```

#### 5. Prometheus não consegue fazer scrape

```bash
# Testar conectividade do container Prometheus
docker exec -it prometheus wget -O- http://192.168.90.104:9100/metrics | head -10

# Verificar rede do container
docker inspect prometheus | grep -A 10 NetworkMode

# Ver logs do Prometheus
docker logs prometheus | tail -50
```

## 📈 Dashboards Disponíveis

### 1. Proxmox Cluster Overview

**UID**: `proxmox-cluster`

**Painéis:**
- Nodes online
- Total VMs/LXCs
- Guests running/stopped
- CPU usage por guest
- Memory usage por guest
- Inventário completo de VMs/LXCs

**Métricas usadas:**
- `pve_up` - Status do Proxmox
- `pve_guest_info` - Informação de guests
- `pve_cpu_usage_ratio` - CPU por guest
- `pve_mem_usage_ratio` - Memória por guest

### 2. Proxmox Hosts Overview

**UID**: `proxmox-hosts`

**Painéis:**
- Hosts online/offline
- CPU usage por host
- Memory usage por host
- Disk usage
- Network I/O
- System load
- Uptime

**Métricas usadas:**
- `node_cpu_seconds_total` - CPU
- `node_memory_*` - Memória
- `node_filesystem_*` - Disco
- `node_network_*` - Rede
- `node_load*` - Load average

### 3. Docker Containers Overview

**UID**: `docker-containers-v2`

**Painéis:**
- Running containers
- CPU usage por container
- Memory usage por container
- Network I/O por container

**Métricas usadas:**
- `container_last_seen` - Status
- `container_cpu_usage_seconds_total` - CPU
- `container_memory_usage_bytes` - Memória
- `container_network_*` - Rede

## 🔄 Manutenção

### Adicionar Novo LXC/VM

1. Editar [hosts.txt](hosts.txt) e adicionar o novo IP
2. Executar deploy:
   ```bash
   python3 scripts/deploy_monitor.py
   ```
3. Aguardar 15-30 segundos para Prometheus detetar o novo target
4. Verificar no dashboard

### Remover LXC/VM

1. Remover do [hosts.txt](hosts.txt)
2. Remover dos ficheiros targets:
   ```bash
   # Editar manualmente ou executar
   python3 scripts/deploy_monitor.py  # Re-gera os targets
   ```
3. Recarregar Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

### Atualizar Exporters

```bash
# Node Exporter - editar versão em deploy_monitor.py
# Linha ~300: NODE_EXPORTER_VERSION = "v1.8.2"

# cAdvisor - editar versão em deploy_monitor.py
# Linha ~378: CADVISOR_VERSION = "v0.47.0"

# Proxmox Exporter - editar em install_proxmox_exporter.sh
# Linha 6: EXPORTER_VERSION="v0.4.2"

# Re-executar deployment
python3 scripts/deploy_monitor.py
```

### Backup de Configurações

```bash
# Backup de configurações Grafana (dashboards, datasources)
docker exec grafana grafana cli admin export-dashboard > grafana_backup.json

# Backup de configurações Prometheus
tar -czf prometheus_backup.tar.gz prometheus/

# Backup completo
tar -czf observability_backup_$(date +%Y%m%d).tar.gz \
    hosts.txt \
    prometheus/ \
    grafana/ \
    docker-compose.yml
```

## 🎯 Próximos Passos Recomendados

1. **Configurar Alertas**
   - Editar [prometheus/alerts/](prometheus/alerts/)
   - Configurar Alertmanager para notificações (email, Slack, etc.)

2. **Integrar Logs**
   - Configurar Alloy para coletar logs dos LXCs/VMs
   - Ver logs no Grafana via Loki

3. **Adicionar Métricas de Aplicação**
   - Instrumentar aplicações com bibliotecas Prometheus
   - Adicionar endpoints `/metrics` nas apps

4. **Métricas de Backup**
   - Monitorizar estado de backups do Proxmox
   - Alertas para backups falhados

5. **Storage Monitoring**
   - Métricas de pools ZFS (se aplicável)
   - IOPS e latência de disco

6. **Network Monitoring**
   - SNMP para switches/routers
   - Métricas de firewall (OPNsense)

## 📚 Recursos Adicionais

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)
- [Proxmox VE Exporter](https://github.com/prometheus-pve/prometheus-pve-exporter)
- [cAdvisor Metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md)

## 💡 Dicas

1. **Otimização de Scrape Interval**: Se tem muitos targets, ajuste o `scrape_interval` em [prometheus.yml](prometheus/prometheus.yml)

2. **Retenção de Dados**: Por padrão Prometheus guarda 15 dias. Ajuste em [docker-compose.yml](docker-compose.yml):
   ```yaml
   command:
     - '--storage.tsdb.retention.time=30d'
   ```

3. **Recursos do Stack**: O stack completo usa ~2-4GB RAM. Ajuste se necessário.

4. **Segurança**: Configure autenticação/SSL no Grafana para ambientes de produção.

5. **Backup Regular**: Agende backups automáticos das configurações.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verificar logs: `docker-compose logs -f [serviço]`
2. Executar health check: `python3 scripts/check_health.py`
3. Ver issues no GitHub: https://github.com/LFDM-85/observability-stack/issues
