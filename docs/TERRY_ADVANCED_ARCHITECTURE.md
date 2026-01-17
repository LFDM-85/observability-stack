# Terry Advanced - Arquitetura com Memória e Auto-Resolução

## 🧠 Visão Geral

O Terry Advanced adiciona capacidades de:
- **Memória persistente** de eventos e soluções
- **Auto-resolução** de problemas conhecidos (safe commands only)
- **Aprendizagem** baseada em padrões históricos
- **Relatórios** detalhados de incidentes

## 🔄 Arquitetura do Workflow

```
┌──────────────────┐
│ Webhook Receiver │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   Verificar Histórico de Eventos       │
│   - Busca eventos similares             │
│   - Identifica padrões recorrentes      │
│   - Recupera soluções anteriores        │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Seletor de Comandos SSH             │
│     (baseado em categoria)              │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      SSH - Investigação Inicial         │
│      (comandos read-only)               │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│    Terry AI - Análise com Contexto      │
│    Inputs:                              │
│    - Output SSH atual                   │
│    - Histórico de eventos similares     │
│    - Soluções anteriores                │
│                                         │
│    Outputs:                             │
│    - Causa raiz identificada            │
│    - Solução proposta                   │
│    - Classificação de risco             │
│    - Comandos sugeridos                 │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   Classificador de Impacto/Risco        │
│   BAIXO: Read-only, restart services    │
│   MÉDIO: Stop services, clear cache     │
│   ALTO: Delete data, modify configs     │
│   CRÍTICO: Shutdown, format, network    │
└────────┬────────────────────────────────┘
         │
         ├─────────────┬──────────────────┐
         │ Baixo/Médio │ Alto/Crítico     │
         ▼             ▼
┌─────────────┐  ┌──────────────────────┐
│ Auto-Resolver│  │ Notificar Admin     │
│ (Safe Mode) │  │ (Approval Required) │
└──────┬──────┘  └──────┬───────────────┘
       │                │
       ▼                ▼
┌─────────────────────────────────────────┐
│       SSH - Execução da Solução         │
│       (se aprovada ou safe)             │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Validação Pós-Resolução             │
│     - Re-executa diagnóstico            │
│     - Verifica se problema foi resolvido│
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│       Gerar Relatório de Incidente      │
│       - Timestamp início/fim            │
│       - Causa raiz                      │
│       - Solução aplicada                │
│       - Resultado (sucesso/falha)       │
│       - Tempo de resolução              │
│       - Impacto estimado                │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Armazenar em Memória/Histórico      │
│     (JSON file ou Database)             │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│       Notificar Discord                 │
│       - Diagnóstico                     │
│       - Ações tomadas                   │
│       - Resultado                       │
│       - Link para relatório             │
└─────────────────────────────────────────┘
```

## 📊 Sistema de Memória

### Estrutura do Histórico (JSON)

```json
{
  "events": [
    {
      "id": "uuid",
      "timestamp": "2026-01-16T20:30:00Z",
      "alert_name": "HostHighDiskUsage",
      "host_ip": "192.168.90.104",
      "severity": "critical",
      "category": "disk",
      "root_cause": "Logs antigos em /var/log acumulados",
      "solution": {
        "commands": [
          "find /var/log -name '*.gz' -mtime +30 -delete",
          "journalctl --vacuum-time=7d"
        ],
        "risk_level": "low",
        "auto_resolved": true
      },
      "outcome": {
        "success": true,
        "resolution_time_seconds": 45,
        "verification": "Disk usage reduced from 92% to 68%"
      },
      "recurrence_count": 3
    }
  ]
}
```

### Localização da Memória

**Opção 1: File System** (mais simples)
```
/home/luismelo/Documents/GitHub/observability-stack/data/terry-memory.json
```

**Opção 2: Redis** (mais escalável)
```
Key: terry:events:{alert_name}:{host_ip}
TTL: 90 dias
```

**Opção 3: SQLite** (melhor para queries)
```
/home/luismelo/Documents/GitHub/observability-stack/data/terry.db

Table: events
- id (PRIMARY KEY)
- timestamp
- alert_name
- host_ip
- category
- root_cause
- solution_json
- outcome_json
- recurrence_count
```

## 🤖 Lógica de Auto-Resolução

### Critérios para Auto-Resolução

