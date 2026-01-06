import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARDS_DIR = os.path.join(BASE_DIR, 'grafana', 'dashboards')

def fix_dashboards():
    if not os.path.exists(DASHBOARDS_DIR):
        print(f"❌ Dashboards directory not found: {DASHBOARDS_DIR}")
        return

    for filename in os.listdir(DASHBOARDS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DASHBOARDS_DIR, filename)
            print(f"🔧 Fixing dashboard: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace variable patterns with fixed UID
            new_content = content.replace('${DS_PROMETHEUS}', 'prometheus')
            new_content = new_content.replace('${ds_prometheus}', 'prometheus')
            
            # Additional common patterns if needed
            new_content = new_content.replace('\"datasource\": \"${DS_PROMETHEUS}\"', '\"datasource\": \"prometheus\"')
            new_content = new_content.replace('\"uid\": \"${DS_PROMETHEUS}\"', '\"uid\": \"prometheus\"')

            if content != new_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Updated {filename}")
            else:
                print(f"✓ No changes needed for {filename}")

if __name__ == "__main__":
    fix_dashboards()
