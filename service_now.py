"""
Leitura e regras de negócio dos chamados do ServiceNow (SN.xlsx) — solicitações de
serviços prediais/facilities (ex: CSC_GP_COMP_ADM_PREDIAL_UTGC).

Módulo sem dependência de Streamlit — só pandas puro.
"""
import io
import pandas as pd

# ── Colunas canônicas (nomes exatamente como vêm do export do ServiceNow) ────
SN_TAREFA      = "Tarefa"
SN_CATEGORIA   = "Descrição resumida"
SN_ANS         = "Definição do ANS"
SN_PRAZO       = "Hora da violação"
SN_SLA         = "Service Level"
SN_STATUS      = "Status"
SN_DESCRICAO   = "Descrição"
SN_ABERTO      = "Aberto(a)"
SN_SOLICITANTE = "Nome"
SN_LOTACAO     = "Lotação"
SN_RESPONSAVEL = "Nome.1"
SN_LOTACAO_RESP= "Lotação.1"
SN_GRUPO       = "Grupo de atribuição"
SN_FASE        = "Fase"
SN_ATIVO       = "Ativo"
SN_CRIACAO     = "Criação"
SN_PERC_DECORRIDO = "Percentual real decorrido"
SN_ENCERRADO   = "Encerrado"
SN_ENCERRADO_POR = "Nome.3"

STATUS_ABERTOS = ["Novo", "Pendente", "Trabalho em andamento"]


def ler_sn(caminho):
    """Lê SN.xlsx (export do ServiceNow) e normaliza colunas/datas."""
    df = pd.read_excel(caminho, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    for col in [SN_PRAZO, SN_ABERTO, SN_CRIACAO, SN_ENCERRADO]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if SN_CATEGORIA in df.columns:
        df[SN_CATEGORIA] = df[SN_CATEGORIA].astype(str).str.strip()
    if SN_GRUPO in df.columns:
        # ex: "CSC_GP_COMP_ADM_PREDIAL_UTGC" -> "UTGC"
        df["_base"] = df[SN_GRUPO].astype(str).str.extract(
            r"(UTGSUL|TIMS|UTGC|EDIVIT)", expand=False).fillna("OUTROS")
    else:
        df["_base"] = "OUTROS"
    return df


DIAS_CRITICO = 7  # chamados que vencem dentro desse número de dias entram como "crítico"


def calcular_prioridade(df, hoje=None, dias_critico=DIAS_CRITICO):
    """
    Calcula, para cada chamado, colunas derivadas de priorização:
      _aberto: bool (ainda não encerrado)
      _vencido: bool (prazo do ANS já passou e ainda está aberto — calculado por conta
                própria, não confia só no campo Service Level, que pode estar defasado)
      _critico: bool (ainda não vencido, mas o prazo cai dentro dos próximos `dias_critico` dias)
      _dias_atraso: dias de atraso (só para vencidos)
      _dias_restantes: dias até o prazo (só para não vencidos, ainda abertos)
      _prioridade: rank numérico (menor = mais urgente) — vencidos primeiro (mais
                   atrasado primeiro), depois críticos (prazo mais próximo primeiro),
                   depois os demais por % do ANS já decorrido
    """
    if hoje is None:
        hoje = pd.Timestamp.now()
    d = df.copy()
    d["_aberto"] = d[SN_ENCERRADO].isna() if SN_ENCERRADO in d.columns else True
    if SN_PRAZO in d.columns:
        d["_vencido"] = d["_aberto"] & d[SN_PRAZO].notna() & (d[SN_PRAZO] < hoje)
        dias = (hoje - d[SN_PRAZO]).dt.total_seconds() / 86400
        d["_dias_atraso"] = dias.where(d["_vencido"], other=pd.NA)
        d["_dias_restantes"] = (-dias).where(d["_aberto"] & ~d["_vencido"], other=pd.NA)
        d["_critico"] = d["_aberto"] & ~d["_vencido"] & d["_dias_restantes"].notna() & (d["_dias_restantes"] <= dias_critico)
    else:
        d["_vencido"] = False
        d["_critico"] = False
        d["_dias_atraso"] = pd.NA
        d["_dias_restantes"] = pd.NA

    perc = d[SN_PERC_DECORRIDO] if SN_PERC_DECORRIDO in d.columns else pd.Series(0, index=d.index)
    # rank: vencidos (0) ordenados pelo maior atraso primeiro; críticos (1) ordenados pelo
    # prazo mais próximo primeiro; demais abertos (2) por % do ANS já decorrido
    rank_vencido  = (-d["_dias_atraso"].fillna(0)).where(d["_vencido"], other=0)
    rank_critico  = d["_dias_restantes"].fillna(9999).where(d["_critico"], other=0)
    rank_aberto_ok = (-perc.fillna(0)).where(d["_aberto"] & ~d["_vencido"] & ~d["_critico"], other=0)
    grupo = pd.Series(2, index=d.index)
    grupo = grupo.where(d["_aberto"], other=3)              # encerrado = grupo 3 (por último)
    grupo = grupo.where(~(d["_aberto"] & ~d["_vencido"] & ~d["_critico"]), other=2)
    grupo = grupo.where(~d["_critico"], other=1)
    grupo = grupo.where(~d["_vencido"], other=0)
    rank_valor = rank_vencido.where(d["_vencido"], rank_critico.where(d["_critico"], rank_aberto_ok))
    d["_prioridade"] = list(zip(grupo, rank_valor))
    return d


def kpis_sn(df):
    total = len(df)
    abertos = int(df["_aberto"].sum()) if "_aberto" in df.columns else 0
    vencidos = int(df["_vencido"].sum()) if "_vencido" in df.columns else 0
    criticos = int(df["_critico"].sum()) if "_critico" in df.columns else 0
    concluidos = total - abertos
    pct_no_prazo = round((abertos - vencidos) / abertos * 100) if abertos > 0 else 0
    return dict(total=total, abertos=abertos, vencidos=vencidos, criticos=criticos,
                concluidos=concluidos, pct_no_prazo=pct_no_prazo)


COLUNAS_RESUMO = [
    SN_TAREFA, SN_CATEGORIA, "_situacao", SN_STATUS, SN_ABERTO, SN_PRAZO,
    "_dias_atraso", "_dias_restantes", SN_SOLICITANTE, SN_LOTACAO,
    SN_RESPONSAVEL, SN_DESCRICAO,
]

COLUNAS_RESUMO_NOMES = [
    "Tarefa", "Categoria", "Situação", "Status", "Aberto em", "Prazo (ANS)",
    "Dias de atraso", "Dias restantes", "Solicitante", "Lotação",
    "Responsável", "Descrição",
]


def exportar_resumo_csv(df_pendentes):
    """Gera o CSV (texto) do resumo de pendências, pronto para download."""
    d = df_pendentes.copy()
    if "_vencido" in d.columns and "_critico" in d.columns:
        d["_situacao"] = d.apply(
            lambda r: "Vencido" if r["_vencido"] else ("Crítico (≤7 dias)" if r["_critico"] else "No prazo"), axis=1)
    for c in COLUNAS_RESUMO:
        if c not in d.columns:
            d[c] = ""
    d = d[COLUNAS_RESUMO].copy()
    d.columns = COLUNAS_RESUMO_NOMES
    for col in ["Aberto em", "Prazo (ANS)"]:
        d[col] = pd.to_datetime(d[col], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    for col in ["Dias de atraso", "Dias restantes"]:
        d[col] = pd.to_numeric(d[col], errors="coerce").round(1)
    buf = io.StringIO()
    d.to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue()
