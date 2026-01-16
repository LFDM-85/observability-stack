# Observability Stack for Proxmox

A complete, Docker-based observability stack optimized for Proxmox VE environments, featuring Prometheus, Grafana, Loki, Alloy, Alertmanager, and comprehensive monitoring for VMs, LXC containers, and the Proxmox host itself.

## 🚀 Features

### Core Monitoring
- **Prometheus**: Metrics collection, storage, and **proactive alerting**
- **Grafana**: Visualization with **automated dashboards** for Proxmox, System, and Docker
- **Node Exporter**: System metrics from Proxmox host, VMs, and LXC containers
- **Proxmox VE Exporter**: Specific metrics for VMs, LXCs, storage, and cluster health
- **cAdvisor**: Docker container monitoring for LXCs running Docker
- **Loki**: Log aggregation system
- **Tempo**: Distributed Tracing backend
- **Alloy**: OpenTelemetry Collector for traces, logs, and metrics
- **Alertmanager**: Alert handling and routing
- **Webhook Adapter**: Custom adapter to bridge alerts to Microsoft Teams and Discord

### Proxmox-Specific Features
- 🏢 **Proxmox Host Monitoring** - CPU, memory, disk, network, and cluster health
- 📦 **LXC Container Detection** - Automatic detection and labeling of LXC containers
- 🖥️ **VM Monitoring** - Full visibility into QEMU/KVM virtual machines
- 🔍 **Automatic Service Discovery** - Detects Docker, MySQL, and other services
- 📊 **Pre-configured Dashboards** - Proxmox Cluster Overview, Hosts Overview, Docker Containers
- 🔔 **Proxmox-specific Alerts** - VM/LXC status, resource exhaustion, node health

## 🎯 Overview

This is a complete, production-ready observability stack that automatically monitors your servers, containers, and applications. Simply add an IP address, run a script, and get instant visibility into CPU, memory, disk, network, Docker containers, and more—all with automated alerting to Discord or Microsoft Teams.

**Key Highlights:**

- 🚀 **Zero-config local monitoring** - Works out of the box for the host running the stack
- 🤖 **Automated remote deployment** - Add an IP and let the scripts handle everything
- 📊 **Pre-configured dashboards** - System, Docker, Prometheus, and Alloy metrics ready to view
- 🔔 **Proactive alerting** - Predictive disk monitoring, resource limits, container health
- 🔐 **SSH key automation** - Passwordless deployment after one-time setup
- 🕵️ **Full Stack Tracing** - Visualize request flows from frontend to database with Tempo & OTLP

## 🏗️ How It Works

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Monitoring Server                             │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Grafana  │◄─┤Prometheus│  │   Loki   │  │  Tempo   │          │
│  │  :3000   │  │  :9990   │  │  :3100   │  │  :3200   │          │
│  └──────────┘  └────▲─────┘  └─────▲────┘  └─────▲────┘          │
│                     │              │             │               │
│                     └──────┬───────┴─────────────┘               │
│                            │                                     │
│                      ┌─────┴─────┐                               │
│                      │   Alloy   │ ◄── OTLP (Traces/Logs/Metrics)│
│                      │  :12345   │                               │
│                      └─────▲─────┘                               │
│                            │                                     │
│  ┌─────────────────────────┼──────────────────────────────────┐  │
│  │  Scrapes metrics        │  Collects logs                   │  │
│  │                         │                                  │  │
│  ▼                         ▼                                  │  │
│  Node Exporter           cAdvisor                             │  │
│                                                               │  │
└─────────────────────┬─────────────────────────────────────────┘  │
                      │                                            │
                      │ SSH + Node Exporter                        │
                      │ (auto-deployed)                            │
                      │                                            │
         ┌────────────┼────────────┐                               │
         │            │            │                               │
         ▼            ▼            ▼                               │
    Remote       Remote       Remote                               │
    Server 1     Server 2     Server N                             │
    :9100        :9100        :9100                                │
