"""
Leitura e regras de negócio dos relatórios RA (Relatório de Acompanhamento) e
SP (Solicitação de Providência) exportados do SAMC Petrobras.

Módulo sem dependência de Streamlit nem de rede — precisa rodar tanto dentro do
app (app_beta.py) quanto isolado no script do GitHub Actions (scripts/status_report.py).
"""
import os
import io
import unicodedata
import pandas as pd

BASES = ["UTGSUL", "TIMS", "UTGC"]

# ── Colunas canônicas (nomes exatamente como vêm do export do SAMC) ──────────
RA_NUMERO        = "Número"
RA_CONTRATO      = "Contrato"
RA_DT_CRIACAO    = "Data de Criação"
RA_DT_ACOMP      = "Data de Acompanhamento"
RA_LOCAL         = "Local"
RA_DESCRICAO     = "Descrição"
RA_TIPO          = "Tipo de RA"
RA_STATUS        = "Status RA"
RA_REGISTRO_SP   = "Registro SP"
RA_NUMERO_SP     = "Número SP"
RA_DESCRICAO_SP  = "Descrição SP"
RA_PRAZO         = "Prazo"
RA_DATA_ATEND_SP = "Data Atendimento SP"
RA_STATUS_SP     = "Status SP"
RA_RESPOSTA      = "Resposta"
RA_EMISSOR       = "Emissor da Resposta"
RA_DATA_RESPOSTA = "Data da Resposta"
RA_ELABORADO     = "Elaborado Por"

SP_NUMERO        = "Número da SP"
SP_STATUS        = "Status"
SP_CONTRATO      = "Contrato"
SP_LOCAL         = "Local"
SP_DESCRICAO     = "Descrição"
SP_PRAZO         = "Prazo Atendimento"
SP_DATA_ATEND    = "Data Atendimento"
SP_STATUS_ATEND  = "Status Atendimento"
SP_RESPOSTA      = "Resposta"
SP_EMISSOR       = "Emissor da Resposta"
SP_DATA_RESPOSTA = "Data da Resposta"
SP_ELABORADO     = "Elaborado Por"
SP_ATENDIDO_POR  = "Atendido Por"
SP_CONCLUIDO_POR = "Concluído Por"

# Colunas do CSV de respostas manuais (registradas pelos coordenadores/supervisores)
RESP_COLS = [
    "id_resposta", "numero_sp", "numero_ra", "base", "resposta_texto",
    "respondido_por", "data_hora_resposta", "status_manual", "email_enviado", "anexo_nome",
]

STATUS_RESPONDIDA   = "Respondida oficialmente"
STATUS_AGUARDANDO   = "Resposta registrada (aguardando SAMC)"
STATUS_SEM_RESPOSTA = "Sem nenhuma resposta"


def _norm(s):
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s


def _col(df, *candidatos):
    """Acha a coluna do df cujo nome (sem acento/maiúscula) bate com um dos candidatos."""
    alvo = {_norm(c) for c in candidatos}
    for c in df.columns:
        if _norm(c) in alvo:
            return c
    return None


def _preparar_datas(df, colunas):
    for col in colunas:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    return df


def _normalizar_base(serie):
    s = serie.astype(str).str.strip().str.upper()
    return s.where(s.isin(BASES), s)


