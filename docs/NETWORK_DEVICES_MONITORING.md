# Monitorização de Dispositivos de Rede

## 📱 Tipos de Dispositivos e Métodos de Monitorização

### ✅ Facilmente Monitorizáveis

#### 1. **Servidores Linux/Windows**

- **Método**: Node Exporter (Linux) / WMI Exporter (Windows)
- **Métricas**: CPU, RAM, disco, rede, processos
- **Setup**: Já implementado com `deploy_monitor.py`

#### 2. **Containers Docker**

- **Método**: cAdvisor
- **Métricas**: CPU, RAM, rede por container
- **Setup**: Já implementado

#### 3. **Proxmox VMs/LXCs**

- **Método**: Proxmox VE Exporter + Node Exporter em cada VM/LXC
- **Métricas**: Estado, recursos, storage
- **Setup**: Em implementação

#### 4. **Routers/Switches (OPNsense, pfSense, etc.)**

- **Método**: SNMP Exporter
- **Métricas**: Tráfego de rede, CPU, interfaces
- **Setup**: Requer configuração SNMP

#### 5. **Câmaras IP**

- **Método**: SNMP Exporter ou Blackbox Exporter
- **Métricas**: Disponibilidade, uptime, tráfego
- **Setup**: Depende do modelo

### ⚠️ Parcialmente Monitorizáveis

#### 6. **Smartphones/Tablets**

- **Método**: Ping monitoring (Blackbox Exporter)
- **Métricas**: Apenas disponibilidade (online/offline)
- **Limitação**: Sem métricas de CPU/RAM (iOS/Android não expõem)

#### 7. **Smart TVs/IoT Devices**

- **Método**: Ping + SNMP (se suportado)
- **Métricas**: Disponibilidade, consumo de rede
- **Limitação**: Maioria não tem SNMP

#### 8. **PCs Desktop (sem agente)**

- **Método**: Ping monitoring
- **Métricas**: Apenas disponibilidade
- **Alternativa**: Instalar Node Exporter para métricas completas

### ❌ Difícil/Impossível

- **Dispositivos Bluetooth** (sem IP)
- **Dispositivos sem rede** (offline)

---

## 🚀 Implementação por Tipo

### Opção 1: Monitorização Básica (Ping - Todos os Dispositivos)

**O que monitoriza**: Disponibilidade (online/offline)

```bash
# Adicionar ao Prometheus
cat >> prometheus/prometheus.yml << 'EOF'

  # Blackbox Exporter - Ping monitoring
  - job_name: 'blackbox_ping'
    metrics_path: /probe
    params:
      module: [icmp]
    static_configs:
      - targets:
          - 10.10.1.100  # Smartphone
          - 10.10.1.101  # PC Desktop
          - 10.10.1.102  # Câmara IP
          - 10.10.1.103  # Smart TV
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
EOF
```

**Adicionar Blackbox Exporter ao docker-compose.yml:**

```yaml
blackbox-exporter:
  image: prom/blackbox-exporter:latest
  container_name: blackbox-exporter
  ports:
    - "9115:9115"
  volumes:
    - ./blackbox/blackbox.yml:/etc/blackbox/blackbox.yml
  command:
    - "--config.file=/etc/blackbox/blackbox.yml"
  restart: unless-stopped
  networks:
    - monitoring
```

### Opção 2: Monitorização Avançada (SNMP - Routers/Switches/Câmaras)

**Para dispositivos com SNMP (OPNsense, câmaras IP profissionais):**

```yaml
snmp-exporter:
  image: prom/snmp-exporter:latest
  container_name: snmp-exporter
  ports:
    - "9116:9116"
  volumes:
    - ./snmp/snmp.yml:/etc/snmp_exporter/snmp.yml
  restart: unless-stopped
  networks:
    - monitoring
```

**Configurar SNMP no OPNsense:**

1. Services → SNMP → Enable
2. Community: `public` (ou criar custom)
3. Adicionar ao Prometheus

### Opção 3: Monitorização de Rede (NetFlow - Tráfego Detalhado)

**Para análise de tráfego de TODOS os dispositivos:**

```yaml
# NetFlow collector
goflow:
  image: cloudflare/goflow:latest
  container_name: goflow
  ports:
    - "2055:2055/udp" # NetFlow
    - "6343:6343/udp" # sFlow
  networks:
    - monitoring
```

**Configurar no OPNsense:**

- Reporting → NetFlow → Enable
- Destination: 10.10.1.159:2055

---

## 📊 Dashboards Recomendados

### Dashboard 1: Network Overview

- **Dispositivos online/offline** (todos)
- **Latência** (ping)
- **Uptime**

### Dashboard 2: SNMP Devices

- **Tráfego de rede** por interface
- **CPU/RAM** (routers/switches)
- **Status de portas**

### Dashboard 3: NetFlow Analysis

- **Top talkers** (quem usa mais banda)
- **Protocolos** (HTTP, HTTPS, DNS, etc.)
- **Tráfego por dispositivo**

---

## 🎯 Recomendação para o Teu Caso

### Setup Inicial (Simples)

1. **Blackbox Exporter** - Ping monitoring
   - Monitorizar disponibilidade de TODOS os dispositivos
   - Smartphones, PCs, câmaras, IoT

2. **SNMP no OPNsense**
   - Tráfego total da rede
   - Dispositivos conectados
   - Bandwidth por interface

### Setup Avançado (Opcional)

3. **NetFlow no OPNsense**
   - Análise detalhada de tráfego
   - Top consumers
   - Análise de protocolos

4. **SNMP em Câmaras IP** (se suportarem)
   - Status individual
   - Uptime
   - Tráfego

---

## 🛠️ Implementação Rápida

Queres que implemente alguma destas opções? Posso criar:

1. **Blackbox Exporter** para ping monitoring (mais simples)
2. **SNMP Exporter** para OPNsense + câmaras
3. **NetFlow** para análise de tráfego detalhada
4. **Combinação** de todas

**Qual preferes?**

---

## 📋 Exemplo de Métricas por Tipo

| Dispositivo        | Disponibilidade | CPU/RAM               | Tráfego      | Detalhes                    |
| ------------------ | --------------- | --------------------- | ------------ | --------------------------- |
| **Servidor Linux** | ✅              | ✅                    | ✅           | Métricas completas          |
| **VM Proxmox**     | ✅              | ✅                    | ✅           | Via Proxmox + Node Exporter |
| **OPNsense**       | ✅              | ✅ (SNMP)             | ✅ (NetFlow) | Router/Firewall             |
| **Câmara IP**      | ✅              | ⚠️ (SNMP se suportar) | ✅ (NetFlow) | Depende do modelo           |
| **Smartphone**     | ✅ (ping)       | ❌                    | ✅ (NetFlow) | Apenas disponibilidade      |
| **PC Desktop**     | ✅ (ping)       | ✅ (com agente)       | ✅ (NetFlow) | Instalar Node Exporter      |
| **Smart TV**       | ✅ (ping)       | ❌                    | ✅ (NetFlow) | Apenas disponibilidade      |
| **IoT Device**     | ✅ (ping)       | ⚠️ (SNMP raro)        | ✅ (NetFlow) | Limitado                    |

---

**Resumo**: Sim, podes monitorizar todos os dispositivos, mas o nível de detalhe varia. Para máximo de informação, recomendo:

1. **Blackbox Exporter** (ping) - TODOS os dispositivos
2. **SNMP** - OPNsense + câmaras (se suportarem)
3. **NetFlow** - Análise de tráfego de TODOS

Queres que implemente alguma destas soluções?