```

### Components

1. **Prometheus** - Collects and stores metrics from all targets
2. **Grafana** - Visualizes metrics with pre-configured dashboards
3. **Loki** - Aggregates logs from containers and system
4. **Tempo** - Stores distributed traces for APM
5. **Alloy** - Telemetry collector (OTLP, Prometheus, Logging)
6. **Node Exporter** - Exports system metrics (CPU, RAM, disk, network)
7. **Alertmanager** - Routes alerts based on rules
8. **Webhook Adapter** - Bridges alerts to Discord/Teams

### Data Flow

1. **Local Monitoring**: Node Exporter + cAdvisor collect metrics from the Docker host
2. **Remote Monitoring**: Deploy script installs Node Exporter on remote servers via SSH
3. **Collection**: Prometheus scrapes all exporters every 15 seconds
4. **Visualization**: Grafana queries Prometheus and displays dashboards
5. **Alerting**: Prometheus evaluates rules → Alertmanager → Webhook Adapter → Discord/Teams

## 🚀 Getting Started

### Prerequisites

- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Python 3** - For deployment scripts
- **SSH Access** - Root access to servers you want to monitor (optional for remote monitoring)

### Quick Start for Proxmox (10 Minutes)

#### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd observability-stack
./setup.sh
```

The setup script will:

- ✅ Verify all configuration files
- ✅ Create `.env` file for webhooks
- ✅ Create `hosts.txt` from template if it doesn't exist
- ✅ Download and provision Grafana dashboards
- ✅ Start all Docker containers

#### Step 2: Configure Hosts

Create your `hosts.txt` file with your Proxmox environment:

```bash
# Copy the example file
cp hosts.txt.example hosts.txt

# Edit with your IPs
nano hosts.txt
```

Example `hosts.txt` for Proxmox:

```text
# Proxmox Host
192.168.90.104  # Proxmox VE Host

# Virtual Machines
192.168.90.105  # VM 100 - OPNsense
10.10.1.156     # VM 101 - Zorin18

# LXC Containers
192.168.90.106  # LXC 200 - adguard
10.10.1.152     # LXC 201 - immich
10.10.1.172     # LXC 202 - n8n
# ... add all your LXCs and VMs
```

> **Note**: The `hosts.txt` file is gitignored for security. Use `hosts.txt.example` as a template.

#### Step 3: Access Grafana

Open your browser to **http://localhost:3000**

