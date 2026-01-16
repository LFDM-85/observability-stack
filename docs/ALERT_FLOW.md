# Fluxo de Alertas - Observability Stack

Documentação do fluxo de alertas através da stack de monitorização.

## 🔄 Arquitetura Atual (v2 - Terry AI)

```
┌─────────────┐
│ Prometheus  │ Detecta problemas
└──────┬──────┘
       │ Firing alerts
       ▼
┌─────────────────┐
│ Alertmanager    │ Agrupa e encaminha
└────────┬────────┘
         │
         │ HTTP POST
         ▼
┌──────────────────┐
│  n8n-adapter     │ Transforma payload
│  (Port 8081)     │ Alertmanager → n8n
└────────┬─────────┘
         │
         │ HTTP POST
         ▼
┌──────────────────────────────────────┐
│           n8n Workflow               │
│      "Terry - Homelab Mechanic"      │
├──────────────────────────────────────┤
│  1. Recebe alerta                    │
│  2. Seleciona comandos SSH           │
│  3. Executa diagnóstico no host      │
│  4. Análise AI (Gemini 1.5 Flash)    │
│  5. Formata resultado Discord        │
└────────┬─────────────────────────────┘
         │
         │ Webhook
         ▼
    ┌─────────┐
    │ Discord │ Notificação com análise AI
    └─────────┘
```

## ✨ Principais Características

### 1. Análise Inteligente com AI
- **Modelo**: Gemini 1.5 Flash (gratuito)
- **Diagnóstico**: SSH automático no host afetado
- **Contexto**: Terry entende o tipo de alerta e executa comandos relevantes
- **Soluções**: Sugere comandos para resolver o problema

### 2. Categorização Automática
O workflow identifica automaticamente:
- 💾 **Disk/Filesystem** → `df -h`, `du` análise
- ⚡ **CPU/Load** → `top`, análise de processos
- 🧠 **Memory** → `free -m`, processos por memória
- ⚙️ **Services** → `systemctl`, `journalctl`
- 🐳 **Docker** → `docker ps`, `docker stats`
- 🏢 **Proxmox** → `qm list`, `pct list`
- 🔍 **Generic** → `uptime`, `dmesg`

### 3. Notificações Ricas
- Embeds Discord formatados
- Cor por severidade (vermelho/amarelo/azul)
- Campos estruturados (Host, Severidade, Categoria)
- Timestamp automático
- Footer com assinatura

## 📊 Configuração Alertmanager

### Receivers
```yaml
receivers:
  - name: 'n8n-terry'
    webhook_configs:
      - url: 'http://n8n-adapter:8081/alerts'
        send_resolved: true
```

### Routing
```yaml
route:
  receiver: 'n8n-terry'  # Default: Todos os alertas
  routes:
    - match:
        severity: critical
      receiver: 'n8n-terry'
      repeat_interval: 30m  # Críticos repetem mais rápido

    - match:
        severity: warning
      receiver: 'n8n-terry'
      repeat_interval: 4h   # Warnings repetem de 4 em 4h
```

## 🔧 Componentes

### n8n-adapter
- **Porta**: 8081
- **Função**: Transforma payload Alertmanager → n8n
- **Código**: [alertmanager_to_n8n_adapter.py](../scripts/alertmanager_to_n8n_adapter.py)
- **Payload de saída**:
```json
{
  "alert_name": "HostHighDiskUsage",
  "host_ip": "192.168.90.104",
  "severity": "critical",
  "message": "Filesystem / is 92% full",
  "status": "firing"
}
```

### n8n Workflow "Terry"
- **Webhook**: `http://10.10.1.172.nip.io:5678/webhook/homelab-alert`
- **Nós principais**:
  1. Webhook Receiver
  2. Seletor de Comandos SSH
  3. SSH Executor
  4. Terry (Gemini AI Analyst)
  5. Discord Formatter
  6. Discord Sender

- **Documentação**: [n8n-workflows/.gitkeep](../n8n-workflows/.gitkeep)

## ⚙️ Rate Limits

| Componente | Limite | Notas |
|------------|--------|-------|
| Gemini API | 15 req/min | Free tier suficiente |
| Discord Webhook | 30 req/min | Bem acima do necessário |
| n8n-adapter | Ilimitado | Local |
| Alertmanager | Configurável | repeat_interval |

## 🚫 Arquitetura Antiga (Deprecated)

