# Resumo da Migração para Proxmox

## ✅ Alterações Realizadas

### 1. Ficheiros de Configuração Atualizados

#### [hosts.txt](hosts.txt)
- ✅ Removidos IPs antigos (192.168.1.x)
- ✅ Adicionados 10 novos hosts do Proxmox:
  - 1 Host Proxmox (192.168.90.104)
  - 2 VMs (OPNsense, Zorin18)
  - 7 LXCs (adguard, immich, n8n, zabbix, passbolt, monit, ollama)

#### [prometheus/targets.json](prometheus/targets.json)
- ✅ Atualizado com todos os 10 IPs novos na porta 9100
- ✅ Label alterado de `env: "internal"` para `env: "proxmox"`

#### [prometheus/docker_targets.json](prometheus/docker_targets.json)
- ✅ Atualizado para apenas LXC 201 (immich) que tem Docker
- ✅ Adicionado label `container: "immich"`

#### [prometheus/prometheus.yml](prometheus/prometheus.yml)
- ✅ Adicionado novo job `proxmox` para o Proxmox VE Exporter
- ✅ Target: `192.168.90.104:9221`
- ✅ Jobs existentes mantidos (remote_hosts, remote_docker, monitoring_stack)

### 2. Dashboards Grafana

#### Removido
- ❌ `mysql-monitoring-dashboard.json` (não necessário)

#### Renomeado/Adaptado
- ✅ `unified-infrastructure-dashboard.json` → `proxmox-hosts-overview.json`
  - Atualizado título para "Proxmox Hosts Overview"
  - UID alterado para `proxmox-hosts`
  - Funciona automaticamente com novos IPs (usa queries dinâmicas)

#### Mantido
- ✅ `docker-containers-dashboard.json`
  - Continua funcional para monitorizar LXC 201 (immich)

#### Criado Novo
- ✅ `proxmox-cluster-dashboard.json`
  - Dashboard específico para métricas do Proxmox VE Exporter
  - Painéis: Nodes online, Total VMs/LXCs, CPU/Memory por guest, Inventário
  - UID: `proxmox-cluster`

### 3. Scripts

#### Novo Script Criado
- ✅ **[scripts/install_proxmox_exporter.sh](scripts/install_proxmox_exporter.sh)**
  - Instala Proxmox VE Exporter no host Proxmox
  - Cria user Prometheus no Proxmox
  - Configura serviço systemd
  - Porta 9221

#### Script Principal Atualizado
- ✅ **[scripts/deploy_monitor.py](scripts/deploy_monitor.py)**
  - **Nova função**: `detect_proxmox_guest(ip)` (linhas 43-89)
    - Deteta se é LXC, VM ou Proxmox host
    - Extrai VMID/hostname
    - Mostra ícones diferentes (📦 LXC, 🖥️ VM, 🏢 Host)

  - **Relatório melhorado** (linhas 877-897)
    - Mostra tipo de Proxmox guest no output
    - Adiciona informação de VMID/nome ao relatório

  - **service_status atualizado** (linhas 757-764)
    - Adiciona campos `proxmox_type` e `proxmox_id`

### 4. Documentação

#### Criada
- ✅ **[PROXMOX_INVENTORY.md](PROXMOX_INVENTORY.md)**
  - Inventário completo do ambiente Proxmox
  - Lista todos os LXCs/VMs com specs
  - Estratégia de monitorização

- ✅ **[PROXMOX_SETUP_GUIDE.md](PROXMOX_SETUP_GUIDE.md)**
  - Guia completo de setup (6500+ palavras)
  - Quick start, arquitetura, troubleshooting
  - Exemplos práticos de comandos

- ✅ **[DEPLOYMENT_IMPROVEMENTS.md](DEPLOYMENT_IMPROVEMENTS.md)** (já existia)
  - Documentação das melhorias feitas anteriormente

## 🎯 Arquitetura Final

