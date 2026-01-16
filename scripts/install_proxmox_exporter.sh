#!/bin/bash
# Script to install Proxmox VE Exporter on Proxmox host
# Usage: ./install_proxmox_exporter.sh [proxmox_host_ip]

set -e

PROXMOX_HOST="${1:-192.168.90.104}"
EXPORTER_VERSION="v0.4.2"
EXPORTER_PORT="9221"
PVE_USER="prometheus@pve"
PVE_PASSWORD=""  # Will be generated

echo "=================================================="
echo "  Proxmox VE Exporter Installation"
echo "=================================================="
echo "Target Host: $PROXMOX_HOST"
echo "Exporter Version: $EXPORTER_VERSION"
echo "Port: $EXPORTER_PORT"
echo ""

# Function to execute commands on Proxmox host
ssh_exec() {
    ssh -o StrictHostKeyChecking=no root@"$PROXMOX_HOST" "$@"
}

echo "📋 Step 1: Creating Prometheus user in Proxmox PVE..."
PVE_PASSWORD=$(openssl rand -base64 32)

# Create user and role for Prometheus monitoring
ssh_exec "pveum user add $PVE_USER --comment 'Prometheus Monitoring User' || true"
ssh_exec "pveum role add Prometheus -privs VM.Audit,Sys.Audit,Sys.Modify,Datastore.Audit || true"
ssh_exec "pveum aclmod / -user $PVE_USER -role Prometheus"
ssh_exec "pveum user token add $PVE_USER monitoring --privsep 0 || echo 'Token already exists'"

echo "✓ Prometheus user created: $PVE_USER"
echo ""

echo "📥 Step 2: Downloading Proxmox VE Exporter..."
ssh_exec "wget -q https://github.com/prometheus-pve/prometheus-pve-exporter/releases/download/${EXPORTER_VERSION}/pve_exporter-${EXPORTER_VERSION}.tar.gz -O /tmp/pve_exporter.tar.gz"
ssh_exec "tar -xzf /tmp/pve_exporter.tar.gz -C /opt/"
ssh_exec "rm /tmp/pve_exporter.tar.gz"

echo "✓ Exporter downloaded and extracted"
echo ""

echo "📝 Step 3: Installing Python dependencies..."
ssh_exec "apt-get update && apt-get install -y python3 python3-pip python3-venv"
ssh_exec "cd /opt && python3 -m venv pve_exporter_env"
ssh_exec "/opt/pve_exporter_env/bin/pip install prometheus-pve-exporter"

echo "✓ Dependencies installed"
echo ""

echo "📝 Step 4: Creating configuration file..."
ssh_exec "mkdir -p /etc/prometheus"

# Get the token value
TOKEN_INFO=$(ssh_exec "pveum user token list $PVE_USER" | grep monitoring || echo "")

cat <<EOF | ssh_exec "cat > /etc/prometheus/pve.yml"
default:
    user: $PVE_USER
    token_name: monitoring
    token_value: <TOKEN_VALUE_HERE>  # Replace manually
    verify_ssl: false
EOF

echo "✓ Configuration file created at /etc/prometheus/pve.yml"
echo "⚠️  IMPORTANT: You need to manually set the token_value in /etc/prometheus/pve.yml"
echo ""

echo "📝 Step 5: Creating systemd service..."
cat <<'EOF' | ssh_exec "cat > /etc/systemd/system/prometheus-pve-exporter.service"
[Unit]
Description=Prometheus Proxmox VE Exporter
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt
ExecStart=/opt/pve_exporter_env/bin/pve_exporter /etc/prometheus/pve.yml --port 9221
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created"
echo ""

echo "🔧 Step 6: Enabling and starting service..."
ssh_exec "systemctl daemon-reload"
ssh_exec "systemctl enable prometheus-pve-exporter"
ssh_exec "systemctl start prometheus-pve-exporter"

sleep 2

echo "✓ Service started"
echo ""

echo "🔍 Step 7: Verifying installation..."
if ssh_exec "systemctl is-active prometheus-pve-exporter" | grep -q "active"; then
    echo "✓ Service is running"
else
    echo "✗ Service is not running. Check logs with:"
    echo "  ssh root@$PROXMOX_HOST journalctl -u prometheus-pve-exporter -n 50"
fi

if ssh_exec "curl -s http://localhost:$EXPORTER_PORT/metrics | head -5" | grep -q "pve"; then
    echo "✓ Metrics endpoint responding"
else
    echo "⚠️  Metrics endpoint not responding yet"
fi

echo ""
echo "=================================================="
echo "  Installation Complete!"
echo "=================================================="
echo ""
echo "📊 Exporter running at: http://$PROXMOX_HOST:$EXPORTER_PORT/metrics"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Get the API token:"
echo "   ssh root@$PROXMOX_HOST 'pveum user token list $PVE_USER'"
echo ""
echo "2. Update the token in /etc/prometheus/pve.yml on the Proxmox host"
echo ""
echo "3. Restart the service:"
echo "   ssh root@$PROXMOX_HOST 'systemctl restart prometheus-pve-exporter'"
echo ""
echo "4. Add to Prometheus targets (already done if using deploy_monitor.py)"
echo ""
echo "5. Check status:"
echo "   ssh root@$PROXMOX_HOST 'systemctl status prometheus-pve-exporter'"
echo "   curl http://$PROXMOX_HOST:$EXPORTER_PORT/metrics"
echo ""