### ❌ Fluxo Direto Discord (Removido)
```
Prometheus → Alertmanager → webhook-adapter → Discord
                          ↘ (Teams webhook)
```

**Porquê removido?**
- ❌ Notificações sem contexto
- ❌ Sem análise inteligente
- ❌ Alertas crus e difíceis de interpretar
- ❌ Duplicação de notificações
- ❌ Ambiente poluído

**Substituído por:**
- ✅ Análise AI com contexto
- ✅ Diagnóstico automático
- ✅ Sugestões de solução
- ✅ Notificações limpas e úteis
- ✅ Fluxo único e centralizado

## 📝 Payload Examples

### Alertmanager → n8n-adapter
```json
{
  "alerts": [{
    "status": "firing",
    "labels": {
      "alertname": "HostHighDiskUsage",
      "instance": "192.168.90.104:9100",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Filesystem / is 92% full on node pve"
    }
  }]
}
```

### n8n-adapter → n8n
```json
{
  "alert_name": "HostHighDiskUsage",
  "host_ip": "192.168.90.104",
  "severity": "critical",
  "message": "Filesystem / is 92% full on node pve",
  "status": "firing"
}
```

### Terry → Discord
```json
{
  "content": "💾 **Alerta Homelab: HostHighDiskUsage**",
  "embeds": [{
    "title": "Diagnóstico do Terry 🔧 (Gemini AI)",
    "description": "**1. Causa Raiz:**\nO filesystem / está com 92% devido a logs...\n\n**2. Solução:**\n```bash\nfind /var/log -name \"*.gz\" -mtime +30 -delete\n```\n\n**3. Urgência:**\n⚠️ Crítico - Resolver nas próximas 24h",
    "color": 16711680,
    "fields": [
      {"name": "Máquina Alvo", "value": "192.168.90.104", "inline": true},
      {"name": "Severidade", "value": "CRITICAL", "inline": true},
      {"name": "Categoria", "value": "disk", "inline": true}
    ],
    "footer": {"text": "Automated by n8n & Gemini AI (1.5-flash)"},
    "timestamp": "2026-01-16T20:00:00.000Z"
  }]
}
```

## 🔍 Troubleshooting

### Alertas não chegam ao Discord

**1. Verificar n8n-adapter**
```bash
docker logs n8n-adapter --tail 50
# Deve mostrar: ✅ Alert sent to n8n: AlertName - Status: 200
```

**2. Verificar n8n workflow**
- Aceder: http://10.10.1.172.nip.io:5678
- Menu "Executions" → Verificar últimas execuções
- Toggle "Active" deve estar VERDE

**3. Verificar Alertmanager**
```bash
docker logs alertmanager --tail 50
# Procurar por erros de envio
```

**4. Testar manualmente**
```bash
cd /home/luismelo/Documents/GitHub/observability-stack
./scripts/test_n8n_integration.sh
```

### Gemini API falha

**Erro comum**: `404 - Model not found`
**Solução**: Endpoint correto é `v1beta`, não `v1`

**Erro comum**: `429 - Quota exceeded`
**Solução**: Usar `gemini-1.5-flash` (estável), não experimental

### SSH falha

**Verificar**:
```bash
ssh root@192.168.90.104
# Deve conectar sem erro
```

**Credenciais no n8n**:
- Nó "SSH - Investigador" → Credentials
- Verificar host: `={{ $json.target_host }}`
- Não alterar esta expressão!

## 📚 Documentação Relacionada

- [N8N Integration Guide](../N8N_INTEGRATION.md)
- [Alertmanager Config](../alertmanager/alertmanager.yml)
- [n8n Adapter Script](../scripts/alertmanager_to_n8n_adapter.py)
- [Test Script](../scripts/test_n8n_integration.sh)

## 🎯 Métricas de Sucesso

| Métrica | Valor | Meta |
|---------|-------|------|
| Latência (alerta→discord) | ~5-10s | <30s |
| Taxa de sucesso | >95% | >90% |
| Análises úteis (feedback) | ~80% | >70% |
| False positives | <5% | <10% |

## 🔐 Segurança

**Credenciais armazenadas no n8n**:
- ✅ Gemini API Key
- ✅ SSH Credentials
- ✅ Discord Webhook URL

**NÃO versionar**:
- ❌ n8n workflow JSON (contém IDs de credenciais)
- ❌ .env (contém webhook URLs)
- ❌ hosts.txt (IPs internos)

**Ver**: [.gitignore](../.gitignore)
