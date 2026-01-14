# Alert Rules Reference

Complete reference for all Prometheus alert rules in this observability stack.

## Summary

| File | Total Alerts | Predictive | Reactive |
|------|-------------|------------|----------|
| `host.yml` | 18 | 4 | 14 |
| `docker.yml` | 9 | 1 | 8 |
| `services.yml` | 6 | 1 | 5 |
| `proxmox.yml` | 11 | 1 | 10 |
| `kubernetes.yml` | 11 | 3 | 8 |
| `slo.yml` | 4 | 0 | 4 |
| **TOTAL** | **59** | **10** | **49** |

---

## Host Alerts (`host.yml`)

### Critical Alerts

| Alert Name | Threshold | Duration | Description |
|------------|-----------|----------|-------------|
| `InstanceDown` | `up == 0` | 1m | Instance unreachable |
| `HostCpuHighUsageCritical` | CPU > 95% | 2m | Critical CPU usage |
| `HostMemoryHighUsageCritical` | Memory > 95% | 2m | Critical memory usage |
| `HostDiskSpaceCritical` | Disk < 5% OR fills in 6h | 2m | Critical disk space |
| `HostOOMKill` | OOM Kill detected | 0m | Kernel killed process |

### Warning Alerts

| Alert Name | Threshold | Duration | Description |
|------------|-----------|----------|-------------|
| `HostCpuHighUsageWarning` | CPU > 80% | 5m | High CPU usage |
| `HostMemoryHighUsageWarning` | Memory > 80% | 5m | High memory usage |
| `HostDiskSpaceWarning` | Disk < 15% OR fills in 24h | 5m | Low disk space |
| `HostHighLoad` | Load > 2x cores | 10m | High load average |
| `HostNetworkReceiveErrors` | Error rate > 1% | 2m | Network receive errors |
| `HostNetworkTransmitErrors` | Error rate > 1% | 2m | Network transmit errors |
| `HostHighIOWait` | IOWait > 10% | 5m | High disk I/O wait |
| `HostTcpConnectionsHigh` | Connections > 10000 | 5m | Too many TCP connections |
| `HostSwapUsageWarning` | Swap > 80% | 5m | High swap usage |

### Predictive Alerts 🔮

| Alert Name | Prediction | Description |
|------------|------------|-------------|
| `HostDiskSpaceWarning` | Disk fills in 24h | Uses `predict_linear()` |
| `HostDiskSpaceCritical` | Disk fills in 6h | Uses `predict_linear()` |
| `HostMemoryPredictiveFill` | Memory exhausts in 2h | Predicts OOM conditions |
| `HostCpuTrendWarning` | CPU > 70% and rising | Detects sustained increase |
| `HostFilesystemInodesPrediction` | Inodes exhaust in 24h | Prevents inode exhaustion |

---

## Docker/Container Alerts (`docker.yml`)

| Alert Name | Type | Description |
|------------|------|-------------|
| `ContainerDown` | Critical | Container not seen for 5 minutes |
| `ContainerHighCpuUsage` | Warning | Container CPU > 80% |
| `ContainerHighCpuUsageCritical` | Critical | Container CPU > 95% |
| `ContainerHighMemoryUsage` | Warning | Container memory > 90% limit |
| `ContainerHighMemoryUsageCritical` | Critical | Container memory > 98% limit |
| `ContainerKilled` | Warning | Container disappeared |
| `ContainerHighThrottleRate` | Warning | Container being throttled |
| `ContainerRestartsHigh` | Warning | Container restarting frequently |
| `ContainerMemoryPredictiveFill` 🔮 | Warning | Container hits memory limit in 1h |

---

## Kubernetes Alerts (`kubernetes.yml`)

### Node Alerts

| Alert Name | Severity | Description |
|------------|----------|-------------|
| `KubernetesNodeNotReady` | Critical | Node not ready for 5+ minutes |
| `KubernetesNodeMemoryPressure` | Warning | Node under memory pressure |
| `KubernetesNodeDiskPressure` | Critical | Node under disk pressure |
| `KubernetesNodeNetworkUnavailable` | Critical | Node network unavailable |

### Pod Alerts