**PERMITIDO (Low Risk)**:
- ✅ Restart services (systemctl restart)
- ✅ Clear caches (apt clean, docker system prune)
- ✅ Rotate logs (journalctl --vacuum)
- ✅ Kill processos específicos (kill -15)
- ✅ Limpar ficheiros temporários (/tmp, *.gz antigos)

**REQUER APROVAÇÃO (Medium Risk)**:
- ⚠️ Stop services (systemctl stop)
- ⚠️ Modificar configurações (sed -i)
- ⚠️ Reinstalar packages (apt install --reinstall)
- ⚠️ Limpar logs ativos (> /var/log/syslog)

**NUNCA AUTO-RESOLVER (High/Critical Risk)**:
- ❌ Delete data directories (rm -rf /data)
- ❌ Format disks (mkfs, dd)
- ❌ Shutdown systems (shutdown, reboot)
- ❌ Network changes (ip addr del, iptables)
- ❌ User management (userdel, passwd)
- ❌ Comandos com sudo su ou su -

### Validador de Comandos (Regex)

```javascript
// Comandos seguros (whitelist)
const SAFE_COMMANDS = [
  /^systemctl restart \w+$/,
  /^journalctl --vacuum-(time|size)=/,
  /^find .+ -delete$/,
  /^docker system prune -f$/,
  /^apt(-get)? clean$/,
  /^kill -15 \d+$/
];

// Comandos perigosos (blacklist)
const DANGEROUS_COMMANDS = [
  /rm -rf/,
  /mkfs/,
  /dd if=/,
  /shutdown/,
  /reboot/,
  /halt/,
  /iptables/,
  /userdel/,
  /deluser/,
  /chmod 777/,
  /> \/dev\/sd[a-z]/
];

function validateCommand(cmd) {
  // Check blacklist first
  if (DANGEROUS_COMMANDS.some(regex => regex.test(cmd))) {
    return { safe: false, risk: 'critical', reason: 'Comando perigoso detectado' };
  }

  // Check whitelist
  if (SAFE_COMMANDS.some(regex => regex.test(cmd))) {
    return { safe: true, risk: 'low', reason: 'Comando seguro' };
  }

  // Default: require approval
  return { safe: false, risk: 'medium', reason: 'Comando requer aprovação manual' };
}
```

## 📝 Sistema de Relatórios

### Formato do Relatório

```markdown
# Relatório de Incidente - HostHighDiskUsage

**ID**: INC-2026-01-16-001
**Timestamp**: 2026-01-16 20:30:00 UTC
**Duração**: 45 segundos

## 📊 Resumo

- **Alerta**: HostHighDiskUsage
- **Host**: 192.168.90.104 (pve)
- **Severidade**: CRITICAL
- **Categoria**: disk

## 🔍 Diagnóstico

### Causa Raiz
Filesystem / está com 92% de utilização devido a:
- Logs comprimidos antigos em /var/log (5.2GB)
- Journal do systemd não rotacionado (3.8GB)
- Cache APT desatualizado (890MB)

### Histórico
Este é o **3º evento similar** nos últimos 30 dias.
Padrão identificado: Logs acumulam-se a cada 10-15 dias.

## 🔧 Solução Aplicada

**Classificação de Risco**: BAIXO
**Modo**: Auto-Resolução (aprovada automaticamente)

**Comandos Executados**:
```bash
find /var/log -name "*.gz" -mtime +30 -delete
journalctl --vacuum-time=7d
apt clean
```

**Resultado**:
- ✅ Sucesso
- Disk usage: 92% → 68% (24% liberado)
- Espaço recuperado: 9.9GB

## ⏱️ Métricas

- **Tempo de Detecção**: 2s (Prometheus → Alertmanager)
- **Tempo de Análise**: 8s (SSH + AI)
- **Tempo de Resolução**: 35s (execução comandos)
- **Tempo Total**: 45s

## 💡 Recomendações

1. **Prevenção**: Configurar cron job para limpeza automática semanal
2. **Monitorização**: Ajustar threshold de alerta para 85%
3. **Capacidade**: Considerar expandir LVM se padrão continuar

## 🔗 Links

- [Ver histórico completo](http://10.10.1.172:3000/d/incidents)
- [Métricas Grafana](http://10.10.1.172:3000/d/node-exporter)
```

### Armazenamento de Relatórios

