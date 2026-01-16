# 🚀 Setup Rápido - Terry Workflow com Claude

Guia de 5 minutos para configurar o workflow no n8n.

## ✅ Pré-requisitos

- n8n instalado e acessível em http://10.10.1.172.nip.io:5678
- Conta Claude.ai (para API Key)
- Acesso SSH aos hosts monitorizados

## 📋 Passo a Passo

### 1️⃣ Obter API Key do Gemini (2 min)

1. Aceda a **https://makersuite.google.com/app/apikey**
2. Login com sua conta Google
3. Clique em **"Create API Key"**
4. Selecione um projeto Google Cloud (ou crie um novo)
5. **Copie a key** (começa com `AIza...`)
   - ⚠️ Guarde-a num local seguro (só aparece uma vez!)

### 2️⃣ Importar Workflow no n8n (1 min)

1. Abra o ficheiro [terry-homelab-mechanic.json](terry-homelab-mechanic.json)
2. **Copie TODO o conteúdo** (Ctrl+A, Ctrl+C)
3. Aceda ao n8n: http://10.10.1.172.nip.io:5678
4. Clique em **"+"** (Add workflow)
5. Menu **⋮** → **"Import from File/URL"**
6. Cole o JSON completo
7. Clique em **"Import"**

### 3️⃣ Configurar Gemini API (1 min)

1. No workflow, clique no nó **"Terry (Analista Gemini)"**
2. Na secção **Credentials**, clique em **"Create New"**
3. Selecione **"Google PaLM API"** ou **"Google AI"**
4. Cole sua **API Key** do Gemini
5. Dê um nome: `Gemini API - Terry`
6. Clique em **"Save"**

### 4️⃣ Configurar SSH (1 min)

1. Clique no nó **"SSH - Investigador"**
2. Na secção **Credentials**, clique em **"Create New"**
3. Escolha:
   - **SSH Password** (mais simples)
   - OU **SSH Private Key** (mais seguro)

**Para SSH Password:**
```
Host: ={{ $json.target_host }}  (já configurado, não altere!)
Port: 22
Username: root
Password: [sua password SSH]
```

**Para SSH Private Key:**
```
Host: ={{ $json.target_host }}  (já configurado, não altere!)
Port: 22
Username: root
Private Key: [cole sua chave privada]
```

4. Clique em **"Save"**

### 5️⃣ Ativar Workflow (30 seg)

1. No canto superior direito, clique no **toggle "Active"**
2. Deve ficar **VERDE** ✅
3. O webhook estará ativo em:
   ```
   http://10.10.1.172.nip.io:5678/webhook/homelab-alert
   ```

## 🧪 Testar

### Teste Manual no n8n

1. Clique no nó **"Teste Manual"**
2. Clique em **"Test workflow"** (botão play no topo)
3. Aguarde ~10 segundos
4. Verifique o **Discord** para a mensagem do Terry

### Teste via Alertmanager

No servidor da observability stack:

```bash
cd /home/luismelo/Documents/GitHub/observability-stack
./scripts/test_n8n_integration.sh
```

**Resultado esperado:**
```
✅ Alert sent to n8n: HighDiskUsage - Status: 200
```

Depois, verifique o Discord!

## 🔍 Verificar Execuções

No n8n, menu lateral → **"Executions"**:
- Verde ✅ = Sucesso
- Vermelho ❌ = Erro (clique para ver detalhes)

## ❌ Troubleshooting

### Workflow não executa

**Causa**: Workflow não está ativo
**Solução**: Toggle "Active" deve estar VERDE

### Erro "Invalid API Key"

**Causa**: API Key do Gemini incorreta
**Solução**: Volte ao nó "Terry (Analista Gemini)" → Credentials → Edite e cole a key correta

### Erro "Quota Exceeded"

**Causa**: Modelo experimental do Gemini atingiu limite gratuito
**Solução**: O workflow agora usa gemini-1.5-flash (estável, sem esse problema)

### SSH falha

**Causa**: Credenciais incorretas ou host inacessível
**Solução**:
1. Teste SSH manualmente: `ssh root@192.168.90.104`
2. Verifique credenciais no nó "SSH - Investigador"

### Discord não recebe

**Causa**: URL do webhook incorreta
**Solução**: Nó "Enviar Discord" → Verifique URL

## 📊 Próximos Passos

1. ✅ Aguarde um alerta real do Prometheus
2. ✅ Verifique o Discord para o diagnóstico do Terry
3. ✅ Ajuste comandos SSH conforme necessário
4. ✅ Adicione mais categorias de alertas

## 🎯 Fluxo Completo

```
Prometheus dispara alerta
    ↓
Alertmanager → n8n-adapter → n8n Webhook
    ↓
Terry seleciona comando SSH
    ↓
Executa SSH no host afetado
    ↓
Claude AI analisa output
    ↓
Envia diagnóstico para Discord
```

## 📚 Mais Informações

- [README Completo](README.md) - Guia detalhado
- [N8N_INTEGRATION.md](../N8N_INTEGRATION.md) - Documentação técnica
- [PROXMOX_SETUP_GUIDE.md](../PROXMOX_SETUP_GUIDE.md) - Setup Proxmox

## 💡 Dicas

- Gemini 1.5 Flash é gratuito e eficiente (evita quotas do modelo experimental)
- Configure SSH com chave privada (mais seguro)
- Verifique "Executions" no n8n para debug
- O Terry aprende com o contexto do alerta
- Rate limit Gemini free tier: 15 req/min (suficiente para alertas)

**Tudo pronto! 🎉**

O Terry está agora a monitorizar o seu homelab 24/7 com análise inteligente!