| Alert Name | Severity | Description |
|------------|----------|-------------|
| `KubernetesPodCrashLooping` | Warning | Pod restarting frequently |
| `KubernetesPodCrashLoopingCritical` | Critical | Pod crashlooping heavily |
| `KubernetesPodNotHealthy` | Warning | Pod in non-running state |

### Predictive Alerts 🔮

| Alert Name | Prediction | Description |
|------------|------------|-------------|
| `KubernetesPVCCapacityPrediction` | PVC fills in 24h | Persistent Volume Claim capacity |
| `KubernetesHPAMaxReplicas` | At max scale | No more scaling possible |
| `KubernetesPodMemoryPrediction` | Pod memory limit in 1h | Container memory prediction |

---

## SLO-Based Alerts (`slo.yml`)

Modern Service Level Objective alerts based on Google SRE practices.

| Alert Name | Severity | Description |
|------------|----------|-------------|
| `SLOErrorBudgetFastBurn` | Critical | 2% of monthly error budget burning in 1h |
| `SLOErrorBudgetSlowBurn` | Warning | 5% of monthly error budget burning in 6h |
| `SLOLatencyHigh` | Warning | P99 latency above 500ms target |
| `SLOAvailabilityLow` | Critical | Availability below 99.9% |
| `ApdexScoreLow` | Warning | Application performance score below 0.85 |

---

## Services/Internal Alerts (`services.yml`)

| Alert Name | Severity | Description |
|------------|----------|-------------|
| `PrometheusConfigReloadFailed` | Warning | Config reload failed |
| `PrometheusTooManyRestarts` | Warning | Prometheus restarting frequently |
| `LokiRequestErrors` | Critical | Loki error rate > 5% |
| `LokiRequestErrorsWarning` | Warning | Loki error rate > 1% |
| `PrometheusStorageAlmostFull` | Critical | Storage > 90% of 10GB limit |
| `PrometheusStoragePredictiveFill` 🔮 | Warning | Storage fills in 24h |

---

## Proxmox Alerts (`proxmox.yml`)

| Alert Name | Severity | Description |
|------------|----------|-------------|
| `ProxmoxNodeDown` | Critical | Proxmox node unreachable |
| `ProxmoxNodeHighCPU` | Warning | Node CPU > 85% |
| `ProxmoxNodeHighCPUCritical` | Critical | Node CPU > 95% |
| `ProxmoxNodeHighMemory` | Warning | Node memory > 90% |
| `ProxmoxNodeHighMemoryCritical` | Critical | Node memory > 98% |
| `ProxmoxNodeHighIOWait` | Warning | Node I/O wait > 15% |
| `ProxmoxGuestDown` | Warning | VM/LXC is down |
| `ProxmoxGuestHighCPU` | Warning | Guest CPU > 85% |
| `ProxmoxGuestHighMemory` | Warning | Guest memory > 90% |
| `ProxmoxStorageHighUsage` | Warning | Storage > 85% |
| `ProxmoxStorageHighUsageCritical` | Critical | Storage > 95% |
| `ProxmoxStoragePredictiveFill` 🔮 | Warning | Storage fills in 24h |

---

## Alertmanager Routing

### Severity Routing

| Severity | Repeat Interval | Receiver |
|----------|-----------------|----------|
| `critical` | 30 minutes | `webhook-critical` |
| `warning` | 4 hours | `webhook-default` |
| SLO alerts | 1 hour | `webhook-default` |

### Inhibition Rules

1. **Critical inhibits Warning** - Same alert and instance
2. **InstanceDown inhibits Host*** - All host alerts for down instances
3. **ContainerDown inhibits Container*** - All container alerts for down containers

---

## Testing Alerts

```bash
# Validate all alert rules
docker exec prometheus promtool check rules /etc/prometheus/alerts/*.yml

# Test webhook delivery
./scripts/test_alerts.sh
```

## Adding Custom Alerts

Create a new YAML file in `prometheus/alerts/` following this template:

```yaml
groups:
  - name: custom_alerts
    interval: 30s
    rules:
      - alert: CustomAlertName
        expr: your_promql_expression > threshold
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Short description"
          description: "Detailed description"
          dashboard: "http://localhost:3000/d/your_dashboard"
```
