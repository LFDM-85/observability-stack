#!/bin/bash
set -e

echo "=========================================="
echo "  Network Discovery Service"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  PROMETHEUS_HOST: ${PROMETHEUS_HOST}"
echo "  PROMETHEUS_PORT: ${PROMETHEUS_PORT}"
echo "  SCAN_INTERVAL: ${SCAN_INTERVAL}s"
echo ""

# Create symlinks to data volume for persistent storage
ln -sf /data/network_devices.txt /app/network_devices.txt 2>/dev/null || true
ln -sf /data/network_devices_discovered.json /app/network_devices_discovered.json 2>/dev/null || true

# Initialize files if they don't exist
if [ ! -f /data/network_devices.txt ]; then
    echo "# Network Devices - Managed automatically by discovery service" > /data/network_devices.txt
    echo "# Format: IP,Name,Type" >> /data/network_devices.txt
fi

if [ ! -f /data/network_devices_discovered.json ]; then
    echo "{}" > /data/network_devices_discovered.json
fi

# Wait for Prometheus to be available
echo "Waiting for Prometheus..."
until curl -s "http://${PROMETHEUS_HOST}:${PROMETHEUS_PORT}/-/ready" > /dev/null 2>&1; do
    echo "  Prometheus not ready, waiting..."
    sleep 5
done
echo "Prometheus is ready!"
echo ""

# Main loop
while true; do
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting network scan..."

    # Run discovery
    cd /app
    python3 network_discovery.py --scan --config /app/network_discovery.yml || echo "Scan failed, will retry"

    # Copy generated targets to data volume
    if [ -f /app/prometheus/network_devices.json ]; then
        cp /app/prometheus/network_devices.json /data/network_devices.json
        echo "Targets saved to /data/network_devices.json"
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scan complete. Next scan in ${SCAN_INTERVAL}s..."
    sleep "${SCAN_INTERVAL}"
done
