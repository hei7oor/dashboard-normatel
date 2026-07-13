"""
Cliente da API REST do Produttivo (https://app.produttivo.com.br) — só leitura,
usado para buscar as atividades de campo (endpoint /works) e os Clientes/Locais
(/resource_places), que juntos dão a mesma informação dos exports manuais
REALIZAR/ANDAMENTO/FINALIZADAS.xlsx que o app_beta.py já sabe ler.

Recebe as credenciais por parâmetro (não lê variável de ambiente sozinho), para
poder ser usado tanto pelo script do GitHub Actions (scripts/sync_produtivo.py)
quanto, no futuro, por dentro do próprio Streamlit.

Autenticação: 3 headers fixos em toda chamada — X-Auth-Login (e-mail), X-Auth-Token
e X-Auth-Register — obtidos no painel do Produttivo em Configurações > API (exige
plano de Automação). Limite de requisições do Produttivo: 600 a cada 5 minutos;
_get_paginado() dá uma pausa curta entre páginas para nunca chegar perto disso.
"""
import time
import requests

BASE_URL = "https://app.produttivo.com.br"
TIMEOUT = 30
PAUSA_ENTRE_PAGINAS = 0.3


class ProdutivoError(Exception):
    pass


def _headers(login, token, register):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Auth-Login": login,
        "X-Auth-Token": token,
        "X-Auth-Register": register,
    }


def _get_paginado(caminho, login, token, register, params=None, max_paginas=1000):
    """Busca todas as páginas de um endpoint de listagem (results + meta.total_pages)
    e devolve a lista completa de resultados."""
    if not (login and token and register):
        raise ProdutivoError(
            "Credenciais do Produttivo não configuradas (login/token/register)."
        )
    params = dict(params or {})
    resultados = []
    pagina = 1
    while True:
        params["page"] = pagina
        try:
            r = requests.get(
                f"{BASE_URL}{caminho}",
                headers=_headers(login, token, register),
                params=params,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise ProdutivoError(f"Falha de conexão com o Produttivo: {e}") from e
        if r.status_code == 401:
            raise ProdutivoError("Login/token do Produttivo inválido ou expirado.")
        if not r.ok:
            raise ProdutivoError(f"Produttivo respondeu {r.status_code}: {r.text[:300]}")
        corpo = r.json()
        resultados.extend(corpo.get("results", []))
        total_paginas = corpo.get("meta", {}).get("total_pages", 1)
        if pagina >= total_paginas or pagina >= max_paginas:
            break
        pagina += 1
        time.sleep(PAUSA_ENTRE_PAGINAS)
    return resultados


def listar_works(login, token, register, updated_after=None):
    """Busca todas as atividades (/works). `updated_after` (AAAA-MM-DD) filtra só
    as atualizadas desde essa data, para sincronizações incrementais."""
    params = {"updated_after": updated_after} if updated_after else {}
    return _get_paginado("/works", login, token, register, params)


def listar_resource_places(login, token, register):
    """Busca todos os Clientes/Locais/Ativos (/resource_places) — usado para
    traduzir resource_place_id em nome legível."""
    return _get_paginado("/resource_places", login, token, register)
