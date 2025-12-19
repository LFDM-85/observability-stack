#!/usr/bin/env python3
"""
Webhook adapter para enviar alertas do Prometheus/Alertmanager para Microsoft Teams
"""
from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# Configurações via variáveis de ambiente
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL', '')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

def send_to_teams(alert_data):
    """Envia alerta formatado para Microsoft Teams"""
    if not TEAMS_WEBHOOK_URL:
        return
    
    alerts = alert_data.get('alerts', [])
    status = alert_data.get('status', 'unknown')
    
    for alert in alerts:
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        # Cor baseada na severidade
        color = {
            'critical': 'FF0000',  # Vermelho
            'warning': 'FFA500',   # Laranja
            'info': '00FF00'       # Verde
        }.get(labels.get('severity', 'info'), '0078D7')
        
        # Emoji baseado na severidade
        emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(labels.get('severity', 'info'), '📊')
        
        # Monta a mensagem para Teams
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"{emoji} {annotations.get('summary', 'Alerta')}",
            "themeColor": color,
            "title": f"{emoji} {labels.get('alertname', 'Alert')}",
            "sections": [
                {
                    "activityTitle": annotations.get('summary', 'Novo alerta'),
                    "activitySubtitle": f"Status: {status.upper()}",
                    "facts": [
                        {"name": "Severidade", "value": labels.get('severity', 'unknown').upper()},
                        {"name": "Instância", "value": labels.get('instance', 'N/A')},
                        {"name": "Job", "value": labels.get('job', 'N/A')},
                        {"name": "Descrição", "value": annotations.get('description', 'N/A')},
                        {"name": "Horário", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ],
                    "markdown": True
                }
            ]
        }
        
        try:
            response = requests.post(TEAMS_WEBHOOK_URL, json=message, timeout=10)
            response.raise_for_status()
            print(f"Alerta enviado para Teams: {labels.get('alertname')}")
        except Exception as e:
            print(f"Erro ao enviar para Teams: {e}")

def send_to_discord(alert_data):
    """Envia alerta formatado para Discord"""
    if not DISCORD_WEBHOOK_URL:
        return
    
    alerts = alert_data.get('alerts', [])
    status = alert_data.get('status', 'unknown')
    
    for alert in alerts:
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        # Cor baseada na severidade
        color = {
            'critical': 0xFF0000,  # Vermelho
            'warning': 0xFFA500,   # Laranja
            'info': 0x00FF00       # Verde
        }.get(labels.get('severity', 'info'), 0x0078D7)
        
        # Emoji baseado na severidade
        emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(labels.get('severity', 'info'), '📊')
        
        # Monta embed para Discord
        embed = {
            "embeds": [{
                "title": f"{emoji} {labels.get('alertname', 'Alert')}",
                "description": annotations.get('summary', 'Novo alerta'),
                "color": color,
                "fields": [
                    {"name": "Status", "value": status.upper(), "inline": True},
                    {"name": "Severidade", "value": labels.get('severity', 'unknown').upper(), "inline": True},
                    {"name": "Instância", "value": labels.get('instance', 'N/A'), "inline": False},
                    {"name": "Job", "value": labels.get('job', 'N/A'), "inline": True},
                    {"name": "Descrição", "value": annotations.get('description', 'N/A'), "inline": False}
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "Prometheus Alertmanager"}
            }]
        }
        
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=10)
            response.raise_for_status()
            print(f"Alerta enviado para Discord: {labels.get('alertname')}")
        except Exception as e:
            print(f"Erro ao enviar para Discord: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({"status": "healthy"}), 200

@app.route('/alerts', methods=['POST'])
def receive_alert():
    """Recebe alertas do Alertmanager e encaminha"""
    try:
        alert_data = request.json
        print(f"Alerta recebido: {json.dumps(alert_data, indent=2)}")
        
        # Envia para ambos os canais
        send_to_teams(alert_data)
        send_to_discord(alert_data)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Erro ao processar alerta: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Webhook Adapter iniciado")
    print(f"Teams configurado: {bool(TEAMS_WEBHOOK_URL)}")
    print(f"Discord configurado: {bool(DISCORD_WEBHOOK_URL)}")
    app.run(host='0.0.0.0', port=8080, debug=False)
