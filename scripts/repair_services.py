import os
import subprocess
import time

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
USERNAME = 'root'
NODE_EXPORTER_VERSION = "1.8.2"

def load_hosts():
    if not os.path.exists(HOSTS_FILE):
        return []
    hosts = []
    with open(HOSTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '@' in line:
                user, ip = line.split('@', 1)
                hosts.append((ip.strip(), user.strip()))
            else:
                hosts.append((line, None))
    return hosts

def ssh_exec(ip, cmd, description=None):
    if description:
        print(f"[{ip}] {description}...")
    
    ssh_cmd = [
        "ssh", 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "ConnectTimeout=10", 
        f"{USERNAME}@{ip}", 
        cmd
    ]
    try:
        result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def repair_host(ip):
    print(f"\n🔧 Repairing {ip}...")
    
    # 1. Check current status and logs
    rc, stdout, stderr = ssh_exec(ip, "systemctl status node_exporter", "Checking status")
    if rc != 0:
        print(f"   ⚠️ Service is not healthy. Fetching logs...")
        _, logs, _ = ssh_exec(ip, "journalctl -u node_exporter -n 20 --no-pager", "Fetching logs")
        print(f"   📄 Logs tail:\n{logs}")
    
    # 2. Check Architecture
    _, arch, _ = ssh_exec(ip, "uname -m", "Checking architecture")
    print(f"   💻 Architecture: {arch}")
    
    # 3. Clean Reinstall
    print(f"   🔄 Performing clean reinstall...")
    
    # Stop and remove service
    ssh_exec(ip, "systemctl stop node_exporter && systemctl disable node_exporter")
    ssh_exec(ip, "rm -f /usr/local/bin/node_exporter /etc/systemd/system/node_exporter.service")
    
    # Download correct binary
    # Assuming AMD64 for now, but should ideally handle ARM if arch detects it
    # Most likely x86_64
    if "aarch64" in arch:
        dist = "arm64"
    else:
        dist = "linux-amd64"
        
    download_url = f"https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.{dist}.tar.gz"
    
    cmds = [
        f"cd /tmp && wget -q {download_url} || curl -L -O {download_url}",
        f"cd /tmp && tar xzf node_exporter-{NODE_EXPORTER_VERSION}.{dist}.tar.gz",
        f"cp /tmp/node_exporter-{NODE_EXPORTER_VERSION}.{dist}/node_exporter /usr/local/bin/",
        "chmod +x /usr/local/bin/node_exporter",
        # Create user if missing
        "id -u node_exporter &>/dev/null || useradd -rs /bin/false node_exporter",
        # Create Service
        """echo '[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target' > /etc/systemd/system/node_exporter.service""",
        "systemctl daemon-reload",
        "systemctl start node_exporter",
        "systemctl enable node_exporter"
    ]
    
    full_cmd = " && ".join(cmds)
    
    # Using 'bash -c' to handle redirects and multiple commands better in SSH
    rc, out, err = ssh_exec(ip, f"bash -c \"{full_cmd}\"", "Installing")
    
    if rc == 0:
        print(f"   ✅ Installation command successful.")
        # Verify
        time.sleep(2)
        rc, out, _ = ssh_exec(ip, "systemctl is-active node_exporter")
        if out == "active":
             print(f"   ✅ Service is ACTIVE.")
        else:
             print(f"   ❌ Service failed to start. Status: {out}")
    else:
        print(f"   ❌ Installation failed: {err}")

def main():
    hosts = load_hosts()
    # Filter only for the known problematic hosts + .131
    # User output showed failures on .131, .133, .134
    targets = ['192.168.1.131', '192.168.1.133', '192.168.1.134']
    
    print(f"Starting repair on target hosts: {targets}")
    
    for ip, _ in hosts:
        if ip in targets:
            repair_host(ip)

if __name__ == "__main__":
    main()
