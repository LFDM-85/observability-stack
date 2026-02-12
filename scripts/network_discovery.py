#!/usr/bin/env python3
"""
Automatic Network Discovery Script
Scans configured subnets and automatically discovers network devices
"""

import json
import os
import yaml
import subprocess
import re
import ipaddress
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Paths - configurable via environment
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', SCRIPT_DIR.parent))
CONFIG_FILE = Path(os.environ.get('CONFIG_FILE', PROJECT_ROOT / "network_discovery.yml"))
DEVICES_FILE = Path(os.environ.get('DEVICES_FILE', PROJECT_ROOT / "network_devices.txt"))
DISCOVERED_DB = Path(os.environ.get('DISCOVERED_DB', PROJECT_ROOT / "network_devices_discovered.json"))
TARGETS_FILE = Path(os.environ.get('TARGETS_FILE', PROJECT_ROOT / "prometheus" / "network_devices.json"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NetworkDiscovery:
    def __init__(self, config_path: Path):
        self.config = self.load_config(config_path)
        self.discovered_devices = self.load_discovered_db()
        self.manual_devices = self.load_manual_devices()
        
    def load_config(self, config_path: Path) -> dict:
        """Load configuration from YAML file"""
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_discovered_db(self) -> dict:
        """Load discovered devices database"""
        if DISCOVERED_DB.exists():
            with open(DISCOVERED_DB, 'r') as f:
                return json.load(f)
        return {}
    
    def save_discovered_db(self):
        """Save discovered devices database"""
        with open(DISCOVERED_DB, 'w') as f:
            json.dump(self.discovered_devices, f, indent=2)
    
    def load_manual_devices(self) -> set:
        """Load manually added devices (IPs)"""
        manual_ips = set()
        if DEVICES_FILE.exists():
            with open(DEVICES_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 1:
                            manual_ips.add(parts[0].strip())
        return manual_ips
    
    def scan_subnet(self, subnet: str) -> List[Dict]:
        """Scan subnet using nmap with ARP discovery"""
        logger.info(f"Scanning subnet: {subnet}")

        try:
            # nmap scan: ARP discovery (works best for local network)
            # -PR: ARP ping (requires raw sockets/root for remote subnets)
            # Falls back to TCP connect for hosts that don't respond to ARP
            cmd = [
                'nmap',
                '-sn',  # Ping scan only
                '-PR',  # ARP ping (best for local network)
                '-PE',  # ICMP echo (fallback)
                '-T4',  # Faster timing
                '--min-rate', '300',
                '--max-retries', '2',
                '--host-timeout', '10s',
                subnet
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            devices = self.parse_nmap_output(result.stdout)

            # Get hostnames (skip port scan for speed)
            for device in devices:
                device['ports'] = []  # Skip individual port scans for speed
                if not device.get('hostname'):
                    device['hostname'] = self.get_hostname(device['ip'])

            return devices
            
        except subprocess.TimeoutExpired:
            logger.error(f"Scan timeout for subnet {subnet}")
            return []
        except FileNotFoundError:
            logger.error("nmap not found. Install with: apt install nmap")
            return []
        except Exception as e:
            logger.error(f"Error scanning subnet {subnet}: {e}")
            return []
    
    def parse_nmap_output(self, output: str) -> List[Dict]:
        """Parse nmap output to extract devices"""
        devices = []
        current_device = None
        
        for line in output.split('\n'):
            # Match IP address line
            ip_match = re.search(r'Nmap scan report for (?:([^\s]+) \()?(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                if current_device:
                    devices.append(current_device)
                
                hostname = ip_match.group(1) if ip_match.group(1) else ''
                ip = ip_match.group(2)
                
                current_device = {
                    'ip': ip,
                    'hostname': hostname,
                    'mac': '',
                    'vendor': ''
                }
            
            # Match MAC address
            mac_match = re.search(r'MAC Address: ([0-9A-F:]+) \(([^)]+)\)', line)
            if mac_match and current_device:
                current_device['mac'] = mac_match.group(1)
                current_device['vendor'] = mac_match.group(2)
        
        if current_device:
            devices.append(current_device)
        
        return devices
    
    def scan_ports(self, ip: str) -> List[int]:
        """Quick port scan for common ports"""
        common_ports = [22, 80, 443, 554, 3389, 445, 139, 8000, 8080]
        open_ports = []

        try:
            cmd = [
                'nmap',
                '-p', ','.join(map(str, common_ports)),
                '--open',
                '-T5',  # Fastest timing
                '--host-timeout', '5s',
                ip
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            for line in result.stdout.split('\n'):
                port_match = re.search(r'(\d+)/tcp\s+open', line)
                if port_match:
                    open_ports.append(int(port_match.group(1)))
        
        except Exception as e:
            logger.debug(f"Port scan error for {ip}: {e}")
        
        return open_ports
    
    def get_hostname(self, ip: str) -> str:
        """Get hostname via reverse DNS"""
        try:
            result = subprocess.run(
                ['host', ip],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            match = re.search(r'pointer (.+)\.', result.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
        
        return ''
    
    def classify_device(self, device: Dict) -> str:
        """Classify device type based on heuristics"""
        
        # Check port-based rules
        for rule in self.config['device_classification']['port_rules']:
            if any(port in device.get('ports', []) for port in rule['ports']):
                return rule['type']
        
        # Check hostname patterns
        hostname = device.get('hostname', '')
        for rule in self.config['device_classification']['hostname_rules']:
            if re.search(rule['pattern'], hostname):
                return rule['type']
        
        # Check MAC vendor
        vendor = device.get('vendor', '')
        for rule in self.config['device_classification']['mac_vendor_rules']:
            if rule['vendor'].lower() in vendor.lower():
                return rule['type']
        
        return 'unknown'
    
    def should_exclude(self, device: Dict) -> bool:
        """Check if device should be excluded"""
        ip = device['ip']
        
        # Check excluded IPs
        if ip in self.config['exclude']['ips']:
            return True
        
        # Check excluded MAC prefixes
        mac = device.get('mac', '')
        for prefix in self.config['exclude']['mac_prefixes']:
            if mac.startswith(prefix):
                return True
        
        return False
    
    def discover(self):
        """Main discovery process"""
        logger.info("=" * 60)
        logger.info("Starting network discovery")
        logger.info("=" * 60)
        
        all_devices = []
        
        # Scan all configured subnets
        for subnet in self.config['subnets']:
            devices = self.scan_subnet(subnet)
            all_devices.extend(devices)
        
        logger.info(f"Found {len(all_devices)} devices")
        
        # Process discovered devices
        new_devices = 0
        updated_devices = 0
        
        for device in all_devices:
            ip = device['ip']
            
            # Skip excluded devices
            if self.should_exclude(device):
                logger.debug(f"Excluding {ip}")
                continue
            
            # Skip manually managed devices
            if ip in self.manual_devices:
                logger.debug(f"Skipping manual device {ip}")
                continue
            
            # Classify device
            device_type = self.classify_device(device)
            
            # Generate device name
            if device.get('hostname'):
                device_name = device['hostname']
            else:
                device_name = f"Device-{ip.split('.')[-1]}"
            
            # Update discovered database
            if ip not in self.discovered_devices:
                # New device
                self.discovered_devices[ip] = {
                    'name': device_name,
                    'type': device_type,
                    'mac': device.get('mac', ''),
                    'vendor': device.get('vendor', ''),
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat(),
                    'ports': device.get('ports', []),
                    'auto_discovered': True
                }
                new_devices += 1
                logger.info(f"✨ New device: {ip} ({device_name}) - {device_type}")
            else:
                # Update existing device
                self.discovered_devices[ip]['last_seen'] = datetime.now().isoformat()
                self.discovered_devices[ip]['ports'] = device.get('ports', [])
                
                # Update type if it was unknown
                if self.discovered_devices[ip]['type'] == 'unknown' and device_type != 'unknown':
                    self.discovered_devices[ip]['type'] = device_type
                    logger.info(f"🔄 Updated type for {ip}: {device_type}")
                
                updated_devices += 1
        
        # Save discovered database
        self.save_discovered_db()
        
        # Update network_devices.txt
        self.update_devices_file()
        
        # Generate Prometheus targets
        self.generate_targets()
        
        logger.info("=" * 60)
        logger.info(f"Discovery complete: {new_devices} new, {updated_devices} updated")
        logger.info("=" * 60)
    
    def _read_all_devices(self):
        """Read all devices from network_devices.txt (deduplicated)"""
        devices = []
        seen_ips = set()
        if DEVICES_FILE.exists():
            with open(DEVICES_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) == 3:
                            ip = parts[0]
                            # Skip duplicates (keep first occurrence)
                            if ip not in seen_ips:
                                seen_ips.add(ip)
                                devices.append({
                                    'ip': ip,
                                    'name': parts[1],
                                    'type': parts[2]
                                })
        return devices

    def update_devices_file(self):
        """Update network_devices.txt with discovered devices"""
        # Read existing manual entries (stop at AUTO-DISCOVERED marker)
        manual_lines = []
        manual_ips = set()
        in_auto_section = False

        if DEVICES_FILE.exists():
            with open(DEVICES_FILE, 'r') as f:
                for line in f:
                    line_stripped = line.strip()
                    # Stop reading manual entries when we hit auto-discovered section
                    if '# AUTO-DISCOVERED' in line_stripped:
                        in_auto_section = True
                        continue
                    if in_auto_section:
                        continue
                    manual_lines.append(line)
                    # Track manual IPs to avoid duplicates
                    if line_stripped and not line_stripped.startswith('#'):
                        parts = line_stripped.split(',')
                        if len(parts) >= 1:
                            manual_ips.add(parts[0].strip())

        # Write back with auto-discovered section
        with open(DEVICES_FILE, 'w') as f:
            # Write manual entries
            for line in manual_lines:
                f.write(line)

            # Write auto-discovered section (excluding IPs already in manual section)
            auto_devices = {ip: info for ip, info in self.discovered_devices.items()
                          if info.get('auto_discovered', False) and ip not in manual_ips}
            if auto_devices:
                f.write('\n# AUTO-DISCOVERED DEVICES (managed automatically)\n')
                for ip, info in sorted(auto_devices.items()):
                    f.write(f"{ip},{info['name']},{info['type']}\n")
        
        logger.info(f"Updated {DEVICES_FILE}")
    
    def generate_targets(self):
        """Generate Prometheus targets JSON"""
        devices = self._read_all_devices()
        targets = []

        for device in devices:
            targets.append({
                'targets': [device['ip']],
                'labels': {
                    'device_name': device['name'],
                    'device_type': device['type']
                }
            })

        # Write targets
        TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TARGETS_FILE, 'w') as f:
            json.dump(targets, f, indent=2)

        logger.info(f"Generated {len(targets)} Prometheus targets")

        # Reload Prometheus
        self._reload_prometheus()

    def _reload_prometheus(self):
        """Reload Prometheus configuration"""
        prometheus_host = os.environ.get('PROMETHEUS_HOST', 'prometheus')
        prometheus_port = os.environ.get('PROMETHEUS_PORT', '9090')
        prometheus_url = f"http://{prometheus_host}:{prometheus_port}/-/reload"

        try:
            result = subprocess.run(
                ['curl', '-s', '-X', 'POST', prometheus_url],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("Prometheus configuration reloaded")
            else:
                logger.warning("Could not reload Prometheus")
        except Exception as e:
            logger.warning(f"Could not reload Prometheus: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Device Discovery')
    parser.add_argument('--scan', action='store_true', help='Run discovery scan')
    parser.add_argument('--config', default=str(CONFIG_FILE), help='Config file path')
    
    args = parser.parse_args()
    
    if args.scan:
        discovery = NetworkDiscovery(Path(args.config))
        discovery.discover()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
