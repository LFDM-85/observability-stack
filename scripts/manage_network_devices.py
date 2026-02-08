#!/usr/bin/env python3
"""
Network Devices Management Script
Reads network_devices.txt and generates Prometheus targets JSON
"""

import json
import os
import sys
import ipaddress
import subprocess
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEVICES_FILE = PROJECT_ROOT / "network_devices.txt"
TARGETS_FILE = PROJECT_ROOT / "prometheus" / "network_devices.json"

def validate_ip(ip_str):
    """Validate IP address"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def read_devices():
    """Read and parse network_devices.txt"""
    if not DEVICES_FILE.exists():
        print(f"❌ Error: {DEVICES_FILE} not found")
        print(f"   Create it from example: cp network_devices.txt.example network_devices.txt")
        sys.exit(1)
    
    devices = []
    with open(DEVICES_FILE, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse CSV: IP,Name,Type
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 3:
                print(f"⚠️  Warning: Line {line_num} invalid format (expected IP,Name,Type): {line}")
                continue
            
            ip, name, device_type = parts
            
            # Validate IP
            if not validate_ip(ip):
                print(f"⚠️  Warning: Line {line_num} invalid IP address: {ip}")
                continue
            
            devices.append({
                'ip': ip,
                'name': name,
                'type': device_type
            })
    
    return devices

def generate_targets(devices):
    """Generate Prometheus targets JSON"""
    targets = []
    
    for device in devices:
        targets.append({
            'targets': [device['ip']],
            'labels': {
                'device_name': device['name'],
                'device_type': device['type'],
                'job': 'blackbox_ping'
            }
        })
    
    return targets

def write_targets(targets):
    """Write targets to JSON file"""
    TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(TARGETS_FILE, 'w') as f:
        json.dump(targets, f, indent=2)
    
    print(f"✅ Generated {len(targets)} targets in {TARGETS_FILE}")

def reload_prometheus():
    """Reload Prometheus configuration"""
    try:
        # Try to reload via HTTP API
        result = subprocess.run(
            ['curl', '-X', 'POST', 'http://localhost:9990/-/reload'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Prometheus configuration reloaded")
        else:
            print("⚠️  Could not reload Prometheus (may need manual restart)")
    except Exception as e:
        print(f"⚠️  Could not reload Prometheus: {e}")
        print("   Restart manually: docker compose restart prometheus")

def main():
    print("=" * 50)
    print("  Network Devices Management")
    print("=" * 50)
    print()
    
    # Read devices
    print(f"📖 Reading devices from {DEVICES_FILE}...")
    devices = read_devices()
    
    if not devices:
        print("⚠️  No valid devices found")
        sys.exit(1)
    
    print(f"✅ Found {len(devices)} valid devices")
    print()
    
    # Show devices
    print("Devices to monitor:")
    for device in devices:
        print(f"  • {device['ip']:15} - {device['name']:20} ({device['type']})")
    print()
    
    # Generate targets
    print("📝 Generating Prometheus targets...")
    targets = generate_targets(devices)
    
    # Write targets
    write_targets(targets)
    print()
    
    # Reload Prometheus
    print("🔄 Reloading Prometheus...")
    reload_prometheus()
    print()
    
    print("=" * 50)
    print("  Done!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("  1. Check Prometheus targets: http://localhost:9990/targets")
    print("  2. View dashboard in Grafana")
    print()

if __name__ == '__main__':
    main()
