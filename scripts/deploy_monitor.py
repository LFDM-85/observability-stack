import json
import os
import subprocess
import sys
import time
import argparse
# from fix_dashboards import fix_dashboards

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
TARGETS_FILE = os.path.join(BASE_DIR, 'prometheus', 'targets.json')

# Node Exporter Version
NODE_EXPORTER_VERSION = "1.8.2"

# CADVISOR Port
CADVISOR_PORT = "9991"

# Default Username
USERNAME = "root"

def test_ssh_connection(ip, username='root'):
    """Test if SSH key authentication is working."""
    if ip in ('127.0.0.1', 'localhost'):
        return True  # Localhost doesn't need SSH
    
    try:
        result = subprocess.run([
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'PasswordAuthentication=no',
            '-o', 'ConnectTimeout=5',
            '-o', 'BatchMode=yes',
            f'{username}@{ip}',
            'echo "test"'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        
        return result.returncode == 0
    except:
        return False

def detect_services(ip):
    """Detect what services are running on the target host."""
    if ip in ('127.0.0.1', 'localhost'):
        return {'docker': False, 'mysql': False, 'postgresql': False}
    
    services = {
        'docker': False,
        'mysql': False,
        'postgresql': False
    }
    
    print(f"🔍 Detecting services on {ip}...")
    
    # Check for Docker
    docker_check = ssh_command(ip, "docker --version 2>/dev/null", check=True)
    if docker_check and "Docker version" in docker_check:
        services['docker'] = True
        print(f"   ✓ Docker detected")
    
    # Check for MySQL/MariaDB (Systemd, Docker, or Port 3306)
    mysql_check = ssh_command(ip, "systemctl is-active mysql 2>/dev/null || systemctl is-active mariadb 2>/dev/null", check=True)
    mysql_docker_check = ""
    if services['docker']:
        mysql_docker_check = ssh_command(ip, "docker ps --format '{{.Image}} {{.Names}}' | grep -E 'mysql|mariadb' || true", check=True)
    
    # Also check TCP port 3306 (more reliable for custom Docker containers)
    mysql_port_check = ssh_command(ip, "netstat -tuln | grep :3306 || ss -tuln | grep :3306 || true", check=True)

    if (mysql_check and mysql_check.strip() == "active") or \
       (mysql_docker_check and mysql_docker_check.strip()) or \
       (mysql_port_check and "3306" in mysql_port_check):
        services['mysql'] = True
        print(f"   ✓ MySQL/MariaDB detected")
    
    # Check for PostgreSQL
    postgres_check = ssh_command(ip, "systemctl is-active postgresql 2>/dev/null", check=True)
    if postgres_check and "active" in postgres_check:
        services['postgresql'] = True
        print(f"   ✓ PostgreSQL detected")
    
    if not any(services.values()):
        print(f"   ℹ️  No additional services detected (Docker, MySQL, PostgreSQL)")
    
    return services

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
        if t.get('labels', {}).get('job') == 'remote_hosts':
            if target_str not in t['targets']:
                t['targets'].append(target_str)
            found = True
            break
    
    if not found:
        targets.append({
            "targets": [target_str],
            "labels": {
                "job": "remote_hosts",
                "env": "internal"
            }
        })
    return targets

def add_docker_target(ip):
    """Add cAdvisor target for Docker monitoring."""
    docker_targets_file = os.path.join(BASE_DIR, 'prometheus', 'docker_targets.json')
    
    # Load existing targets
    if os.path.exists(docker_targets_file):
        with open(docker_targets_file, 'r') as f:
            try:
                targets = json.load(f)
            except json.JSONDecodeError:
                targets = []
    else:
        targets = []
    
    target_str = f"{ip}:{CADVISOR_PORT}"
    
    # Check if target already exists
    found = False
    for t in targets:
        if target_str in t.get('targets', []):
            return
        if t.get('labels', {}).get('job') == 'remote_docker':
            if target_str not in t['targets']:
                t['targets'].append(target_str)
            found = True
            break
    
    if not found:
        targets.append({
            "targets": [target_str],
            "labels": {
                "env": "internal"
            }
        })
    
    # Save targets
    os.makedirs(os.path.dirname(docker_targets_file), exist_ok=True)
    with open(docker_targets_file, 'w') as f:
        json.dump(targets, f, indent=2)
    
    print(f"✅ Added Docker target: {target_str}")

def add_mysql_target(ip):
    """Add MySQL exporter target for database monitoring."""
    mysql_targets_file = os.path.join(BASE_DIR, 'prometheus', 'mysql_targets.json')
    
    # Load existing targets
    if os.path.exists(mysql_targets_file):
        with open(mysql_targets_file, 'r') as f:
            try:
                targets = json.load(f)
            except json.JSONDecodeError:
                targets = []
    else:
        targets = []
    
    target_str = f"{ip}:9104"
    
    # Check if target already exists
    found = False
    for t in targets:
        if target_str in t.get('targets', []):
            return
        if t.get('labels', {}).get('job') == 'remote_mysql':
            if target_str not in t['targets']:
                t['targets'].append(target_str)
            found = True
            break
    
    if not found:
        targets.append({
            "targets": [target_str],
            "labels": {
                "env": "internal"
            }
        })
    
    # Save targets
    os.makedirs(os.path.dirname(mysql_targets_file), exist_ok=True)
    with open(mysql_targets_file, 'w') as f:
        json.dump(targets, f, indent=2)
    
    print(f"✅ Added MySQL target: {target_str}")

def ssh_command(ip, cmd, check=False):
    """Execute command locally or via SSH"""
    # Loopback is always local
    is_loopback = ip in ("127.0.0.1", "localhost")
    
    if is_loopback:
        # Executar localmente
        try:
            # On Windows, we should translate some basic things or just fail if it's a linux cmd
            if os.name == 'nt' and not is_loopback:
                print(f"[{ip}] Warning: Running Linux commands on Windows might fail.")
            
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if check and result.returncode != 0:
                # Silêncio para comandos de check, erro para comandos de ação
                if not cmd.startswith('ls ') and not cmd.startswith('systemctl is-active'):
                    print(f"[{ip}] Error: {result.stderr.strip() or 'Command failed'}")
                return None
            return result.stdout
        except Exception as e:
            print(f"[{ip}] Exception: {e}")
            return None
    else:
        # Executar remotamente via SSH
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"{USERNAME}@{ip}", cmd]
        # If on Windows, we might need to ensure ssh is available, but usually it is in modern Win10/11
        try:
            result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if check and result.returncode != 0:
                # Only show error if not a check command
                if not cmd.startswith('ls ') and not cmd.startswith('systemctl is-active'):
                    print(f"[{ip}] SSH Error: {result.stderr.strip()}")
                return None
            return result.stdout
        except Exception as e:
            if not cmd.startswith('ls ') and not cmd.startswith('systemctl is-active'):
                print(f"[{ip}] SSH Connection Error: {e}")
                print(f"[{ip}] TIP: Ensure SSH is enabled and authorized_keys is configured for root.")
            return None

def install_node_exporter(ip, arch="amd64"):
    """Install Node Exporter on the given IP"""
    print(f"🔧 Installing Node Exporter on {ip}...")
    
    # Skip localhost - it's already monitored by the node-exporter container
    if ip in ('127.0.0.1', 'localhost'):
        print(f"⏭️  Skipping {ip} - already monitored by node-exporter service")
        return True
    
    # Check if Node Exporter is already installed and running
    # check=False because is-active returns non-zero if not active, we want to handle that string
    check_cmd = "systemctl is-active node_exporter"
    status = ssh_command(ip, check_cmd, check=False)
    
    if status and status.strip() == "active":
        print(f"✓ Node Exporter already running on {ip}")
        return True
    
    should_reinstall = False
    
    if status and ("failed" in status or "activating" in status):
        print(f"⚠️  Node Exporter service is in state: {status.strip()}. Scheduling clean reinstall...")
        should_reinstall = True
    elif status and "inactive" in status:
        print(f"ℹ️  Node Exporter service exists but is inactive. Attempting to start...")
        ssh_command(ip, "systemctl start node_exporter", check=True)
        time.sleep(2)
        # Check again
        new_status = ssh_command(ip, check_cmd, check=False)
        if new_status and new_status.strip() == "active":
             print(f"✓ Node Exporter started successfully")
             return True
        else:
             print(f"⚠️  Failed to start existing service (Status: {new_status.strip() if new_status else 'Unknown'}). Scheduling clean reinstall...")
             should_reinstall = True
             
    if should_reinstall:
        # Force stop and cleanup to allow fresh install
        print(f"   🧹 Removing old service and binary...")
        ssh_command(ip, "systemctl stop node_exporter", check=False)
        ssh_command(ip, "systemctl disable node_exporter", check=False)
        ssh_command(ip, "rm -f /etc/systemd/system/node_exporter.service", check=False)
        ssh_command(ip, "rm -f /usr/local/bin/node_exporter", check=False)
        # Proceed to installation logic below...
    else:
        # Check if binary exists but service isn't running (and wasn't just checked above)
        check_bin_cmd = "ls /usr/local/bin/node_exporter"
        res_bin = ssh_command(ip, check_bin_cmd, check=False)
        
        if res_bin and "/usr/local/bin/node_exporter" in res_bin:
            print(f"[{ip}] Node Exporter binary found, but service not active/configured. Starting/Enabling...")
            sudo = "sudo " if USERNAME != "root" else ""
            res = ssh_command(ip, f"{sudo}systemctl daemon-reload && {sudo}systemctl start node_exporter && {sudo}systemctl enable node_exporter", check=False)
            
            # Verify if it actually started
            time.sleep(2)
            final_status = ssh_command(ip, check_cmd, check=False)
            if final_status and final_status.strip() == "active":
                return True
            else:
                print(f"⚠️  Failed to start existing binary. It might be corrupted. Proceeding with reinstall...")
                # Cleanup
                ssh_command(ip, "rm -f /usr/local/bin/node_exporter", check=False)


    print(f"[{ip}] Installing Node Exporter v{NODE_EXPORTER_VERSION} ({arch})...")
    
    # Check for wget if running locally and installation is needed
    if ip in ("127.0.0.1", "localhost"):
        res_wget = ssh_command(ip, "wget --version")
        if not res_wget:
            print(f"[{ip}] Warning: 'wget' is not installed. If Node Exporter download is needed, this will fail.")
    
    # Installation commands
    sudo = "sudo " if USERNAME != "root" else ""
    commands = [
        f"cd /tmp && wget -q https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.linux-{arch}.tar.gz",
        f"cd /tmp && tar xvfz node_exporter-{NODE_EXPORTER_VERSION}.linux-{arch}.tar.gz",
        f"{sudo}mv /tmp/node_exporter-{NODE_EXPORTER_VERSION}.linux-{arch}/node_exporter /usr/local/bin/",
        "rm -rf /tmp/node_exporter-*",
        f"{sudo}useradd -rs /bin/false node_exporter 2>/dev/null || true",
        f"""echo '[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target' | {sudo}tee /etc/systemd/system/node_exporter.service > /dev/null""",
        f"{sudo}systemctl daemon-reload",
        f"{sudo}systemctl start node_exporter",
        f"{sudo}systemctl enable node_exporter"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"[{ip}] Step {i+1}/{len(commands)}: Running...")
        result = ssh_command(ip, cmd, check=True)
        if result is None:
            print(f"[{ip}] Installation failed at step {i+1}")
            return False
            
    print(f"[{ip}] Installation successful.")
    return True

def install_cadvisor(ip):
    """Install cAdvisor for Docker container monitoring."""
    print(f"🐳 Installing cAdvisor on {ip}...")
    
    # Check if already running
    check_cmd = "systemctl is-active cadvisor"
    if ssh_command(ip, check_cmd, check=True) and ssh_command(ip, check_cmd, check=True).strip() == "active":
        print(f"✓ cAdvisor already running on {ip}")
        return True
    
    # cAdvisor version
    cadvisor_version = "v0.47.0"
    
    # Installation commands
    sudo = "sudo " if USERNAME != "root" else ""
    commands = [
        f"cd /tmp && wget -q https://github.com/google/cadvisor/releases/download/{cadvisor_version}/cadvisor-{cadvisor_version}-linux-amd64",
        f"chmod +x /tmp/cadvisor-{cadvisor_version}-linux-amd64",
        f"{sudo}mv /tmp/cadvisor-{cadvisor_version}-linux-amd64 /usr/local/bin/cadvisor",
        f"""echo '[Unit]
Description=cAdvisor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cadvisor -port={CADVISOR_PORT}
Restart=always

[Install]
WantedBy=multi-user.target' | {sudo}tee /etc/systemd/system/cadvisor.service > /dev/null""",
        f"{sudo}systemctl daemon-reload",
        f"{sudo}systemctl start cadvisor",
        f"{sudo}systemctl enable cadvisor"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"[{ip}] Step {i+1}/{len(commands)}: Running...")
        result = ssh_command(ip, cmd, check=True)
        if result is None:
            print(f"[{ip}] cAdvisor installation failed at step {i+1}")
            return False
            
    print(f"[{ip}] cAdvisor installation successful.")
    return True

def install_mysqld_exporter(ip):
    """Install MySQL/MariaDB exporter for database monitoring."""
    print(f"🗄️  Installing MySQL Exporter on {ip}...")
    
    # Check if already running
    check_cmd = "systemctl is-active mysqld_exporter"
    if ssh_command(ip, check_cmd, check=True) and ssh_command(ip, check_cmd, check=True).strip() == "active":
        print(f"✓ MySQL Exporter already running on {ip}")
        return True
    
    # MySQL Exporter version
    exporter_version = "0.15.1"
    
    # Create MySQL monitoring user
    print(f"[{ip}] Creating MySQL monitoring user...")
    sudo = "sudo " if USERNAME != "root" else ""
    mysql_user_cmd = f"""{sudo}mysql -e "CREATE USER IF NOT EXISTS 'exporter'@'localhost' IDENTIFIED BY 'exporterpass' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;" 2>/dev/null || \
{sudo}mariadb -e "CREATE USER IF NOT EXISTS 'exporter'@'localhost' IDENTIFIED BY 'exporterpass' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;" 2>/dev/null"""
    
    result = ssh_command(ip, mysql_user_cmd, check=True)
    if result is None:
        print(f"⚠️  Could not create MySQL user. Continuing anyway (may already exist)...")
    
    # Installation commands
    sudo = "sudo " if USERNAME != "root" else ""
    commands = [
        f"cd /tmp && wget -q https://github.com/prometheus/mysqld_exporter/releases/download/v{exporter_version}/mysqld_exporter-{exporter_version}.linux-amd64.tar.gz",
        f"cd /tmp && tar xzf mysqld_exporter-{exporter_version}.linux-amd64.tar.gz",
        f"{sudo}mv /tmp/mysqld_exporter-{exporter_version}.linux-amd64/mysqld_exporter /usr/local/bin/",
        "rm -rf /tmp/mysqld_exporter-*",
        f"{sudo}useradd -rs /bin/false mysqld_exporter 2>/dev/null || true",
        f"{sudo}mkdir -p /etc/mysqld_exporter",
        f"""echo 'DATA_SOURCE_NAME="exporter:exporterpass@(localhost:3306)/"' | {sudo}tee /etc/mysqld_exporter/mysqld_exporter.env > /dev/null""",
        f"{sudo}chmod 600 /etc/mysqld_exporter/mysqld_exporter.env",
        f"""echo '[Unit]
Description=MySQL Exporter
After=network.target

[Service]
Type=simple
User=mysqld_exporter
EnvironmentFile=/etc/mysqld_exporter/mysqld_exporter.env
ExecStart=/usr/local/bin/mysqld_exporter --web.listen-address=:9104
Restart=always

[Install]
WantedBy=multi-user.target' | {sudo}tee /etc/systemd/system/mysqld_exporter.service > /dev/null""",
        f"{sudo}systemctl daemon-reload",
        f"{sudo}systemctl start mysqld_exporter",
        f"{sudo}systemctl enable mysqld_exporter"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"[{ip}] Step {i+1}/{len(commands)}: Running...")
        result = ssh_command(ip, cmd, check=True)
        if result is None:
            print(f"[{ip}] MySQL Exporter installation failed at step {i+1}")
            return False
            
    print(f"[{ip}] MySQL Exporter installation successful.")
    return True

def verify_cadvisor_running(ip):
    """Verify that cAdvisor is running and accessible."""
    print(f"🔍 Verifying cAdvisor on {ip}...")

    # Check if service is active
    status = ssh_command(ip, "systemctl is-active cadvisor", check=False)
    if not status or status.strip() != "active":
        print(f"   ✗ cAdvisor service is not active (status: {status.strip() if status else 'unknown'})")
        return False
    print(f"   ✓ cAdvisor service is active")

    # Check if port is listening
    port_check = ssh_command(ip, f"netstat -tuln | grep :{CADVISOR_PORT} || ss -tuln | grep :{CADVISOR_PORT}", check=False)
    if not port_check:
        print(f"   ✗ Port {CADVISOR_PORT} is not listening")
        return False
    print(f"   ✓ Port {CADVISOR_PORT} is listening")

    # Check Docker socket permissions
    docker_socket_check = ssh_command(ip, "ls -l /var/run/docker.sock", check=False)
    if docker_socket_check:
        print(f"   ✓ Docker socket accessible: {docker_socket_check.strip()}")

    # Try to fetch metrics from cAdvisor
    metrics_check = ssh_command(ip, f"curl -s http://localhost:{CADVISOR_PORT}/metrics | head -5", check=False)
    if not metrics_check or "container_" not in metrics_check:
        print(f"   ✗ cAdvisor metrics endpoint not responding correctly")
        return False
    print(f"   ✓ cAdvisor metrics endpoint responding")

    return True

def verify_target_health(ip, timeout=30):
    """Verify that Prometheus can scrape the target."""
    import requests
    import time

    target_endpoint = f"{ip}:9100"
    if ip in ('127.0.0.1', 'localhost'):
        return True  # Skip localhost verification

    print(f"🔍 Verifying target health for {target_endpoint}...")

    prometheus_url = "http://localhost:9990/api/v1/targets"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(prometheus_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for target in data.get('data', {}).get('activeTargets', []):
                    if target_endpoint in target.get('scrapeUrl', ''):
                        health = target.get('health')
                        if health == 'up':
                            print(f"✓ Target {target_endpoint} is UP and healthy")
                            return True
                        else:
                            print(f"⚠️  Target {target_endpoint} status: {health}")
        except requests.exceptions.ConnectionError:
            print(f"[{ip}] Prometheus not reachable at {prometheus_url}. Retrying...")
        except Exception as e:
            print(f"[{ip}] Error verifying target health: {e}")

        time.sleep(2)

    print(f"⚠️  Could not verify target health within {timeout}s")
    return False

def verify_prometheus_scraping(ip, port, job_name, timeout=30):
    """Verify that Prometheus can scrape a specific target endpoint."""
    import requests
    import time

    if ip in ('127.0.0.1', 'localhost'):
        return True

    target_endpoint = f"{ip}:{port}"
    print(f"🔍 Verifying Prometheus can scrape {target_endpoint} (job: {job_name})...")

    prometheus_url = "http://localhost:9990/api/v1/targets"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(prometheus_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for target in data.get('data', {}).get('activeTargets', []):
                    scrape_url = target.get('scrapeUrl', '')
                    if target_endpoint in scrape_url:
                        health = target.get('health')
                        last_error = target.get('lastError', '')

                        if health == 'up':
                            print(f"   ✓ Prometheus scraping {target_endpoint} successfully")
                            return True
                        else:
                            print(f"   ✗ Prometheus scrape status: {health}")
                            if last_error:
                                print(f"   Error: {last_error}")
                            return False
        except requests.exceptions.ConnectionError:
            pass  # Prometheus not ready yet
        except Exception as e:
            print(f"   ⚠️  Error checking Prometheus: {e}")

        time.sleep(2)

    print(f"   ⚠️  Could not verify Prometheus scraping within {timeout}s")
    print(f"   💡 Tip: Check if Prometheus container is running and {target_endpoint} is reachable from Prometheus")
    return False

def main():
    parser = argparse.ArgumentParser(
        description='Deploy Node Exporter to monitoring targets',
        epilog='Example: python3 deploy_monitor.py --setup-keys'
    )
    parser.add_argument('--setup-keys', action='store_true',
                       help='Setup SSH keys before deployment')
    parser.add_argument('--skip-health-check', action='store_true',
                       help='Skip health verification after deployment')
    parser.add_argument('--username', '-u', default='root',
                       help='SSH username (default: root)')
    args = parser.parse_args()
    
    global USERNAME
    USERNAME = args.username
    
    print("🚀 Node Exporter Deployment Script")
    print("=" * 50)
    
    # Check if setup_ssh_key.py exists and offer to run it
    if args.setup_keys:
        setup_script = os.path.join(BASE_DIR, 'scripts', 'setup_ssh_key.py')
        if os.path.exists(setup_script):
            print("\n🔐 Running SSH key setup...\n")
            result = subprocess.run(['python3', setup_script, '--all'])
            if result.returncode != 0:
                print("\n⚠️  SSH key setup had issues. Continue anyway? (y/n): ", end='')
                if input().lower() != 'y':
                    sys.exit(1)
            print()
    
    hosts = load_hosts()
    if not hosts:
        print("⚠️  No hosts found in hosts.txt")
        return
    
    print(f"📋 Found {len(hosts)} host(s) to process\n")
    
    targets = load_targets()
    changes_made = False
    results = []
    service_status = {}  # Track detailed service status per host

    for ip, specific_user in hosts:
        # Determine which user to use for this host
        current_username = specific_user if specific_user else USERNAME
        
        print(f"\n{'='*50}")
        print(f"Processing: {current_username}@{ip}")
        print(f"{'='*50}\n")
        
        # Skip localhost - already monitored
        if ip in ('127.0.0.1', 'localhost'):
            print(f"⏭️  Skipping {ip} - already monitored by node-exporter service\n")
            results.append((ip, 'skipped'))
            continue
        
        # Check SSH connectivity
        # IMPORTANT: We must temporarily update the global USERNAME so helper functions use it
        # This is a hack because helper functions rely on global USERNAME
        original_global_username = USERNAME
        USERNAME = current_username
        
        if not test_ssh_connection(ip, current_username):
            print(f"✗ SSH key authentication failed for {current_username}@{ip}")
            print(f"   Please run: python3 scripts/setup_ssh_key.py {ip} --username {current_username}")
            print(f"   Or run with --setup-keys flag\n")
            results.append((ip, 'ssh_failed'))
            # Restore global username before continuing
            USERNAME = original_global_username
            continue

        
        
        # Validate OS and Architecture
        os_info = ssh_command(ip, "cat /etc/os-release | grep PRETTY_NAME", check=False) or "Unknown Linux"
        os_name = os_info.replace('PRETTY_NAME=', '').strip().strip('"')
        print(f"   💻 OS: {os_name}")
        
        arch = ssh_command(ip, "uname -m", check=True).strip()
        go_arch = "amd64"
        if "aarch64" in arch or "armv8" in arch:
            go_arch = "arm64"
        elif "armv7" in arch:
            go_arch = "armv7"
        print(f"   cpu: {arch} (binary: {go_arch})")
        
        # Check port availability (firewall or other services)
        print(f"   🔍 Checking ports...")
        for port, name in [(9100, "Node Exporter"), (9991, "cAdvisor"), (9104, "MySQL Exporter")]:
            # Check if port is listening
            listening = ssh_command(ip, f"netstat -tuln | grep :{port} || ss -tuln | grep :{port}", check=False)
            if listening:
               # Check if it's our service
               proc = ssh_command(ip, f"lsof -i :{port} || netstat -tulpn | grep :{port}", check=False)
               print(f"      - Port {port} ({name}) is LISTENING")
            else:
               # Validate if we can bind (not blocked by firewall logic, but verifies if free)
               print(f"      - Port {port} ({name}) is FREE")

        # Detect services on the host
        detected_services = detect_services(ip)
        print()  # Blank line for readability
        
        # Initialize service status for this host
        service_status[ip] = {
            'node_exporter': {'installed': False, 'healthy': False},
            'cadvisor': {'installed': False, 'healthy': False, 'prometheus_scrape': False},
            'mysql_exporter': {'installed': False, 'healthy': False}
        }

        # Always ensure Node Exporter is installed and running
        node_exporter_success = install_node_exporter(ip, go_arch)
        service_status[ip]['node_exporter']['installed'] = node_exporter_success

        if node_exporter_success:
            # Add to targets if not already present
            if not is_target_configured(ip, targets):
                targets = add_target(ip, targets)
                changes_made = True

            # Install cAdvisor if Docker is detected
            if detected_services.get('docker'):
                cadvisor_installed = install_cadvisor(ip)
                service_status[ip]['cadvisor']['installed'] = cadvisor_installed

                if cadvisor_installed:
                    add_docker_target(ip)
                    print(f"✅ Docker monitoring configured for {ip}")

                    # Verify cAdvisor is actually working
                    cadvisor_healthy = verify_cadvisor_running(ip)
                    service_status[ip]['cadvisor']['healthy'] = cadvisor_healthy

                    if cadvisor_healthy:
                        print(f"✅ cAdvisor verified and working on {ip}")

                        # Check if Prometheus can scrape it
                        if not args.skip_health_check:
                            prometheus_scrape = verify_prometheus_scraping(ip, CADVISOR_PORT, 'remote_docker', timeout=15)
                            service_status[ip]['cadvisor']['prometheus_scrape'] = prometheus_scrape
                    else:
                        print(f"⚠️  cAdvisor installed but not responding correctly on {ip}")
                        print(f"   💡 Tip: Run 'python3 scripts/diagnose_monitoring.py {ip}' for detailed diagnostics")
                else:
                    print(f"⚠️  Failed to install cAdvisor on {ip}")

            # Install MySQL Exporter if MySQL is detected
            if detected_services.get('mysql'):
                mysql_installed = install_mysqld_exporter(ip)
                service_status[ip]['mysql_exporter']['installed'] = mysql_installed

                if mysql_installed:
                    add_mysql_target(ip)
                    print(f"✅ MySQL monitoring configured for {ip}")

                    # Verify MySQL Exporter health
                    if not args.skip_health_check:
                        mysql_scrape = verify_prometheus_scraping(ip, '9104', 'remote_mysql', timeout=15)
                        service_status[ip]['mysql_exporter']['prometheus_scrape'] = mysql_scrape
                else:
                    print(f"⚠️  Failed to install MySQL Exporter on {ip}")

            print(f"✅ Host {ip} processed successfully")

            if not args.skip_health_check:
                node_health = verify_target_health(ip)
                service_status[ip]['node_exporter']['healthy'] = node_health

                if node_health:
                    results.append((ip, 'healthy'))
                else:
                    results.append((ip, 'unhealthy'))
            else:
                results.append((ip, 'skipped_health'))
        else:
            print(f"❌ Failed to ensure Node Exporter on {ip}")
            results.append((ip, 'failed'))
        
        # Restore global username for next iteration
        USERNAME = original_global_username

    # Save targets if there were changes
    if changes_made:
        save_targets(targets)
        print(f"\n✅ Updated {TARGETS_FILE}")
        print("📊 Prometheus should pick up changes automatically")

    # Always ensure dashboards are correctly configured
    # print("\n🔧 Checking Grafana dashboards...")
    # fix_dashboards()

    # Display summary
    print("\n" + "="*50)
    print("📊 Deployment Summary:")
    print("="*50)
    for ip, status in results:
        status_icons = {
            'skipped': '⏭️',
            'ssh_failed': '✗',
            'configured_healthy': '✓',
            'configured_unhealthy': '⚠️',
            'configured_skipped_health': '⏭️',
            'configured_install_failed': '✗',
            'new_healthy': '✓',
            'new_unhealthy': '⚠️',
            'new_skipped_health': '⏭️',
            'new_failed': '✗',
            'healthy': '✓',
            'unhealthy': '⚠️',
            'failed': '✗'
        }
        icon = status_icons.get(status, '?')
        status_text = status.replace('_', ' ').title()
        print(f"{icon} {ip:20s} - {status_text}")

    # Display detailed service status
    if service_status:
        print("\n" + "="*50)
        print("🔍 Detailed Service Status:")
        print("="*50)

        for ip, services in service_status.items():
            print(f"\n📍 {ip}:")

            # Node Exporter
            ne_status = services['node_exporter']
            if ne_status['installed']:
                health_icon = '✓' if ne_status['healthy'] else '⚠️'
                print(f"   {health_icon} Node Exporter: Installed & {'Healthy' if ne_status['healthy'] else 'Needs attention'}")
            else:
                print(f"   ✗ Node Exporter: Installation failed")

            # cAdvisor
            ca_status = services['cadvisor']
            if ca_status['installed']:
                if ca_status['healthy']:
                    scrape_icon = '✓' if ca_status['prometheus_scrape'] else '⚠️'
                    scrape_text = 'Prometheus scraping OK' if ca_status['prometheus_scrape'] else 'Prometheus cannot scrape'
                    print(f"   {scrape_icon} cAdvisor: Installed & Healthy - {scrape_text}")
                else:
                    print(f"   ⚠️  cAdvisor: Installed but not responding")
            elif ne_status['installed']:
                print(f"   ℹ️  cAdvisor: Not installed (Docker not detected)")

            # MySQL Exporter
            mysql_status = services['mysql_exporter']
            if mysql_status['installed']:
                scrape_icon = '✓' if mysql_status.get('prometheus_scrape') else '⚠️'
                scrape_text = 'Prometheus scraping OK' if mysql_status.get('prometheus_scrape') else 'Check Prometheus scraping'
                print(f"   {scrape_icon} MySQL Exporter: Installed - {scrape_text}")
            elif ne_status['installed']:
                print(f"   ℹ️  MySQL Exporter: Not installed (MySQL not detected)")

    # Identify issues and provide recommendations
    print("\n" + "="*50)
    print("💡 Recommendations:")
    print("="*50)

    failed_ssh = [ip for ip, status in results if status == 'ssh_failed']
    if failed_ssh:
        print("\n🔐 SSH Connection Issues:")
        print(f"   - Run: python3 scripts/setup_ssh_key.py --all")
        print(f"   - Or manually: python3 scripts/setup_ssh_key.py {failed_ssh[0]}")

    # Check for cAdvisor issues
    cadvisor_issues = []
    for ip, services in service_status.items():
        ca = services['cadvisor']
        if ca['installed'] and not ca['healthy']:
            cadvisor_issues.append(ip)
        elif ca['installed'] and ca['healthy'] and not ca['prometheus_scrape']:
            cadvisor_issues.append(ip)

    if cadvisor_issues:
        print("\n🐳 cAdvisor Issues Detected:")
        for ip in cadvisor_issues:
            print(f"   - {ip}: Run diagnostics with: python3 scripts/diagnose_monitoring.py {ip}")
        print("\n   Common solutions:")
        print("   1. Check firewall: sudo firewall-cmd --add-port=9991/tcp --permanent && sudo firewall-cmd --reload")
        print("   2. Check cAdvisor logs: journalctl -u cadvisor -n 50")
        print("   3. Restart cAdvisor: sudo systemctl restart cadvisor")
        print(f"   4. Verify from Prometheus container can reach the host: docker exec -it prometheus wget -O- http://<IP>:{CADVISOR_PORT}/metrics")

    # Check if Prometheus is accessible
    prometheus_accessible = False
    for ip, services in service_status.items():
        if services['cadvisor'].get('prometheus_scrape') or services['mysql_exporter'].get('prometheus_scrape'):
            prometheus_accessible = True
            break

    if not prometheus_accessible and not args.skip_health_check:
        print("\n⚠️  Prometheus Health Check:")
        print("   - Could not verify Prometheus scraping. Ensure Prometheus container is running:")
        print("   - Run: docker-compose ps prometheus")
        print("   - Check Prometheus targets: http://localhost:9990/targets")

    print("\n✅ Deployment complete!")
    print("\n📊 Next steps:")
    print("   1. Check Prometheus targets: http://localhost:9990/targets")
    print("   2. View Grafana dashboards: http://localhost:3000")
    print("   3. Run health check: python3 scripts/check_health.py")
    print("   4. Verify targets: python3 scripts/verify_prometheus_targets.py")

if __name__ == "__main__":
    main()