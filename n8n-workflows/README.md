# Workflow n8n - Terry Homelab Mechanic

Este workflow automatiza a análise de alertas do Prometheus/Alertmanager com diagnóstico inteligente via SSH e IA.

## 📋 Workflow: terry-homelab-mechanic.json

### Fluxo Completo

```
Alertmanager → n8n-adapter → n8n Webhook
    ↓
Unificar Dados (aceita webhook ou teste manual)
    ↓
Selecionar Comando SSH (analisa alerta e escolhe comandos)
    ↓
SSH - Investigador (executa comandos no host)
    ↓
Terry (Analista Gemini) - Gemini 1.5 Flash (analisa output)
    ↓
Formatar Discord (cria embed rico)
    ↓
Enviar Discord
```

## 🚀 Como Importar para o n8n

### Passo 1: Copiar JSON

Copie todo o conteúdo do ficheiro [terry-homelab-mechanic.json](terry-homelab-mechanic.json).

### Passo 2: Importar no n8n

1. Aceda ao n8n: **http://10.10.1.172.nip.io:5678**
2. Clique em **"+ Add workflow"** (canto superior direito)
3. Clique nos **3 pontos** (menu) → **"Import from File/URL"**
4. Cole o JSON completo
5. Clique em **"Import"**

### Passo 3: Configurar Credenciais SSH

1. Clique no nó **"SSH - Investigador"**
2. Em **"Credentials"**, clique em **"Create New"**
3. Escolha **"SSH Password"** ou **"SSH Private Key"**
4. Configure:
   - **Host**: `={{ $json.target_host }}` (já configurado)
   - **Port**: `22`
   - **Username**: `root` (ou seu utilizador)
   - **Password/Private Key**: Insira as credenciais

### Passo 4: Ativar Workflow

1. Clique no **toggle "Active"** no canto superior direito (deve ficar verde)
2. O webhook ficará disponível em:
   ```
   http://10.10.1.172.nip.io:5678/webhook/homelab-alert
   ```

## 🧪 Testar o Workflow

### Teste Manual (dentro do n8n)

1. Clique no nó **"Teste Manual"**
2. Clique em **"Execute Workflow"**
3. Verifique o Discord para a mensagem do Terry

### Teste via Script (da stack observability)

```bash
cd /home/luismelo/Documents/GitHub/observability-stack
./scripts/test_n8n_integration.sh
```

## ⚙️ Personalização

### Alterar Comandos SSH

Edite o nó **"Selecionar Comando"** para adicionar ou modificar comandos SSH por categoria:

```javascript
// Exemplo: Adicionar categoria para MySQL
if (alertName.toLowerCase().includes('mysql')) {
  category = "mysql";
  sshCommand = "systemctl status mysql; tail -50 /var/log/mysql/error.log";
}
```

### Categorias Existentes

O workflow identifica automaticamente:
- **disk/filesystem** → Análise de espaço em disco
- **cpu/load** → Análise de processos e carga
- **memory/ram** → Análise de memória
- **down/service/instance** → Serviços falhados
- **docker/container** → Análise de containers
- **proxmox/vm/lxc** → Análise Proxmox
- **generic** → Diagnóstico geral

### Configurar Gemini API

O workflow usa **Gemini 1.5 Flash** (gratuito e estável, sem problemas de quota).

**Passo 1: Obter API Key**
1. Aceda a https://makersuite.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em **Create API Key**
4. Selecione um projeto Google Cloud
5. Copie a key (começa com `AIza...`)

**Passo 2: Configurar no n8n**
1. No workflow, clique no nó **"Terry (Analista Gemini)"**
2. Em **Credentials**, clique em **Create New**
3. Escolha **"Google PaLM API"** ou **"Google AI"**
4. Cole sua API Key
5. Clique em **Save**

**Nota sobre quotas**: O Gemini 1.5 Flash tem limites generosos no free tier (15 req/min, 1500 req/dia), suficiente para monitorização de homelab

### Alterar Discord Webhook

No nó **"Enviar Discord"**, altere a URL para o seu webhook do Discord.

## 🔍 Formato do Payload (Alertmanager → n8n)

O n8n-adapter transforma alertas Alertmanager para este formato:

```json
{
  "alert_name": "HostHighDiskUsage",
  "host_ip": "192.168.90.104",
  "severity": "critical",
  "message": "Filesystem / is 92% full",
  "status": "firing"
}
```

## 📊 Exemplo de Resposta no Discord

```
💾 Alerta Homelab: HostHighDiskUsage

╔══ Diagnóstico do Terry 🔧 ══╗

**1. Causa Raiz:**
O filesystem / está com 92% de utilização devido a logs antigos em /var/log.

**2. Solução:**
# Limpar logs antigos
find /var/log -name "*.gz" -mtime +30 -delete
journalctl --vacuum-time=7d

**3. Urgência:**
⚠️ Crítico - Resolver nas próximas 24h

╠═══════════════════════════════╣
🖥️ Máquina: 192.168.90.104
⚠️ Severidade: CRITICAL
📂 Categoria: disk
📝 Mensagem: Filesystem / is 92% full
╚═══════════════════════════════╝
Automated by n8n & Gemini AI | Proxmox Monitoring
```

## 🛠️ Troubleshooting

### Webhook não recebe alertas

```bash
# Verificar logs do adapter
docker logs -f n8n-adapter

# Verificar URL configurada
docker inspect n8n-adapter | grep N8N_WEBHOOK_URL
```

### SSH falha

1. Verifique se o host está acessível: `ssh root@192.168.90.104`
2. Verifique credenciais SSH no nó "SSH - Investigador"
3. Teste comandos manualmente

### Gemini API não responde

1. Verifique a API Key
2. Verifique se não excedeu o limite (15 req/min no free tier)
3. Teste manualmente:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: SUA_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}'
```

### Erro "Quota Exceeded"

**Solução**: O workflow agora usa gemini-1.5-flash (modelo estável) em vez de gemini-2.0-flash-exp (experimental com quotas limitadas)

### Discord não recebe

1. Verifique a URL do webhook no nó "Enviar Discord"
2. Teste manualmente:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content": "Test"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK
```

## 📚 Mais Informações

- **Documentação completa**: [N8N_INTEGRATION.md](../N8N_INTEGRATION.md)
- **Setup da stack**: [README.md](../README.md)
- **Guia Proxmox**: [PROXMOX_SETUP_GUIDE.md](../PROXMOX_SETUP_GUIDE.md)

## 🔐 Segurança

**NUNCA partilhe publicamente:**
- ❌ Discord Webhook URL
- ❌ Gemini API Key (começa com AIza...)
- ❌ Credenciais SSH

Use sempre **Credentials** do n8n para armazenar dados sensíveis.

## ⚙️ Especificações do Workflow

- **Modelo AI**: Gemini 1.5 Flash (gemini-1.5-flash)
- **Rate Limit**: 15 requisições/minuto (free tier)
- **Máx Tokens**: 2048 tokens por resposta
- **Temperatura**: 0.7 (balanceado entre criatividade e precisão)
- **Linguagem**: Português de Portugal
