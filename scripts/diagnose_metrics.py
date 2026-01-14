import os
import subprocess
import argparse

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
USERNAME = 'root'
METRIC_ENDPOINTS = [
    {'name': 'Node Exporter', 'port': 9100, 'url': 'http://localhost:9100/metrics', 'pattern': 'node_cpu_seconds_total'},
    {'name': 'cAdvisor', 'port': 9991, 'url': 'http://localhost:9991/metrics', 'pattern': 'container_cpu_usage_seconds_total'},
    {'name': 'MySQL Exporter', 'port': 9104, 'url': 'http://localhost:9104/metrics', 'pattern': 'mysql_up'}
]

def load_hosts():
    print(f"DEBUG: Looking for hosts file at {HOSTS_FILE}")
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

def ssh_check_metrics(ip, endpoint):
    """
    Connects to the remote host via SSH and curls the localhost metrics endpoint.
    Reason: This validates if the service is running and listening on localhost.
    Network firewalls might still block external access, but this proves the service is up.
    """
    # Use curl locally on the machine
    cmd = f"curl -s --connect-timeout 2 {endpoint['url']} | grep -q '{endpoint['pattern']}' && echo 'OK' || echo 'FAIL'"
    
    ssh_cmd = [
        "ssh", 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "ConnectTimeout=5", 
        f"{USERNAME}@{ip}", 
        cmd
    ]
    
    try:
        # On Windows, subprocess.run needs careful handling if ssh is involved
        result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode == 0 and "OK" in result.stdout:
            return "UP (Metrics Found)"
        elif result.returncode == 0 and "FAIL" in result.stdout:
            # Check if port is open but metrics missing or different
            return "DOWN (Service running but metrics missing?)"
        else:
            # Maybe service is down
            # Try to check if service is active
            service_cmd = f"systemctl is-active {endpoint['name'].lower().replace(' ', '_').replace('cadvisor', 'cadvisor')}"
            # Mapping service names might be tricky, try generic port check
            check_port = f"netstat -tuln | grep :{endpoint['port']}"
            check_res = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USERNAME}@{ip}", check_port], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if str(endpoint['port']) in check_res.stdout:
                return "FAIL (Port Open, Curl Failed)"
            else:
                return "DOWN (Port Closed)"
    except Exception as e:
        return f"ERROR ({str(e)})"

def main():
    hosts = load_hosts()
    if not hosts:
        print("No hosts found.")
        return

    print(f"{'HOST':<20} | {'SERVICE':<20} | {'STATUS':<30}")
    print("-" * 80)

    for ip, specific_user in hosts:
        # Note: simplistic user handling, assuming root or relying on ssh config if not provided
        # The deploy_monitor.py used global USERNAME or specific user.
        # Here we just use what we have or default to root.
        
        print(f"[{ip}] Checking...")
        for ep in METRIC_ENDPOINTS:
            status = ssh_check_metrics(ip, ep)
            print(f"{ip:<20} | {ep['name']:<20} | {status:<30}")

if __name__ == "__main__":
    main()
