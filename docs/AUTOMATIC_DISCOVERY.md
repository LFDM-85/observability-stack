# Automatic Network Discovery

## 🔍 Overview

Automatic network discovery scans configured subnets periodically and automatically detects and monitors network devices.

**Features:**

- ✅ Automatic device detection via nmap
- ✅ Device type classification (camera, PC, smartphone, etc.)
- ✅ Periodic scanning (every 5 minutes)
- ✅ Preserves manual device entries
- ✅ Automatic Prometheus target generation

---

## 🚀 Setup

### Prerequisites

- Root access (for network scanning)
- `nmap` installed
- Python 3 with `pyyaml`

### Installation

```bash
# Run setup script (as root)
sudo bash scripts/setup_network_discovery.sh
```

This will:

1. Install dependencies (`nmap`, `python3-yaml`)
2. Run initial test scan
3. Setup cron job (every 5 minutes)
4. Create log file

---

## ⚙️ Configuration

Edit `network_discovery.yml`:

```yaml
subnets:
  - 10.10.1.0/24 # Your subnets
  - 192.168.90.0/24

scan_interval: 300 # 5 minutes

# Exclude monitoring server itself
exclude:
  ips:
    - 10.10.1.159
```

### Device Classification Rules

**Port-based detection:**

```yaml
port_rules:
  - ports: [554, 8000, 8080]
    type: camera
  - ports: [3389]
    type: pc
```

**Hostname patterns:**

```yaml
hostname_rules:
  - pattern: "(?i)(iphone|ipad)"
    type: smartphone
  - pattern: "(?i)desktop-"
    type: pc
```

**MAC vendor:**

```yaml
mac_vendor_rules:
  - vendor: "Apple"
    type: smartphone
  - vendor: "Hikvision"
    type: camera
```

---

## 📊 How It Works

### 1. Network Scan

Every 5 minutes (configurable):

- Scans all configured subnets
- Uses `nmap` for device detection
- Performs ping + ARP scan
- Quick port scan for classification

### 2. Device Classification

Automatically identifies device types using:

- **Open ports**: 554 (RTSP) = camera, 3389 (RDP) = PC
- **Hostname**: "iPhone" = smartphone, "DESKTOP-" = PC
- **MAC vendor**: Apple = smartphone, Hikvision = camera

### 3. Database Update

Maintains `network_devices_discovered.json`:

```json
{
  "10.10.1.100": {
    "name": "iPhone-Luis",
    "type": "smartphone",
    "mac": "AA:BB:CC:DD:EE:FF",
    "vendor": "Apple",
    "first_seen": "2024-02-08T20:00:00",
    "last_seen": "2024-02-08T23:15:00",
    "ports": [],
    "auto_discovered": true
  }
}
```

### 4. File Updates

Updates `network_devices.txt`:

```
# Manual entries (preserved)
10.10.1.1,OPNsense,router

# AUTO-DISCOVERED DEVICES (managed automatically)
10.10.1.100,iPhone-Luis,smartphone
10.10.1.120,Camera-Entrance,camera
```

### 5. Prometheus Integration

Automatically generates `prometheus/network_devices.json` with all devices.

---

## 🎯 Usage

### Manual Scan

```bash
# Run discovery manually
python3 scripts/network_discovery.py --scan
```

### View Discovered Devices

```bash
# View database
cat network_devices_discovered.json | jq

# View active devices
cat network_devices.txt | grep -A 100 "AUTO-DISCOVERED"
```

### Check Logs

```bash
# View discovery log
tail -f /var/log/network_discovery.log

# View recent discoveries
grep "New device" /var/log/network_discovery.log
```

### Manage Cron

```bash
# List cron jobs
crontab -l

# Edit cron (to change interval)
crontab -e

# Remove automatic discovery
crontab -e  # Delete the network_discovery line
```

---

## 🔧 Device Management

### Manual vs Auto-Discovered

**Manual devices** (top of `network_devices.txt`):

- Added manually
- Never modified by scanner
- Full control over name and type

**Auto-discovered devices** (bottom, after `# AUTO-DISCOVERED`):

- Added automatically
- Updated by scanner
- Can be promoted to manual

