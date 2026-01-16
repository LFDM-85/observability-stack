#!/bin/bash
# Script para testar integração Alertmanager -> n8n Terry Workflow

echo "🧪 Testando integração Alertmanager -> n8n..."
echo ""

# Verifica se o n8n-adapter está rodando
if ! docker ps | grep -q n8n-adapter; then
    echo "❌ Container n8n-adapter não está rodando!"
    echo "Execute: docker compose up -d n8n-adapter"
    exit 1
fi

echo "✅ Container n8n-adapter está rodando"
echo ""

# Payload de teste simulando alerta do Alertmanager
PAYLOAD='{
  "receiver": "n8n-terry",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighDiskUsage",
        "instance": "192.168.90.104:9100",
        "job": "remote_hosts",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Host disk usage high on 192.168.90.104",
        "description": "Filesystem / is 92% full on 192.168.90.104"
      },
      "startsAt": "2024-01-16T10:00:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph"
    }
  ],
  "groupLabels": {
    "alertname": "HighDiskUsage"
  },
  "commonLabels": {
    "alertname": "HighDiskUsage",
    "severity": "critical"
  },
  "commonAnnotations": {
    "summary": "Host disk usage high"
  },
  "externalURL": "http://alertmanager:9093"
}'

echo "📤 Enviando alerta de teste para o adapter..."
echo ""

# Envia para o adapter (que vai transformar e enviar para n8n)
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  http://localhost:8081/alerts)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "Status HTTP: $HTTP_CODE"
echo "Resposta: $BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Alerta enviado com sucesso!"
    echo ""
    echo "🔍 Verifique:"
    echo "1. Logs do n8n-adapter: docker logs n8n-adapter"
    echo "2. Seu workflow n8n (Terry) deve ter recebido o webhook"
    echo "3. Verifique o Discord para a mensagem do Terry"
else
    echo "❌ Erro ao enviar alerta!"
    echo ""
    echo "Debug:"
    echo "- Logs do adapter: docker logs n8n-adapter"
    echo "- Verifique se o n8n está acessível em http://10.10.1.172:5678"
fi