```
Proxmox Host (192.168.90.104)
├── Node Exporter (:9100)
├── Proxmox VE Exporter (:9221)  ← Novo
└── cAdvisor (:9991) [se tiver Docker local]

VMs (2)
├── VM 100 - OPNsense (192.168.90.105)
│   └── Node Exporter (:9100)
└── VM 101 - Zorin18 (10.10.1.156)
    └── Node Exporter (:9100)

LXCs (7)
├── LXC 200 - adguard (192.168.90.106)
│   └── Node Exporter (:9100)
├── LXC 201 - immich (10.10.1.152)
│   ├── Node Exporter (:9100)
│   └── cAdvisor (:9991)  ← Para containers Docker
├── LXC 202 - n8n (10.10.1.172)
│   └── Node Exporter (:9100)
├── LXC 203 - zabbix (10.10.1.116)
│   └── Node Exporter (:9100)
├── LXC 204 - passbolt (10.10.1.183)
│   └── Node Exporter (:9100)
├── LXC 205 - monit (10.10.1.148)
│   └── Node Exporter (:9100)
└── LXC 206 - ollama (10.10.1.117)
    └── Node Exporter (:9100)

           ↓ (scrape métricas)

    Prometheus (:9990)
    ├── Job: monitoring_stack (serviços locais)
    ├── Job: remote_hosts (Node Exporter)
    ├── Job: remote_docker (cAdvisor)
    └── Job: proxmox (Proxmox VE Exporter)  ← Novo

           ↓ (query métricas)

      Grafana (:3000)
      ├── Proxmox Cluster Overview  ← Novo
      ├── Proxmox Hosts Overview (renomeado)
      └── Docker Containers Overview
```

## 💡 Sugestões de Melhorias

### 1. Melhorias de Curto Prazo (Imediatas)

#### A) Adicionar Descoberta Automática via Proxmox API
**Problema**: Atualmente, precisa adicionar IPs manualmente no `hosts.txt`

**Solução**: Criar script que usa Proxmox API para descobrir automaticamente LXCs/VMs

```python
# scripts/sync_proxmox_hosts.py
"""
- Conecta à API do Proxmox
- Lista todos os LXCs/VMs running
- Extrai IPs de cada guest
- Atualiza automaticamente hosts.txt e targets.json
- Pode ser executado via cron (ex: de hora em hora)
"""
```

**Benefícios**:
- Zero manutenção manual ao adicionar/remover VMs
- Sempre sincronizado com o estado real do Proxmox
- Menos erros humanos

**Complexidade**: Média (2-3 horas implementação)

#### B) Adicionar Health Checks no docker-compose
**Problema**: Não há health checks nos containers

**Solução**: Adicionar health checks ao [docker-compose.yml](docker-compose.yml)

