# Setup GitHub Authentication para Clone

## Problema

GitHub não aceita password authentication desde 2021. Precisas usar:

- **Personal Access Token (PAT)** - Recomendado para HTTPS
- **SSH Key** - Alternativa

## Solução 1: Personal Access Token (Recomendado)

### 1. Criar PAT no GitHub

1. Ir para: https://github.com/settings/tokens
2. Clicar em **Generate new token** → **Generate new token (classic)**
3. Configurar:
   - **Note**: `observability-stack-deployment`
   - **Expiration**: 90 days (ou No expiration)
   - **Scopes**: Selecionar `repo` (acesso completo a repositórios)
4. Clicar **Generate token**
5. **COPIAR O TOKEN** (só aparece uma vez!)

### 2. Clonar com PAT

```bash
# No servidor 10.10.1.159
cd /root

# Usar token como password
git clone https://LFDM-85:YOUR_TOKEN_HERE@github.com/LFDM-85/observability-stack.git

# Ou configurar credential helper para guardar token
git config --global credential.helper store
git clone https://github.com/LFDM-85/observability-stack.git
# Quando pedir username: LFDM-85
# Quando pedir password: colar o token
```

### 3. Atualizar auto_deploy.sh

```bash
cd /root/observability-stack

# Editar script para usar token
nano scripts/auto_deploy.sh

# Mudar linha:
# REPO_URL="https://github.com/YOUR_USERNAME/observability-stack.git"
# Para:
# REPO_URL="https://LFDM-85:YOUR_TOKEN@github.com/LFDM-85/observability-stack.git"
```

## Solução 2: SSH Key (Alternativa)

### 1. Gerar SSH Key no Servidor

```bash
# No servidor 10.10.1.159
ssh-keygen -t ed25519 -C "monit@10.10.1.159"

# Ver chave pública
cat ~/.ssh/id_ed25519.pub
```

### 2. Adicionar no GitHub

1. Copiar output do comando acima
2. Ir para: https://github.com/settings/keys
3. Clicar **New SSH key**
4. Title: `monit-10.10.1.159`
5. Key: Colar a chave pública
6. Clicar **Add SSH key**

### 3. Clonar com SSH

```bash
# No servidor 10.10.1.159
cd /root
git clone git@github.com:LFDM-85/observability-stack.git
```

### 4. Atualizar auto_deploy.sh

```bash
cd /root/observability-stack
nano scripts/auto_deploy.sh

# Mudar:
# REPO_URL="https://github.com/YOUR_USERNAME/observability-stack.git"
# Para:
# REPO_URL="git@github.com:LFDM-85/observability-stack.git"
```

## Quick Fix (Agora)

```bash
# No servidor 10.10.1.159

# Opção A: Criar PAT e usar
git clone https://LFDM-85:ghp_YOURTOKEN@github.com/LFDM-85/observability-stack.git /root/observability-stack

# Opção B: Usar SSH (se já tens chave configurada)
git clone git@github.com:LFDM-85/observability-stack.git /root/observability-stack

# Depois de clonar
cd /root/observability-stack
cp .env.example .env
nano .env  # Configurar webhooks
bash scripts/auto_deploy.sh
```

## Verificar Autenticação

```bash
# Testar se git funciona
git ls-remote https://github.com/LFDM-85/observability-stack.git
```
