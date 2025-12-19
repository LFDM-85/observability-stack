# Observability Stack

A complete, Docker-based observability stack featuring Prometheus, Grafana, Loki, Alloy, Alertmanager, and a custom Webhook Adapter for Microsoft Teams and Discord integration.

## 🚀 Features

- **Prometheus**: Metrics collection and storage.
- **Grafana**: Visualization and dashboards.
- **Loki**: Log aggregation system.
- **Alloy**: OpenTelemetry Collector distribution for unified telemetry.
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
    The included `setup.sh` script automates the initialization process, checks for required files, and helps you configure your environment.
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

## 📊 Accessing Services

Once the stack is up and running, you can access the services at the following URLs:

| Service | URL | Default Credentials |
|:---|:---|:---|
| **Grafana** | `http://localhost:3000` | `admin` / `admin` |
| **Prometheus** | `http://localhost:9090` | N/A |
| **Alertmanager** | `http://localhost:9093` | N/A |
| **Loki** | `http://localhost:3100` | N/A |
| **Alloy** | `http://localhost:12345` | N/A |

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
├── alloy/              # Alloy configuration
├── grafana/            # Grafana provisioning
├── loki/               # Loki configuration
├── prometheus/         # Prometheus configuration & rules
├── webhook-adapter/    # Python-based webhook adapter
├── .env                # Environment variables (created by setup.sh)
├── docker-compose.yml  # Stack definition
├── setup.sh            # Setup helper script
└── diagnose.sh         # Diagnostic helper script
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
