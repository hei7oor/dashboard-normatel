"""
Sincroniza as atividades de campo do Produttivo via API, substituindo o export
manual de REALIZAR.xlsx / ANDAMENTO.xlsx / FINALIZADAS.xlsx.

Roda de forma independente do Streamlit — usado pelo GitHub Actions
(.github/workflows/sync-produtivo.yml). Busca todas as atividades (/works) e os
Clientes/Locais (/resource_places) via produtivo_api, separa por status em 3
tabelas com as MESMAS colunas que o app_beta.py (ler_produtivo) já sabe ler, e
grava os 3 arquivos direto no repositório do GitHub (via github_store, API de
Contents — sem precisar de `git` instalado no runner).

Variáveis de ambiente necessárias:
  PRODUTTIVO_LOGIN     -> e-mail cadastrado como login da API no Produttivo
  PRODUTTIVO_TOKEN     -> Authentication Token (painel Produttivo > Configurações > API)
  PRODUTTIVO_REGISTER  -> Device Token (idem)
  GITHUB_TOKEN         -> token com permissão de escrita no repo (mesmo usado no
                          status report de RA/SP)

Mapeamento de status do Produttivo -> arquivo/rótulo usado pelo dashboard:
  not_started        -> REALIZAR.xlsx     ("A realizar")
  started             -> ANDAMENTO.xlsx    ("Em andamento")
  finished / reviewed -> FINALIZADAS.xlsx  ("Finalizada")
  canceled            -> ignorado (não entra em nenhum dos 3 arquivos, igual ao
                          export manual, que nunca trouxe atividades canceladas)
"""
import io
import os
import sys
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pandas as pd

from produtivo_api import listar_works, listar_resource_places, ProdutivoError
from github_store import gravar_arquivo_binario, REPO_PADRAO

DIAS_HISTORICO_PADRAO = 90  # busca só atividades atualizadas nos últimos N dias
                            # (sem isso, a 1a sincronização baixa TODO o histórico
                            # da conta, página por página — já demorou mais de 4h
                            # numa conta com muitos anos de atividades acumuladas)

STATUS_PARA_ARQUIVO = {
    "not_started": ("REALIZAR.xlsx", "A realizar"),
    "started": ("ANDAMENTO.xlsx", "Em andamento"),
    "finished": ("FINALIZADAS.xlsx", "Finalizada"),
    "reviewed": ("FINALIZADAS.xlsx", "Finalizada"),
}

COLUNAS = [
    "Título", "Status", "Cliente ou Local", "Formulário",
    "Data e hora inicial", "Data e hora final",
    "Quando foi criada", "Quando foi iniciada", "Quando foi finalizada",
    "ID da Atividade", "ID externo",
]


def _nome_local(resource_place):
    return resource_place.get("hierarchy_name") or resource_place.get("name") or ""


def _fmt_data(valor_iso):
    """Converte um timestamp ISO 8601 da API (ex: 2026-07-12T08:00:00-03:00) para
    o formato DD/MM/AAAA HH:MM:SS que ler_produtivo() já espera (app_beta.py lê essa
    coluna com pd.to_datetime(..., dayfirst=True) — se a gente gravasse o ISO cru,
    esse dayfirst=True interpreta errado datas com dia <= 12, ex: 2026-07-12 virava
    07/12 em vez de 12/07). Vazio/None vira string vazia."""
    if not valor_iso:
        return ""
    dt = pd.to_datetime(valor_iso, errors="coerce")
    if pd.isna(dt):
        return ""
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def montar_tabelas(works, resource_places):
    """Transforma a lista bruta de /works em 3 DataFrames (realizar/andamento/
    finalizadas), no mesmo formato de colunas do export manual do Produttivo."""
    nomes_local = {rp["id"]: _nome_local(rp) for rp in resource_places if "id" in rp}

    linhas = {"REALIZAR.xlsx": [], "ANDAMENTO.xlsx": [], "FINALIZADAS.xlsx": []}
    for w in works:
        destino = STATUS_PARA_ARQUIVO.get(w.get("status"))
        if destino is None:
            continue  # canceled ou status desconhecido: fora dos 3 arquivos
        arquivo, status_label = destino
        quando_finalizada = w.get("updated_status_to_finished_at") or w.get("updated_status_to_reviewed_at")
        linhas[arquivo].append({
            "Título": w.get("title") or "",
            "Status": status_label,
            "Cliente ou Local": nomes_local.get(w.get("resource_place_id"), ""),
            "Formulário": "",
            "Data e hora inicial": _fmt_data(w.get("start_time")),
            "Data e hora final": _fmt_data(w.get("end_time")),
            "Quando foi criada": _fmt_data(w.get("created_at")),
            "Quando foi iniciada": _fmt_data(w.get("updated_status_to_started_at")),
            "Quando foi finalizada": _fmt_data(quando_finalizada),
            "ID da Atividade": w.get("id") or w.get("work_number") or "",
            "ID externo": w.get("external_id") or "",
        })

    return {
        arquivo: pd.DataFrame(dados, columns=COLUNAS)
        for arquivo, dados in linhas.items()
    }


def _xlsx_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


def main():
    login = os.environ.get("PRODUTTIVO_LOGIN")
    token = os.environ.get("PRODUTTIVO_TOKEN")
    register = os.environ.get("PRODUTTIVO_REGISTER")
    token_gh = os.environ.get("GITHUB_TOKEN")

    if not token_gh:
        print("GITHUB_TOKEN não configurado — não é possível gravar os arquivos no repositório.", flush=True)
        return

    dias = int(os.environ.get("PRODUTTIVO_DIAS_HISTORICO", DIAS_HISTORICO_PADRAO))
    updated_after = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d")

    try:
        # atividades em aberto: sem limite de data (não crescem indefinidamente,
        # são só o que ainda não foi concluído)
        abertas = listar_works(login, token, register,
                                statuses=["not_started", "started"], rotulo="em aberto")
        # finalizadas: essas sim acumulam ano após ano, então limita ao período
        # recente (senão a sincronização baixa anos de histórico a cada execução)
        finalizadas = listar_works(login, token, register, updated_after=updated_after,
                                    statuses=["finished", "reviewed"], rotulo="finalizadas")
        works = abertas + finalizadas
        resource_places = listar_resource_places(login, token, register)
    except ProdutivoError as e:
        print(f"Falha ao buscar dados do Produttivo: {e}", flush=True)
        return
    print(f"{len(abertas)} em aberto + {len(finalizadas)} finalizadas (últimos {dias} dias) "
          f"+ {len(resource_places)} clientes/locais recebidos do Produttivo.", flush=True)

    tabelas = montar_tabelas(works, resource_places)
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for arquivo, df in tabelas.items():
        conteudo = _xlsx_bytes(df)
        ok, erro = gravar_arquivo_binario(
            f"dados/{arquivo}", conteudo,
            f"Sincronização automática do Produttivo ({agora}) — {len(df)} atividades",
            token_gh, repo=REPO_PADRAO,
        )
        if ok:
            print(f"{arquivo}: {len(df)} atividades gravadas.")
        else:
            print(f"{arquivo}: falha ao gravar — {erro}")


if __name__ == "__main__":
    main()
