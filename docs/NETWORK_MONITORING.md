# Network Device Monitoring Guide

## 📱 Overview

This setup monitors the availability of all network devices using ICMP ping via Blackbox Exporter.

**Supported Devices:**

- Smartphones, tablets
- PCs, laptops
- Cameras (IP cameras)
- Smart TVs, IoT devices
- Network equipment (routers, switches)
- Any device with an IP address

**Metrics Available:**

- ✅ Availability (online/offline)
- ✅ Ping latency
- ✅ Uptime percentage
- ✅ Historical connectivity

---

## 🚀 Quick Start

### 1. Add Devices

Edit `network_devices.txt`:

```bash
nano network_devices.txt
```

Format: `IP,Name,Type`

```
# Smartphones
10.10.1.100,iPhone Luis,smartphone
10.10.1.101,Samsung Galaxy,smartphone

# Cameras
10.10.1.120,Camera Entrance,camera
10.10.1.121,Camera Garden,camera

# Computers
10.10.1.110,Desktop Office,pc
10.10.1.111,Laptop,laptop

# IoT
10.10.1.130,Smart TV,tv
10.10.1.131,Smart Speaker,iot
```

### 2. Generate Targets

```bash
python3 scripts/manage_network_devices.py
```

This will:

- Validate IP addresses
- Generate Prometheus targets
- Reload Prometheus configuration

### 3. View Dashboard

1. Open Grafana: http://10.10.1.159:3000
2. Navigate to **Network Devices Overview** dashboard
3. See device status, latency, and uptime

---

## 📊 Dashboard Panels

### 1. Device Status

- Bar gauge showing online/offline status
- Green = Online, Red = Offline

### 2. Ping Latency

- Time series graph of ping response times
- Shows network performance over time

### 3. Uptime (24h)

- Gauge showing uptime percentage
- Based on last 24 hours

### 4. Device List

- Table with all devices
- Columns: Device, Type, IP, Status, Latency, Uptime

---

## 🔧 Management

### Add New Device

```bash
# 1. Edit file
nano network_devices.txt

# 2. Add line
10.10.1.150,New Device,type

# 3. Regenerate targets
python3 scripts/manage_network_devices.py
```

### Remove Device

```bash
# 1. Edit file
nano network_devices.txt

# 2. Delete or comment out line
# 10.10.1.150,Old Device,type

# 3. Regenerate targets
python3 scripts/manage_network_devices.py
```

### Bulk Import

```bash
# Create CSV file
cat > devices.csv << 'EOF'
10.10.1.100,Device1,smartphone
10.10.1.101,Device2,pc
10.10.1.102,Device3,camera
EOF

# Append to network_devices.txt
cat devices.csv >> network_devices.txt

# Regenerate
python3 scripts/manage_network_devices.py
```

---

## 🎯 Device Types

Use these standard types for consistency:

| Type         | Description        | Examples                |
| ------------ | ------------------ | ----------------------- |
| `smartphone` | Mobile phones      | iPhone, Android         |
| `tablet`     | Tablets            | iPad, Android tablet    |
| `pc`         | Desktop computers  | Windows PC, Mac         |
| `laptop`     | Portable computers | Laptop, MacBook         |
| `camera`     | IP cameras         | Security cameras        |
| `tv`         | Smart TVs          | Samsung TV, LG TV       |
| `iot`        | IoT devices        | Smart speakers, sensors |
| `router`     | Network equipment  | OPNsense, pfSense       |
| `switch`     | Network switches   | Managed switches        |
| `server`     | Servers            | Linux server, NAS       |

---

## 🔍 Troubleshooting

### Device Shows Offline

**Check connectivity:**

```bash
# From monitoring server
ping 10.10.1.XXX
```

**Possible causes:**

- Device is actually offline
- Firewall blocking ICMP
- Device doesn't respond to ping
- Wrong IP address

### No Devices in Dashboard

**Verify Prometheus targets:**

1. Open: http://10.10.1.159:9990/targets
2. Look for `blackbox_ping` job
3. Check if targets are listed

**Regenerate targets:**

```bash
python3 scripts/manage_network_devices.py
```

### Blackbox Exporter Not Running

```bash
# Check container
docker compose ps blackbox-exporter

# View logs
docker compose logs blackbox-exporter

# Restart
docker compose restart blackbox-exporter
```

### High Latency

**Normal ranges:**

- Local network (LAN): 1-5ms
- Across subnets: 5-20ms
- WiFi devices: 10-50ms

**If consistently high:**

- Check network congestion
- Verify WiFi signal strength
- Check for network loops

---

## 📈 Metrics Reference

### `probe_success`

- **Type**: Gauge
- **Values**: 0 (offline) or 1 (online)
- **Labels**: `instance`, `device_name`, `device_type`

### `probe_duration_seconds`

- **Type**: Gauge
- **Unit**: Seconds
- **Description**: Time taken for ping probe

### `probe_icmp_duration_seconds`

- **Type**: Gauge
- **Unit**: Seconds
- **Description**: ICMP round-trip time

---

## 🔔 Alerting

### Create Alert for Offline Devices

Add to `prometheus/alerts/network.yml`:

```yaml
groups:
  - name: network_devices
    rules:
      - alert: DeviceOffline
        expr: probe_success{job="blackbox_ping"} == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Device {{ $labels.device_name }} is offline"
          description: "{{ $labels.device_name }} ({{ $labels.instance }}) has been offline for 5 minutes"
```

---

## 🎨 Customization

### Change Probe Interval

Edit `prometheus/prometheus.yml`:

```yaml
- job_name: "blackbox_ping"
  scrape_interval: 30s # Default: 15s
  scrape_timeout: 10s # Default: 10s
```

### Add HTTP Probe

For devices with web interfaces:

Edit `prometheus/prometheus.yml`:

```yaml
- job_name: "blackbox_http"
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
    - targets:
        - http://10.10.1.120 # Camera web interface
```

---

## 📚 Advanced Usage

### Export Device List

```bash
# JSON format
curl -s http://localhost:9990/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job=="blackbox_ping") | {device: .labels.device_name, ip: .labels.instance, status: .health}'

# CSV format
echo "Device,IP,Status" > devices_status.csv
curl -s http://localhost:9990/api/v1/targets | \
  jq -r '.data.activeTargets[] | select(.labels.job=="blackbox_ping") | [.labels.device_name, .labels.instance, .health] | @csv' >> devices_status.csv
```

### Monitor Specific Subnet

```bash
# Generate list of IPs in subnet
for i in {1..254}; do
  echo "10.10.1.$i,Device-$i,unknown"
done > subnet_scan.txt

# Test which respond
cat subnet_scan.txt | while IFS=, read ip name type; do
  if ping -c 1 -W 1 $ip > /dev/null 2>&1; then
    echo "$ip,$name,$type"
  fi
done > active_devices.txt
```

---

## 🔗 Related Documentation

- [Blackbox Exporter Documentation](https://github.com/prometheus/blackbox_exporter)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