### Promote to Manual

To take control of an auto-discovered device:

```bash
# 1. Copy device line from AUTO-DISCOVERED section
# 2. Move to top of file (manual section)
# 3. Edit name/type as desired

# Example:
nano network_devices.txt

# Move this line:
# 10.10.1.100,Device-100,smartphone

# To top and edit:
# 10.10.1.100,Luis iPhone,smartphone
```

### Exclude Device

Add to `network_discovery.yml`:

```yaml
exclude:
  ips:
    - 10.10.1.XXX # Device to exclude
```

---

## 🔍 Troubleshooting

### No Devices Discovered

**Check nmap:**

```bash
# Test nmap manually
sudo nmap -sn 10.10.1.0/24
```

**Check permissions:**

```bash
# Scanner needs root for ARP scan
sudo python3 scripts/network_discovery.py --scan
```

**Check configuration:**

```bash
# Verify subnets are correct
cat network_discovery.yml
```

### Wrong Device Types

**Add custom rule:**

Edit `network_discovery.yml`:

```yaml
hostname_rules:
  - pattern: "my-device-name"
    type: correct_type
```

**Or promote to manual** and set type manually.

### Devices Disappearing

Devices are **never removed** automatically. They're marked with `last_seen` timestamp.

To clean old devices:

```bash
# Edit discovered database
nano network_devices_discovered.json
# Remove old entries
```

### Scan Too Slow

**Reduce scan scope:**

```yaml
subnets:
  - 10.10.1.0/25 # Smaller subnet (128 IPs instead of 254)
```

**Increase timeout:**
Edit `network_discovery.py`, change:

```python
'--host-timeout', '30s',  # Increase if needed
```

---

## 📈 Performance

### Scan Times

| Subnet Size   | Approximate Time |
| ------------- | ---------------- |
| /24 (254 IPs) | 1-2 minutes      |
| /25 (128 IPs) | 30-60 seconds    |
| /26 (64 IPs)  | 15-30 seconds    |

### Resource Usage

- **CPU**: Low (spikes during scan)
- **Network**: Minimal (ping + ARP)
- **Disk**: <1MB for database

---

## 🔒 Security Considerations

### Network Scanning

- Scanning may trigger IDS/IPS alerts
- Inform network admin before enabling
- Some devices may not respond to scans

### Permissions

- Requires root for ARP scanning
- Runs as cron job (root context)
- Log file readable by all

### Privacy

- Discovered database contains MAC addresses
- Added to `.gitignore` by default
- Don't commit to public repos

---

## 🎨 Customization

### Change Scan Interval

Edit cron job:

```bash
crontab -e

# Change from every 5 minutes:
*/5 * * * * ...

# To every 10 minutes:
*/10 * * * * ...

# To hourly:
0 * * * * ...
```

### Add Custom Classification

Edit `network_discovery.yml`:

```yaml
port_rules:
  - ports: [8123] # Home Assistant
    type: homeassistant
    confidence: high

hostname_rules:
  - pattern: "(?i)homeassistant"
    type: homeassistant
```

### Integration with Other Tools

Export discovered devices:

```bash
# JSON format
cat network_devices_discovered.json

# CSV format
echo "IP,Name,Type,MAC,Vendor,First Seen,Last Seen" > discovered.csv
jq -r 'to_entries[] | [.key, .value.name, .value.type, .value.mac, .value.vendor, .value.first_seen, .value.last_seen] | @csv' network_devices_discovered.json >> discovered.csv
```

---

## 📚 Files

| File                                 | Purpose               |
| ------------------------------------ | --------------------- |
| `network_discovery.yml`              | Configuration         |
| `scripts/network_discovery.py`       | Scanner script        |
| `scripts/setup_network_discovery.sh` | Setup script          |
| `network_devices_discovered.json`    | Discovered devices DB |
| `/var/log/network_discovery.log`     | Scan logs             |

---

## 🔗 Related

- [Network Monitoring Guide](NETWORK_MONITORING.md)
- [Blackbox Exporter](https://github.com/prometheus/blackbox_exporter)
- [Nmap Documentation](https://nmap.org/book/man.html)
