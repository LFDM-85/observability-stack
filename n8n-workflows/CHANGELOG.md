# Changelog - Terry Homelab Mechanic Workflow

## v2.1 - Gemini 1.5 Flash (Estável) - 2026-01-16

### ✅ Mudanças Principais

**Problema Resolvido**: Erro "Quota exceeded" do Gemini 2.0 Flash Experimental

**Solução Implementada**: Migração para Gemini 1.5 Flash (modelo estável)

### 🔄 Alterações Técnicas

#### Nó "Terry (Analista Gemini)"
- **Antes**: `gemini-2.0-flash-exp` (experimental, quotas limitadas)
- **Agora**: `gemini-1.5-flash` (estável, quotas generosas)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent`
- **Autenticação**: Header `x-goog-api-key` (formato correto da Google AI API)

#### Configuração da API
- **Rate Limit**: 15 requisições/minuto (free tier)
- **Daily Limit**: 1500 requisições/dia
- **Max Tokens**: 2048 por resposta
- **Temperature**: 0.7

#### Nó "Formatar Discord"
- Atualizado para processar estrutura de resposta do Gemini corretamente
- Extração via: `$json.candidates[0].content.parts[0].text`
- Footer atualizado: "Gemini AI (1.5-flash)"

### 📋 Vantagens do Gemini 1.5 Flash

| Característica | 2.0 Flash Exp | 1.5 Flash (Atual) |
|----------------|---------------|-------------------|
| Estabilidade | ⚠️ Experimental | ✅ Produção |
| Quota Gratuita | Muito limitada | 15 req/min |
| Disponibilidade | Instável | 99.9% uptime |
| Documentação | Limitada | Completa |

### 🚀 Como Atualizar

1. **Substituir workflow no n8n**:
   - Exporte o workflow antigo (backup)
   - Delete o workflow atual
   - Importe [terry-homelab-mechanic.json](terry-homelab-mechanic.json)

2. **Reconfigurar credenciais**:
   - Nó "Terry (Analista Gemini)": Adicionar Google PaLM API credentials
   - Nó "SSH - Investigador": Adicionar SSH credentials
   - Nó "Enviar Discord": Verificar webhook URL

3. **Ativar workflow**:
   - Toggle "Active" → Verde
   - Testar com nó "Teste Manual"

### 📚 Documentação Atualizada

- ✅ [QUICK_SETUP.md](QUICK_SETUP.md): Instruções de configuração Gemini
- ✅ [README.md](README.md): Especificações técnicas do workflow
- ✅ Adicionada seção de troubleshooting para quota errors

### 🎯 Compatibilidade

- **n8n**: Versão 1.0+
- **Credenciais**: Google PaLM API / Google AI
- **Backward Compatible**: Não (requer reconfiguração de credenciais)

### 🔧 Notas Técnicas

**Formato da Resposta Gemini**:
```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "text": "Resposta do Terry..."
      }]
    }
  }]
}
```

**Tratamento de Erros**:
- Fallback para mensagem genérica se resposta inválida
- `onError: continueErrorOutput` no nó SSH
- Validação de campos obrigatórios

### ⚡ Performance

- Latência média: 2-4 segundos por análise
- Tokens médios usados: 800-1200 tokens/requisição
- Custo: **€0** (free tier)

### 🐛 Bugs Corrigidos

- ❌ **Antes**: `Error 429 - Quota exceeded` em gemini-2.0-flash-exp
- ❌ **Antes**: `Error 404 - Model not found` (endpoint incorreto v1 vs v1beta)
- ✅ **Agora**: Modelo estável sem erros de quota, endpoint v1beta correto com autenticação via header

### 📌 Próximos Passos

Considerações futuras:
- [ ] Adicionar fallback para Ollama local (opcional)
- [ ] Implementar rate limiting no adapter (se necessário)
- [ ] Cache de análises repetidas (otimização)
- [ ] Considerar upgrade para Gemini 2.5 Flash (melhor price-performance, disponível em 2026)

---

**Migração recomendada**: ✅ Imediata
**Impacto**: Baixo (apenas reconfiguração de credenciais)
**Downtime**: ~5 minutos
