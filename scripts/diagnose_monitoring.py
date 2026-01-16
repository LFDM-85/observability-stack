#!/usr/bin/env python3
"""
Diagnostic and fix script for monitoring targets
Checks firewall, SELinux, service status and fixes common issues
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS_FILE = os.path.join(BASE_DIR, 'hosts.txt')

def load_hosts():
    """Load hosts from hosts.txt"""
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
                hosts.append((line, 'root'))
    return hosts

def ssh_exec(ip, user, cmd):
    """Execute command via SSH"""
    if ip in ('127.0.0.1', 'localhost'):
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    else:
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', 
                   f'{user}@{ip}', cmd]
        result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.returncode, result.stdout, result.stderr

def diagnose_host(ip, user):
    """Run comprehensive diagnostics on a host"""
    print(f"\n{'='*70}")
    print(f"🔍 DIAGNOSTICS FOR {user}@{ip}")
    print(f"{'='*70}\n")
    
    issues = []
    fixes = []
    
    # 1. Check if node_exporter service exists and its status
    print("1️⃣  Checking Node Exporter service...")
    rc, out, err = ssh_exec(ip, user, "systemctl status node_exporter")
    if rc != 0:
        print(f"   ❌ Service not found or not running")
        print(f"      Error: {err.strip()}")
        issues.append("Service not running")
    else:
        print(f"   ✅ Service status:")
        for line in out.split('\n')[:5]:
            print(f"      {line}")
    
    # 2. Check if binary exists
    print("\n2️⃣  Checking Node Exporter binary...")
    rc, out, err = ssh_exec(ip, user, "ls -lh /usr/local/bin/node_exporter")
    if rc != 0:
        print(f"   ❌ Binary not found")
        issues.append("Binary missing")
    else:
        print(f"   ✅ Binary exists: {out.strip()}")
    
    # 3. Check if port 9100 is listening
    print("\n3️⃣  Checking port 9100...")
    rc, out, err = ssh_exec(ip, user, "ss -tlnp | grep :9100 || netstat -tlnp | grep :9100")
    if rc != 0 or not out.strip():
        print(f"   ❌ Port 9100 is NOT listening")
        issues.append("Port not listening")
    else:
        print(f"   ✅ Port 9100 is listening:")
        print(f"      {out.strip()}")
    
    # 4. Check firewall status
    print("\n4️⃣  Checking firewall...")
    rc, out, err = ssh_exec(ip, user, "firewall-cmd --list-ports 2>/dev/null || iptables -L -n | grep 9100")
    if "9100" not in out:
        print(f"   ⚠️  Port 9100 may not be open in firewall")
        issues.append("Firewall blocking")
        fixes.append("firewall")
    else:
        print(f"   ✅ Firewall seems configured")
    
    # 5. Check SELinux
    print("\n5️⃣  Checking SELinux...")
    rc, out, err = ssh_exec(ip, user, "getenforce 2>/dev/null")
    if out.strip() == "Enforcing":
        print(f"   ⚠️  SELinux is in Enforcing mode")
        issues.append("SELinux may be blocking")
        fixes.append("selinux")
    elif out.strip() == "Permissive":
        print(f"   ✅ SELinux is in Permissive mode")
    else:
        print(f"   ✅ SELinux is disabled or not present")
    
    # 6. Test connectivity from Prometheus server
    print("\n6️⃣  Testing connectivity from localhost...")
    result = subprocess.run(['curl', '-s', '-m', '5', f'http://{ip}:9100/metrics'], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode == 0 and 'node_' in result.stdout:
        print(f"   ✅ Can reach Node Exporter metrics")
        print(f"      Sample: {result.stdout.split()[0][:100]}...")
    else:
        print(f"   ❌ Cannot reach Node Exporter metrics")
        print(f"      Error: {result.stderr}")
        issues.append("Node Exporter unreachable")

    # 7. Check cAdvisor (if Docker is present)
    print("\n7️⃣  Checking cAdvisor (Docker monitoring)...")
    # Check if docker is running
    rc, out, err = ssh_exec(ip, user, "command -v docker && systemctl is-active docker")
    if rc == 0 and out.strip() == "active":
        print(f"   🐳 Docker is running. Checking cAdvisor...")
        
        # Check cAdvisor service
        rc, out, err = ssh_exec(ip, user, "systemctl is-active cadvisor")
        if rc != 0:
            print(f"   ❌ cAdvisor service not running or missing")
            issues.append("cAdvisor not running")
        else:
            print(f"   ✅ cAdvisor service is active")
            
            # Check port 9991
            rc, out, err = ssh_exec(ip, user, "ss -tlnp | grep :9991 || netstat -tlnp | grep :9991")
            if rc != 0 or not out.strip():
                print(f"   ❌ Port 9991 (cAdvisor) is NOT listening")
                issues.append("cAdvisor port not listening")
            else:
                print(f"   ✅ Port 9991 is listening")

            # Check firewall for 9991
            rc, out, err = ssh_exec(ip, user, "firewall-cmd --list-ports 2>/dev/null || iptables -L -n | grep 9991")
            if "9991" not in out:
                print(f"   ⚠️  Port 9991 may be blocked by firewall")
                issues.append("cAdvisor firewall blocking")
                fixes.append("firewall_cadvisor")
            else:
                print(f"   ✅ Firewall allows 9991")

            # Check connectivity
            print(f"   🔄 Testing cAdvisor connectivity...")
            result = subprocess.run(['curl', '-s', '-m', '5', f'http://{ip}:9991/metrics'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0 and 'container_' in result.stdout:
                print(f"   ✅ Can reach cAdvisor metrics")
            else:
                print(f"   ❌ Cannot reach cAdvisor metrics")
                issues.append("cAdvisor unreachable")
    else:
        print(f"   ℹ️  Docker not detected or not active. Skipping cAdvisor checks.")
    
    # 8. Check journal for errors
    print("\n8️⃣  Checking recent logs...")
    rc, out, err = ssh_exec(ip, user, "journalctl -u node_exporter -n 20 --no-pager 2>/dev/null")
    if rc == 0 and out:
        print(f"   📋 Recent logs:")
        for line in out.split('\n')[-10:]:
            if line.strip():
                print(f"      {line}")
    
    # Summary
    print(f"\n{'='*70}")
    if not issues:
        print("✅ NO ISSUES FOUND - Host appears healthy")
    else:
        print(f"⚠️  FOUND {len(issues)} ISSUE(S):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        if fixes:
            print(f"\n💡 SUGGESTED FIXES:")
            if "firewall" in fixes:
                print(f"\n   🔥 Firewall Fix (Node Exporter):")
                print(f"      firewall-cmd --permanent --add-port=9100/tcp")
                print(f"      firewall-cmd --reload")
                
            if "firewall_cadvisor" in fixes:
                print(f"\n   🔥 Firewall Fix (cAdvisor):")
                print(f"      firewall-cmd --permanent --add-port=9991/tcp")
                print(f"      firewall-cmd --reload")
            
            if "selinux" in fixes:
                print(f"\n   🔒 SELinux Fix:")
                print(f"      # Option 1: Allow the port")
                print(f"      semanage port -a -t http_port_t -p tcp 9100")
                print(f"      # Option 2: Set to permissive (less secure)")
                print(f"      setenforce 0")
                print(f"      sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config")
    
    print(f"{'='*70}\n")
    return issues, fixes

def auto_fix_host(ip, user):
    """Attempt to automatically fix common issues"""
    print(f"\n🔧 ATTEMPTING AUTO-FIX FOR {ip}...")
    
    fixes_applied = []
    
    # Fix 1: Restart service
    print("\n1️⃣  Restarting Node Exporter service...")
    rc, out, err = ssh_exec(ip, user, "systemctl restart node_exporter && systemctl enable node_exporter")
    if rc == 0:
        print("   ✅ Service restarted")
        fixes_applied.append("service_restart")
    else:
        print(f"   ❌ Failed to restart: {err}")
    
    # Fix 2: Open firewall port
    print("\n2️⃣  Opening firewall port 9100...")
    # Try firewalld first
    rc, out, err = ssh_exec(ip, user, "firewall-cmd --permanent --add-port=9100/tcp && firewall-cmd --reload 2>/dev/null")
    if rc == 0:
        print("   ✅ Firewall port opened (firewalld)")
        fixes_applied.append("firewall_firewalld")
    else:
        # Try iptables
        rc, out, err = ssh_exec(ip, user, "iptables -C INPUT -p tcp --dport 9100 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 9100 -j ACCEPT")
        if rc == 0:
            print("   ✅ Firewall port opened (iptables)")
            ssh_exec(ip, user, "service iptables save 2>/dev/null")
            fixes_applied.append("firewall_iptables")
        else:
            print("   ⚠️  Could not configure firewall (may not be needed)")
    
    # Fix 3: SELinux - allow port
    print("\n3️⃣  Configuring SELinux...")
    rc, out, err = ssh_exec(ip, user, "semanage port -a -t http_port_t -p tcp 9100 2>/dev/null || semanage port -m -t http_port_t -p tcp 9100 2>/dev/null")
    if rc == 0:
        print("   ✅ SELinux port policy updated")
        fixes_applied.append("selinux")
    else:
    else:
        print("   ℹ️  SELinux not configured (may not be needed)")

    # Fix 4: Firewall for cAdvisor (if needed)
    print("\n4️⃣  Checking cAdvisor firewall (9991)...")
    # Only if port 9991 is not open
    rc, out, err = ssh_exec(ip, user, "firewall-cmd --list-ports 2>/dev/null")
    if rc == 0 and "9991" not in out:
        print("   Configuring firewall for cAdvisor...")
        ssh_exec(ip, user, "firewall-cmd --permanent --add-port=9991/tcp && firewall-cmd --reload 2>/dev/null")
        fixes_applied.append("firewall_cadvisor")
    else:
         print("   ℹ️  Port 9991 seems OK or firewalld not active")
    
    # Fix 5: Verify service is actually running
    print("\n5️⃣  Verifying service status...")
    import time
    time.sleep(3)
    rc, out, err = ssh_exec(ip, user, "systemctl is-active node_exporter")
    if out.strip() == "active":
        print("   ✅ Service is active")
        fixes_applied.append("service_active")
    else:
        print(f"   ❌ Service still not active: {out.strip()}")
    
    print(f"\n✅ Applied {len(fixes_applied)} fix(es): {', '.join(fixes_applied)}")
    return fixes_applied

def main():
    if len(sys.argv) > 1:
        # Diagnostic specific host
        if sys.argv[1] == '--fix':
            # Auto-fix all hosts
            hosts = load_hosts()
            for ip, user in hosts:
                if ip in ('127.0.0.1', 'localhost'):
                    continue
                auto_fix_host(ip, user)
                print("\n⏳ Waiting 5 seconds before testing...")
                import time
                time.sleep(5)
                diagnose_host(ip, user)
        else:
            # Diagnose specific IP
            target_ip = sys.argv[1]
            user = sys.argv[2] if len(sys.argv) > 2 else 'root'
            diagnose_host(target_ip, user)
            
            print("\n❓ Do you want to attempt auto-fix? (y/n): ", end='')
            if input().lower() == 'y':
                auto_fix_host(target_ip, user)
                print("\n⏳ Waiting 5 seconds before re-testing...")
                import time
                time.sleep(5)
                diagnose_host(target_ip, user)
    else:
        # Diagnose all hosts
        hosts = load_hosts()
        print(f"📋 Found {len(hosts)} host(s) to diagnose\n")
        
        unhealthy = []
        for ip, user in hosts:
            if ip in ('127.0.0.1', 'localhost'):
                continue
            issues, _ = diagnose_host(ip, user)
            if issues:
                unhealthy.append((ip, user))
        
        if unhealthy:
            print(f"\n{'='*70}")
            print(f"⚠️  SUMMARY: {len(unhealthy)} unhealthy host(s)")
            print(f"{'='*70}")
            for ip, user in unhealthy:
                print(f"   ❌ {user}@{ip}")
            
            print("\n❓ Do you want to attempt auto-fix on all unhealthy hosts? (y/n): ", end='')
            if input().lower() == 'y':
                for ip, user in unhealthy:
                    auto_fix_host(ip, user)
                
                print("\n⏳ Waiting 10 seconds before re-testing all...")
                import time
                time.sleep(10)
                
                print("\n" + "="*70)
                print("🔄 RE-TESTING ALL HOSTS")
                print("="*70)
                for ip, user in unhealthy:
                    diagnose_host(ip, user)
        else:
            print("\n✅ ALL HOSTS ARE HEALTHY!")

if __name__ == "__main__":
    main()