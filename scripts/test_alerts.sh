#!/bin/bash
# Alert Testing Script
# Triggers test alerts and verifies webhook delivery

PROMETHEUS_URL="http://localhost:9990"
ALERTMANAGER_URL="http://localhost:9093"

echo "🧪 Alert Testing Script"
echo "======================================================"
echo ""

# Check if Prometheus is accessible
echo "📡 Checking Prometheus connectivity..."
if ! curl -s "$PROMETHEUS_URL/-/healthy" > /dev/null; then
    echo "✗ Prometheus is not accessible at $PROMETHEUS_URL"
    exit 1
fi
echo "✓ Prometheus is accessible"
echo ""

# Check if Alertmanager is accessible
echo "📡 Checking Alertmanager connectivity..."
if ! curl -s "$ALERTMANAGER_URL/-/healthy" > /dev/null; then
    echo "✗ Alertmanager is not accessible at $ALERTMANAGER_URL"
    exit 1
fi
echo "✓ Alertmanager is accessible"
echo ""

# Check webhook configuration
echo "🔧 Checking webhook configuration..."
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found"
else
    if grep -q "DISCORD_WEBHOOK_URL=http" ../.env || grep -q "TEAMS_WEBHOOK_URL=http" ../.env; then
        echo "✓ Webhook URL(s) configured in .env"
    else
        echo "⚠️  Webhook URLs not configured in .env"
        echo "   Alerts will not be delivered to Discord/Teams"
    fi
fi
echo ""

# Send test alert to Alertmanager
echo "🚀 Sending test alert to Alertmanager..."

START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST "$ALERTMANAGER_URL/api/v2/alerts" \
  -H "Content-Type: application/json" \
  -d "[{
    \"labels\": {
      \"alertname\": \"TestAlert\",
      \"severity\": \"info\",
      \"instance\": \"test-server\",
      \"job\": \"test\"
    },
    \"annotations\": {
      \"summary\": \"🧪 Alert System Test\",
      \"description\": \"This is a test alert to verify the alert delivery system is working correctly.\"
    },
    \"startsAt\": \"$START_TIME\"
  }]"

echo ""
echo ""
echo "✅ Test alert sent!"
echo ""

# Wait a moment for processing
echo "⏱️  Waiting 5 seconds for alert processing..."
sleep 5
echo ""

# Check if alert appears in Alertmanager
echo "🔍 Checking if alert appears in Alertmanager..."
ALERTS=$(curl -s "$ALERTMANAGER_URL/api/v2/alerts" | grep -c "TestAlert" || echo "0")

if [ "$ALERTS" -gt 0 ]; then
    echo "✓ Test alert is visible in Alertmanager"
else
    echo "✗ Test alert not found in Alertmanager"
fi
echo ""

# Instructions
echo "======================================================"
echo "📋 Next Steps:"
echo "======================================================"
echo ""
echo "1. Check Alertmanager UI:"
echo "   → $ALERTMANAGER_URL"
echo ""
echo "2. Check for webhook delivery:"
echo "   → Discord: Check your Discord channel"
echo "   → Teams: Check your Teams channel"
echo ""
echo "3. View alert in Grafana:"
echo "   → http://localhost:3000/alerting/list"
echo ""
echo "4. If webhooks didn't arrive:"
echo "   → Check webhook-adapter logs:"
echo "     docker logs webhook-adapter"
echo ""
echo "   → Verify .env configuration:"
echo "     cat .env | grep WEBHOOK"
echo ""
echo "======================================================"
