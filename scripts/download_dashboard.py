import urllib.request
import os

DASHBOARDS = {
    "node_exporter_full.json": "https://raw.githubusercontent.com/rfmoz/grafana-dashboards/master/prometheus/node-exporter-full.json",
    "docker_containers.json": "https://raw.githubusercontent.com/fcwu/docker-dashboard-cadvisor-grafana/master/Grafana_Dashboard.json",
    "prometheus_overview.json": "https://grafana.com/api/dashboards/3662/revisions/2/download",
    "alloy_overview.json": "https://grafana.com/api/dashboards/21245/revisions/1/download"
}

dest_dir = os.path.join(os.path.dirname(__file__), "../grafana/dashboards")
os.makedirs(dest_dir, exist_ok=True)

for filename, url in DASHBOARDS.items():
    dest_file = os.path.join(dest_dir, filename)
    try:
        print(f"Downloading {filename} from {url}...")
        urllib.request.urlretrieve(url, dest_file)
        print(f"Saved to {dest_file}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
