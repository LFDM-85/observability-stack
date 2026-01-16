# Inventário Proxmox - 192.168.90.104

## Host Proxmox
- **IP**: 192.168.90.104
- **Node**: pve
- **Monitorização**: Node Exporter + Proxmox Exporter

## Virtual Machines (QEMU/KVM)

### VM 100 - OPNsense-Firewall
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 4 vCPUs (uso: 1.77%)
- **RAM**: 4 GB (4.3 GB em uso)
- **IP**: _Aguardando configuração manual_
- **Função**: Firewall/Gateway
- **Monitorização**: Node Exporter (se suportado)

### VM 101 - Zorin18
- **Status**: Running (uptime: 8.2 dias)
- **CPU**: 4 vCPUs (uso: 0.16%)
- **RAM**: 16 GB (2.6 GB em uso)
- **Disco**: 320 GB
- **IP**: _Aguardando configuração manual_
- **Tags**: Linux, Testing
- **Função**: Desktop Linux para testes
- **Monitorização**: Node Exporter + Docker (se instalado)

## LXC Containers

### LXC 200 - adguard
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 2 vCPUs (uso: 0.04%)
- **RAM**: 2 GB (432 MB em uso)
- **Disco**: 10 GB (987 MB usado)
- **IP**: 192.168.90.106
- **Tags**: adblock, community-script
- **Função**: DNS AdGuard
- **Monitorização**: Node Exporter

### LXC 201 - immich
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 4 vCPUs (uso: 0.11%)
- **RAM**: 4 GB (722 MB em uso)
- **Disco**: 1 TB (9.7 GB usado)
- **IP**: 10.10.1.152
- **Tags**: community-script, photos
- **Função**: Gestão de fotos
- **Monitorização**: Node Exporter + Docker (containers)

### LXC 202 - n8n
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 2 vCPUs (uso: 0.01%)
- **RAM**: 4 GB (426 MB em uso)
- **Disco**: 31 GB (6.1 GB usado)
- **IP**: 10.10.1.172
- **Tags**: automation, community-script
- **Função**: Automação/Workflows
- **Monitorização**: Node Exporter + Docker (se aplicável)

### LXC 203 - zabbix
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 4 vCPUs (uso: 0.17%)
- **RAM**: 4 GB (261 MB em uso)
- **Disco**: 20 GB (2.1 GB usado)
- **IP**: 10.10.1.116
- **Tags**: community-script, monitoring
- **Função**: Sistema de monitorização Zabbix
- **Monitorização**: Node Exporter

### LXC 204 - passbolt
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 2 vCPUs (uso: 0.36%)
- **RAM**: 2 GB (336 MB em uso)
- **Disco**: 12 GB (4.4 GB usado)
- **IP**: 10.10.1.183
- **Tags**: passbolt
- **Função**: Gestor de passwords
- **Monitorização**: Node Exporter

### LXC 205 - monit
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 4 vCPUs (uso: 0.37%)
- **RAM**: 8 GB (711 MB em uso)
- **Disco**: 263 GB (10.2 GB usado)
- **IP**: 10.10.1.148
- **Tags**: monit
- **Função**: Sistema de monitorização atual
- **Monitorização**: Node Exporter
- **Nota**: Este LXC parece ser o sistema de monitorização existente

### LXC 206 - ollama
- **Status**: Running (uptime: 8.3 dias)
- **CPU**: 5 vCPUs (uso: 0%)
- **RAM**: 10 GB (60 MB em uso)
- **Disco**: 52 GB (738 MB usado)
- **IP**: 10.10.1.117
- **Tags**: ai
- **Função**: LLM/AI (Ollama)
- **Monitorização**: Node Exporter

## Resumo de Rede

### Rede 192.168.90.x (Rede Principal)
- 192.168.90.104 - Host Proxmox
- 192.168.90.106 - LXC 200 (adguard)
- 192.168.90.x - VM 100 (OPNsense) - _IP a confirmar_
- 192.168.90.x - VM 101 (Zorin18) - _IP a confirmar_

### Rede 10.10.1.x (Rede Interna)
- 10.10.1.116 - LXC 203 (zabbix)
- 10.10.1.117 - LXC 206 (ollama)
- 10.10.1.148 - LXC 205 (monit)
- 10.10.1.152 - LXC 201 (immich)
- 10.10.1.172 - LXC 202 (n8n)
- 10.10.1.183 - LXC 204 (passbolt)

## Estratégia de Monitorização

### 1. Host Proxmox (192.168.90.104)
- Node Exporter (porta 9100) - Métricas do host
- Proxmox VE Exporter (porta 9221) - Métricas específicas Proxmox
- cAdvisor (porta 9991) - Se usar Docker no host

### 2. LXC Containers
- Node Exporter em cada LXC
- cAdvisor apenas nos LXCs com Docker (201-immich, possivelmente 202-n8n)

### 3. Virtual Machines
- Node Exporter nas VMs Linux
- WMI Exporter se houver VMs Windows

### 4. Métricas Específicas Proxmox
- Status de VMs/LXCs
- Uso de storage pools
- Cluster health (se aplicável)
- Backup status
- Network traffic

## Observações

1. **LXC 205 (monit)** parece ser um sistema de monitorização existente - avaliar se substituir ou integrar
2. **LXC 203 (zabbix)** também é monitorização - pode coexistir com Prometheus/Grafana
3. **LXC 201 (immich)** com 1TB de disco - provavelmente usa Docker internamente
4. **VM 100 (OPNsense)** - sendo firewall, pode ter limitações para instalar exporters
5. Duas redes distintas (192.168.90.x e 10.10.1.x) - garantir conectividade

## Próximos Passos

1. ✅ Confirmar IPs das VMs 100 e 101
2. ⏳ Atualizar hosts.txt com todos os IPs
3. ⏳ Instalar Proxmox VE Exporter no host
4. ⏳ Deploy Node Exporter em todos LXCs/VMs
5. ⏳ Identificar LXCs com Docker e instalar cAdvisor
6. ⏳ Criar dashboards específicos para Proxmox
7. ⏳ Integrar com Proxmox API para descoberta automática
