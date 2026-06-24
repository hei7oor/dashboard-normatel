# Controle de Versões — Dashboard Normatel

## Como funciona

Este projeto tem **duas versões** que rodam independentes:

| Versão | Arquivo | Como rodar | Porta |
|--------|---------|-----------|-------|
| **ESTÁVEL** (apresentação) | `app.py` | `INSTALAR_E_RODAR.bat` | 8501 |
| **BETA** (testes novos) | `app_beta.py` | `RODAR_BETA.bat` | 8502 |

> A versão **estável nunca é alterada**. Toda novidade entra primeiro no BETA.
> Quando o beta estiver aprovado, ele vira a nova estável.

---

## Histórico

### v1.0 — Estável (apresentação)
- Dashboard SAP + Produtivo
- KPIs, Curva S, gráficos por base
- Filtros inteligentes na lateral
- Assistente IA flutuante (respostas dos dados, sem API)

### BETA — em desenvolvimento
- 📅 **Agenda de Atividades** — ordens pendentes agrupadas por prazo (atrasadas / próximos 7 dias / futuras)
- 🔍 **Detalhamento** — busca por número da ordem com ficha completa
- Selo BETA no cabeçalho

---

## Comandos Git úteis

```bash
# Ver em qual versão você está
git branch --show-current

# Voltar para a versão estável (apresentação)
git checkout main

# Ir para a versão beta
git checkout beta

# Salvar uma nova alteração
git add -A
git commit -m "descrição da mudança"

# Ver todas as versões salvas
git log --oneline
```
