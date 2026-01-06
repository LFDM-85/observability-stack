import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARDS_DIR = os.path.join(BASE_DIR, 'grafana', 'dashboards')

def fix_dashboards():
    if not os.path.exists(DASHBOARDS_DIR):
        print(f"❌ Dashboards directory not found: {DASHBOARDS_DIR}")
        return

    # Regex to find ${DS_...} or similar patterns
    # Matches patterns like ${DS_PROMETHEUS}, ${ds_prometheus}, ${DS_THEMIS}, ${DS_THERMIS}
    ds_pattern = re.compile(r'\${DS_[A-Z_]+}|\${ds_[a-z_]+}')
    
    # Specific patterns for datasource and uid fields in JSON
    datasource_field_pattern = re.compile(r'\"datasource\":\s*\"\${[^"}]*}\"')
    uid_field_pattern = re.compile(r'\"uid\":\s*\"\${[^"}]*}\"')

    for filename in os.listdir(DASHBOARDS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DASHBOARDS_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content
            
            # 1. Handle LOKI first to avoid it being caught by generic loops if needed
            new_content = re.sub(r'\${DS_LOKI}|\${ds_loki}', 'loki', new_content)
            
            # 2. General replacement for other DS variables to 'prometheus'
            # (Matches ${DS_PROMETHEUS}, ${DS_THEMIS}, ${DS_THERMIS}, etc.)
            def ds_replacer(match):
                if 'LOKI' in match.group(0).upper():
                    return 'loki'
                return 'prometheus'
            
            new_content = ds_pattern.sub(ds_replacer, new_content)
            
            # 3. Clean up the specific JSON fields
            # "datasource": "${DS_X}" -> "datasource": "prometheus"
            new_content = datasource_field_pattern.sub('\"datasource\": \"prometheus\"', new_content)
            new_content = uid_field_pattern.sub('\"uid\": \"prometheus\"', new_content)

            if content != new_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Normalized: {filename}")
            else:
                print(f"✓ Already correct: {filename}")

if __name__ == "__main__":
    fix_dashboards()
