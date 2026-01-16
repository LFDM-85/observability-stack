# Melhorias no Script de Deploy

## Problema Identificado

Apenas os containers Docker da máquina **192.168.1.135** apareciam no Grafana Dashboard, apesar de existirem 6 máquinas configuradas no [hosts.txt](hosts.txt):
- 192.168.1.136
- 192.168.1.130
- 192.168.1.131
- 192.168.1.135 ✓ (única funcionando)
- 192.168.1.133
- 192.168.1.134

## Causa Raiz

O script [deploy_monitor.py](scripts/deploy_monitor.py) instalava o cAdvisor mas **não validava** se:
1. O serviço estava realmente a funcionar após instalação
2. A porta 9991 estava acessível
3. O endpoint de métricas estava a responder
4. O Prometheus conseguia fazer scrape dos targets

## Melhorias Implementadas

### 1. Nova Função: `verify_cadvisor_running(ip)`

Valida se o cAdvisor está operacional:
- ✅ Verifica status do serviço systemd (`systemctl is-active cadvisor`)
- ✅ Confirma que a porta 9991 está a ouvir
- ✅ Testa acesso ao Docker socket (`/var/run/docker.sock`)
- ✅ Valida resposta do endpoint de métricas (`http://IP:9991/metrics`)

**Localização**: [scripts/deploy_monitor.py:489-519](scripts/deploy_monitor.py#L489-L519)

### 2. Nova Função: `verify_prometheus_scraping(ip, port, job_name, timeout)`

Verifica se o Prometheus consegue fazer scrape do target:
- ✅ Consulta a API do Prometheus (`/api/v1/targets`)
- ✅ Confirma que o target está no estado "up"
- ✅ Mostra erros de scraping se existirem
- ✅ Fornece dicas de troubleshooting

**Localização**: [scripts/deploy_monitor.py:558-600](scripts/deploy_monitor.py#L558-L600)

### 3. Rastreamento Detalhado de Status

Adiciona dicionário `service_status` que rastreia por máquina:
```python
service_status[ip] = {
    'node_exporter': {'installed': bool, 'healthy': bool},
    'cadvisor': {'installed': bool, 'healthy': bool, 'prometheus_scrape': bool},
    'mysql_exporter': {'installed': bool, 'healthy': bool}
}
```

**Localização**: [scripts/deploy_monitor.py:707-711](scripts/deploy_monitor.py#L707-L711)

### 4. Validações Durante o Deploy

Após instalar o cAdvisor:
1. Executa `verify_cadvisor_running()` para confirmar funcionamento
2. Se saudável, executa `verify_prometheus_scraping()` para confirmar scraping
3. Atualiza `service_status` com resultados

**Localização**: [scripts/deploy_monitor.py:723-747](scripts/deploy_monitor.py#L723-L747)

### 5. Relatório Detalhado Final

Novo relatório em 3 secções:

#### A) Resumo de Deployment
```
📊 Deployment Summary:
==================================================
✓ 192.168.1.135      - Healthy
⚠️ 192.168.1.136      - Unhealthy
```

#### B) Status Detalhado por Serviço
```
🔍 Detailed Service Status:
==================================================

📍 192.168.1.135:
   ✓ Node Exporter: Installed & Healthy
   ✓ cAdvisor: Installed & Healthy - Prometheus scraping OK
   ℹ️  MySQL Exporter: Not installed (MySQL not detected)

📍 192.168.1.136:
   ✓ Node Exporter: Installed & Healthy
   ⚠️  cAdvisor: Installed but not responding
```

#### C) Recomendações Específicas
```
💡 Recommendations:
==================================================

🐳 cAdvisor Issues Detected:
   - 192.168.1.136: Run diagnostics with: python3 scripts/diagnose_monitoring.py 192.168.1.136

   Common solutions:
   1. Check firewall: sudo firewall-cmd --add-port=9991/tcp --permanent
   2. Check cAdvisor logs: journalctl -u cadvisor -n 50
   3. Restart cAdvisor: sudo systemctl restart cadvisor
   4. Verify from Prometheus container: docker exec -it prometheus wget -O- http://<IP>:9991/metrics
```

**Localização**: [scripts/deploy_monitor.py:818-904](scripts/deploy_monitor.py#L818-L904)

## Como Usar

### Deploy Completo com Validações
```bash
python3 scripts/deploy_monitor.py
```

### Deploy com Setup de SSH Keys
```bash
python3 scripts/deploy_monitor.py --setup-keys
```

### Deploy sem Health Checks (mais rápido)
```bash
python3 scripts/deploy_monitor.py --skip-health-check
```

## Troubleshooting

### Se cAdvisor não aparecer no Dashboard

1. **Execute o script de deploy** para ver o relatório detalhado:
   ```bash
   python3 scripts/deploy_monitor.py
   ```

2. **Verifique o relatório** na secção "Detailed Service Status" para identificar máquinas com problemas

3. **Para máquinas com problemas**, execute diagnóstico:
   ```bash
   python3 scripts/diagnose_monitoring.py 192.168.1.136
   ```

4. **Ou use auto-fix** para corrigir automaticamente:
   ```bash
   python3 scripts/diagnose_monitoring.py 192.168.1.136 --fix
   ```

5. **Verifique targets no Prometheus**:
   - Aceda a `http://SERVIDOR:9990/targets`
   - Procure pelo job `remote_docker`
   - Confirme que todos os IPs estão "UP"

6. **Verifique dashboard no Grafana**:
   - Aceda a `http://SERVIDOR:3000`
   - Abra "Docker Containers Overview v2"
   - Confirme que containers de todas as máquinas aparecem

## Scripts de Diagnóstico Disponíveis

1. **verify_prometheus_targets.py** - Mostra estado de todos os targets
   ```bash
   python3 scripts/verify_prometheus_targets.py
   ```

2. **diagnose_monitoring.py** - Diagnóstico detalhado por máquina
   ```bash
   python3 scripts/diagnose_monitoring.py 192.168.1.136
   python3 scripts/diagnose_monitoring.py --fix  # Auto-fix em todas
   ```

3. **check_health.py** - Saúde geral do sistema
   ```bash
   python3 scripts/check_health.py
   ```

## Problemas Comuns

### Firewall bloqueando porta 9991
```bash
# No servidor remoto
sudo firewall-cmd --add-port=9991/tcp --permanent
sudo firewall-cmd --reload
```

### cAdvisor não consegue aceder ao Docker socket
```bash
# No servidor remoto
sudo ls -l /var/run/docker.sock
sudo journalctl -u cadvisor -n 50
```

### Prometheus não consegue aceder ao cAdvisor
```bash
# No servidor Prometheus (container)
docker exec -it prometheus wget -O- http://192.168.1.136:9991/metrics
```

### Verificar configuração dos targets
```bash
# Ver ficheiro de targets Docker
cat prometheus/docker_targets.json

# Deve conter todos os IPs na porta 9991
```

## Ficheiros Modificados

- [scripts/deploy_monitor.py](scripts/deploy_monitor.py) - Adicionadas 3 novas funções e relatório detalhado

## Integração com Workflow Existente

As melhorias são **retrocompatíveis** e não quebram o workflow existente:
- ✅ Mantém argumentos CLI existentes
- ✅ Mantém estrutura de ficheiros JSON
- ✅ Compatível com scripts de diagnóstico existentes
- ✅ Adiciona apenas validações extra sem remover funcionalidades

## Próximos Passos Recomendados

Quando implementar no servidor da empresa:

1. Fazer backup dos ficheiros de configuração atuais
2. Executar `python3 scripts/deploy_monitor.py`
3. Analisar o relatório detalhado
4. Corrigir problemas identificados usando os comandos sugeridos
5. Verificar dashboard do Grafana
6. Configurar monitorização regular com `check_health.py`
