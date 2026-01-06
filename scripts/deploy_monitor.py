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
    os.makedirs(os.path.dirname(TARGETS_FILE), exist_ok=True)
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

def ssh_command(ip, cmd, check=False):
    """Execute command locally or via SSH"""
    local_ips = ("127.0.0.1", "localhost", "192.168.1.148")
    if ip in local_ips:
        # Executar localmente
        try:
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if check and result.returncode != 0:
                print(f"[{ip}] Error: {result.stderr.strip() or 'Command failed'}")
                return None
            return result.stdout
        except Exception as e:
            print(f"[{ip}] Exception: {e}")
            return None
    else:
        # Executar remotamente via SSH
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"root@{ip}", cmd]
        try:
            result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if check and result.returncode != 0:
                print(f"[{ip}] SSH Error: {result.stderr.strip()}")
                return None
            return result.stdout
        except Exception as e:
            print(f"[{ip}] SSH Exception: {e}")
            return None

def install_node_exporter(ip):
    print(f"[{ip}] Checking/Installing Node Exporter...")
    
    # Check if binary exists
    check_bin_cmd = "ls /usr/local/bin/node_exporter"
    res_bin = ssh_command(ip, check_bin_cmd)
    
    # Check if already running
    check_svc_cmd = "systemctl is-active node_exporter"
    res_svc = ssh_command(ip, check_svc_cmd)
    
    if (res_bin and "/usr/local/bin/node_exporter" in res_bin) or (res_svc and res_svc.strip() == "active"):
        print(f"[{ip}] Node Exporter is already installed/active.")
        # Ensure it's started and enabled if it exists but is not active
        if not (res_svc and res_svc.strip() == "active"):
            print(f"[{ip}] Starting and enabling existing Node Exporter...")
            ssh_command(ip, "sudo systemctl daemon-reload && sudo systemctl start node_exporter && sudo systemctl enable node_exporter", check=True)
        return True

    print(f"[{ip}] Installing Node Exporter v{NODE_EXPORTER_VERSION}...")
    
    # Check for wget if running locally and installation is needed
    if ip in ("127.0.0.1", "localhost", "192.168.1.148"):
        res_wget = ssh_command(ip, "wget --version")
        if not res_wget:
            print(f"[{ip}] Warning: 'wget' is not installed. If Node Exporter download is needed, this will fail.")
    
    # Installation commands
    commands = [
        f"cd /tmp && wget -q https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"cd /tmp && tar xvfz node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"sudo mv /tmp/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/",
        "rm -rf /tmp/node_exporter-*",
        "sudo useradd -rs /bin/false node_exporter 2>/dev/null || true",
        """echo '[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/node_exporter.service > /dev/null""",
        "sudo systemctl daemon-reload",
        "sudo systemctl start node_exporter",
        "sudo systemctl enable node_exporter"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"[{ip}] Step {i+1}/{len(commands)}: Running...")
        result = ssh_command(ip, cmd, check=True)
        if result is None:
            print(f"[{ip}] Installation failed at step {i+1}")
            return False
            
    print(f"[{ip}] Installation successful.")
    return True

def main():
    hosts = load_hosts()
    targets = load_targets()
    
    if not hosts:
        print("❌ No hosts found in hosts.txt")
        return

    print(f"📋 Found {len(hosts)} host(s) to process\n")
    
    updated = False
    for ip in hosts:
        if not is_target_configured(ip, targets):
            print(f"\n▶️  Processing new host: {ip}")
            if install_node_exporter(ip):
                targets = add_target(ip, targets)
                updated = True
                print(f"✅ Host {ip} configured successfully")
            else:
                print(f"❌ Failed to configure {ip}")
        else:
            print(f"✓ Host {ip} already configured.")

    if updated:
        save_targets(targets)
        print(f"\n✅ Updated {TARGETS_FILE}")
        print("📊 Prometheus should pick up changes automatically")
    else:
        print("\n⚠️  No changes made to targets.")

if __name__ == "__main__":
    main()