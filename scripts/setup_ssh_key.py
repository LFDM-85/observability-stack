#!/usr/bin/env python3
"""
SSH Key Setup Script
Automates SSH key-based authentication setup for remote hosts.
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

def check_ssh_key_exists():
    """Check if SSH key pair exists, create if not."""
    ssh_dir = Path.home() / '.ssh'
    private_key = ssh_dir / 'id_rsa'
    public_key = ssh_dir / 'id_rsa.pub'
    
    if not private_key.exists() or not public_key.exists():
        print("🔑 No SSH key found. Generating new SSH key pair...")
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        try:
            subprocess.run([
                'ssh-keygen',
                '-t', 'rsa',
                '-b', '4096',
                '-f', str(private_key),
                '-N', '',  # No passphrase
                '-C', f'observability-stack@{os.uname().nodename}'
            ], check=True)
            print(f"✓ SSH key generated: {private_key}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to generate SSH key: {e}")
            return False
    else:
        print(f"✓ SSH key exists: {private_key}")
    
    return True

def test_ssh_connection(ip, username='root'):
    """Test SSH connection without password."""
    try:
        result = subprocess.run([
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'PasswordAuthentication=no',
            '-o', 'ConnectTimeout=5',
            '-o', 'BatchMode=yes',
            f'{username}@{ip}',
            'echo "Connection successful"'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def setup_ssh_key(ip, username='root', password=None):
    """Setup SSH key on remote host using password authentication."""
    ssh_dir = Path.home() / '.ssh'
    public_key = ssh_dir / 'id_rsa.pub'
    
    if not public_key.exists():
        print("✗ Public key not found. Please run with --generate-key first.")
        return False
    
    with open(public_key, 'r') as f:
        pub_key_content = f.read().strip()
    
    print(f"\n📡 Setting up SSH key for {username}@{ip}...")
    
    # If password not provided, ask for it
    if password is None:
        password = getpass.getpass(f"Enter password for {username}@{ip}: ")
    
    # Commands to execute on remote host
    commands = [
        'mkdir -p ~/.ssh',
        'chmod 700 ~/.ssh',
        f'echo "{pub_key_content}" >> ~/.ssh/authorized_keys',
        'chmod 600 ~/.ssh/authorized_keys',
        'echo "SSH key added successfully"'
    ]
    
    try:
        # Use sshpass to provide password
        import shutil
        if not shutil.which('sshpass'):
            print("\n⚠️  sshpass not found. Installing is recommended for automation.")
            print("    Ubuntu/Debian: sudo apt-get install sshpass")
            print("    CentOS/RHEL: sudo yum install sshpass")
            print("\nAttempting manual SSH (you'll need to enter password)...")
            
            # Fallback: manual SSH
            ssh_command = '; '.join(commands)
            result = subprocess.run([
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                f'{username}@{ip}',
                ssh_command
            ])
            return result.returncode == 0
        else:
            # Use sshpass
            ssh_command = '; '.join(commands)
            result = subprocess.run([
                'sshpass',
                '-p', password,
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                f'{username}@{ip}',
                ssh_command
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                print("✓ SSH key installed successfully")
                return True
            else:
                print(f"✗ Failed to install SSH key: {result.stderr.decode()}")
                return False
    
    except Exception as e:
        print(f"✗ Error during SSH key setup: {e}")
        return False

def setup_hosts_from_file(hosts_file):
    """Setup SSH keys for all hosts in hosts.txt."""
    if not os.path.exists(hosts_file):
        print(f"✗ Hosts file not found: {hosts_file}")
        return
    
    with open(hosts_file, 'r') as f:
        hosts = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    if not hosts:
        print("⚠️  No hosts found in hosts.txt")
        return
    
    print(f"\n📋 Found {len(hosts)} host(s) to configure\n")
    
    results = []
    for ip in hosts:
        # Skip localhost
        if ip in ('127.0.0.1', 'localhost'):
            print(f"⏭️  Skipping {ip} (localhost)")
            results.append((ip, 'skipped'))
            continue
        
        # Test if already configured
        if test_ssh_connection(ip):
            print(f"✓ {ip} - SSH key already configured")
            results.append((ip, 'already_configured'))
            continue
        
        # Setup SSH key
        success = setup_ssh_key(ip)
        
        if success:
            # Verify
            if test_ssh_connection(ip):
                print(f"✓ {ip} - SSH key setup verified")
                results.append((ip, 'success'))
            else:
                print(f"⚠️  {ip} - SSH key installed but verification failed")
                results.append((ip, 'partial'))
        else:
            print(f"✗ {ip} - SSH key setup failed")
            results.append((ip, 'failed'))
        
        print()  # Blank line between hosts
    
    # Summary
    print("\n" + "="*50)
    print("📊 Summary:")
    print("="*50)
    for ip, status in results:
        status_icon = {
            'success': '✓',
            'already_configured': '✓',
            'skipped': '⏭️',
            'partial': '⚠️',
            'failed': '✗'
        }.get(status, '?')
        print(f"{status_icon} {ip:20s} - {status}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Setup SSH key-based authentication for monitoring hosts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate SSH key if needed
  python3 setup_ssh_key.py --generate-key
  
  # Setup single host
  python3 setup_ssh_key.py 192.168.1.100
  
  # Setup all hosts from hosts.txt
  python3 setup_ssh_key.py --all
  
  # Test connection
  python3 setup_ssh_key.py --test 192.168.1.100
        """
    )
    
    parser.add_argument('ip', nargs='?', help='IP address to setup')
    parser.add_argument('--all', action='store_true', help='Setup all hosts from hosts.txt')
    parser.add_argument('--test', metavar='IP', help='Test SSH connection to IP')
    parser.add_argument('--generate-key', action='store_true', help='Generate SSH key pair if not exists')
    parser.add_argument('--username', '-u', default='root', help='SSH username (default: root)')
    parser.add_argument('--hosts-file', default='../hosts.txt', help='Path to hosts.txt file')
    
    args = parser.parse_args()
    
    # Resolve hosts file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hosts_file = os.path.join(script_dir, args.hosts_file)
    
    print("🔐 SSH Key Setup for Observability Stack")
    print("=" * 50 + "\n")
    
    # Generate key if requested or if needed
    if args.generate_key or args.all or args.ip:
        if not check_ssh_key_exists():
            sys.exit(1)
    
    # Test connection
    if args.test:
        print(f"🧪 Testing SSH connection to {args.test}...")
        if test_ssh_connection(args.test, args.username):
            print(f"✓ SSH key authentication working for {args.test}")
            sys.exit(0)
        else:
            print(f"✗ SSH key authentication failed for {args.test}")
            print(f"   Run: python3 setup_ssh_key.py {args.test}")
            sys.exit(1)
    
    # Setup all hosts
    if args.all:
        setup_hosts_from_file(hosts_file)
    
    # Setup single host
    elif args.ip:
        if args.ip in ('127.0.0.1', 'localhost'):
            print("⏭️  Skipping localhost - no SSH setup needed")
            sys.exit(0)
        
        if test_ssh_connection(args.ip, args.username):
            print(f"✓ SSH key already configured for {args.ip}")
            sys.exit(0)
        
        success = setup_ssh_key(args.ip, args.username)
        
        if success and test_ssh_connection(args.ip, args.username):
            print(f"\n✓ SSH key setup complete for {args.ip}")
            print(f"   You can now deploy monitoring with: python3 deploy_monitor.py")
            sys.exit(0)
        else:
            print(f"\n✗ SSH key setup failed for {args.ip}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
