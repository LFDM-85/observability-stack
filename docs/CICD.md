# CI/CD com GitHub Actions

Este projeto utiliza GitHub Actions para automatizar o deployment da stack de observabilidade para o servidor de monitorização (10.10.1.159).

## 🚀 Como Funciona

### Trigger Automático

O deployment é executado automaticamente quando:

- Há push para a branch `main` ou `master`
- Execução manual via GitHub Actions UI

### Workflow

1. **Checkout** - Baixa o código do repositório
2. **Setup SSH** - Configura chave SSH para acesso ao servidor
3. **Test Connection** - Verifica conectividade SSH
4. **Create Package** - Cria tarball excluindo ficheiros desnecessários
5. **Upload** - Envia package para o servidor
6. **Backup** - Cria backup do deployment atual
7. **Extract** - Extrai novo código
8. **Verify** - Verifica ficheiros `.env` e `hosts.txt`
9. **Restart Stack** - Para, atualiza e reinicia containers Docker
10. **Health Check** - Verifica saúde da stack

## 🔐 Configuração de Secrets

### 1. Gerar Chave SSH

**Na tua máquina local:**

```bash
# Gerar chave SSH dedicada para CI/CD
ssh-keygen -t rsa -b 4096 -f ~/.ssh/deploy_key_github -C "github-actions@observability"

# Copiar chave pública para o servidor
ssh-copy-id -i ~/.ssh/deploy_key_github.pub root@10.10.1.159

# Testar acesso
ssh -i ~/.ssh/deploy_key_github root@10.10.1.159 'echo "SSH OK"'
```

### 2. Adicionar Secret no GitHub

1. Ir para o repositório no GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Clicar em **New repository secret**
4. Nome: `DEPLOY_SSH_KEY`
5. Valor: Conteúdo da chave privada

```bash
# Copiar conteúdo da chave privada
cat ~/.ssh/deploy_key_github
```

**Copiar TODO o output (incluindo `-----BEGIN` e `-----END`)** e colar no campo "Secret".

### 3. Verificar Configuração

Após adicionar o secret, fazer um commit de teste:

```bash
git add .
git commit -m "test: CI/CD deployment"
git push origin main
```

Ir para **Actions** no GitHub e verificar se o workflow executa com sucesso.

## 📋 Pré-requisitos no Servidor

O servidor **10.10.1.159** deve ter:

- ✅ Docker e Docker Compose instalados
- ✅ Python 3 (para health checks)
- ✅ Acesso SSH configurado
- ✅ Ficheiro `.env` configurado (não versionado)
- ✅ Ficheiro `hosts.txt` configurado (não versionado)

### Setup Inicial do Servidor

**Executar uma vez no servidor:**

```bash
# Instalar dependências
apt update
apt install -y docker.io docker-compose python3 python3-pip

# Criar diretório de deployment
mkdir -p /root/observability-stack

# Criar ficheiros de configuração
cd /root/observability-stack
nano .env          # Configurar webhooks
nano hosts.txt     # Adicionar IPs dos hosts
```

## 🔄 Execução Manual

Para executar o deployment manualmente:

1. Ir para **Actions** no GitHub
2. Selecionar workflow **Deploy to Monitoring Server**
3. Clicar em **Run workflow**
4. Escolher branch e environment
5. Clicar em **Run workflow**

## 🛡️ Segurança

### Ficheiros Não Versionados

Os seguintes ficheiros **NÃO** são versionados (`.gitignore`):

- `.env` - Contém webhooks sensíveis
- `hosts.txt` - Lista de IPs privados
- `*.pem`, `*.key` - Chaves SSH
- `*_data/` - Dados dos volumes Docker

### Secrets do GitHub

- ✅ Chave SSH armazenada como secret encriptado
- ✅ Nunca exposta nos logs
- ✅ Removida após cada execução

## 📊 Monitorização do Deployment

### Verificar Logs

```bash
# SSH para o servidor
ssh root@10.10.1.159

# Ver logs dos containers
cd /root/observability-stack
docker compose logs -f

# Health check manual
python3 scripts/check_health.py
```

### Aceder aos Serviços

Após deployment bem-sucedido:

- **Grafana**: http://10.10.1.159:3000
- **Prometheus**: http://10.10.1.159:9990
- **Alertmanager**: http://10.10.1.159:9093

## 🔧 Troubleshooting

### Deployment Falha

**Verificar logs no GitHub Actions:**

1. Ir para **Actions**
2. Clicar no workflow falhado
3. Expandir step que falhou

**Erros comuns:**

#### SSH Connection Failed

```bash
# Verificar chave SSH no servidor
ssh root@10.10.1.159 'cat ~/.ssh/authorized_keys'

# Verificar secret no GitHub
# Settings → Secrets → DEPLOY_SSH_KEY
```

#### Docker Not Running

```bash
# SSH para servidor
ssh root@10.10.1.159

# Verificar Docker
systemctl status docker
systemctl start docker
```

#### .env ou hosts.txt Missing

```bash
# SSH para servidor
ssh root@10.10.1.159
cd /root/observability-stack

# Criar ficheiros
cp .env.example .env
nano .env  # Configurar

cp hosts.txt.example hosts.txt
nano hosts.txt  # Adicionar IPs
```

### Rollback

Se o deployment falhar, o backup automático permite rollback:

```bash
# SSH para servidor
ssh root@10.10.1.159

# Listar backups
ls -lh /root/observability-stack-backup-*

# Restaurar backup
cd /root
rm -rf observability-stack
mv observability-stack-backup-YYYYMMDD-HHMMSS observability-stack

# Reiniciar stack
cd observability-stack
docker compose up -d
```

## 🎯 Workflow Avançado

### Deployment para Staging

Criar branch `staging` e ajustar workflow:

```yaml
on:
  push:
    branches:
      - main # Production
      - staging # Staging
```

### Notificações

Adicionar notificações Discord/Slack no final do workflow:

```yaml
- name: Notify deployment
  if: always()
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK_URL }} \
      -H "Content-Type: application/json" \
      -d '{"content": "Deployment ${{ job.status }}"}'
```

## 📚 Recursos

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSH Key Management](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
