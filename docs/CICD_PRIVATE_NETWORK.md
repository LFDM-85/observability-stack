# CI/CD para Rede Privada (10.10.1.159)

## ⚠️ Problema: GitHub Actions Não Acede a Redes Privadas

O GitHub Actions corre em servidores da GitHub na cloud, que **não têm acesso** à tua rede local (10.10.1.x).

**Erro:**

```
ssh: connect to host 10.10.1.159 port 22: Connection timed out
```

## 🔧 Soluções

### Opção 1: Pull-Based Deployment (Recomendado - Simples)

O servidor **10.10.1.159** faz pull do código do GitHub periodicamente.

#### Setup

**1. No servidor 10.10.1.159:**

```bash
# SSH para o servidor
ssh root@10.10.1.159

# Clonar repositório
cd /root
git clone https://github.com/YOUR_USERNAME/observability-stack.git
cd observability-stack

# Configurar ficheiros
cp .env.example .env
nano .env  # Adicionar webhooks

cp hosts.txt.example hosts.txt
nano hosts.txt  # Adicionar IPs

# Testar deployment manual
bash scripts/auto_deploy.sh
```

**2. Configurar Cron para Auto-Update:**

```bash
# Editar crontab
crontab -e

# Adicionar linha para verificar updates a cada 5 minutos
*/5 * * * * cd /root/observability-stack && bash scripts/auto_deploy.sh >> /var/log/auto-deploy.log 2>&1
```

**Ou executar manualmente quando quiseres fazer deploy:**

```bash
ssh root@10.10.1.159 'cd /root/observability-stack && bash scripts/auto_deploy.sh'
```

#### Workflow

```bash
# Na tua máquina local
git add .
git commit -m "feat: add new dashboard"
git push origin main

# No servidor (automático via cron ou manual)
ssh root@10.10.1.159 'cd /root/observability-stack && bash scripts/auto_deploy.sh'
```

---

### Opção 2: Self-Hosted GitHub Runner (Avançado)

Instalar um GitHub Actions runner **na tua rede local** que tenha acesso ao 10.10.1.159.

#### Setup

**1. Criar Runner no GitHub:**

1. Ir para: `https://github.com/YOUR_USERNAME/observability-stack/settings/actions/runners`
2. Clicar em **New self-hosted runner**
3. Escolher **Linux**
4. Copiar comandos de instalação

**2. Instalar Runner (numa máquina na rede 10.10.1.x):**

```bash
# Exemplo: instalar na própria máquina 10.10.1.159 ou noutra na mesma rede
ssh root@10.10.1.159

# Criar diretório para runner
mkdir -p /opt/actions-runner && cd /opt/actions-runner

# Download (seguir instruções do GitHub)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configurar
./config.sh --url https://github.com/YOUR_USERNAME/observability-stack --token YOUR_TOKEN

# Instalar como serviço
sudo ./svc.sh install
sudo ./svc.sh start
```

**3. Atualizar Workflow:**

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: self-hosted # Em vez de ubuntu-latest
```

---

### Opção 3: Webhook + Script Local

Configurar webhook do GitHub para notificar o servidor quando há push.

#### Setup

**1. No servidor 10.10.1.159:**

```bash
# Instalar webhook listener
apt install -y webhook

# Criar script de deployment
cat > /opt/deploy-webhook.sh << 'EOF'
#!/bin/bash
cd /root/observability-stack
bash scripts/auto_deploy.sh
EOF

chmod +x /opt/deploy-webhook.sh

# Configurar webhook
cat > /etc/webhook.conf << 'EOF'
[
  {
    "id": "deploy-observability",
    "execute-command": "/opt/deploy-webhook.sh",
    "command-working-directory": "/root/observability-stack",
    "response-message": "Deployment triggered"
  }
]
EOF

# Iniciar webhook listener
webhook -hooks /etc/webhook.conf -port 9000 -verbose
```

**2. No GitHub:**

1. Ir para: `Settings → Webhooks → Add webhook`
2. Payload URL: `http://SEU_IP_PUBLICO:9000/hooks/deploy-observability`
3. Content type: `application/json`
4. Events: `Just the push event`

---

## 📊 Comparação de Soluções

| Solução                | Complexidade | Automação   | Segurança   | Recomendado          |
| ---------------------- | ------------ | ----------- | ----------- | -------------------- |
| **Pull-Based (Cron)**  | ⭐ Baixa     | ⭐⭐ Média  | ⭐⭐⭐ Alta | ✅ Sim (simples)     |
| **Self-Hosted Runner** | ⭐⭐⭐ Alta  | ⭐⭐⭐ Alta | ⭐⭐ Média  | ✅ Sim (avançado)    |
| **Webhook**            | ⭐⭐ Média   | ⭐⭐⭐ Alta | ⭐ Baixa    | ⚠️ Requer IP público |

---

## 🚀 Recomendação

Para o teu caso, recomendo **Opção 1 (Pull-Based)**:

### Setup Rápido

```bash
# 1. SSH para servidor
ssh root@10.10.1.159

# 2. Clonar repo
cd /root
git clone https://github.com/YOUR_USERNAME/observability-stack.git
cd observability-stack

# 3. Configurar
cp .env.example .env && nano .env
cp hosts.txt.example hosts.txt && nano hosts.txt

# 4. Primeiro deployment
bash scripts/auto_deploy.sh

# 5. Configurar auto-update (opcional)
echo "*/10 * * * * cd /root/observability-stack && bash scripts/auto_deploy.sh >> /var/log/auto-deploy.log 2>&1" | crontab -
```

### Workflow de Desenvolvimento

```bash
# Na tua máquina
git add .
git commit -m "feat: new feature"
git push origin main

# Deployment automático (via cron) ou manual
ssh root@10.10.1.159 'cd /root/observability-stack && bash scripts/auto_deploy.sh'
```

---

## 🔧 Troubleshooting

### Deployment Manual Falha

```bash
# Ver logs
ssh root@10.10.1.159
tail -f /var/log/auto-deploy.log

# Executar manualmente para debug
cd /root/observability-stack
bash -x scripts/auto_deploy.sh
```

### Git Pull Falha

```bash
# Reset para estado limpo
cd /root/observability-stack
git reset --hard origin/main
git pull
```

---

## 📚 Próximos Passos

1. ✅ Escolher solução (recomendo Pull-Based)
2. ✅ Fazer setup no servidor
3. ✅ Testar deployment manual
4. ✅ Configurar cron (opcional)
5. ✅ Fazer push e verificar auto-deployment