```yaml
services:
  prometheus:
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  grafana:
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Benefícios**:
- `docker-compose ps` mostra estado real de saúde
- Restart automático de containers não saudáveis

**Complexidade**: Baixa (30 minutos)

#### C) Adicionar Alertas Básicas
**Problema**: Sem alertas configurados

**Solução**: Criar ficheiros de alertas básicos em `prometheus/alerts/`

```yaml
# prometheus/alerts/basic.yml
groups:
  - name: basic
    interval: 1m
    rules:
      # Host down
      - alert: HostDown
        expr: up{job="remote_hosts"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Host {{ $labels.instance }} is down"

      # High CPU
      - alert: HighCPU
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU on {{ $labels.instance }}"

      # High Memory
      - alert: HighMemory
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"

      # Disk almost full
      - alert: DiskAlmostFull
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk almost full on {{ $labels.instance }}"

      # VM/LXC stopped
      - alert: ProxmoxGuestStopped
        expr: pve_guest_info{status="stopped"} == 1
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "Proxmox guest {{ $labels.name }} ({{ $labels.id }}) is stopped"
```

**Benefícios**:
- Notificação proativa de problemas
- Reduz downtime

**Complexidade**: Baixa (1 hora)

### 2. Melhorias de Médio Prazo (1-2 semanas)

#### D) Integração com Proxmox Backup Server
**Problema**: Sem visibilidade do estado de backups

**Solução**:
1. Instalar Proxmox Backup Server Exporter
2. Adicionar dashboard para monitorizar backups
3. Alertas para backups falhados

**Benefícios**:
- Garantir integridade de backups
- Histórico de backups

**Complexidade**: Média

#### E) Logging Centralizado (Loki)
**Problema**: Loki está no stack mas não configurado para coletar logs

**Solução**:
1. Instalar Alloy em cada LXC/VM
2. Configurar shipping de logs para Loki
3. Criar dashboards de logs no Grafana

**Benefícios**:
- Logs centralizados de todos os LXCs/VMs
- Correlação de métricas com logs
- Pesquisa rápida de erros

**Complexidade**: Média-Alta

#### F) Métricas de Aplicação
**Problema**: Apenas métricas de infraestrutura, sem métricas de aplicação

**Solução**: Instrumentar aplicações críticas (immich, n8n, etc.)

**Benefícios**:
- Métricas específicas de negócio
- Debug de problemas de aplicação

**Complexidade**: Varia por aplicação

### 3. Melhorias de Longo Prazo (1+ mês)

#### G) High Availability
**Problema**: Single point of failure no stack de monitorização

**Solução**:
- Prometheus HA (2+ instâncias)
- Grafana HA
- Shared storage (NFS, Ceph)

**Complexidade**: Alta

#### H) Long-term Storage (Thanos/Victoria Metrics)
**Problema**: Retenção limitada do Prometheus (15-30 dias)

**Solução**: Integrar Thanos ou Victoria Metrics para retenção de longo prazo

**Complexidade**: Alta

#### I) Métricas de Rede Avançadas
**Problema**: Métricas básicas de rede

**Solução**:
- SNMP Exporter para switches
- Integração com OPNsense para métricas de firewall
- Flow monitoring (NetFlow/sFlow)

**Complexidade**: Alta

## 🔧 Validações Necessárias

Antes de usar em produção, execute estes testes:

### 1. Teste de Conectividade
```bash
# Testar SSH para todos os hosts
for ip in $(grep -v '^#' hosts.txt | grep -v '^$' | awk '{print $1}'); do
    echo "Testing $ip..."
    ssh -o ConnectTimeout=5 root@$ip "echo OK" || echo "FAILED: $ip"
done
```

### 2. Teste de Deploy
```bash
# Deploy em modo dry-run (se implementar)
python3 scripts/deploy_monitor.py --dry-run

# Deploy real
python3 scripts/deploy_monitor.py
```

### 3. Teste de Scraping
```bash
# Verificar todos os targets
python3 scripts/verify_prometheus_targets.py

# Deve mostrar todos os 10 hosts UP
```

### 4. Teste de Dashboards
```bash
# Aceder aos dashboards
xdg-open http://localhost:3000

# Verificar:
# 1. Proxmox Cluster Overview mostra VMs/LXCs
# 2. Proxmox Hosts Overview mostra métricas de todos os hosts
# 3. Docker Containers mostra containers do immich
```

### 5. Teste de Alertas (após configurar)
```bash
# Simular host down
ssh root@192.168.90.106 'systemctl stop node_exporter'

# Aguardar 2 minutos, verificar alerta no Prometheus
curl http://localhost:9990/api/v1/alerts

# Restaurar
ssh root@192.168.90.106 'systemctl start node_exporter'
```

## 📋 Checklist de Deploy

- [ ] 1. Clonar repositório no servidor
- [ ] 2. Configurar acesso SSH passwordless para todos os hosts
- [ ] 3. Subir stack Docker (`docker-compose up -d`)
- [ ] 4. Instalar Proxmox VE Exporter no host Proxmox
- [ ] 5. Configurar token API do Proxmox
- [ ] 6. Executar deploy de exporters (`python3 scripts/deploy_monitor.py`)
- [ ] 7. Verificar targets no Prometheus (http://localhost:9990/targets)
- [ ] 8. Aceder ao Grafana (http://localhost:3000)
- [ ] 9. Verificar dashboards aparecem com dados
- [ ] 10. Configurar alertas básicas
- [ ] 11. Configurar Alertmanager para notificações
- [ ] 12. Agendar backups de configurações
- [ ] 13. Documentar password do Grafana
- [ ] 14. (Opcional) Configurar SSL/TLS
- [ ] 15. (Opcional) Configurar autenticação adicional

## 🚀 Comandos Rápidos de Referência

```bash
# Stack management
docker-compose up -d          # Iniciar stack
docker-compose down           # Parar stack
docker-compose restart        # Reiniciar stack
docker-compose logs -f        # Ver logs

# Deployment
python3 scripts/deploy_monitor.py                    # Deploy completo
python3 scripts/deploy_monitor.py --setup-keys       # Setup SSH + deploy
python3 scripts/deploy_monitor.py --skip-health-check # Deploy sem validação

# Diagnostics
python3 scripts/verify_prometheus_targets.py          # Ver targets
python3 scripts/diagnose_monitoring.py <IP>           # Diagnosticar host
python3 scripts/diagnose_monitoring.py <IP> --fix     # Auto-fix host
python3 scripts/check_health.py                       # Health check geral

# Proxmox
./scripts/install_proxmox_exporter.sh 192.168.90.104  # Instalar exporter
ssh root@192.168.90.104 'systemctl status prometheus-pve-exporter'
curl http://192.168.90.104:9221/metrics | head -20   # Testar métricas

# Backup
tar -czf backup_$(date +%Y%m%d).tar.gz hosts.txt prometheus/ grafana/
```

## 📊 Métricas Chave a Monitorizar

### Por Host (Node Exporter)
- **CPU**: `node_cpu_seconds_total`
- **Memory**: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
- **Disk**: `node_filesystem_avail_bytes / node_filesystem_size_bytes`
- **Network**: `rate(node_network_receive_bytes_total[5m])`
- **Load**: `node_load1`, `node_load5`, `node_load15`

### Proxmox (Proxmox VE Exporter)
- **Guests**: `pve_guest_info`
- **CPU por guest**: `pve_cpu_usage_ratio`
- **Memory por guest**: `pve_mem_usage_ratio`
- **Disk por guest**: `pve_disk_usage_bytes`
- **Status**: `pve_guest_info{status="running"}`

### Docker (cAdvisor)
- **Containers**: `container_last_seen`
- **CPU**: `rate(container_cpu_usage_seconds_total[5m])`
- **Memory**: `container_memory_usage_bytes`
- **Network**: `rate(container_network_receive_bytes_total[5m])`

## ✅ Validação Final

A migração está completa quando:

1. ✅ Todos os 10 hosts aparecem UP no Prometheus
2. ✅ Proxmox VE Exporter mostra métricas de VMs/LXCs
3. ✅ Grafana mostra 3 dashboards funcionais
4. ✅ cAdvisor monitoriza containers do immich
5. ✅ Scripts de deploy/diagnóstico funcionam
6. ✅ Documentação completa disponível

## 🎉 Conclusão

O projeto foi completamente adaptado para o ambiente Proxmox com:
- ✅ 10 hosts configurados (1 Proxmox host + 2 VMs + 7 LXCs)
- ✅ 4 tipos de exporters (Node, cAdvisor, Proxmox VE, stack local)
- ✅ 3 dashboards Grafana otimizados
- ✅ Scripts de deployment e diagnóstico atualizados
- ✅ Documentação completa (setup guide + inventário)
- ✅ Detecção automática de tipo de guest (LXC/VM/Host)

**Status**: Pronto para produção com as validações acima ✅