```bash
/home/luismelo/Documents/GitHub/observability-stack/reports/
├── 2026-01/
│   ├── INC-2026-01-16-001.md
│   ├── INC-2026-01-16-002.md
│   └── summary.json
├── 2026-02/
│   └── ...
└── index.json  # Índice global
```

## 🎯 Prompt Terry Advanced (Gemini)

```
Tu és o Terry, SysAdmin especialista em Linux, Docker e Proxmox com capacidade de:
1. ANALISAR problemas baseado em contexto histórico
2. PROPOR soluções com classificação de risco
3. AUTO-RESOLVER problemas de baixo risco
4. APRENDER com eventos recorrentes

CONTEXTO HISTÓRICO:
{histórico de eventos similares}

ALERTA ATUAL:
Nome: {alert_name}
Host: {host_ip}
Severidade: {severity}
Mensagem: {message}

DIAGNÓSTICO SSH:
{ssh_output}

TAREFA:
1. Analisa o output SSH e identifica a causa raiz
2. Verifica se este problema já ocorreu antes (consulta histórico)
3. Propõe uma solução com comandos específicos
4. Classifica cada comando por nível de risco:
   - LOW: Comandos seguros (restart, clean, rotate)
   - MEDIUM: Requer aprovação (stop, modify configs)
   - HIGH: Comandos destrutivos (delete, format)
   - CRITICAL: Impacto severo (shutdown, network changes)

5. Se todos os comandos forem LOW risk, indica "AUTO_RESOLVE: YES"
6. Se houver comandos MEDIUM+, indica "REQUIRES_APPROVAL: YES"

FORMATO DE RESPOSTA:
```json
{
  "root_cause": "Descrição da causa raiz",
  "solution": {
    "commands": ["comando1", "comando2"],
    "risk_classification": {
      "comando1": "LOW",
      "comando2": "LOW"
    },
    "overall_risk": "LOW",
    "auto_resolve": true
  },
  "explanation": "Explicação técnica em PT-PT",
  "prevention": "Como prevenir no futuro"
}
```

Sê breve, técnico e preciso. Responde SEMPRE em JSON válido.
```

## 🔐 Segurança

### Validações Obrigatórias

1. **Syntax Check**: Validar sintaxe bash antes de executar
2. **Dry Run**: Simular comando quando possível (--dry-run)
3. **Backup**: Backup de configs antes de modificar
4. **Rollback**: Possibilidade de reverter mudanças
5. **Audit Log**: Registar todos os comandos executados

### Permissões SSH

```yaml
# Criar user terry com permissões limitadas
# /etc/sudoers.d/terry
terry ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart *
terry ALL=(ALL) NOPASSWD: /usr/bin/journalctl --vacuum-*
terry ALL=(ALL) NOPASSWD: /usr/bin/find /var/log -name *.gz -delete
terry ALL=(ALL) NOPASSWD: /usr/bin/docker system prune -f
terry ALL=(ALL) NOPASSWD: /usr/bin/apt clean
```

## 📈 Métricas de Performance

| Métrica | Valor Alvo | Alerta |
|---------|-----------|--------|
| Tempo de análise | < 10s | > 30s |
| Taxa de auto-resolução | > 60% | < 40% |
| Sucesso auto-resolução | > 95% | < 90% |
| False positives | < 5% | > 10% |
| Recorrências evitadas | > 30% | < 20% |

## 🚀 Implementação

### Fase 1: Memória e Histórico
- [ ] Criar estrutura de armazenamento (JSON file)
- [ ] Implementar busca de eventos similares
- [ ] Adicionar contagem de recorrências

### Fase 2: Auto-Resolução
- [ ] Implementar classificador de risco
- [ ] Criar validador de comandos
- [ ] Adicionar execução condicional

### Fase 3: Relatórios
- [ ] Gerar relatórios markdown
- [ ] Calcular métricas de resolução
- [ ] Armazenar histórico de incidentes

### Fase 4: Aprendizagem
- [ ] Identificar padrões recorrentes
- [ ] Sugerir prevenções automáticas
- [ ] Dashboard de insights

## 📚 Referências

- [Incident Response Best Practices](https://response.pagerduty.com/)
- [SRE Handbook - Google](https://sre.google/sre-book/table-of-contents/)
- [ITIL Incident Management](https://www.axelos.com/best-practice-solutions/itil)
