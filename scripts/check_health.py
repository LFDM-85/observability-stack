#!/usr/bin/env python3
"""
Health Check Script
Provides overall system health status for the observability stack.
"""

import requests
import json
import sys

PROMETHEUS_URL = "http://localhost:9990"
GRAFANA_URL = "http://localhost:3000"

def check_prometheus_targets():
    """Check status of all Prometheus targets."""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
        if response.status_code != 200:
            return None, "Prometheus API not accessible"
        
        data = response.json().get('data', {})
        targets = data.get('activeTargets', [])
        
        up = sum(1 for t in targets if t.get('health') == 'up')
        down = sum(1 for t in targets if t.get('health') != 'up')
        
        return {
            'total': len(targets),
            'up': up,
            'down': down,
            'targets': targets
        }, None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to Prometheus"
    except Exception as e:
        return None, str(e)

def check_active_alerts():
    """Check for active alerts in Prometheus."""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5)
        if response.status_code != 200:
            return None, "Prometheus alerts API not accessible"
        
        data = response.json().get('data', {})
        alerts = data.get('alerts', [])
        
        firing = [a for a in alerts if a.get('state') == 'firing']
        pending = [a for a in alerts if a.get('state') == 'pending']
        
        return {
            'total': len(alerts),
            'firing': firing,
            'pending': pending
        }, None
    except Exception as e:
        return None, str(e)

def check_metrics_availability():
    """Check what metrics are available."""
    try:
        # Check for node metrics
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': 'up{job=~"monitoring_stack|remote_hosts|remote_docker|remote_mysql"}'},
            timeout=5
        )
        
        if response.status_code != 200:
            return None, "Prometheus query API not accessible"
        
        data = response.json().get('data', {})
        results = data.get('result', [])
        
        metrics = {}
        for r in results:
            job = r['metric'].get('job', 'unknown')
            instance = r['metric'].get('instance', 'unknown')
            value = r['value'][1]
            metrics[f"{job}/{instance}"] = value == '1'
        
        return metrics, None
    except Exception as e:
        return None, str(e)

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_section(title):
    """Print a section divider."""
    print(f"\n{title}")
    print(f"{'-'*60}")

def main():
    print("\n🏥 Observability Stack Health Check")
    print_header("System Status")
    
    overall_health = True
    
    # Check Prometheus targets
    print_section("📡 Prometheus Targets")
    targets_data, error = check_prometheus_targets()
    
    if error:
        print(f"✗ {error}")
        overall_health = False
    else:
        print(f"Total Targets: {targets_data['total']}")
        print(f"✓ Up: {targets_data['up']}")
        if targets_data['down'] > 0:
            print(f"✗ Down: {targets_data['down']}")
            overall_health = False
            print("\nDown targets:")
            for target in targets_data['targets']:
                if target.get('health') != 'up':
                    labels = target.get('labels', {})
                    job = labels.get('job', 'unknown')
                    instance = labels.get('instance', 'unknown')
                    health = target.get('health', 'unknown')
                    last_error = target.get('lastError', 'N/A')
                    print(f"  ✗ {job}/{instance} - {health}")
                    if last_error and last_error != 'N/A':
                        print(f"    Error: {last_error}")
    
    # Check active alerts
    print_section("🔔 Active Alerts")
    alerts_data, error = check_active_alerts()
    
    if error:
        print(f"✗ {error}")
        overall_health = False
    else:
        if alerts_data['firing']:
            print(f"🔥 Firing: {len(alerts_data['firing'])}")
            for alert in alerts_data['firing']:
                name = alert['labels'].get('alertname', 'unknown')
                severity = alert['labels'].get('severity', 'unknown')
                summary = alert['annotations'].get('summary', 'No summary')
                print(f"  ✗ [{severity.upper()}] {name}")
                print(f"    {summary}")
        else:
            print("✓ No firing alerts")
        
        if alerts_data['pending']:
            print(f"⏱️  Pending: {len(alerts_data['pending'])}")
            for alert in alerts_data['pending']:
                name = alert['labels'].get('alertname', 'unknown')
                print(f"  ⏱️  {name}")
    
    #Check metrics availability
    print_section("📊 Metrics Availability")
    metrics, error = check_metrics_availability()
    
    if error:
        print(f"✗ {error}")
        overall_health = False
    else:
        if metrics:
            for key, available in metrics.items():
                icon = "✓" if available else "✗"
                status = "Available" if available else "Unavailable"
                print(f"{icon} {key:40s} - {status}")
                if not available:
                    overall_health = False
        else:
            print("⚠️  No node_exporter metrics found")
            overall_health = False
    
    # Overall health summary
    print_header("Overall Health")
    if overall_health:
        print("✅ System is HEALTHY")
        sys.exit(0)
    else:
        print("⚠️  System has ISSUES - see details above")
        sys.exit(1)

if __name__ == '__main__':
    main()
