#!/usr/bin/env python3
"""
Verify Prometheus targets health and display detailed status
"""

import requests
import json
import sys
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9990"

def get_targets():
    """Get all targets from Prometheus"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Prometheus at", PROMETHEUS_URL)
        print("   Make sure Prometheus is running:")
        print("   docker-compose ps prometheus")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fetching targets: {e}")
        sys.exit(1)

def format_uptime(last_scrape):
    """Calculate time since last scrape"""
    if not last_scrape:
        return "Never"
    try:
        scrape_time = datetime.fromisoformat(last_scrape.replace('Z', '+00:00'))
        now = datetime.now(scrape_time.tzinfo)
        delta = now - scrape_time
        
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s ago"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        else:
            return f"{int(delta.total_seconds() / 3600)}h ago"
    except:
        return last_scrape

def display_targets(data):
    """Display targets in a formatted table"""
    active_targets = data.get('data', {}).get('activeTargets', [])
    
    if not active_targets:
        print("⚠️  No targets configured")
        return
    
    # Group by job
    jobs = {}
    for target in active_targets:
        job = target.get('labels', {}).get('job', 'unknown')
        if job not in jobs:
            jobs[job] = []
        jobs[job].append(target)
    
    print("\n" + "="*100)
    print(f"📊 PROMETHEUS TARGETS STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100 + "\n")
    
    total_up = 0
    total_down = 0
    
    for job_name, targets in sorted(jobs.items()):
        print(f"📁 Job: {job_name}")
        print("-" * 100)
        
        for target in sorted(targets, key=lambda x: x.get('scrapeUrl', '')):
            health = target.get('health', 'unknown')
            scrape_url = target.get('scrapeUrl', 'N/A')
            instance = target.get('labels', {}).get('instance', 'N/A')
            last_scrape = target.get('lastScrape', 'Never')
            last_error = target.get('lastError', '')
            scrape_duration = target.get('lastScrapeDuration', 0)
            
            # Status icon
            if health == 'up':
                icon = "✅"
                total_up += 1
            elif health == 'down':
                icon = "❌"
                total_down += 1
            else:
                icon = "⚠️"
            
            print(f"  {icon} {instance:30s} | Health: {health:8s} | Last: {format_uptime(last_scrape):15s} | Duration: {scrape_duration:.3f}s")
            
            if last_error:
                print(f"     💥 Error: {last_error}")
            
            # For MySQL and Docker, show additional info
            if 'mysql' in job_name.lower():
                print(f"     🗄️  MySQL Exporter - Port 9104")
            elif 'docker' in job_name.lower():
                print(f"     🐳 cAdvisor - Port 9991")
            elif 'remote' in job_name.lower() or 'node' in job_name.lower():
                print(f"     💻 Node Exporter - Port 9100")
        
        print()
    
    print("="*100)
    print(f"📈 SUMMARY: {total_up} UP | {total_down} DOWN | Total: {total_up + total_down}")
    print("="*100 + "\n")
    
    # Show unhealthy targets
    if total_down > 0:
        print("⚠️  UNHEALTHY TARGETS:\n")
        for job_name, targets in jobs.items():
            for target in targets:
                if target.get('health') == 'down':
                    instance = target.get('labels', {}).get('instance', 'N/A')
                    error = target.get('lastError', 'Unknown error')
                    print(f"   ❌ {instance}")
                    print(f"      Job: {job_name}")
                    print(f"      Error: {error}")
                    print()

def check_metrics(instance):
    """Check if specific metrics are available for an instance"""
    print(f"\n🔍 Checking metrics for {instance}...")
    
    queries = {
        'Node Exporter': 'up{instance="' + instance + '",job="remote_hosts"}',
        'CPU Usage': 'rate(node_cpu_seconds_total{instance="' + instance + '"}[5m])',
        'Memory': 'node_memory_MemAvailable_bytes{instance="' + instance + '"}',
        'Disk': 'node_filesystem_avail_bytes{instance="' + instance + '"}'
    }
    
    for name, query in queries.items():
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            data = response.json()
            result = data.get('data', {}).get('result', [])
            
            if result:
                print(f"   ✅ {name}: OK ({len(result)} series)")
            else:
                print(f"   ❌ {name}: No data")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            # Check specific instance metrics
            if len(sys.argv) < 3:
                print("Usage: verify_prometheus_targets.py --check <instance>")
                print("Example: verify_prometheus_targets.py --check 192.168.1.131:9100")
                sys.exit(1)
            check_metrics(sys.argv[2])
        elif sys.argv[1] == '--json':
            # Output raw JSON
            data = get_targets()
            print(json.dumps(data, indent=2))
        else:
            print("Unknown option:", sys.argv[1])
            print("Usage: verify_prometheus_targets.py [--check <instance> | --json]")
    else:
        # Default: show formatted status
        data = get_targets()
        display_targets(data)
        
        # Offer to check metrics for down targets
        down_targets = []
        for target in data.get('data', {}).get('activeTargets', []):
            if target.get('health') == 'down':
                instance = target.get('labels', {}).get('instance')
                if instance:
                    down_targets.append(instance)
        
        if down_targets:
            print("\n💡 TIP: Run diagnostics with:")
            print(f"   python3 scripts/diagnose_monitoring.py {down_targets[0].split(':')[0]}")

if __name__ == "__main__":
    main()