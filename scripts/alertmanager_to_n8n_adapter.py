#!/usr/bin/env python3
"""
Alertmanager to n8n Webhook Adapter
Transforma alertas do formato Alertmanager para o formato esperado pelo workflow n8n Terry
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import os

N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'http://10.10.1.172:5678/webhook/homelab-alert')
PORT = 8081

class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Processa alertas do Alertmanager e envia para n8n"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            # Parse do payload do Alertmanager
            alertmanager_payload = json.loads(post_data.decode('utf-8'))

            # Processa cada alerta
            for alert in alertmanager_payload.get('alerts', []):
                # Extrai informações do alerta
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})

                # Extrai IP da instância (remove porta se existir)
                instance = labels.get('instance', '')
                host_ip = instance.split(':')[0] if ':' in instance else instance

                # Se não tiver IP, tenta outras labels
                if not host_ip or host_ip == '':
                    host_ip = labels.get('host', labels.get('exported_instance', 'unknown'))

                # Monta payload para n8n no formato esperado
                n8n_payload = {
                    'alert_name': labels.get('alertname', 'Unknown'),
                    'host_ip': host_ip,
                    'severity': labels.get('severity', 'warning'),
                    'message': annotations.get('summary', annotations.get('description', 'No description')),
                    'status': alert.get('status', 'firing')
                }

                # Envia para n8n
                try:
                    response = requests.post(N8N_WEBHOOK_URL, json=n8n_payload, timeout=10)
                    print(f"✅ Alert sent to n8n: {n8n_payload['alert_name']} - Status: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error sending to n8n: {str(e)}")

            # Responde ao Alertmanager
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())

        except Exception as e:
            print(f"❌ Error processing alert: {str(e)}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        """Customiza logging"""
        print(f"[Alertmanager→n8n] {format % args}")

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), AlertHandler)
    print(f"🚀 Alertmanager to n8n adapter listening on port {PORT}")
    print(f"📡 Forwarding to: {N8N_WEBHOOK_URL}")
    server.serve_forever()
