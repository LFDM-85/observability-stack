FROM python:3.11-slim

# Install nmap and other dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pyyaml

WORKDIR /app

# Copy scripts
COPY scripts/network_discovery.py /app/network_discovery.py
COPY scripts/manage_network_devices.py /app/manage_network_devices.py

# Create prometheus directory for targets
RUN mkdir -p /app/prometheus /data

ENV PROMETHEUS_HOST=prometheus
ENV PROMETHEUS_PORT=9090
ENV SCAN_INTERVAL=300

CMD ["sh", "-c", "echo 'Network Discovery Service starting...' && \
    echo 'Waiting for Prometheus...' && \
    sleep 10 && \
    while true; do \
        echo \"[$(date '+%Y-%m-%d %H:%M:%S')] Starting network scan...\" && \
        python3 /app/network_discovery.py --scan --config /app/network_discovery.yml && \
        echo \"[$(date '+%Y-%m-%d %H:%M:%S')] Scan complete. Next scan in ${SCAN_INTERVAL}s...\" && \
        sleep ${SCAN_INTERVAL}; \
    done"]
