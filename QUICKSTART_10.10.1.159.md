# Quick Start - Deployment em 10.10.1.159

Guia rápido para copiar e iniciar a stack na máquina de monitorização.

## 📦 Passo 1: Copiar Stack para 10.10.1.159

**Na tua máquina local:**

```bash
# Comprimir o projeto (excluindo .git e dados)
cd /home/luismelo/Documents/GitHub
tar --exclude='observability-stack/.git' \
    --exclude='observability-stack/prometheus_data' \
    --exclude='observability-stack/grafana_data' \
    --exclude='observability-stack/loki_data' \
    -czf observability-stack.tar.gz observability-stack/

# Copiar para a máquina de monitorização
scp observability-stack.tar.gz root@10.10.1.159:/root/

# SSH para a máquina
ssh root@10.10.1.159
```

**Na máquina 10.10.1.159:**

```bash
# Extrair
cd /root
tar -xzf observability-stack.tar.gz
cd observability-stack

# Dar permissões de execução aos scripts
chmod +x setup.sh diagnose.sh scripts/*.sh scripts/*.py
```

## 🔍 Passo 2: Verificar Rede e Conectividade

```bash
# Executar script de verificação de rede
bash scripts/verify_network.sh
```

**Se encontrares problemas de conectividade:**

### Configurar Firewall no OPNsense

1. Aceder ao OPNsense: http://10.10.1.1 ou https://192.168.90.105
2. Ir para **Firewall → Rules → LAN**
3. Adicionar nova regra:
   - **Action**: Pass
   - **Interface**: LAN
   - **Protocol**: TCP
   - **Source**: 10.10.1.159 (single host)
   - **Destination**: 192.168.90.104 (single host)
   - **Destination Port Range**: Custom → 22, 9100, 9221
   - **Description**: "Monitoring Stack to Proxmox"
4. Clicar **Save** e **Apply Changes**

## 🔑 Passo 3: Configurar SSH

```bash
# Gerar chave SSH (se não existir)
ssh-keygen -t rsa -b 4096

# Distribuir para todos os hosts
python3 scripts/setup_ssh_key.py --all

# Testar acesso ao Proxmox
ssh root@192.168.90.104 'echo "SSH OK"'
```

## 🚀 Passo 4: Iniciar Stack

```bash
# Executar setup
./setup.sh

# Verificar containers
docker compose ps
```

**Todos os containers devem estar "Up".**

## 📊 Passo 5: Instalar Exporters

### No Proxmox Host

```bash
# Instalar Proxmox VE Exporter
./scripts/install_proxmox_exporter.sh 192.168.90.104
```

**Seguir instruções para configurar API token.**

### Em Todos os Hosts

```bash
# Deploy automático
python3 scripts/deploy_monitor.py
```

## ✅ Passo 6: Verificar

```bash
# Health check
python3 scripts/check_health.py

# Aceder ao Grafana
# Browser: http://10.10.1.159:3000
# Login: admin / admin
```

## 🔧 Adicionar Mais Hosts

**Editar `hosts.txt`:**

```bash
nano hosts.txt
```

**Adicionar novos IPs:**

```text
# Novos LXCs
10.10.1.200
10.10.1.201

# Novas VMs
10.10.1.210
```

**Re-executar deployment:**

```bash
python3 scripts/deploy_monitor.py
```

**Aguardar 15-30 segundos** - Prometheus deteta automaticamente os novos targets.

## 🆘 Troubleshooting Rápido

### Container não inicia

```bash
docker logs <container_name>
docker compose restart <container_name>
```

### Target "down" no Prometheus

```bash
# Diagnosticar host específico
python3 scripts/diagnose_monitoring.py <IP_DO_HOST>

# Auto-fix
python3 scripts/diagnose_monitoring.py <IP_DO_HOST> --fix
```

### Sem conectividade ao Proxmox (192.168.90.104)

```bash
# Testar ping
ping -c 3 192.168.90.104

# Testar porta
nc -zv 192.168.90.104 9100

# Se falhar: verificar firewall OPNsense
```

## 📚 Documentação Completa

- [DEPLOYMENT_GUIDE_10.10.1.159.md](DEPLOYMENT_GUIDE_10.10.1.159.md) - Guia detalhado
- [README.md](README.md) - Documentação geral
- [PROXMOX_SETUP_GUIDE.md](PROXMOX_SETUP_GUIDE.md) - Setup Proxmox específico
