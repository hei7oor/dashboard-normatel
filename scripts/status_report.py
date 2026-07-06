"""
Envia o status report diário de RA/SP (SAMC Petrobras) por e-mail.

Roda de forma independente do Streamlit — usado pelo GitHub Actions
(.github/workflows/status-report-diario.yml), agendado para 07:00 (Brasília).

Variáveis de ambiente necessárias:
  GMAIL_EMAIL          -> conta Gmail remetente
  GMAIL_APP_PASSWORD   -> senha de app dessa conta Gmail, para enviar o e-mail via SMTP
  GITHUB_TOKEN         -> token com permissão de escrita no repo, para gravar o
                          histórico diário de KPIs (usado no cálculo de variação)
"""
import os
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pandas as pd
import ra_sp
from email_utils import enviar_email
from github_store import gravar_linha_append, REPO_PADRAO

EMAIL_HEITOR = "heitor.fernandes@normatel.com.br"
CAMINHO_RA           = os.path.join(RAIZ, "dados", "RA.xlsx")
CAMINHO_SP           = os.path.join(RAIZ, "dados", "SP.xlsx")
CAMINHO_RESPOSTAS    = os.path.join(RAIZ, "dados", "respostas_manuais.csv")
CAMINHO_HISTORICO    = os.path.join(RAIZ, "dados", "historico_kpis.csv")
HISTORICO_COLS = ["data", "total_sp", "sem_resposta", "aguardando", "respondida", "atrasada", "pct_respondido"]


def calcular_variacao(geral_hoje):
    if not os.path.exists(CAMINHO_HISTORICO):
        return None
    hist = pd.read_csv(CAMINHO_HISTORICO, dtype=str)
    if hist.empty:
        return None
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    hist = hist[hist["data"] != hoje_str]
    if hist.empty:
        return None
    ontem = hist.iloc[-1]
    data_ant = pd.to_datetime(ontem["data"]).strftime("%d/%m/%Y")
    return {
        "sem_resposta": geral_hoje["sem_resposta"] - int(ontem["sem_resposta"]),
        "atrasada": geral_hoje["atrasada"] - int(ontem["atrasada"]),
        "data_anterior": data_ant,
    }


def gravar_historico_hoje(geral_hoje, token):
    if not token:
        return
    linha = {"data": datetime.now().strftime("%Y-%m-%d"), **{k: geral_hoje.get(k, 0) for k in HISTORICO_COLS if k != "data"}}
    gravar_linha_append("dados/historico_kpis.csv", HISTORICO_COLS, linha,
                         "Histórico diário de KPIs RA/SP", token, repo=REPO_PADRAO)


def main():
    gmail_email = os.environ.get("GMAIL_EMAIL")
    gmail_senha = os.environ.get("GMAIL_APP_PASSWORD")
    token_gh = os.environ.get("GITHUB_TOKEN")

    if not os.path.exists(CAMINHO_SP):
        print("dados/SP.xlsx não encontrado — nada a reportar.")
        return

    sp = ra_sp.ler_sp(CAMINHO_SP)
    ra = ra_sp.ler_ra(CAMINHO_RA) if os.path.exists(CAMINHO_RA) else pd.DataFrame()
    respostas = ra_sp.ler_respostas_manuais(CAMINHO_RESPOSTAS)

    status_df = ra_sp.combinar_status(sp, respostas)
    geral, por_base = ra_sp.kpis_ra_sp(ra, status_df)
    variacao = calcular_variacao(geral)

    corpo = ra_sp.montar_corpo_status_diario(geral, por_base, variacao, data_hoje=datetime.now())
    ok, erro = enviar_email(EMAIL_HEITOR, "Status diário RA/SP — SAMC Petrobras", corpo, gmail_email, gmail_senha)
    if ok:
        print("E-mail de status diário enviado com sucesso.")
    else:
        print(f"Falha ao enviar e-mail: {erro}")

    gravar_historico_hoje(geral, token_gh)


if __name__ == "__main__":
    main()
