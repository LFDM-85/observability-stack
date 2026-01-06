import json
import os
import subprocess
import sys
import time
import argparse
from fix_dashboards import fix_dashboards

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')
TARGETS_FILE = os.path.join(BASE_DIR, 'prometheus', 'targets.json')

# Node Exporter Version
NODE_EXPORTER_VERSION = "1.8.2"

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
                "env": "production"
            }
        })
    return targets

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
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"root@{ip}", cmd]
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

def install_node_exporter(ip):
    """Install Node Exporter on the given IP"""
    print(f"🔧 Installing Node Exporter on {ip}...")
    
    # Skip localhost - it's already monitored by the node-exporter container
    if ip in ('127.0.0.1', 'localhost'):
        print(f"⏭️  Skipping {ip} - already monitored by node-exporter service")
        return True
    
    # Check if Node Exporter is already installed and running
    check_cmd = "systemctl is-active node_exporter"
    if ssh_command(ip, check_cmd, check=True) and ssh_command(ip, check_cmd, check=True).strip() == "active":
        print(f"✓ Node Exporter already running on {ip}")
        return True
    
    # Check if binary exists but service isn't running
    check_bin_cmd = "ls /usr/local/bin/node_exporter"
    res_bin = ssh_command(ip, check_bin_cmd)
    
    if res_bin and "/usr/local/bin/node_exporter" in res_bin:
        print(f"[{ip}] Node Exporter binary found, but service not active. Starting and enabling...")
        ssh_command(ip, "systemctl daemon-reload && systemctl start node_exporter && systemctl enable node_exporter", check=True)
        return True

    print(f"[{ip}] Installing Node Exporter v{NODE_EXPORTER_VERSION}...")
    
    # Check for wget if running locally and installation is needed
    if ip in ("127.0.0.1", "localhost"):
        res_wget = ssh_command(ip, "wget --version")
        if not res_wget:
            print(f"[{ip}] Warning: 'wget' is not installed. If Node Exporter download is needed, this will fail.")
    
    # Installation commands
    commands = [
        f"cd /tmp && wget -q https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"cd /tmp && tar xvfz node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz",
        f"mv /tmp/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/",
        "rm -rf /tmp/node_exporter-*",
        "useradd -rs /bin/false node_exporter 2>/dev/null || true",
        """echo '[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target' | tee /etc/systemd/system/node_exporter.service > /dev/null""",
        "systemctl daemon-reload",
        "systemctl start node_exporter",
        "systemctl enable node_exporter"
    ]
    
    for i, cmd in enumerate(commands):
        print(f"[{ip}] Step {i+1}/{len(commands)}: Running...")
        result = ssh_command(ip, cmd, check=True)
        if result is None:
            print(f"[{ip}] Installation failed at step {i+1}")
            return False
            
    print(f"[{ip}] Installation successful.")
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

def main():
    parser = argparse.ArgumentParser(
        description='Deploy Node Exporter to monitoring targets',
        epilog='Example: python3 deploy_monitor.py --setup-keys'
    )
    parser.add_argument('--setup-keys', action='store_true',
                       help='Setup SSH keys before deployment')
    parser.add_argument('--skip-health-check', action='store_true',
                       help='Skip health verification after deployment')
    args = parser.parse_args()
    
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
    
    for ip in hosts:
        print(f"\n{'='*50}")
        print(f"Processing: {ip}")
        print(f"{'='*50}\n")
        
        # Skip localhost - already monitored
        if ip in ('127.0.0.1', 'localhost'):
            print(f"⏭️  Skipping {ip} - already monitored by node-exporter service\n")
            results.append((ip, 'skipped'))
            continue
        
        # Check SSH connectivity
        if not test_ssh_connection(ip):
            print(f"✗ SSH key authentication failed for {ip}")
            print(f"   Please run: python3 scripts/setup_ssh_key.py {ip}")
            print(f"   Or run with --setup-keys flag\n")
            results.append((ip, 'ssh_failed'))
            continue
        
        # Check if already configured
        if is_target_configured(ip, targets):
            print(f"✓ Host {ip} already configured in Prometheus targets.")
            # Ensure Node Exporter is installed and running even if target is configured
            if install_node_exporter(ip):
                if not args.skip_health_check:
                    if verify_target_health(ip):
                        results.append((ip, 'configured_healthy'))
                    else:
                        results.append((ip, 'configured_unhealthy'))
                else:
                    results.append((ip, 'configured_skipped_health'))
            else:
                print(f"❌ Failed to ensure Node Exporter is running on {ip}")
                results.append((ip, 'configured_install_failed'))
            continue # Move to next host
        
        # New host - install Node Exporter and add to targets
        print(f"\n▶️  Processing new host: {ip}")
        if install_node_exporter(ip):
            targets = add_target(ip, targets)
            changes_made = True
            print(f"✅ Host {ip} configured successfully")
            if not args.skip_health_check:
                if verify_target_health(ip):
                    results.append((ip, 'new_healthy'))
                else:
                    results.append((ip, 'new_unhealthy'))
            else:
                results.append((ip, 'new_skipped_health'))
        else:
            print(f"❌ Failed to install Node Exporter on {ip}")
            results.append((ip, 'new_failed'))

    # Save targets if there were changes
    if changes_made:
        save_targets(targets)
        print(f"\n✅ Updated {TARGETS_FILE}")
        print("📊 Prometheus should pick up changes automatically")
    else:
        print("\n⚠️  No changes made to targets.")

    # Always ensure dashboards are correctly configured
    print("\n🔧 Checking Grafana dashboards...")
    fix_dashboards()

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
            'new_failed': '✗'
        }
        icon = status_icons.get(status, '?')
        status_text = status.replace('_', ' ').title()
        print(f"{icon} {ip:20s} - {status_text}")
    
    # Final recommendations
    failed_ssh = [ip for ip, status in results if status == 'ssh_failed']
    if failed_ssh:
        print("\n💡 Recommendations:")
        print(f"   - Run: python3 scripts/setup_ssh_key.py --all")
        print(f"   - Or manually: python3 scripts/setup_ssh_key.py {failed_ssh[0]}")

if __name__ == "__main__":
    main()