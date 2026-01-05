import urllib.request
import os

url = "https://raw.githubusercontent.com/rfmoz/grafana-dashboards/master/prometheus/node-exporter-full.json"
dest_dir = os.path.join(os.path.dirname(__file__), "../grafana/dashboards")
dest_file = os.path.join(dest_dir, "node_exporter_full.json")

os.makedirs(dest_dir, exist_ok=True)

try:
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, dest_file)
    print(f"Saved to {dest_file}")
except Exception as e:
    print(f"Error: {e}")
