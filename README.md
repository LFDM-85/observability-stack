# Observability Stack

A complete, Docker-based observability stack featuring Prometheus, Grafana, Loki, Alloy, Alertmanager, and a custom Webhook Adapter for Microsoft Teams and Discord integration.

## 🚀 Features

- **Prometheus**: Metrics collection, storage, and **proactive alerting**.
- **Grafana**: Visualization with **automated dashboards** for System, Docker, and Prometheus.
- **Node Exporter**: Built-in collector for local host metrics.
- **Loki**: Log aggregation system.
- **Alloy**: OpenTelemetry Collector distribution with **cAdvisor integration** and system monitoring.
- **Alertmanager**: Alert handling and routing.
- **Webhook Adapter**: Custom adapter to bridge alerts to Microsoft Teams and Discord.

## 🎯 Overview

This is a complete, production-ready observability stack that automatically monitors your servers, containers, and applications. Simply add an IP address, run a script, and get instant visibility into CPU, memory, disk, network, Docker containers, and more—all with automated alerting to Discord or Microsoft Teams.

**Key Highlights:**

- 🚀 **Zero-config local monitoring** - Works out of the box for the host running the stack
- 🤖 **Automated remote deployment** - Add an IP and let the scripts handle everything
- 📊 **Pre-configured dashboards** - System, Docker, Prometheus, and Alloy metrics ready to view
- 🔔 **Proactive alerting** - Predictive disk monitoring, resource limits, container health
- 🔐 **SSH key automation** - Passwordless deployment after one-time setup

## 🏗️ How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Server                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Grafana  │  │Prometheus│  │   Loki   │  │  Alloy   │  │
│  │  :3000   │◄─┤  :9990   │◄─┤  :3100   │◄─┤  :12345  │  │
│  └──────────┘  └────┬─────┘  └──────────┘  └─────┬────┘  │
│                     │                              │        │
│  ┌──────────────────┼──────────────────────────────┘       │
│  │  Scrapes metrics │  Collects logs                       │
│  │                  │                                       │
│  ▼                  ▼                                       │
│  Node Exporter   cAdvisor    (local host metrics)         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ SSH + Node Exporter
                      │ (auto-deployed)
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    Remote       Remote       Remote
    Server 1     Server 2     Server N
    :9100        :9100        :9100
```

### Components

1. **Prometheus** - Collects and stores metrics from all targets
2. **Grafana** - Visualizes metrics with pre-configured dashboards
3. **Loki** - Aggregates logs from containers and system
4. **Alloy** - Telemetry collector with cAdvisor for container metrics
5. **Node Exporter** - Exports system metrics (CPU, RAM, disk, network)
6. **Alertmanager** - Routes alerts based on rules
7. **Webhook Adapter** - Bridges alerts to Discord/Teams

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

### Quick Start (5 Minutes)

#### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd observability-stack
./setup.sh
```

The setup script will:

- ✅ Verify all configuration files
- ✅ Create `.env` file for webhooks
- ✅ Download and provision Grafana dashboards
- ✅ Start all Docker containers

#### Step 2: Access Grafana

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

#### Step 4: Add Remote Servers (Optional)

To monitor additional servers:

1. **Add IPs to hosts.txt**:

   ```bash
   echo "192.168.1.100" >> hosts.txt
   echo "10.0.0.50" >> hosts.txt
   ```

2. **Setup SSH keys** (one-time per server):

   ```bash
   cd scripts
   python3 setup_ssh_key.py --all
   ```

   - Enter the root password when prompted
   - SSH keys will be automatically configured

3. **Deploy monitoring**:

   ```bash
   python3 deploy_monitor.py
   ```

   - Installs Node Exporter on each server
   - Adds targets to Prometheus
   - Verifies health

4. **Verify everything works**:
   ```bash
   python3 check_health.py
   ```

Done! Your remote servers now appear in Grafana dashboards.

### Understanding Your Setup

After setup, you have:

- **8 Docker containers** running the monitoring stack
- **4 pre-configured dashboards** in Grafana
- **Automatic scraping** every 15 seconds
- **Alert rules** monitoring for issues
- **30 days** of metric retention

## 📊 Automated Dashboards & Alerts

The stack automatically provisions popular dashboards and matching alerting rules:

### Dashboards

- **Node Exporter Full**: CPU, RAM, Disk, and Network for Linux hosts.
- **Docker Containers**: Detailed performance metrics per container (**cAdvisor**).
- **Prometheus Overview**: Health and performance of the Prometheus server.
- **Grafana Alloy**: Monitoring for the telemetry collector.

### Proactive Alerts

- **Predictive Disk Monitoring**: Alerts when a disk is projected to be full in 24h based on current trends.
- **Resource Limits**: Alerts for high CPU/Memory usage at both host and container levels.
- **System Load**: Detects high Load Average relative to the number of CPU cores.
- **Container Health**: Monitors for containers stopping or crash-looping.

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

> [!TIP]
> For detailed workflow and troubleshoting, see the automation documentation in the project root.

## 📊 Accessing Services

Once the stack is up and running, you can access the services at the following URLs:

| Service          | URL                      | Default Credentials |
| :--------------- | :----------------------- | :------------------ |
| **Grafana**      | `http://localhost:3000`  | `admin` / `admin`   |
| **Prometheus**   | `http://localhost:9990`  | N/A                 |
| **Alertmanager** | `http://localhost:9093`  | N/A                 |
| **Loki**         | `http://localhost:3100`  | N/A                 |
| **Alloy**        | `http://localhost:12345` | N/A                 |

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
├── scripts/            # Automation & dashboard scripts
├── webhook-adapter/    # Python-based webhook adapter
├── .env                # Environment variables (created by setup.sh)
├── docker-compose.yml  # Stack definition
├── setup.sh            # Setup helper script
└── diagnose.sh         # Diagnostic helper script
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