- **Username**: `admin`
- **Password**: `admin` (you'll be prompted to change it)

**You'll immediately see data** from the local host (the machine running Docker)!

#### Step 3: Configure Webhooks (Optional)

To receive alerts on Discord or Microsoft Teams:

1. Edit `.env` file:

   ```bash
   nano .env
   ```

2. Add your webhook URLs:

   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
   ```

3. Restart the webhook adapter:
   ```bash
   docker compose restart webhook-adapter
   ```

#### Step 4: Install Proxmox VE Exporter (Required)

Install the Proxmox VE Exporter on your Proxmox host to get VM/LXC metrics:

```bash
./scripts/install_proxmox_exporter.sh 192.168.90.104
```

Follow the prompts to configure the API token. See [PROXMOX_SETUP_GUIDE.md](PROXMOX_SETUP_GUIDE.md) for detailed instructions.

#### Step 5: Deploy Monitoring to All Hosts

Setup SSH keys and deploy Node Exporter to all hosts in `hosts.txt`:

```bash
# Setup SSH keys (one-time)
cd scripts
python3 setup_ssh_key.py --all

# Deploy monitoring (installs Node Exporter, cAdvisor where needed)
python3 deploy_monitor.py
```

The script will:
- ✅ Detect if each host is a Proxmox host, VM, or LXC
- ✅ Install Node Exporter on all hosts
- ✅ Install cAdvisor on hosts with Docker
- ✅ Verify Prometheus can scrape all targets
- ✅ Show detailed status report

#### Step 6: Verify Everything Works

```bash
python3 scripts/check_health.py
```

Done! Your Proxmox environment is now fully monitored with dashboards in Grafana.

### Understanding Your Proxmox Setup

After setup, you have:

- **8 Docker containers** running the monitoring stack
- **3 Proxmox-optimized dashboards** in Grafana:
  - **Proxmox Cluster Overview** - VM/LXC status, CPU, memory per guest
  - **Proxmox Hosts Overview** - System metrics for all hosts (Proxmox, VMs, LXCs)
  - **Docker Containers** - Container metrics for LXCs running Docker
- **4 Prometheus jobs** collecting metrics:
  - `monitoring_stack` - Local stack services
  - `remote_hosts` - Node Exporter (all hosts)
  - `remote_docker` - cAdvisor (Docker hosts)
  - `proxmox` - Proxmox VE Exporter (cluster metrics)
- **Automatic scraping** every 15 seconds
- **59 Alert rules** monitoring for issues (including Proxmox-specific)
- **30 days** of metric retention

## 📚 Proxmox Documentation

For detailed Proxmox setup and configuration:

- **[PROXMOX_SETUP_GUIDE.md](PROXMOX_SETUP_GUIDE.md)** - Complete setup guide with troubleshooting
- **[PROXMOX_INVENTORY.md](PROXMOX_INVENTORY.md)** - Environment inventory and architecture
- **[PROXMOX_MIGRATION_SUMMARY.md](PROXMOX_MIGRATION_SUMMARY.md)** - Changes and improvement suggestions

## 📊 Automated Dashboards & Alerts

The stack automatically provisions popular dashboards and matching alerting rules:

### Dashboards

- **Node Exporter Full**: CPU, RAM, Disk, and Network for Linux hosts.
- **Docker Containers**: Detailed performance metrics per container (**cAdvisor**).
- **Prometheus Overview**: Health and performance of the Prometheus server.
- **Grafana Alloy**: Monitoring for the telemetry collector.

### Proactive & Predictive Alerts 🔮

This stack includes **59 alert rules** across 6 categories with modern predictive capabilities:

| Category | Alerts | Predictive |
|----------|--------|------------|
| Host Monitoring | 18 | 4 |
| Docker/Containers | 9 | 1 |
| Kubernetes | 11 | 3 |
| Proxmox | 11 | 1 |
| Services | 6 | 1 |
| SLO-Based | 4 | - |

**Key Features:**

- **Predictive Disk/Memory Monitoring**: Uses `predict_linear()` to forecast exhaustion 2-24h in advance.
- **CPU Trend Detection**: Alerts when CPU usage is high AND trending upward.
- **SLO Error Budget Burn Rate**: Multi-window, multi-burn-rate alerts based on Google SRE practices.
- **Apdex Score Monitoring**: Application performance index tracking.
- **Smart Inhibitions**: Avoids alert storms by suppressing related alerts.

> 📄 See [ALERTS.md](ALERTS.md) for complete alert reference documentation.

## ⚙️ Configuration Highlights

### Simplified Prometheus Jobs

The stack uses a streamlined Prometheus configuration:

- **`monitoring_stack`** - Single job for all internal services (Prometheus, Grafana, Loki, Alloy, Node Exporter, cAdvisor)
- **`remote_hosts`** - Auto-discovered remote servers via file-based service discovery

This consolidation:

- ✅ Simplifies configuration management
- ✅ Reduces UI clutter in Prometheus
- ✅ Makes it easier to apply global labels
- ✅ Clearly separates local vs remote monitoring

You can view all targets at: **http://localhost:9990/targets**

## 🤖 Monitoring Remote Hosts

This stack includes tools to automate the deployment of Node Exporter to remote Linux servers and automatically configure Prometheus to monitor them.

1.  **Prepare the Host List:**
    Edit the `hosts.txt` file and add the IP addresses of the servers you want to monitor (one per line). Local host metrics are already collected by default through the internal `node-exporter` service.

    ```text
    192.168.1.50
    10.0.0.12
    ```

2.  **Run the Deployment:**
    Run the deployment script to install Node Exporter on the targets and update the monitoring config:

    ```bash
    python scripts/deploy_monitor.py
    ```

    _Note: The script uses SSH key authentication. Run `python3 scripts/setup_ssh_key.py --all` first to configure passwordless SSH._

3.  **Automatic Discovery:**
    Prometheus watches for changes in `prometheus/targets.json`. New targets will appear under the **`remote_hosts`** job in Prometheus and Grafana automatically without restarting the stack.

### Automatic Docker & Database Monitoring

The deployment script automatically detects and monitors:

🐳 **Docker Containers**

- Detects if Docker is running on the remote host
- Installs cAdvisor as a systemd service (port 8080)
- Metrics appear under the `remote_docker` job
- Container metrics integrate into existing dashboards

🗄️ **MySQL/MariaDB Databases**

- Automatically detects MySQL or MariaDB
- Installs mysqld_exporter as a systemd service (port 9104)
- Creates monitoring user with limited privileges
- Metrics appear under the `remote_mysql` job
- Dashboards available for database performance

🐘 **PostgreSQL** (Coming Soon)

- PostgreSQL exporter
- Automatic detection and installation

**Example workflow:**

```bash
# Add servers to hosts.txt
# Option 1: Just IP (assumes root user)
echo "192.168.1.50" > hosts.txt

# Option 2: Specific User (recommended for non-root servers)
echo "ubuntu@10.0.0.120" >> hosts.txt

# Deploy monitoring (auto-detects Docker)
python3 scripts/deploy_monitor.py

# ...
# ✅ Docker monitoring configured
```

### 🔐 Permissions & Troubleshooting (Non-root users)

If you are using a non-root user (e.g., `ubuntu@10.0.1.50`), the deployment script requires **sudo** privileges to install services and move binaries.

#### 1. Setup Passwordless Sudo (Recommended for Automation)

To allow the script to run without a terminal interrupt, add your user to the sudoers file on the **target host**:

```bash
sudo visudo
# Add this at the end:
your_username ALL=(ALL) NOPASSWD: ALL
```

#### 2. Full Manual Recovery (If script fails midway)

If the script fails due to a password prompt, the installation might be incomplete (e.g., binaries moved but service not created). Run this block on the **target host** to fix it:

```bash
# 1. Move binary to system path
sudo mv /tmp/node_exporter-1.8.2.linux-amd64/node_exporter /usr/local/bin/

# 2. Create system user
sudo useradd -rs /bin/false node_exporter || true

# 3. Create service unit
sudo tee /etc/systemd/system/node_exporter.service <<EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# 4. Start and Enable
sudo systemctl daemon-reload
sudo systemctl start node_exporter
sudo systemctl enable node_exporter
```

#### 3. Common Errors

- `Permission denied`: The user needs `sudo` but it's not being used or failing.
- `sudo: a terminal is required`: You haven't configured `NOPASSWD` and `sudo` is asking for a password.
- `Unit node_exporter.service not found`: The script failed before creating the service file. Follow the **Manual Recovery** above.

## �️ Full Stack Observability (APM)

The stack now supports **Application Performance Monitoring** and **Distributed Tracing** out of the box via OpenTelemetry (OTLP).

### 1. Application Tracing & Metrics (OTLP)

Point your applications to the **Alloy** collector using the standard OTLP protocol. Alloy acts as a unified receiver and automatically routes:

- **Traces** → Grafana Tempo
- **Metrics** → Prometheus
- **Logs** → Loki

**Endpoints:**

- **gRPC:** `http://<monitoring-server-ip>:4317` (Recommended for production)
- **HTTP:** `http://<monitoring-server-ip>:4318` (Easier for web/testing)

#### 📝 Instrumentation Example

You don't need to change your stack's architecture. Just add the OpenTelemetry SDK to your app.

**Example (Node.js/Python/Go/Java):**
Most OpenTelemetry SDKs are configured simply via environment variables:

```bash
# Point to the Monitoring Server (Alloy)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://monitor.local:4317"
export OTEL_SERVICE_NAME="my-backend-service"
export OTEL_TRACES_EXPORTER="otlp"
export OTEL_METRICS_EXPORTER="otlp"
```

### 2. Viewing Traces in Grafana

Once your application is sending data, you can visualize the full journey of requests:

1.  **Go to Explore**: Open Grafana (`http://localhost:3000`) and click on the Compass icon (Explore).
2.  **Select Source**: Choose **Tempo** from the top dropdown.
3.  **Search Traces**:
    - Use the **Search** tab to find traces by `Service Name`, `Duration`, or HTTP tags.
    - Click on a **Trace ID** to open the Waterfall view.
4.  **Waterfall View**:
    - This view shows the entire request lifecycle.
    - **Bars** represent spans (individual operations).
    - You can pinpoint exactly where latency occurs (e.g., "Why did this API call take 2s?" -> "Ah, the SQL query took 1.8s").

### 3. Reverse Proxy Monitoring (Traefik)

Includes a dedicated Prometheus job for **Traefik**.

1.  Enable metrics in your Traefik config:
    ```yaml
    metrics:
      prometheus:
        addEntryPointsLabels: true
        addRoutersLabels: true
    ```
2.  Ensure Traefik is reachable at `traefik:8082` (or update `prometheus/prometheus.yml` target).

## �🔔 Alerting Rules

The alerting stack has been significantly enhanced and refactored based on the [Awesome Prometheus Alerts](https://samber.github.io/awesome-prometheus-alerts/) collection. Alerts are now modularized in `prometheus/alerts/`:

- **`host.yml`**: CPU, Memory, Disk, and Networking (errors, drops) alerts for Linux hosts.
- **`docker.yml`**: Container health, resource usage, throttling, and kills.
- **`proxmox.yml`**: Proxmox Node and Guest (VM/LXC) status and resource usage.
- **`kubernetes.yml`**: Node status, Pod crash loops, API latency, and Kubelet health.
- **`services.yml`**: Internal stack monitoring (Prometheus, Loki, Alertmanager).

All alerts include direct links to relevant Grafana dashboards in Discord/Teams notifications for faster troubleshooting.

## 🤖 Automated Production Deployment

The stack includes automation tools for production-ready deployment with minimal manual intervention.

### Quick Start

1.  **Setup SSH Keys (One-Time):**

    ```bash
    python3 scripts/setup_ssh_key.py --all
    ```

    This sets up passwordless SSH authentication for all hosts in `hosts.txt`.

2.  **Deploy Monitoring:**

    ```bash
    python3 scripts/deploy_monitor.py
    ```

    Or combine SSH setup and deployment:

    ```bash
    python3 scripts/deploy_monitor.py --setup-keys
    ```

3.  **Verify System Health:**

    ```bash
    python3 scripts/check_health.py
    ```

4.  **Test Alerts:**
    ```bash
    ./scripts/test_alerts.sh
    ```

### Available Scripts

- **`setup_ssh_key.py`** - Automates SSH key distribution using password authentication
- **`deploy_monitor.py`** - Deploys Node Exporter with validation and health checks
- **`check_health.py`** - Shows overall system health, target status, and active alerts
- **`test_alerts.sh`** - Triggers test alerts to verify webhook delivery

### SSH Key Troubleshooting

If `setup_ssh_key.py` fails with `Permission denied (publickey,...)`, the remote server doesn't allow password authentication. Use one of these methods:

**Option 1: Temporarily enable password authentication on the remote server**

```bash
# On the REMOTE server (e.g., 192.168.1.100):
sudo sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# On your monitoring server, copy the key:
ssh-copy-id root@192.168.1.100

# Then revert on the remote server:
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

**Option 2: Manually copy the SSH key**

```bash
# On your monitoring server, display the public key:
cat ~/.ssh/id_rsa.pub

# On the REMOTE server, add the key:
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "PASTE_YOUR_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

After setting up the key, verify with:

```bash
ssh root@192.168.1.100 echo "SSH OK"
```

### Docker Network Troubleshooting

If a target is reachable from the host but Prometheus shows it as "down", the Docker container may not have network access to the target.

**1. Verify host-level connectivity:**

```bash
# Test from the host (should work)
nc -zv 192.168.1.100 9100
```

**2. Test from inside the Prometheus container:**

```bash
# If this fails, it's a Docker network issue
docker exec prometheus wget -qO- http://192.168.1.100:9100/metrics | head -5
```

**3. Check Docker network configuration:**

```bash
docker network ls
docker network inspect monitoring
```

**4. Common solutions:**

- Ensure the `monitoring` network uses the `bridge` driver (default)
- Check if the host firewall allows Docker bridge traffic
- For hosts on different subnets, ensure proper routing exists

> [!TIP]
> For detailed workflow and troubleshooting, see the automation documentation in the project root.

## 📊 Accessing Services

Once the stack is up and running, you can access the services at the following URLs:

| Service          | URL                      | Default Credentials |
| :--------------- | :----------------------- | :------------------ |
| **Grafana**      | `http://localhost:3000`  | `admin` / `admin`   |
| **Prometheus**   | `http://localhost:9990`  | N/A                 |
| **Alertmanager** | `http://localhost:9093`  | N/A                 |
| **Loki**         | `http://localhost:3100`  | N/A                 |
| **Tempo**        | `http://localhost:3200`  | N/A (Use Grafana)   |
| **Alloy (UI)**   | `http://localhost:12345` | N/A                 |
| **Alloy (OTLP)** | `:4317` (gRPC) / `:4318` | N/A                 |

## 🩺 Diagnosis

If you encounter any issues, run the diagnostic script to check the health of all services:

```bash
./diagnose.sh
```

This script will verify container status, check service health endpoints, and provide useful debug information.

## 📁 Directory Structure

```text
observability-stack/
├── alertmanager/       # Alertmanager configuration
├── alloy/              # Alloy configuration (with cAdvisor)
├── grafana/            # Grafana provisioning & dashboards
├── loki/               # Loki configuration
├── prometheus/         # Prometheus configuration & rules
├── tempo/              # Tempo configuration
├── scripts/            # Automation & dashboard scripts
├── webhook-adapter/    # Python-based webhook adapter
├── .env                # Environment variables (created by setup.sh)
├── docker-compose.yml  # Stack definition
├── setup.sh            # Setup helper script
└── diagnose.sh         # Diagnostic helper script
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
