# Troubleshooting GitHub Actions Deployment

## Erro: "Process completed with exit code 1" no Setup SSH

### Causa Provável

O secret `DEPLOY_SSH_KEY` não está configurado no GitHub ou está vazio.

### Solução

#### 1. Gerar e Configurar Chave SSH

```bash
cd /home/luismelo/Documents/GitHub/observability-stack

# Executar script de setup
bash scripts/setup_cicd.sh
```

O script irá:

- ✅ Gerar chave SSH
- ✅ Copiar para o servidor 10.10.1.159
- ✅ Testar conexão
- ✅ Mostrar a chave privada para copiar

#### 2. Adicionar Secret no GitHub

1. **Copiar a chave privada** que o script mostra (TODO o conteúdo, incluindo `-----BEGIN` e `-----END`)

2. **Ir para o repositório no GitHub:**

   ```
   https://github.com/SEU_USERNAME/observability-stack/settings/secrets/actions
   ```

3. **Clicar em "New repository secret"**

4. **Preencher:**
   - Name: `DEPLOY_SSH_KEY`
   - Secret: Colar a chave privada completa

5. **Clicar "Add secret"**

#### 3. Testar Deployment

```bash
# Fazer um commit de teste
git add .
git commit -m "test: verify CI/CD deployment"
git push origin main
```

**Verificar em:**

```
https://github.com/SEU_USERNAME/observability-stack/actions
```

---

## Erro: SSH Connection Failed

### Verificar Conectividade

```bash
# Testar SSH manualmente
ssh root@10.10.1.159 'echo "SSH OK"'
```

Se falhar:

#### Opção 1: Configurar Chave SSH no Servidor

```bash
# Copiar chave pública para servidor
ssh-copy-id -i ~/.ssh/deploy_key_github.pub root@10.10.1.159

# Testar
ssh -i ~/.ssh/deploy_key_github root@10.10.1.159 'echo "OK"'
```

#### Opção 2: Verificar Firewall

```bash
# Verificar se porta 22 está acessível
nc -zv 10.10.1.159 22
```

Se falhar, verificar firewall no servidor ou OPNsense.

---

## Erro: .env or hosts.txt Missing

### Solução

```bash
# SSH para servidor
ssh root@10.10.1.159

# Criar ficheiros de configuração
cd /root/observability-stack

# Criar .env
cp .env.example .env
nano .env  # Adicionar webhooks

# Criar hosts.txt
cp hosts.txt.example hosts.txt
nano hosts.txt  # Adicionar IPs
```

**Depois, re-executar deployment:**

- GitHub → Actions → Re-run workflow

---

## Erro: Docker Not Installed

### Solução

```bash
# SSH para servidor
ssh root@10.10.1.159

# Instalar Docker
apt update
apt install -y docker.io docker-compose

# Verificar instalação
docker --version
docker-compose --version

# Adicionar user ao grupo docker (opcional)
usermod -aG docker root
```

---

## Erro: Containers Not Starting

### Diagnóstico

```bash
# SSH para servidor
ssh root@10.10.1.159
cd /root/observability-stack

# Ver logs
docker compose logs

# Ver logs de container específico
docker compose logs prometheus
docker compose logs grafana
```

### Soluções Comuns

#### Falta de Espaço em Disco

```bash
# Verificar espaço
df -h

# Limpar containers antigos
docker system prune -a
```

#### Porta Já em Uso

```bash
# Verificar portas em uso
ss -tlnp | grep -E ':(3000|9990|9093)'

# Parar serviço conflituoso ou mudar porta no docker-compose.yml
```

---

## Verificar Deployment Manual

Se o GitHub Actions falhar, podes fazer deployment manual:

```bash
# Na tua máquina local
cd /home/luismelo/Documents/GitHub/observability-stack

# Criar package
tar --exclude='.git' --exclude='*_data' -czf stack.tar.gz .

# Copiar para servidor
scp stack.tar.gz root@10.10.1.159:/tmp/

# SSH para servidor
ssh root@10.10.1.159

# Extrair e iniciar
cd /root/observability-stack
tar -xzf /tmp/stack.tar.gz
docker compose down
docker compose up -d

# Verificar
docker compose ps
```

---

## Rollback em Caso de Falha

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

---

## Logs Detalhados do GitHub Actions

Para ver logs detalhados:

1. Ir para: `https://github.com/SEU_USERNAME/observability-stack/actions`
2. Clicar no workflow falhado
3. Clicar em cada step para expandir logs
4. Procurar por mensagens de erro (linhas com ❌)

---

## Contactar Suporte

Se o problema persistir:

1. **Copiar logs do GitHub Actions**
2. **Executar diagnóstico:**
   ```bash
   ssh root@10.10.1.159
   cd /root/observability-stack
   ./diagnose.sh
   ```
3. **Verificar conectividade:**
   ```bash
   bash scripts/verify_network.sh
   ```

---

## Checklist de Verificação

Antes de fazer deployment via CI/CD, verificar:

- [ ] Secret `DEPLOY_SSH_KEY` configurado no GitHub
- [ ] SSH funciona: `ssh root@10.10.1.159 'echo OK'`
- [ ] Docker instalado no servidor
- [ ] Ficheiro `.env` configurado no servidor
- [ ] Ficheiro `hosts.txt` configurado no servidor
- [ ] Espaço em disco suficiente (>10GB)
- [ ] Portas 3000, 9990, 9093 livres
