# Observability Stack

A complete, Docker-based observability stack featuring Prometheus, Grafana, Loki, Alloy, Alertmanager, and a custom Webhook Adapter for Microsoft Teams and Discord integration.

## 🚀 Features

- **Prometheus**: Metrics collection and storage.
- **Grafana**: Visualization with **automated dashboards** for System, Docker, and Prometheus.
- **Loki**: Log aggregation system.
- **Alloy**: OpenTelemetry Collector distribution with **cAdvisor integration** for deep container monitoring.
- **Alertmanager**: Alert handling and routing.
- **Webhook Adapter**: Custom adapter to bridge alerts to Microsoft Teams and Discord.

## 📋 Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## 🛠️ Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd observability-stack
    ```

2.  **Run the setup script:**
    The included `setup.sh` script automates the initialization process, checks for required files, **downloads popular Grafana dashboards**, and helps you configure your environment.

    ```bash
    ./setup.sh
    ```

    Follow the on-screen prompts to build and start the stack.

3.  **Configure Webhooks (Optional):**
    If you want to receive alerts on Discord or Microsoft Teams, edit the generated `.env` file:
    ```env
    DISCORD_WEBHOOK_URL=your_discord_webhook_url
    TEAMS_WEBHOOK_URL=your_teams_webhook_url
    ```
    Then restart the webhook adapter:
    ```bash
    docker-compose restart webhook-adapter
    ```

## 📊 Automated Dashboards

The stack automatically provisions the following popular dashboards:

- **Node Exporter Full**: CPU, RAM, Disk, and Network for Linux hosts.
- **Docker Containers**: Detailed performance metrics per container (**cAdvisor**).
- **Prometheus Overview**: Health and performance of the Prometheus server.
- **Grafana Alloy**: Monitoring for the telemetry collector.

## 🤖 Monitoring Remote Hosts

This stack includes tools to automate the deployment of Node Exporter to remote Linux servers and automatically configure Prometheus to monitor them.

1.  **Prepare the Host List:**
    Edit the `hosts.txt` file and add the IP addresses of the servers you want to monitor (one per line).

    ```text
    192.168.1.50
    10.0.0.12
    ```

2.  **Run the Deployment:**
    Run the deployment script to install Node Exporter on the targets and update the monitoring config:

    ```bash
    python scripts/deploy_monitor.py
    ```

    _Note: The script attempts to SSH into the targets using the current user's SSH keys. Ensure you have passwordless SSH or `ssh-agent` configured for the target machines._

3.  **Automatic Discovery:**
    Prometheus watches for changes in `prometheus/targets.json`. New targets will appear in Prometheus and Grafana automatically without restarting the stack.

## 📊 Accessing Services

Once the stack is up and running, you can access the services at the following URLs:

| Service          | URL                      | Default Credentials |
| :--------------- | :----------------------- | :------------------ |
| **Grafana**      | `http://localhost:3000`  | `admin` / `admin`   |
| **Prometheus**   | `http://localhost:9090`  | N/A                 |
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
