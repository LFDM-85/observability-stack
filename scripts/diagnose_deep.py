import os
import subprocess
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
USERNAME = 'root'

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

def ssh_exec(ip, cmd, description):
    print(f"   > {description}...")
    ssh_cmd = [
        "ssh", 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "ConnectTimeout=5", 
        f"{USERNAME}@{ip}", 
        cmd
    ]
    try:
        result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            return f"ERROR: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

def main():
    hosts = load_hosts()
    print(f"Starting deep diagnosis on {len(hosts)} hosts...")
    print("="*60)

    for ip, specific_user in hosts:
        print(f"\n[{ip}] Diagnosing...")
        
        # 1. Connectivity
        ping = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
        if ping != 0:
            print("   ⚠️  PING FAILED - Host might be down or ICMP blocked")
        
        # 2. Check detected containers (for MySQL detection debugging)
        containers = ssh_exec(ip, "docker ps --format '{{.ID}} | {{.Image}} | {{.Names}}'", "Listing Docker Containers")
        print(f"   📦 Containers:\n{containers}")
        
        # 3. Check Services Status
        services = ["node_exporter", "cadvisor", "mysqld_exporter"]
        for svc in services:
            status = ssh_exec(ip, f"systemctl status {svc} | grep 'Active:'", f"Checking {svc}")
            print(f"   ⚙️  {svc}: {status}")

        # 4. Check Listening Ports
        ports = ssh_exec(ip, "netstat -tuln | grep -E '9100|9991|9104'", "Checking Open Ports")
        print(f"   🔌 Listen Ports:\n{ports}")
        
        # 5. Check Firewall
        firewall = ssh_exec(ip, "ufw status 2>/dev/null || echo 'UFW not found'", "Checking Firewall")
        print(f"   🛡️  Firewall: {firewall}")

if __name__ == "__main__":
    main()
