# Integração n8n Terry Workflow com Alertmanager

Este documento explica como integrar o workflow "Terry - Homelab Mechanic" do n8n com o Alertmanager para análise inteligente e automatizada de alertas.

## 📋 Visão Geral

Quando um alerta é disparado pelo Prometheus, o fluxo é:

```
Prometheus → Alertmanager → n8n-adapter → n8n (Terry Workflow) → SSH Analysis → Gemini AI → Discord
```

### Componentes

1. **Prometheus**: Detecta problemas e dispara alertas
2. **Alertmanager**: Gerencia e roteia alertas
3. **n8n-adapter**: Converte formato Alertmanager → n8n
4. **n8n Terry Workflow**: Recebe alerta, conecta por SSH, analisa logs, pede análise à IA
5. **Discord**: Recebe diagnóstico detalhado do Terry

## 🚀 Setup

### Passo 1: Verificar URL do n8n

O workflow n8n tem um webhook em:
```
http://10.10.1.172:5678/webhook/homelab-alert
```

Se o seu n8n está noutro endereço, edite o [.env](.env):

```bash
# .env
N8N_WEBHOOK_URL=http://<seu-n8n-host>:<porta>/webhook/homelab-alert
```

### Passo 2: Deploy da Stack

```bash
# Inicia todos os serviços (incluindo n8n-adapter)
docker compose up -d

# Verifica se o adapter está rodando
docker ps | grep n8n-adapter
```

### Passo 3: Ativar Workflow no n8n

1. Aceda ao n8n: `http://10.10.1.172:5678`
2. Importe o workflow "Terry - Homelab Mechanic"
3. **IMPORTANTE**: Clique em "Activate" (botão toggle no canto superior direito)
4. Verifique o webhook está ativo: Settings → Webhook → Production URL

### Passo 4: Configurar SSH no Workflow

No nó **"SSH - Investigador"** do workflow n8n:

1. Adicione as credenciais SSH para aceder aos seus hosts
2. Configure:
   - **Host**: `={{ $json.target_host }}` (já configurado)
   - **Port**: `22`
   - **Username**: `root` (ou seu utilizador com sudo)
   - **Authentication**: Password ou Private Key

### Passo 5: Testar Integração

Execute o script de teste:

```bash
./scripts/test_n8n_integration.sh
```

Este script:
- ✅ Verifica se o n8n-adapter está rodando
- 📤 Envia um alerta de teste simulando "HighDiskUsage"
- 🔍 Mostra a resposta do adapter

**Resultado esperado**: Deve receber uma mensagem no Discord com o diagnóstico do Terry!

## 🔧 Configuração do Alertmanager

O [alertmanager.yml](alertmanager/alertmanager.yml) está configurado para enviar **todos os alertas** para o Terry:

```yaml
route:
  routes:
    # n8n Terry Workflow - All alerts (parallel notification)
    - receiver: 'n8n-terry'
      continue: true
      repeat_interval: 30m

receivers:
  - name: 'n8n-terry'
    webhook_configs:
      - url: 'http://n8n-adapter:8081/alerts'
        send_resolved: true
```

**Nota**: `continue: true` significa que os alertas também são enviados para Teams/Discord via webhook-adapter.

## 📊 Como Funciona

### 1. Formato do Alerta (Alertmanager)

O Alertmanager envia alertas neste formato:

```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighDiskUsage",
        "instance": "192.168.90.104:9100",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Host disk usage high",
        "description": "Filesystem / is 92% full"
      }
    }
  ]
}
```

### 2. Transformação (n8n-adapter)

O adapter [alertmanager_to_n8n_adapter.py](scripts/alertmanager_to_n8n_adapter.py) transforma para:

```json
{
  "alert_name": "HighDiskUsage",
  "host_ip": "192.168.90.104",
  "severity": "critical",
  "message": "Filesystem / is 92% full",
  "status": "firing"
}
```

### 3. Workflow n8n

O workflow Terry:

1. **Recebe o alerta** via webhook
2. **Seleciona comando SSH** apropriado baseado no alert_name:
   - `HighDiskUsage` → `df -h; du -ahx /var /home | sort -rh | head -10`
   - `HighCPU` → `top -b -n 1 | head -15`
   - `HighMemory` → `free -m; ps aux --sort=-%mem | head -10`
3. **Executa SSH** no host afetado
4. **Envia output + contexto** para Gemini AI
5. **Formata resposta** e envia para Discord

### 4. Exemplo de Resposta do Terry

```
🚨 **Alerta Homelab: HighDiskUsage**

## 1. Análise da Causa Raiz

O disco `/` está com 92% de utilização. Análise do `du` mostra:
- `/var/log`: 45GB (logs antigos)
- `/var/lib/docker`: 23GB (imagens não utilizadas)

## 2. Solução Proposta

- Limpar logs antigos: `find /var/log -name "*.gz" -mtime +30 -delete`
- Limpar Docker: `docker system prune -a --volumes`

## 3. Importante

- ⚠️ Fazer backup antes de limpar
- ⚠️ Verificar se há processos a escrever nos ficheiros
```

## 🐛 Troubleshooting

### Adapter não está a enviar para n8n

```bash
# Verificar logs do adapter
docker logs n8n-adapter

# Testar conectividade
docker exec n8n-adapter curl -v http://10.10.1.172:5678/webhook/homelab-alert
```

### Workflow n8n não está a receber webhooks

1. Verifique se o workflow está **ativo** (toggle verde)
2. Abra o workflow e clique em "Listen for Test Event" no nó Webhook
3. Execute `./scripts/test_n8n_integration.sh`
4. Deve aparecer os dados no n8n

### SSH falha no workflow

1. Verifique as credenciais SSH no nó "SSH - Investigador"
2. Teste SSH manualmente: `ssh root@<host_ip>`
3. Certifique-se que o n8n consegue alcançar o host (firewall?)

### Gemini AI não responde

1. Verifique a API key no nó "Terry (Analista)"
2. Teste a API manualmente:
```bash
curl -X POST \
  -H "X-goog-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

### Discord não recebe mensagem

1. Verifique a URL do webhook Discord no nó "HTTP Request"
2. Teste o webhook manualmente:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content": "Test"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

## 🔐 Segurança

### API Keys e Webhooks

**NUNCA** partilhe publicamente:
- Discord Webhook URL
- Gemini API Key
- SSH Credentials

No n8n, use sempre **Credentials** para armazenar dados sensíveis.

### SSH Access

O workflow precisa de acesso SSH aos hosts. Recomendações:

1. **Crie um utilizador dedicado**:
```bash
useradd -m -s /bin/bash terry
echo "terry ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/journalctl, /usr/bin/df, /usr/bin/du, /usr/bin/free, /usr/bin/top" >> /etc/sudoers.d/terry
```

2. **Use SSH Keys** em vez de passwords
3. **Restrinja comandos** no `sudoers` (exemplo acima)

## 📝 Personalização

### Adicionar Novos Alertas

Edite o nó **"Selecionar Comando"** no workflow n8n:

```javascript
if (alertName && alertName.includes("MySQL")) {
  cmd = "systemctl status mysql; tail -50 /var/log/mysql/error.log";
}
```

### Mudar Modelo IA

No nó **"Terry (Analista)"**, pode mudar para outro modelo:

```
gemini-2.5-flash → gemini-1.5-pro (mais inteligente, mais lento)
```

### Adicionar Outros Destinos

Duplique o nó **"HTTP Request"** e configure para:
- Microsoft Teams
- Slack
- Email (via SendGrid, SMTP)
- PagerDuty

## 📚 Referências

- [Alertmanager Webhook Config](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config)
- [n8n Webhook Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [Gemini API](https://ai.google.dev/docs)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)

## 🎯 Próximos Passos

- [ ] Adicionar autenticação no adapter (Basic Auth, API Key)
- [ ] Implementar rate limiting no adapter
- [ ] Criar dashboard no Grafana com estatísticas das análises do Terry
- [ ] Adicionar persistência das análises (SQLite, PostgreSQL)
- [ ] Implementar feedback loop (👍/👎 no Discord para melhorar prompts)
