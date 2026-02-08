#!/bin/bash
# Setup script for automatic network discovery

set -e

echo "=========================================="
echo "  Network Discovery Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script should be run as root for best results"
    echo "   Some features may not work without root privileges"
    echo ""
fi

# 1. Install dependencies
echo "1. Installing dependencies..."
if command -v apt &> /dev/null; then
    apt update
    apt install -y nmap python3-yaml
elif command -v yum &> /dev/null; then
    yum install -y nmap python3-pyyaml
else
    echo "⚠️  Could not detect package manager"
    echo "   Please install manually: nmap, python3-yaml"
fi

# Install Python dependencies
pip3 install pyyaml 2>/dev/null || python3 -m pip install pyyaml

echo "✅ Dependencies installed"
echo ""

# 2. Test nmap
echo "2. Testing nmap..."
if command -v nmap &> /dev/null; then
    echo "✅ nmap found: $(nmap --version | head -1)"
else
    echo "❌ nmap not found"
    exit 1
fi
echo ""

# 3. Test initial scan
echo "3. Running test scan..."
cd "$(dirname "$0")/.."
python3 scripts/network_discovery.py --scan

echo ""
echo "✅ Test scan complete"
echo ""

# 4. Setup cron job
echo "4. Setting up automatic discovery (cron)..."

CRON_CMD="*/5 * * * * cd $(pwd) && /usr/bin/python3 scripts/network_discovery.py --scan >> /var/log/network_discovery.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "network_discovery.py"; then
    echo "⚠️  Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added (runs every 5 minutes)"
fi

echo ""

# 5. Create log file
echo "5. Creating log file..."
touch /var/log/network_discovery.log
chmod 644 /var/log/network_discovery.log
echo "✅ Log file: /var/log/network_discovery.log"
echo ""

# Summary
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Network discovery is now running automatically every 5 minutes"
echo ""
echo "Commands:"
echo "  • Manual scan:  python3 scripts/network_discovery.py --scan"
echo "  • View log:     tail -f /var/log/network_discovery.log"
echo "  • List cron:    crontab -l"
echo "  • Remove cron:  crontab -e (delete the network_discovery line)"
echo ""
echo "Configuration: network_discovery.yml"
echo "Discovered DB:  network_devices_discovered.json"
echo ""