def ler_ra(caminho):
    """Lê RA.xlsx (Relatório de Acompanhamento) e normaliza colunas/datas."""
    df = pd.read_excel(caminho, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    if RA_NUMERO not in df.columns:
        col = _col(df, RA_NUMERO)
        if col:
            df = df.rename(columns={col: RA_NUMERO})
    df = _preparar_datas(df, [RA_DT_CRIACAO, RA_DT_ACOMP, RA_REGISTRO_SP,
                               RA_PRAZO, RA_DATA_ATEND_SP, RA_DATA_RESPOSTA])
    if RA_LOCAL in df.columns:
        df[RA_LOCAL] = _normalizar_base(df[RA_LOCAL])
    return df


def ler_sp(caminho):
    """Lê SP.xlsx (Solicitação de Providência) e normaliza colunas/datas."""
    df = pd.read_excel(caminho, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    if SP_NUMERO not in df.columns:
        col = _col(df, SP_NUMERO)
        if col:
            df = df.rename(columns={col: SP_NUMERO})
    df = _preparar_datas(df, [SP_PRAZO, SP_DATA_ATEND, SP_DATA_RESPOSTA])
    if SP_LOCAL in df.columns:
        df[SP_LOCAL] = _normalizar_base(df[SP_LOCAL])
    # extrai o número da RA-mãe a partir do número da SP (ex: "RA-178/2025-SP-1" -> "RA-178/2025")
    if SP_NUMERO in df.columns:
        df["_numero_ra"] = df[SP_NUMERO].astype(str).str.extract(r"^(.*)-SP-\d+$", expand=False).fillna(df[SP_NUMERO])
    return df


def ler_respostas_manuais(caminho):
    """Lê dados/respostas_manuais.csv. Se não existir ainda, retorna DataFrame vazio com o schema certo."""
    if not caminho or not os.path.exists(caminho):
        return pd.DataFrame(columns=RESP_COLS)
    try:
        df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    except Exception:
        # linha com número de campos diferente do cabeçalho (schema mudou entre commits) —
        # não deixa a aba inteira quebrar, só ignora as linhas problemáticas.
        df = pd.read_csv(caminho, dtype=str, keep_default_na=False, engine="python", on_bad_lines="skip")
    for col in RESP_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[RESP_COLS]


def csv_para_texto(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def ultima_resposta_manual_por_sp(df_respostas):
    """Mantém só a resposta manual mais recente por número de SP (histórico completo fica no CSV)."""
    if df_respostas.empty:
        return df_respostas
    d = df_respostas.copy()
    d = d.sort_values("data_hora_resposta")
    return d.drop_duplicates("numero_sp", keep="last")


def combinar_status(df_sp, df_respostas, hoje=None):
    """
    Cruza SP com as respostas manuais registradas no app e calcula:
      _status_final: Respondida oficialmente / Resposta registrada (aguardando SAMC) / Sem nenhuma resposta
      _atrasada: prazo vencido e SAMC ainda sem resposta oficial
      _resposta_manual_texto / _resposta_manual_por / _resposta_manual_quando: última resposta manual (se houver)
    """
    if hoje is None:
        hoje = pd.Timestamp.today().normalize()
    d = df_sp.copy()
    if d.empty:
        for c in ["_status_final", "_atrasada", "_resposta_manual_texto",
                  "_resposta_manual_por", "_resposta_manual_quando"]:
            d[c] = None
        return d

    ultimas = ultima_resposta_manual_por_sp(df_respostas)
    manual_por_sp = ultimas.set_index("numero_sp") if not ultimas.empty else pd.DataFrame()

    def _tem_manual(numero_sp):
        return not manual_por_sp.empty and numero_sp in manual_por_sp.index

    resp_oficial = d[SP_RESPOSTA].astype(str).str.strip() if SP_RESPOSTA in d.columns else pd.Series("", index=d.index)
    tem_resposta_oficial = resp_oficial.notna() & (resp_oficial != "") & (resp_oficial.str.lower() != "nan")

    status_final = []
    resp_texto, resp_por, resp_quando = [], [], []
    for idx, row in d.iterrows():
        numero_sp = row.get(SP_NUMERO)
        if tem_resposta_oficial.loc[idx]:
            status_final.append(STATUS_RESPONDIDA)
        elif _tem_manual(numero_sp):
            status_final.append(STATUS_AGUARDANDO)
        else:
            status_final.append(STATUS_SEM_RESPOSTA)
        if _tem_manual(numero_sp):
            m = manual_por_sp.loc[numero_sp]
            resp_texto.append(m["resposta_texto"])
            resp_por.append(m["respondido_por"])
            resp_quando.append(m["data_hora_resposta"])
        else:
            resp_texto.append(None); resp_por.append(None); resp_quando.append(None)

    d["_status_final"] = status_final
    d["_resposta_manual_texto"] = resp_texto
    d["_resposta_manual_por"] = resp_por
    d["_resposta_manual_quando"] = resp_quando

    if SP_PRAZO in d.columns:
        prazo_vencido = d[SP_PRAZO].notna() & (d[SP_PRAZO] < hoje)
    else:
        prazo_vencido = pd.Series(False, index=d.index)
    cancelada = d[SP_STATUS].astype(str).str.strip().str.lower().eq("cancelado") if SP_STATUS in d.columns else pd.Series(False, index=d.index)
    d["_atrasada"] = prazo_vencido & (d["_status_final"] != STATUS_RESPONDIDA) & ~cancelada

    return d


def anexar_data_abertura(df_sp, df_ra):
    """
    Anexa à SP as informações que só existem na RA-mãe:
      _data_abertura: data em que a SP foi registrada (coluna `Registro SP` da RA) —
                      cai para a `Data de Criação` da RA quando não disponível.
      _descricao_ra: o texto da própria RA (`Descrição`) — "o que pede a RA", que é
                     diferente do que a SP pede (`Descrição` da própria SP).
    Usada nos filtros rápidos de período e nos cards da aba RA/SP.
    """
    d = df_sp.copy()
    if df_ra is None or df_ra.empty or RA_NUMERO_SP not in df_ra.columns:
        d["_data_abertura"] = pd.NaT
        d["_descricao_ra"] = None
        return d

    mapa_sp = (df_ra.dropna(subset=[RA_NUMERO_SP])
               .drop_duplicates(RA_NUMERO_SP, keep="last")
               .set_index(RA_NUMERO_SP))
    data_por_sp = mapa_sp[RA_REGISTRO_SP] if RA_REGISTRO_SP in mapa_sp.columns else pd.Series(dtype="datetime64[ns]")
    d["_data_abertura"] = d[SP_NUMERO].map(data_por_sp)

    mapa_ra = None
    if RA_NUMERO in df_ra.columns:
        mapa_ra = (df_ra.dropna(subset=[RA_NUMERO])
                   .drop_duplicates(RA_NUMERO, keep="last")
                   .set_index(RA_NUMERO))

    if mapa_ra is not None and RA_DT_CRIACAO in mapa_ra.columns and "_numero_ra" in d.columns:
        data_por_ra = mapa_ra[RA_DT_CRIACAO]
        faltando = d["_data_abertura"].isna()
        d.loc[faltando, "_data_abertura"] = d.loc[faltando, "_numero_ra"].map(data_por_ra)

    if mapa_ra is not None and RA_DESCRICAO in mapa_ra.columns and "_numero_ra" in d.columns:
        d["_descricao_ra"] = d["_numero_ra"].map(mapa_ra[RA_DESCRICAO])
    else:
        d["_descricao_ra"] = None
    return d


def kpis_ra_sp(df_ra, df_sp_status):
    """Totais gerais e por base, a partir do SP já combinado com combinar_status()."""
    def _bloco(df):
        total = len(df)
        cancelada = df[SP_STATUS].astype(str).str.strip().str.lower().eq("cancelado").sum() if SP_STATUS in df.columns else 0
        sem_resposta = int((df["_status_final"] == STATUS_SEM_RESPOSTA).sum()) if "_status_final" in df.columns else 0
        aguardando = int((df["_status_final"] == STATUS_AGUARDANDO).sum()) if "_status_final" in df.columns else 0
        respondida = int((df["_status_final"] == STATUS_RESPONDIDA).sum()) if "_status_final" in df.columns else 0
        atrasada = int(df["_atrasada"].sum()) if "_atrasada" in df.columns else 0
        pct = round(respondida / total * 100) if total > 0 else 0
        return dict(total_sp=total, cancelada=int(cancelada), sem_resposta=sem_resposta,
                    aguardando=aguardando, respondida=respondida, atrasada=atrasada, pct_respondido=pct)

    geral = _bloco(df_sp_status)
    por_base = {}
    if SP_LOCAL in df_sp_status.columns:
        for base in BASES:
            por_base[base] = _bloco(df_sp_status[df_sp_status[SP_LOCAL] == base])
    geral["total_ra"] = len(df_ra) if df_ra is not None else 0
    return geral, por_base


RESPONSAVEL_COLS = ["numero_sp", "frente", "responsavel"]


def carregar_responsaveis(caminho):
    """
    Lê dados/responsaveis_sp.csv — mapeamento manual (numero_sp -> frente/responsável)
    feito pelo Heitor pra distribuir as pendências entre a equipe. SPs que ainda não
    foram classificadas nesse arquivo aparecem como "(a classificar)".
    """
    if not caminho or not os.path.exists(caminho):
        return pd.DataFrame(columns=RESPONSAVEL_COLS)
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    for col in RESPONSAVEL_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[RESPONSAVEL_COLS]


def anexar_responsavel(df_sp, df_responsaveis):
    """Anexa `_frente`/`_responsavel` à SP a partir do mapeamento manual por numero_sp."""
    d = df_sp.copy()
    if df_responsaveis is None or df_responsaveis.empty:
        d["_frente"] = "(a classificar)"
        d["_responsavel"] = "(a classificar)"
        return d
    mapa = df_responsaveis.drop_duplicates("numero_sp", keep="last").set_index("numero_sp")
    d["_frente"] = d[SP_NUMERO].map(mapa["frente"]).fillna("(a classificar)")
    d["_responsavel"] = d[SP_NUMERO].map(mapa["responsavel"]).fillna("(a classificar)")
    d.loc[d["_frente"] == "", "_frente"] = "(a classificar)"
    d.loc[d["_responsavel"] == "", "_responsavel"] = "(a classificar)"
    return d


def kpis_por_responsavel(status_df):
    """
    Distribuição das pendências (SP ainda sem resposta oficial) por responsável/frente —
    mesmo formato da planilha de distribuição manual. Retorna um DataFrame com colunas
    responsavel, frente, qtde, vencidas, no_prazo, ordenado da maior pra menor pendência.
    """
    if "_responsavel" not in status_df.columns:
        return pd.DataFrame(columns=["responsavel", "frente", "qtde", "vencidas", "no_prazo"])
    pend = status_df[status_df["_status_final"] != STATUS_RESPONDIDA]
    if pend.empty:
        return pd.DataFrame(columns=["responsavel", "frente", "qtde", "vencidas", "no_prazo"])
    g = pend.groupby(["_responsavel", "_frente"], dropna=False).agg(
        qtde=("_status_final", "size"),
        vencidas=("_atrasada", "sum"),
    ).reset_index()
    g["vencidas"] = g["vencidas"].astype(int)
    g["no_prazo"] = g["qtde"] - g["vencidas"]
    g.columns = ["responsavel", "frente", "qtde", "vencidas", "no_prazo"]
    return g.sort_values("qtde", ascending=False)


def montar_corpo_email_resposta(numero_sp, numero_ra, base, descricao, resposta_texto, respondido_por):
    return f"""
    <div style="font-family:Arial,sans-serif;font-size:14px;color:#222">
      <h2 style="color:#1B5E20">Nova resposta registrada — {numero_sp}</h2>
      <p>Um coordenador/supervisor registrou uma resposta pelo Dashboard Normatel.
      Copie o texto abaixo e lance no SAMC.</p>
      <table style="border-collapse:collapse;width:100%;margin:12px 0">
        <tr><td style="padding:4px 8px;color:#666">RA</td><td style="padding:4px 8px"><b>{numero_ra}</b></td></tr>
        <tr><td style="padding:4px 8px;color:#666">SP</td><td style="padding:4px 8px"><b>{numero_sp}</b></td></tr>
        <tr><td style="padding:4px 8px;color:#666">Base</td><td style="padding:4px 8px"><b>{base}</b></td></tr>
        <tr><td style="padding:4px 8px;color:#666">Pendência</td><td style="padding:4px 8px">{descricao}</td></tr>
        <tr><td style="padding:4px 8px;color:#666">Respondido por</td><td style="padding:4px 8px">{respondido_por}</td></tr>
      </table>
      <p style="background:#F4F6F4;border-left:4px solid #2E7D32;padding:10px 14px;white-space:pre-wrap">{resposta_texto}</p>
    </div>
    """


def montar_corpo_status_diario(geral, por_base, variacao=None, data_hoje=None):
    """
    Corpo do e-mail de status diário — enxuto, só com o essencial: resumo geral,
    evolução em relação à captura anterior e a quebra por base.
    """
    data_hoje_str = data_hoje.strftime("%d/%m/%Y") if data_hoje is not None else ""

    linhas_base = ""
    for base, kp in por_base.items():
        linhas_base += (
            f'<tr><td style="padding:4px 8px"><b>{base}</b></td>'
            f'<td style="padding:4px 8px;text-align:center">{kp["total_sp"]}</td>'
            f'<td style="padding:4px 8px;text-align:center;color:#E53935"><b>{kp["sem_resposta"]}</b></td>'
            f'<td style="padding:4px 8px;text-align:center;color:#E53935"><b>{kp["atrasada"]}</b></td>'
            f'<td style="padding:4px 8px;text-align:center">{kp["pct_respondido"]}%</td></tr>'
        )

    def _seta(valor):
        if valor > 0: return f'<span style="color:#E53935">▲ +{valor}</span>'
        if valor < 0: return f'<span style="color:#2E7D32">▼ {valor}</span>'
        return '<span style="color:#888">= 0</span>'

    if variacao:
        data_ant = variacao.get("data_anterior", "posição anterior")
        variacao_html = (
            f'<div style="background:#F4F6F4;border-radius:8px;padding:10px 14px;margin:10px 0">'
            f'<b>Evolução desde {data_ant}:</b><br>'
            f'Sem resposta: {_seta(variacao.get("sem_resposta", 0))} &nbsp;&nbsp;|&nbsp;&nbsp; '
            f'Atrasadas: {_seta(variacao.get("atrasada", 0))}'
            f'</div>'
        )
    else:
        variacao_html = (
            '<p style="color:#888">Primeira captura no novo formato de acompanhamento — '
            'a partir de amanhã este e-mail já mostra a evolução dia a dia.</p>'
        )

    return f"""
    <div style="font-family:Arial,sans-serif;font-size:14px;color:#222">
      <h2 style="color:#1B5E20">Status diário RA/SP — SAMC Petrobras{' — ' + data_hoje_str if data_hoje_str else ''}</h2>
      <p>Total de SP: <b>{geral['total_sp']}</b> &nbsp;|&nbsp;
         Sem resposta: <b style="color:#E53935">{geral['sem_resposta']}</b> &nbsp;|&nbsp;
         Atrasadas: <b style="color:#E53935">{geral['atrasada']}</b> &nbsp;|&nbsp;
         % respondido: <b>{geral['pct_respondido']}%</b></p>
      {variacao_html}
      <h3 style="color:#1B5E20">Por base</h3>
      <table style="border-collapse:collapse;width:100%;margin:12px 0;border:1px solid #eee">
        <tr style="background:#F4F6F4">
          <th style="padding:4px 8px;text-align:left">Base</th>
          <th style="padding:4px 8px">Total SP</th>
          <th style="padding:4px 8px">Sem resposta</th>
          <th style="padding:4px 8px">Atrasadas</th>
          <th style="padding:4px 8px">% respondido</th>
        </tr>
        {linhas_base}
      </table>
    </div>
    """
