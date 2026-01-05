import json
import os
import subprocess
import sys
import time

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
TARGETS_FILE = os.path.join(BASE_DIR, 'prometheus', 'targets.json')

# Node Exporter Version
NODE_EXPORTER_VERSION = "1.8.2"

def load_hosts():
    if not os.path.exists(HOSTS_FILE):
        return []
    with open(HOSTS_FILE, 'r') as f:
        lines = f.readlines()
    # Filter comments and empty lines
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

def load_targets():
    if not os.path.exists(TARGETS_FILE):
        return []
    try:
        with open(TARGETS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_targets(targets):
    with open(TARGETS_FILE, 'w') as f:
        json.dump(targets, f, indent=2)

def is_target_configured(ip, targets):
    target_str = f"{ip}:9100"
    for t in targets:
        if target_str in t.get('targets', []):
            return True
    return False

def add_target(ip, targets):
    target_str = f"{ip}:9100"
    # Check if we have a group for automatic discovery
    found = False
    for t in targets:
        if t.get('labels', {}).get('job') == 'node_exporter_auto':
             if target_str not in t['targets']:
                 t['targets'].append(target_str)
             found = True
             break
    
    if not found:
        targets.append({
            "targets": [target_str],
            "labels": {
                "job": "node_exporter_auto",
                "env": "production"
            }
        })
    return targets

def install_node_exporter(ip):
    print(f"[{ip}] Checking/Installing Node Exporter...")
    
    # Check if already running
    check_cmd = "systemctl is-active node_exporter"
    res = ssh_command(ip, check_cmd)
    if res and res.strip() == "active":
        print(f"[{ip}] Node Exporter is already active.")
        return True

    print(f"[{ip}] Installing Node Exporter v{NODE_EXPORTER_VERSION}...")
    
    # Installation commands
    commands = [
        f"wget https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"tar xvfz node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"sudo mv node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/",
        "rm -rf node_exporter-*",
        # Create user
        "sudo useradd -rs /bin/false node_exporter || true",
        # Create service file
        f"""echo '[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/node_exporter.service""",
        "sudo systemctl daemon-reload",
        "sudo systemctl start node_exporter",
        "sudo systemctl enable node_exporter"
    ]
    
    for cmd in commands:
        if not ssh_command(ip, cmd, check=True):
            print(f"[{ip}] Failed to run: {cmd}")
            return False
            
    print(f"[{ip}] Installation successful.")
    return True

def ssh_command(ip, cmd, check=False):
    import subprocess
    
    if ip in ("127.0.0.1", "localhost"):
        # Executa localmente
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if check and result.returncode != 0:
                print(f"Error running command locally: {result.stderr}")
                return None
            return result.stdout
        except Exception as e:
            print(f"Local exception for {ip}: {e}")
            return None
    else:
        # Mantém SSH para hosts remotos
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"root@{ip}", cmd]
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            if check and result.returncode != 0:
                print(f"Error running command on {ip}: {result.stderr}")
                return None
            return result.stdout
        except Exception as e:
            print(f"SSH exception for {ip}: {e}")
            return None

def main():
    hosts = load_hosts()
    targets = load_targets()
    
    if not hosts:
        print("No hosts found in hosts.txt")
        return

    updated = False
    for ip in hosts:
        if not is_target_configured(ip, targets):
            print(f"Processing new host: {ip}")
            if install_node_exporter(ip):
                targets = add_target(ip, targets)
                updated = True
            else:
                print(f"Skipping configuration for {ip} due to installation failure.")
        else:
            print(f"Host {ip} already configured.")

    if updated:
        save_targets(targets)
        print(f"Updated {TARGETS_FILE}. Prometheus should pick up changes automatically.")
    else:
        print("No changes made to targets.")

if __name__ == "__main__":
    main()
