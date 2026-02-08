# Verificação Rápida do Proxmox Exporter

## Status Atual

O user `prometheus@pve` já existe no Proxmox, o que indica que já houve uma tentativa de instalação anterior.

## Verificação Rápida

```bash
# SSH para o Proxmox host
ssh root@192.168.90.104

# Verificar se exporter está instalado
which pve_exporter

# Verificar se serviço existe
systemctl status prometheus-pve-exporter

# Verificar se está a responder
curl http://localhost:9221/metrics | head -20
```

## Cenários Possíveis

### Cenário 1: Exporter Instalado mas Não Configurado

```bash
# SSH para Proxmox
ssh root@192.168.90.104

# Verificar configuração
cat /etc/default/prometheus-pve-exporter

# Se ficheiro não existir ou estiver incompleto, criar:
cat > /etc/default/prometheus-pve-exporter << 'EOF'
PVE_USER=prometheus@pve
PVE_TOKEN_NAME=monitoring
PVE_TOKEN_VALUE=SEU_TOKEN_AQUI
PVE_VERIFY_SSL=false
EOF

# Reiniciar serviço
systemctl restart prometheus-pve-exporter
systemctl status prometheus-pve-exporter
```

### Cenário 2: Token API Não Criado

1. **Aceder Proxmox Web UI**: https://192.168.90.104:8006
2. **Datacenter → Permissions → API Tokens**
3. **Verificar se existe token** para user `prometheus@pve`
4. **Se não existir, criar:**
   - User: `prometheus@pve`
   - Token ID: `monitoring`
   - **Desmarcar** "Privilege Separation"
   - Copiar token

5. **Configurar no exporter:**

```bash
ssh root@192.168.90.104
nano /etc/default/prometheus-pve-exporter
# Adicionar PVE_TOKEN_VALUE=SEU_TOKEN
systemctl restart prometheus-pve-exporter
```

### Cenário 3: Exporter Não Instalado

```bash
# SSH para Proxmox
ssh root@192.168.90.104

# Instalar
apt update
apt install -y python3-pip
pip3 install prometheus-pve-exporter

# Criar serviço systemd
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

# Criar configuração (com token)
cat > /etc/default/prometheus-pve-exporter << 'EOF'
PVE_USER=prometheus@pve
PVE_TOKEN_NAME=monitoring
PVE_TOKEN_VALUE=SEU_TOKEN_AQUI
PVE_VERIFY_SSL=false
EOF

# Iniciar
systemctl daemon-reload
systemctl enable prometheus-pve-exporter
systemctl start prometheus-pve-exporter
systemctl status prometheus-pve-exporter
```

## Teste Final

```bash
# Do servidor de monitorização (10.10.1.159)
curl http://192.168.90.104:9221/metrics | grep pve_up

# Deve retornar:
# pve_up{node="pve"} 1
```

## Permissões do User prometheus@pve

Se o exporter estiver a correr mas sem métricas, verificar permissões:

```bash
# No Proxmox Web UI
# Datacenter → Permissions → Add → User Permission

# Path: /
# User: prometheus@pve
# Role: PVEAuditor
```

## Troubleshooting

### Erro: "Connection refused"

```bash
# Verificar se serviço está a correr
systemctl status prometheus-pve-exporter

# Ver logs
journalctl -u prometheus-pve-exporter -f
```

### Erro: "Authentication failed"

- Token API está errado ou expirado
- Criar novo token no Proxmox Web UI

### Firewall Bloqueando

```bash
# No Proxmox, verificar firewall
pve-firewall status

# Se ativo, adicionar regra para porta 9221
```

## Comando Rápido de Verificação

```bash
# Executar no servidor de monitorização
ssh root@192.168.90.104 'systemctl status prometheus-pve-exporter && curl -s http://localhost:9221/metrics | grep pve_up'
```
