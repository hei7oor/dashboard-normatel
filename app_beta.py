import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, io, base64, os, re, time
from datetime import datetime, date

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Normatel — Dashboard de Planejamento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

HOJE = pd.Timestamp(datetime.today().date())

# ── Paleta Normatel ──────────────────────────────────────────────────────────
G1  = "#1B5E20"   # verde muito escuro
G2  = "#2E7D32"   # verde escuro
G3  = "#388E3C"   # verde médio
G4  = "#4CAF50"   # verde principal
G5  = "#81C784"   # verde claro
G6  = "#C8E6C9"   # verde pálido
WH  = "#FFFFFF"
BG  = "#F4F6F4"   # fundo levemente esverdeado
DR  = "#E53935"   # vermelho alerta
AM  = "#FFA000"   # âmbar atenção
AZ1 = "#1565C0"   # azul UTGSUL
AZ2 = "#E65100"   # laranja TIMS
AZ3 = "#2E7D32"   # verde UTGC
ROXO= "#6A1B9A"   # roxo Produtivo

COR_BASE = {"UTGSUL": AZ1, "TIMS": AZ2, "UTGC": AZ3}

# ── Formato brasileiro de números (milhar com ponto, sem vírgula) ─────────────
def fmt_br(x):
    try:
        return format(int(round(float(x))), ",d").replace(",", ".")
    except Exception:
        return str(x)

# ── Logo ─────────────────────────────────────────────────────────────────────
def logo_b64(path):
    if os.path.exists(path):
        with open(path,"rb") as f: return base64.b64encode(f.read()).decode()
    return None

# Tenta carregar logos disponíveis (prioridade: logo enviado pelo usuário)
LOGO_WHITE = logo_b64("logo_white.png")    # logo branco para fundo verde
LOGO_COLOR = logo_b64("logo_normatel.png") # logo colorido (fallback)
CONTRATO   = "4600682358"

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, html, body {{ font-family:'Inter',sans-serif !important; }}
[data-testid="stAppViewContainer"] {{ background:{BG}; }}
[data-testid="stHeader"] {{ background:transparent; }}

/* ── Esconde a sidebar completamente ──────────── */
[data-testid="stSidebar"] {{ display:none !important; }}
[data-testid="stSidebarCollapseButton"] {{ display:none !important; }}
[data-testid="collapsedControl"] {{ display:none !important; }}

/* ── BARRA DE FILTROS (topo) ──────────────────── */
.filtros-wrap {{ margin-bottom: 2px; }}
.flt-lbl {{
  font-size:.66rem; font-weight:700; color:{G2};
  letter-spacing:1px; margin:0 0 3px 2px; text-transform:uppercase;
}}
/* multiselect / select / input limpos no corpo */
[data-baseweb="select"] > div {{
  border-radius:9px !important; border:1px solid #e0e6e0 !important;
  background:white !important; min-height:38px !important;
  box-shadow:0 1px 3px rgba(0,0,0,.05);
}}
[data-baseweb="tag"] {{ background:{G3} !important; border-radius:14px !important; }}
[data-baseweb="tag"] span {{ color:white !important; font-size:.72rem !important; }}
[data-testid="stDateInput"] > div {{
  border-radius:9px !important; border:1px solid #e0e6e0 !important;
  box-shadow:0 1px 3px rgba(0,0,0,.05);
}}
[data-testid="stTextInput"] > div {{
  border-radius:9px !important; border:1px solid #e0e6e0 !important;
  box-shadow:0 1px 3px rgba(0,0,0,.05);
}}

/* ── SIDEBAR — moderna, compacta, fixa ───────── */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {G1} 0%, {G2} 100%);
  box-shadow: 2px 0 18px rgba(0,0,0,.22);
  border-right: 1px solid rgba(255,255,255,.08);
}}
/* compacta o espaçamento geral interno */
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
  padding-top: 14px !important;
}}

/* Títulos de seção — minimalistas */
[data-testid="stSidebar"] h3 {{
  color: rgba(255,255,255,.6) !important;
  font-size:.68rem !important; font-weight:700 !important;
  text-transform: uppercase; letter-spacing:1.2px;
  border: none; padding: 0; margin: 6px 0 2px 2px;
}}

/* Labels dos campos */
[data-testid="stSidebar"] label {{
  color: rgba(255,255,255,.8) !important;
  font-size:.78rem !important; font-weight:500 !important;
}}

/* Divisores — bem sutis */
[data-testid="stSidebar"] hr {{
  border-color: rgba(255,255,255,.1) !important; margin: 8px 0;
}}

/* ── Inputs: fundo branco translúcido, cantos suaves ── */
[data-testid="stSidebar"] input {{
  background: white !important;
  color: {G1} !important;
  border-radius: 9px !important;
  font-size: .82rem !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background: white !important;
  border-radius: 9px !important;
  border: none !important;
  min-height: 38px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.12);
}}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {{
  color: {G1} !important;
  font-size: .8rem !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
  background: {G3} !important; border-radius:20px !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] span {{
  color: white !important; font-size:.72rem !important;
}}

/* Date input */
[data-testid="stSidebar"] [data-testid="stDateInput"] > div {{
  background: white !important; border-radius:9px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.12);
}}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
  color: {G1} !important;
}}

/* Radio (Fonte de dados) — pílulas compactas */
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{
  gap: 4px !important;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
  background: rgba(255,255,255,.08) !important;
  border: 1px solid rgba(255,255,255,.18) !important;
  border-radius: 9px !important; padding: 7px 12px !important;
  color: white !important; font-size:.78rem !important;
  margin: 0; display:flex; transition:.15s;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
  background: rgba(255,255,255,.16) !important;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
  background: white !important; color: {G2} !important;
  border-color: white !important; font-weight:700 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.15);
}}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
  color: inherit !important; font-size:.78rem !important;
}}

/* Text input busca */
[data-testid="stSidebar"] [data-testid="stTextInput"] > div {{
  background: rgba(255,255,255,.1) !important;
  border: 1px solid rgba(255,255,255,.22) !important;
  border-radius: 9px !important;
}}
[data-testid="stSidebar"] [data-testid="stTextInput"] input {{
  background: transparent !important;
  color: white !important;
}}
[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {{
  color: rgba(255,255,255,.45) !important;
}}

/* Botão recarregar */
[data-testid="stSidebar"] .stButton>button {{
  background: rgba(255,255,255,.12) !important;
  color: white !important;
  border: 1px solid rgba(255,255,255,.28) !important;
  border-radius: 9px !important;
  font-weight:600 !important; font-size:.78rem !important;
  width:100%; transition:.2s;
}}
[data-testid="stSidebar"] .stButton>button:hover {{
  background: white !important; color: {G2} !important;
}}

/* Expanders IA na sidebar — compactos */
[data-testid="stSidebar"] [data-testid="stExpander"] {{
  border: none !important; background: rgba(255,255,255,.06) !important;
  border-radius: 8px !important; margin-bottom: 3px;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
  font-size:.76rem !important; color: white !important; padding: 6px 10px !important;
}}

/* Caption / small text na sidebar */
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
  color: rgba(255,255,255,.6) !important; font-size:.73rem !important;
}}

/* ── HEADER FIXO NO TOPO ────────────────────────── */
.norm-header {{
  background: linear-gradient(120deg, {G1} 0%, {G2} 55%, {G3} 100%);
  padding: 14px 24px; border-radius: 0 0 14px 14px;
  box-shadow: 0 4px 20px rgba(27,94,32,.45);
  display: flex; align-items: center; gap: 20px;
  position: sticky; top: 0; z-index: 999;
  margin-bottom: 16px;
}}
/* empurra o conteúdo do Streamlit para baixo para não ficar atrás da barra nativa */
[data-testid="stAppViewContainer"] > section > div:first-child {{
  padding-top: 0 !important;
}}
.norm-header-logo img {{
  max-height: 48px; max-width: 200px;
  display: block;
}}
.norm-header-text {{ flex:1; padding-left: 4px; }}
.norm-header-text h1 {{
  margin:0; color:white; font-size:1.4rem; font-weight:800; letter-spacing:-.3px;
}}
.norm-header-text p {{
  margin:4px 0 0; color:rgba(255,255,255,.72); font-size:.82rem;
}}
.norm-header-info {{
  text-align:right; white-space:nowrap;
}}
.norm-header-info .label {{
  color:rgba(255,255,255,.55); font-size:.68rem;
  text-transform:uppercase; letter-spacing:.7px; display:block;
}}
.norm-header-info .value {{
  color:white; font-size:.88rem; font-weight:700; display:block;
}}

/* ── KPI CARDS ──────────────────────────────────── */
div[data-testid="metric-container"] {{
  background: white; border-radius:12px; padding:16px 18px;
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
  border-top: 4px solid {G4};
  transition: transform .15s, box-shadow .15s;
}}
div[data-testid="metric-container"]:hover {{
  transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.12);
}}
div[data-testid="metric-container"] label {{
  color:{G2}!important; font-size:.72rem!important; font-weight:700!important;
  text-transform:uppercase; letter-spacing:.6px;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  color:{G1}!important; font-size:1.75rem!important; font-weight:800!important;
}}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {{font-size:.78rem!important;}}

/* ── SEÇÃO TÍTULO ────────────────────────────────── */
.sec-title {{
  font-size:.82rem; font-weight:700; color:{G2};
  text-transform:uppercase; letter-spacing:.8px;
  border-left: 3px solid {G4}; padding-left:10px;
  margin: 24px 0 12px;
}}

/* ── TABS ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: white; border-radius:10px; padding:4px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  gap: 4px;
}}
.stTabs [data-baseweb="tab"] {{
  border-radius:8px; font-weight:600; font-size:.82rem;
  color:{G2} !important; padding:8px 20px; border:none;
}}
.stTabs [aria-selected="true"] {{
  background: {G4} !important; color:white !important;
  box-shadow: 0 2px 8px rgba(76,175,80,.4);
}}

/* ── RADIO SELETOR ──────────────────────────────── */
div[role="radiogroup"] {{ gap:8px; }}
div[role="radiogroup"] label {{
  border-radius:8px; border:2px solid {G6}!important;
  background:white!important; padding:7px 16px!important;
  font-weight:600!important; color:{G2}!important;
  font-size:.82rem!important; transition:.15s;
}}
div[role="radiogroup"] label:has(input:checked) {{
  background:{G4}!important; border-color:{G4}!important; color:white!important;
}}

/* ── EXPANDER ───────────────────────────────────── */
.streamlit-expanderHeader {{
  background:white; border-radius:10px;
  font-weight:700; color:{G2}!important; font-size:.85rem!important;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}}

/* ── IA CHAT CARD ────────────────────────────────── */
.ia-card {{
  background: linear-gradient(135deg, {G1}, {G3});
  border-radius:14px; padding:20px 24px;
  box-shadow: 0 4px 20px rgba(27,94,32,.3);
  margin-bottom: 16px;
}}
.ia-card h3 {{ color:white; margin:0 0 4px; font-size:1rem; font-weight:700; }}
.ia-card p  {{ color:rgba(255,255,255,.8); margin:0; font-size:.82rem; }}

/* ── COLUNA IA FIXA ──────────────────────────── */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {{
  position: sticky;
  top: 0.5rem;
  max-height: 96vh;
  overflow-y: auto;
  overflow-x: hidden;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"]::-webkit-scrollbar {{
  width: 4px;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {{
  background: {G5}; border-radius: 4px;
}}

/* ── ALERTA/BADGE ─────────────────────────────── */
.badge {{
  display:inline-block; padding:3px 10px; border-radius:20px;
  font-size:.72rem; font-weight:700; margin:2px;
}}
.badge-ok  {{ background:{G6}; color:{G1}; }}
.badge-att {{ background:#FFF8E1; color:#E65100; }}
.badge-err {{ background:#FFEBEE; color:#C62828; }}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# CONSTANTES / COLUNAS
# ════════════════════════════════════════════════════════════════════════════
BASES_SAP = ["UTGSUL","TIMS","UTGC"]
PASTA     = "dados"

# Nomes canônicos internos das colunas SAP (mapeados do Excel real)
S_ORDEM = "Ordem";  S_STATUS = "Status sistema"; S_TEXTO = "Texto breve"
S_ENT   = "Data de entrada"; S_BASE = "Data-base fim"; S_REAL = "Dt.real fim"
S_ABC   = "Criticidade"; S_GPM = "Disciplina"; S_CENTRO = "Centro de Trabalho"
S_LOCAL = "Local de instalação"; S_PLANO = "Plano manut."; S_STATUSUSR = "Status usuário"

P_TITULO = "Título"; P_STATUS = "Status"; P_LOCAL = "Cliente ou Local"
P_CRIADA = "Quando foi criada"; P_INIC = "Quando foi iniciada"
P_FIN    = "Quando foi finalizada"; P_DT_FIM = "Data e hora final"
P_DT_INI = "Data e hora inicial"; P_FORM = "Formulário"

MAPA = {
    "sap": ["SAP"],   # arquivo único com 1 aba por base
    "prod": {
        "realizar":    ["REALIZAR","A REALIZAR"],
        "andamento":   ["ANDAMENTO","EM ANDAMENTO"],
        "finalizadas": ["FINALIZADAS","FINALIZADA"],
    }
}

# nomes ABC e disciplinas amigáveis
DISCIPLINA_NOME = {
    "REF":"Refrigeração","CIV":"Civil","ELE":"Elétrica","MEC":"Mecânica",
    "SOP":"Sopro/Utilidades","COM":"Comunicação","CAL":"Caldeiraria",
    "AUT":"Automação","INS":"Instrumentação","INST":"Instrumentação",
}

# ════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE LEITURA
# ════════════════════════════════════════════════════════════════════════════
def encontrar_arquivo(pasta, padroes):
    if not os.path.isdir(pasta): return None
    for arq in os.listdir(pasta):
        nome = arq.upper()
        if any(p.upper() in nome for p in padroes) and arq.lower().endswith((".xlsx",".xls",".csv")):
            return os.path.join(pasta, arq)
    return None

def _achar_col(cols, *chaves):
    """Encontra a coluna cujo nome (minúsculo) contém todas as chaves."""
    for c in cols:
        cl = str(c).lower()
        if all(k in cl for k in chaves):
            return c
    return None

@st.cache_data(show_spinner=False)
def ler_sap(caminho):
    """Lê SAP.xlsx — cada aba é uma base. Mapeia colunas e deriva tipo."""
    xl = pd.ExcelFile(caminho, engine="openpyxl")
    resultado = {}
    for aba in xl.sheet_names:
        df = xl.parse(aba)
        df.columns = [str(c).strip() for c in df.columns]
        cols = list(df.columns)
        mapa = {
            _achar_col(cols, "ordem"):        S_ORDEM,
            _achar_col(cols, "status", "sis"): S_STATUS,
            _achar_col(cols, "status", "u"):   S_STATUSUSR,
            _achar_col(cols, "texto"):         S_TEXTO,
            _achar_col(cols, "entr"):          S_ENT,
            _achar_col(cols, "base", "fim"):   S_BASE,
            _achar_col(cols, "real"):          S_REAL,
            _achar_col(cols, "abc"):           S_ABC,
            _achar_col(cols, "gpm"):           S_GPM,
            _achar_col(cols, "centrab"):       S_CENTRO,
            _achar_col(cols, "local"):         S_LOCAL,
            _achar_col(cols, "pln"):           S_PLANO,
        }
        ren = {orig: canon for orig, canon in mapa.items() if orig and orig in df.columns}
        df = df.rename(columns=ren)
        df = df.dropna(how="all")
        if S_ORDEM not in df.columns:
            continue
        # datas no formato DD.MM.AAAA
        for col in [S_ENT, S_BASE, S_REAL]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        # tipo: com plano de manutenção = PREVENTIVA, senão CORRETIVA
        if S_PLANO in df.columns:
            tem = (df[S_PLANO].notna()
                   & (df[S_PLANO].astype(str).str.strip().str.lower() != "nan")
                   & (df[S_PLANO].astype(str).str.strip() != ""))
            df["_tipo"] = tem.map({True: "PREVENTIVA", False: "CORRETIVA"})
        else:
            df["_tipo"] = "CORRETIVA"
        # criticidade limpa
        if S_ABC in df.columns:
            df[S_ABC] = df[S_ABC].astype(str).str.strip().str.upper().replace({"NAN": "Sem classif."})
        # disciplina amigável
        if S_GPM in df.columns:
            df["_disc"] = df[S_GPM].astype(str).str.strip().str.upper().map(
                lambda x: DISCIPLINA_NOME.get(x, x if x and x != "NAN" else "Outros"))
        resultado[aba.upper().strip()] = df
    return resultado

@st.cache_data(show_spinner=False)
def ler_produtivo(caminho):
    df = pd.read_excel(caminho, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    for col in [P_CRIADA, P_INIC, P_FIN, P_DT_INI, P_DT_FIM]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    df["_base"]      = df[P_TITULO].str.extract(r"(UTGSUL|TIMS|UTGC)", expand=False).fillna("OUTROS")
    df["_tipo_serv"] = df[P_TITULO].str.extract(r"^([A-Z]{2,4})\s*-", expand=False).fillna("OUTROS")
    return df

# ════════════════════════════════════════════════════════════════════════════
# AUTO-CARREGAMENTO (sem UI de upload)
# ════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def carregar_todos():
    sap  = {b: None for b in BASES_SAP}
    prod = {"realizar":None,"andamento":None,"finalizadas":None}
    log  = []
    # SAP — arquivo único com 1 aba por base
    c = encontrar_arquivo(PASTA, MAPA["sap"])
    if c:
        try:
            abas = ler_sap(c)   # {BASE: df}
            for base in BASES_SAP:
                if base in abas and not abas[base].empty:
                    sap[base] = abas[base]
                    log.append((base, len(abas[base]), "sap"))
        except Exception:
            pass
    # Produtivo
    for key, padroes in MAPA["prod"].items():
        c = encontrar_arquivo(PASTA, padroes)
        if c:
            try:
                df = ler_produtivo(c)
                prod[key] = df
                log.append((key, len(df), "prod"))
            except: pass
    return sap, prod, log

sap_data, prod_data, _log = carregar_todos()

if "chat"        not in st.session_state: st.session_state.chat = []
if "chat_aberto" not in st.session_state: st.session_state.chat_aberto = False

# ════════════════════════════════════════════════════════════════════════════
# DADOS COMBINADOS
# ════════════════════════════════════════════════════════════════════════════
def tem_sap(base):
    df = sap_data.get(base)
    return df is not None and not df.empty

def sap_base(base):
    df = sap_data.get(base)
    return df.copy() if df is not None else pd.DataFrame()

prod_all_frames = [df for df in prod_data.values() if df is not None]
PROD = pd.concat(prod_all_frames, ignore_index=True) if prod_all_frames else pd.DataFrame()

sap_ok  = [b for b in BASES_SAP if tem_sap(b)]
prod_ok = not PROD.empty

# ════════════════════════════════════════════════════════════════════════════
# RANGE DE DATAS GLOBAL (para o filtro de período)
# ════════════════════════════════════════════════════════════════════════════
all_dates = []
for b in sap_ok:
    df = sap_base(b)
    if S_BASE in df.columns: all_dates.extend(df[S_BASE].dropna().tolist())
if prod_ok and P_DT_FIM in PROD.columns:
    all_dates.extend(PROD[P_DT_FIM].dropna().tolist())

if all_dates:
    dt_min = pd.Timestamp(min(all_dates)).date()
    dt_max = pd.Timestamp(max(all_dates)).date()
else:
    dt_min = date(2025, 1, 1)
    dt_max = date.today()

# ════════════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
logo_src = LOGO_WHITE or LOGO_COLOR
logo_tag = f'<div class="norm-header-logo"><img src="data:image/png;base64,{logo_src}"></div>' if logo_src else ""

st.markdown(f"""
<div class="norm-header">
  {logo_tag}
  <div class="norm-header-text">
    <h1>Dashboard de Planejamento</h1>
    <p>Gestão Integrada de Manutenção &nbsp;·&nbsp; SAP PM + Produtivo &nbsp;·&nbsp; UTGSUL &nbsp;·&nbsp; TIMS &nbsp;·&nbsp; UTGC</p>
  </div>
  <div class="norm-header-info">
    <span class="label">Contrato</span>
    <span class="value">{CONTRATO}</span>
    <span class="label" style="margin-top:8px">Atualizado em</span>
    <span class="value">{HOJE.strftime('%d/%m/%Y')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# BARRA DE FILTROS — topo da página (sem sidebar verde)
# ════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="filtros-wrap">', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([1.4, 1.6, 1.1, 0.7])
    with f1:
        st.markdown('<div class="flt-lbl">📅 PERÍODO</div>', unsafe_allow_html=True)
        periodo = st.date_input("p", value=(dt_min, dt_max),
                                min_value=dt_min, max_value=dt_max,
                                format="DD/MM/YYYY",
                                key="periodo_global", label_visibility="collapsed")
        if len(periodo) == 2:
            p_ini, p_fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
        else:
            p_ini, p_fim = pd.Timestamp(dt_min), pd.Timestamp(dt_max)
    with f2:
        st.markdown('<div class="flt-lbl">🏭 BASES</div>', unsafe_allow_html=True)
        bases_disp = sap_ok if sap_ok else ["UTGSUL","TIMS","UTGC"]
        bases_sel  = st.multiselect("b", bases_disp, default=[],
                                    placeholder="Todas as bases",
                                    key="bases_sel", label_visibility="collapsed")
        if not bases_sel:
            bases_sel = bases_disp
    with f3:
        st.markdown('<div class="flt-lbl">📊 FONTE</div>', unsafe_allow_html=True)
        fonte = st.selectbox("f", ["SAP + Produtivo","Apenas SAP","Apenas Produtivo"],
                             key="fonte_sel", label_visibility="collapsed")
    with f4:
        st.markdown('<div class="flt-lbl">&nbsp;</div>', unsafe_allow_html=True)
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    mostrar_sap  = fonte != "Apenas Produtivo"
    mostrar_prod = fonte != "Apenas SAP"

    g1, g2, g3, g4 = st.columns([1.1, 1.3, 1.3, 1.4])
    with g1:
        st.markdown('<div class="flt-lbl">🔧 TIPO DE ORDEM</div>', unsafe_allow_html=True)
        tipos_ord = st.multiselect("t", ["PREVENTIVA","CORRETIVA"],
                                   default=[],
                                   placeholder="Todos", key="tipos_ord",
                                   label_visibility="collapsed")
        if not tipos_ord:
            tipos_ord = ["PREVENTIVA","CORRETIVA"]
    with g2:
        st.markdown('<div class="flt-lbl">⚙️ STATUS</div>', unsafe_allow_html=True)
        if prod_ok:
            status_prod = st.multiselect("s", ["A realizar","Em andamento","Finalizada"],
                                         default=[],
                                         placeholder="Todos", key="status_prod",
                                         label_visibility="collapsed")
            if not status_prod:
                status_prod = ["A realizar","Em andamento","Finalizada"]
        else:
            status_prod = ["A realizar","Em andamento","Finalizada"]
    with g3:
        st.markdown('<div class="flt-lbl">🛠️ SERVIÇO</div>', unsafe_allow_html=True)
        if prod_ok:
            tipos_serv = sorted(PROD["_tipo_serv"].unique().tolist())
            serv_sel = st.multiselect("sv", tipos_serv, default=[],
                                      placeholder="Todos", key="serv_sel",
                                      label_visibility="collapsed")
            if not serv_sel:
                serv_sel = tipos_serv
        else:
            serv_sel = []
    with g4:
        st.markdown('<div class="flt-lbl">🔍 BUSCA LIVRE</div>', unsafe_allow_html=True)
        busca = st.text_input("q", placeholder="Pesquisar serviço, local...",
                              key="busca_geral", label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

if not sap_ok and not prod_ok:
    st.error("Nenhum dado encontrado na pasta **dados/**. Adicione os arquivos Excel e clique em 🔄 Atualizar Dados.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ════════════════════════════════════════════════════════════════════════════
def filtrar_sap(df):
    d = df.copy()
    if tipos_ord and "_tipo" in d.columns:
        d = d[d["_tipo"].isin(tipos_ord)]
    if S_BASE in d.columns:
        d = d[(d[S_BASE] >= p_ini) & (d[S_BASE] <= p_fim)]
    if busca and S_TEXTO in d.columns:
        d = d[d[S_TEXTO].str.contains(busca, case=False, na=False)]
    return d

def filtrar_prod(df):
    d = df[df["_base"].isin(bases_sel)].copy() if bases_sel else df.copy()
    if status_prod and P_STATUS in d.columns:
        d = d[d[P_STATUS].isin(status_prod)]
    if serv_sel and "_tipo_serv" in d.columns:
        d = d[d["_tipo_serv"].isin(serv_sel)]
    col_dt = P_DT_FIM if P_DT_FIM in d.columns else P_FIN
    if col_dt in d.columns:
        d = d[(d[col_dt].isna()) | ((d[col_dt] >= p_ini) & (d[col_dt] <= p_fim))]
    if busca and P_TITULO in d.columns:
        d = d[d[P_TITULO].str.contains(busca, case=False, na=False)]
    return d

def kpis_sap(df):
    total = len(df)
    prev  = len(df[df["_tipo"].str.contains("PREV",na=False)]) if "_tipo" in df.columns else 0
    corr  = len(df[df["_tipo"].str.contains("CORR",na=False)]) if "_tipo" in df.columns else 0
    exec_ = int(df[S_REAL].notna().sum()) if S_REAL in df.columns else 0
    abert = total - exec_
    if S_REAL in df.columns and S_BASE in df.columns:
        d2 = df.dropna(subset=[S_REAL,S_BASE])
        atr = int(((d2[S_REAL]-d2[S_BASE]).dt.days > 0).sum())
    else: atr = 0
    pct = round((exec_-atr)/exec_*100) if exec_>0 else 0
    return dict(total=total,prev=prev,corr=corr,exec_=exec_,abert=abert,atraso=atr,pct=pct)

def kpis_prod(df):
    total = len(df)
    fin   = int((df[P_STATUS]=="Finalizada").sum()) if P_STATUS in df.columns else 0
    and_  = int((df[P_STATUS]=="Em andamento").sum()) if P_STATUS in df.columns else 0
    real  = int((df[P_STATUS]=="A realizar").sum()) if P_STATUS in df.columns else 0
    return dict(total=total, finalizadas=fin, and_=and_, real=real,
                pct=round(fin/total*100) if total>0 else 0,
                fin_perc=round(fin/total*100) if total>0 else 0,
                andamento=and_, realizar=real)

# ════════════════════════════════════════════════════════════════════════════
# FUNÇÕES IA — pré-carrega respostas dos dados (sem API)
# ════════════════════════════════════════════════════════════════════════════
def _calcular_respostas_ia():
    """Calcula todas as respostas IA uma vez e guarda em session_state."""
    r = {}
    for b in sap_ok:
        df = filtrar_sap(sap_base(b))
        if df.empty: continue
        atrasadas = 0
        if S_BASE in df.columns and S_REAL in df.columns:
            atrasadas = int(((df[S_BASE] < HOJE) & df[S_REAL].isna()).sum())
        kp = kpis_sap(df)
        r[b] = {**kp, "atrasadas": atrasadas}

    prod_r = {}
    if prod_ok:
        df_p = filtrar_prod(PROD)
        if not df_p.empty:
            prod_r = kpis_prod(df_p)

    bases = list(r.keys())
    # % de execução por base (executadas / total)
    def _execp(b):
        t = r[b].get("total", 0)
        return (r[b].get("exec_", 0) / t * 100) if t else 0

    respostas = {}

    # 0 — Resumo geral
    linhas = []
    tot_g = exec_g = abert_g = 0
    for b in bases:
        d = r[b]
        tot_g += d.get("total", 0); exec_g += d.get("exec_", 0); abert_g += d.get("abert", 0)
        linhas.append(f"**{b}** — {fmt_br(d.get('total',0))} ordens · {fmt_br(d.get('exec_',0))} executadas ({_execp(b):.0f}%) · {fmt_br(d.get('abert',0))} abertas")
    if linhas:
        ep = (exec_g/tot_g*100) if tot_g else 0
        cab = f"📊 **{fmt_br(tot_g)} ordens** no período · **{fmt_br(exec_g)} executadas ({ep:.0f}%)** · **{fmt_br(abert_g)} em aberto**"
        corpo = "\n\n".join(linhas)
        rodape = f"\n\n⚙️ **Produtivo:** {fmt_br(prod_r.get('total',0))} atividades, {fmt_br(prod_r.get('finalizadas',0))} finalizadas ({prod_r.get('fin_perc',0):.0f}%)" if prod_r else ""
        respostas[0] = f"{cab}\n\n{corpo}{rodape}"
    else:
        respostas[0] = "Sem dados SAP no período selecionado."

    # 1 — Pendências e atrasos
    linhas = []
    tot_at = 0
    for b in bases:
        at = r[b].get("atrasadas", 0); ab = r[b].get("abert", 0); tot_at += at
        alerta = "🔴" if at > 0 else "🟢"
        linhas.append(f"{alerta} **{b}** — {fmt_br(ab)} ordens em aberto, **{fmt_br(at)} já vencidas**")
    if linhas:
        respostas[1] = f"⏰ **{fmt_br(tot_at)} ordens vencidas** (prazo passou e não foram executadas):\n\n" + "\n\n".join(linhas)
    else:
        respostas[1] = "Sem dados SAP."

    # 2 — Preventivas vs Corretivas
    linhas = []
    tp = tc = 0
    for b in bases:
        prev = r[b].get("prev", 0); corr = r[b].get("corr", 0); tp += prev; tc += corr
        tot_pc = prev + corr
        perc_p = (prev/tot_pc*100) if tot_pc else 0
        linhas.append(f"**{b}** — {fmt_br(prev)} preventivas ({perc_p:.0f}%) · {fmt_br(corr)} corretivas")
    if linhas:
        tt = tp + tc
        pp = (tp/tt*100) if tt else 0
        diag = "✅ Predomínio de preventivas (manutenção planejada — ideal)." if pp >= 50 else "⚠️ Corretivas em alta — atenção ao planejamento preventivo."
        respostas[2] = f"🔧 **{fmt_br(tp)} preventivas vs {fmt_br(tc)} corretivas** ({pp:.0f}% preventivas)\n\n" + "\n\n".join(linhas) + f"\n\n{diag}"
    else:
        respostas[2] = "Sem dados SAP."

    # 3 — Ranking de desempenho
    if bases:
        rank = sorted(bases, key=_execp, reverse=True)
        linhas = []
        medalhas = ["🥇", "🥈", "🥉"]
        for i, b in enumerate(rank):
            m = medalhas[i] if i < 3 else "▪️"
            linhas.append(f"{m} **{b}** — {_execp(b):.0f}% executado · {fmt_br(r[b].get('atrasadas',0))} vencidas")
        respostas[3] = "🏆 **Ranking por % de execução:**\n\n" + "\n\n".join(linhas)
    else:
        respostas[3] = "Sem dados SAP."

    # 4 — Status Produtivo
    if prod_r:
        t = prod_r.get("total", 0)
        fin = prod_r.get("finalizadas", 0); an = prod_r.get("andamento", 0); re_ = prod_r.get("realizar", 0)
        pa = (an/t*100) if t else 0; pr_ = (re_/t*100) if t else 0
        respostas[4] = (f"⚙️ **{fmt_br(t)} atividades de campo:**\n\n"
                        f"✅ **Finalizadas:** {fmt_br(fin)} ({prod_r.get('fin_perc',0):.0f}%)\n\n"
                        f"🔄 **Em andamento:** {fmt_br(an)} ({pa:.0f}%)\n\n"
                        f"📋 **A realizar:** {fmt_br(re_)} ({pr_:.0f}%)")
    else:
        respostas[4] = "Nenhum dado do Produtivo carregado."

    return respostas

# Pré-calcula respostas uma única vez por sessão (recalcula se filtros mudaram)
_cache_key = f"{p_ini}{p_fim}{bases_sel}{tipos_ord}{status_prod}{serv_sel}{busca}{fonte}"
if st.session_state.get("_ia_cache_key") != _cache_key:
    st.session_state["_ia_respostas"] = _calcular_respostas_ia()
    st.session_state["_ia_cache_key"] = _cache_key

_IA_RESPOSTAS = st.session_state["_ia_respostas"]

_IA_PERGUNTAS = [
    ("📊", "Resumo geral"),
    ("⏰", "Pendências e atrasos"),
    ("🔧", "Preventivas vs Corretivas"),
    ("🏆", "Ranking das bases"),
    ("⚙️", "Status Produtivo"),
]

# Widget IA — injetado como HTML fixo no canto inferior direito
# Os dados já estão pré-calculados em _IA_RESPOSTAS
_ia_html_items = ""
for i, (icon, txt) in enumerate(_IA_PERGUNTAS):
    resp = _IA_RESPOSTAS.get(i, "—").replace("\n", "<br>").replace("**", "")
    _ia_html_items += (
        f'<details style="margin:4px 0;border-radius:8px;overflow:hidden">'
        f'<summary style="background:#f0f7f0;padding:7px 10px;cursor:pointer;font-size:.78rem;font-weight:600;color:{G1};list-style:none">{icon} {txt}</summary>'
        f'<div style="background:#fafafa;padding:8px 12px;font-size:.76rem;color:#333;line-height:1.5;border-top:1px solid #e8f5e9">{resp}</div>'
        f'</details>'
    )

_ia_html = (
    f'<div id="ia-fab-container">'
    f'<input type="checkbox" id="ia-toggle" style="display:none">'
    f'<label for="ia-toggle" id="ia-fab">🤖</label>'
    f'<div id="ia-panel">'
    f'<div style="background:linear-gradient(120deg,{G1},{G2});padding:10px 14px;display:flex;justify-content:space-between;align-items:center">'
    f'<span style="color:white;font-weight:700;font-size:.88rem">🤖 Assistente IA</span>'
    f'<label for="ia-toggle" style="color:rgba(255,255,255,.7);cursor:pointer;font-size:.8rem">✕ fechar</label>'
    f'</div>'
    f'<div style="padding:8px 10px;max-height:380px;overflow-y:auto">'
    f'<p style="font-size:.72rem;color:#888;margin:4px 0 8px;font-weight:600">CLIQUE PARA VER A ANÁLISE</p>'
    f'{_ia_html_items}'
    f'</div></div></div>'
    f'<style>'
    f'#ia-fab-container{{position:fixed;bottom:24px;right:24px;z-index:99999}}'
    f'#ia-fab{{width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,{G1},{G4});color:white;font-size:1.4rem;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 18px rgba(27,94,32,.5);cursor:pointer;user-select:none;position:relative;z-index:2}}'
    f'#ia-panel{{display:none;position:absolute;bottom:64px;right:0;width:300px;background:white;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.2);border:1px solid #e0e0e0;overflow:hidden}}'
    f'#ia-toggle:checked ~ #ia-panel{{display:block}}'
    f'#ia-toggle:checked ~ #ia-fab{{background:linear-gradient(135deg,#555,#777)}}'
    f'details summary::-webkit-details-marker{{display:none}}'
    f'</style>'
)
st.markdown(_ia_html, unsafe_allow_html=True)

def graf_layout(fig, h=360):
    fig.update_layout(height=h, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                      font_family="Inter", margin=dict(t=36,b=28,l=8,r=8),
                      legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig.update_xaxes(showgrid=False, linecolor="#E8E8E8")
    fig.update_yaxes(showgrid=True,  gridcolor="#F0F0F0", linecolor="#E8E8E8")
    return fig

def pizza(labels, values, colors, title, h=290):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, marker_colors=colors,
        hole=0.50, textinfo="label+percent",
        textfont=dict(size=11,family="Inter"),
        hovertemplate="%{label}: <b>%{value:,}</b> (%{percent})<extra></extra>",
    ))
    fig.update_layout(height=h, showlegend=False,
                      title=dict(text=title,font=dict(size=12,color=G2,family="Inter"),x=0.5),
                      margin=dict(t=38,b=6,l=6,r=6), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def curva_s(df_plan, col_plan, df_exec, col_exec, label_exec="Executado", h=370):
    plan = (df_plan.dropna(subset=[col_plan])
            .assign(mes=lambda x: x[col_plan].dt.to_period("M"))
            .groupby("mes").size().sort_index().cumsum().reset_index())
    plan.columns = ["mes","Planejado"]; plan["mes"] = plan["mes"].astype(str)

    exec_ = (df_exec.dropna(subset=[col_exec])
             .assign(mes=lambda x: x[col_exec].dt.to_period("M"))
             .groupby("mes").size().sort_index().cumsum().reset_index())
    exec_.columns = ["mes", label_exec]; exec_["mes"] = exec_["mes"].astype(str)

    c = pd.merge(plan, exec_, on="mes", how="outer").sort_values("mes").ffill().fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c["mes"], y=c["Planejado"],
        mode="lines+markers", name="Planejado",
        line=dict(color=AM, width=3, dash="dot"),
        marker=dict(size=5,color=AM),
        fill="tozeroy", fillcolor="rgba(255,160,0,.07)"))
    fig.add_trace(go.Scatter(x=c["mes"], y=c[label_exec],
        mode="lines+markers", name=label_exec,
        line=dict(color=G4, width=3),
        marker=dict(size=7, color=G4, line=dict(width=2,color=G2)),
        fill="tozeroy", fillcolor="rgba(76,175,80,.12)"))
    graf_layout(fig, h)
    fig.update_layout(hovermode="x unified")
    return fig

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD — TELA CHEIA
# ════════════════════════════════════════════════════════════════════════════

# Coleta os dados filtrados para a base selecionada
def get_sap_filtrado(bases=None):
    frames=[]
    for b in (bases or bases_sel or sap_ok):
        if not tem_sap(b): continue
        df = sap_base(b); df["_base"] = b
        frames.append(filtrar_sap(df))
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()

# ════════════════════════════════════════════════════════════════════════════
# NAVEGAÇÃO: BASE
# ════════════════════════════════════════════════════════════════════════════
nav_opts = ["🌐 Visão Geral", "📅 Programação"] + (bases_sel if bases_sel else sap_ok) + ["🔍 Detalhamento"]
base_nav = st.radio("", nav_opts, horizontal=True,
                    key="base_nav", label_visibility="collapsed")
st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════
# VISÃO CONSOLIDADA
# ════════════════════════════════════════════════════════════════════════════
if base_nav == "🌐 Visão Geral":

    # ── KPIs SAP ──────────────────────────────────────────────────────────────
    if mostrar_sap and sap_ok:
        df_sap_all = get_sap_filtrado()
        kp = kpis_sap(df_sap_all) if not df_sap_all.empty else {}

        st.markdown('<p class="sec-title">📋 SAP — Ordens de Manutenção</p>', unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Total Ordens",   f"{fmt_br(kp.get('total',0))}")
        c2.metric("Preventivas",    f"{fmt_br(kp.get('prev',0))}")
        c3.metric("Corretivas",     f"{fmt_br(kp.get('corr',0))}")
        c4.metric("Executadas",     f"{fmt_br(kp.get('exec_',0))}")
        c5.metric("Abertas",        f"{fmt_br(kp.get('abert',0))}")
        c6.metric("% No Prazo",     f"{kp.get('pct',0)}%")

        pg1,pg2,pg3 = st.columns(3)
        bases_v = [b for b in (bases_sel or sap_ok) if tem_sap(b)]
        with pg1:
            vals=[len(filtrar_sap(sap_base(b))) for b in bases_v]
            st.plotly_chart(pizza(bases_v,vals,[COR_BASE.get(b,G4) for b in bases_v],
                "Ordens por Base"), use_container_width=True)
        with pg2:
            st.plotly_chart(pizza(["Preventivas","Corretivas"],[kp.get("prev",0),kp.get("corr",0)],
                [G4,AZ2],"Tipo de Ordem"), use_container_width=True)
        with pg3:
            ex=kp.get("exec_",0); ab=kp.get("abert",0)
            st.plotly_chart(pizza(["Executadas","Abertas"],[ex,ab],
                [G4,G5],"Execução"), use_container_width=True)

        # Curva S consolidada SAP
        st.markdown('<p class="sec-title">Curva S — Planejado × Executado (SAP)</p>', unsafe_allow_html=True)
        if not df_sap_all.empty and S_BASE in df_sap_all and S_REAL in df_sap_all:
            st.plotly_chart(curva_s(df_sap_all,S_BASE,df_sap_all.dropna(subset=[S_REAL]),S_REAL),
                            use_container_width=True)

        # Ordens por mês e base
        if not df_sap_all.empty and S_BASE in df_sap_all.columns:
            st.markdown('<p class="sec-title">Ordens por Mês e Base</p>', unsafe_allow_html=True)
            dm = (df_sap_all.dropna(subset=[S_BASE])
                  .assign(mes=lambda x: x[S_BASE].dt.to_period("M").astype(str))
                  .groupby(["mes","_base"]).size().reset_index(name="Qtd"))
            fig_b = px.bar(dm,x="mes",y="Qtd",color="_base",barmode="stack",text_auto=True,
                           color_discrete_map=COR_BASE)
            graf_layout(fig_b,340)
            st.plotly_chart(fig_b,use_container_width=True)

        # ── Criticidade (ABC) e Disciplina ──────────────────────────────────
        if not df_sap_all.empty and (S_ABC in df_sap_all.columns or "_disc" in df_sap_all.columns):
            st.markdown('<p class="sec-title">Criticidade & Disciplina</p>', unsafe_allow_html=True)
            ca, cb = st.columns(2)
            with ca:
                if S_ABC in df_sap_all.columns:
                    cores_abc = {"A":DR,"B":AM,"C":G4,"Sem classif.":"#BDBDBD"}
                    dabc = df_sap_all[S_ABC].value_counts()
                    ordem_abc = [x for x in ["A","B","C","Sem classif."] if x in dabc.index]
                    dabc = dabc.reindex(ordem_abc)
                    figA = px.bar(x=dabc.index, y=dabc.values, color=dabc.index,
                                  color_discrete_map=cores_abc,
                                  text=[fmt_br(v) for v in dabc.values])
                    figA.update_traces(textposition="outside")
                    graf_layout(figA, 300)
                    figA.update_layout(showlegend=False,
                        title=dict(text="Ordens por Criticidade (A=crítico)",font=dict(size=12,color=G2),x=0.5))
                    figA.update_xaxes(title=""); figA.update_yaxes(title="")
                    st.plotly_chart(figA, use_container_width=True)
            with cb:
                if "_disc" in df_sap_all.columns:
                    dd = df_sap_all["_disc"].value_counts().head(8).sort_values()
                    figD = px.bar(x=dd.values, y=dd.index, orientation="h",
                                  text=[fmt_br(v) for v in dd.values],
                                  color_discrete_sequence=[G3])
                    figD.update_traces(textposition="outside")
                    graf_layout(figD, 300)
                    figD.update_layout(showlegend=False,
                        title=dict(text="Top Disciplinas",font=dict(size=12,color=G2),x=0.5))
                    figD.update_xaxes(title=""); figD.update_yaxes(title="")
                    st.plotly_chart(figD, use_container_width=True)

    # ── KPIs Produtivo ────────────────────────────────────────────────────────
    if mostrar_prod and prod_ok:
        df_p = filtrar_prod(PROD)
        kpp  = kpis_prod(df_p)

        st.markdown('<p class="sec-title">⚙️ Produtivo — Atividades de Campo</p>', unsafe_allow_html=True)
        p1,p2,p3,p4,p5 = st.columns(5)
        p1.metric("Total Atividades", f"{fmt_br(kpp['total'])}")
        p2.metric("Finalizadas",      f"{fmt_br(kpp['finalizadas'])}")
        p3.metric("Em Andamento",     f"{fmt_br(kpp['and_'])}")
        p4.metric("A Realizar",       f"{fmt_br(kpp['real'])}")
        p5.metric("% Concluído",      f"{kpp['pct']}%")

        pp1,pp2,pp3 = st.columns(3)
        bpv = [b for b in (bases_sel or BASES_SAP)]
        with pp1:
            cnt = df_p["_base"].value_counts().reindex(bpv,fill_value=0)
            st.plotly_chart(pizza(cnt.index.tolist(),cnt.values.tolist(),
                [COR_BASE.get(b,G4) for b in cnt.index],"Atividades por Base"), use_container_width=True)
        with pp2:
            st.plotly_chart(pizza(["Finalizadas","Em Andamento","A Realizar"],
                [kpp["finalizadas"],kpp["and_"],kpp["real"]],[G4,AM,"#90CAF9"],
                "Status Atividades"), use_container_width=True)
        with pp3:
            ts = df_p["_tipo_serv"].value_counts().head(5)
            st.plotly_chart(pizza(ts.index.tolist(),ts.values.tolist(),
                [G4,AM,AZ1,AZ2,ROXO],"Tipo de Serviço"), use_container_width=True)

        # Curva S Produtivo
        st.markdown('<p class="sec-title">Curva S — Planejado × Finalizado (Produtivo)</p>', unsafe_allow_html=True)
        if P_DT_FIM in df_p.columns and P_FIN in df_p.columns:
            df_fin = df_p[df_p[P_STATUS]=="Finalizada"]
            fig_cs = curva_s(df_p, P_DT_FIM, df_fin, P_FIN, "Finalizado")
            st.plotly_chart(fig_cs, use_container_width=True)

        # Atividades por mês
        if P_FIN in df_p.columns:
            st.markdown('<p class="sec-title">Atividades Finalizadas por Mês e Base</p>', unsafe_allow_html=True)
            dm2 = (df_p[df_p[P_STATUS]=="Finalizada"].dropna(subset=[P_FIN])
                   .assign(mes=lambda x: x[P_FIN].dt.to_period("M").astype(str))
                   .groupby(["mes","_base"]).size().reset_index(name="Qtd"))
            fig_b2 = px.bar(dm2,x="mes",y="Qtd",color="_base",barmode="stack",text_auto=True,
                            color_discrete_map=COR_BASE)
            graf_layout(fig_b2,320)
            st.plotly_chart(fig_b2,use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# PROGRAMAÇÃO FUTURA — atividades do dia, Gantt e carga por semana
# ════════════════════════════════════════════════════════════════════════════
elif base_nav == "📅 Programação":
    st.markdown('<p class="sec-title">📅 Programação de Atividades</p>', unsafe_allow_html=True)

    dfp = get_sap_filtrado()
    if dfp.empty or S_BASE not in dfp.columns:
        st.info("Sem ordens para programar no filtro atual.")
    else:
        pend = dfp.copy()
        if S_REAL in pend.columns:
            pend = pend[pend[S_REAL].isna()]
        pend = pend.dropna(subset=[S_BASE]).sort_values(S_BASE)

        hoje = HOJE
        d7   = hoje + pd.Timedelta(days=7)
        d30  = hoje + pd.Timedelta(days=30)

        atras_df = pend[pend[S_BASE] < hoje]
        hoje_df  = pend[pend[S_BASE].dt.normalize() == hoje]
        sem_df   = pend[(pend[S_BASE] >= hoje) & (pend[S_BASE] <= d7)]
        mes_df   = pend[(pend[S_BASE] >= hoje) & (pend[S_BASE] <= d30)]

        # críticas (A) vencidas — destaque para gestão
        crit_venc = atras_df[atras_df[S_ABC] == "A"] if S_ABC in atras_df.columns else atras_df.iloc[0:0]

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("🔴 Vencidas",          fmt_br(len(atras_df)))
        k2.metric("🅰️ Críticas vencidas", fmt_br(len(crit_venc)))
        k3.metric("📍 Para hoje",         fmt_br(len(hoje_df)))
        k4.metric("🗓️ Próximos 7 dias",   fmt_br(len(sem_df)))
        k5.metric("📦 Próximos 30 dias",  fmt_br(len(mes_df)))
        st.markdown("---")

        ABC_COR = {"A":DR,"B":AM,"C":G4}
        def _abc_tag(r):
            a = str(r.get(S_ABC, "")) if S_ABC in r else ""
            if a in ("A","B","C"):
                return f'<span style="background:{ABC_COR[a]};color:white;padding:1px 7px;border-radius:10px;font-size:.66rem;font-weight:700">{a}</span>'
            return ""

        # ── Ordens críticas vencidas (prioridade máxima) ────────────────────
        if not crit_venc.empty:
            st.markdown(f'<div style="font-weight:700;color:{DR};font-size:1rem;margin-bottom:6px">🅰️ Ordens Críticas Vencidas — prioridade ({fmt_br(len(crit_venc))})</div>', unsafe_allow_html=True)
            cards = ""
            for _, r in crit_venc.sort_values(S_BASE).head(15).iterrows():
                ordem = r.get(S_ORDEM,"—"); texto = str(r.get(S_TEXTO,""))[:55]
                bse = r.get("_base",""); cor = COR_BASE.get(bse,G4)
                prazo = r[S_BASE].strftime("%d/%m/%Y") if pd.notna(r[S_BASE]) else "—"
                dias = (HOJE - r[S_BASE]).days if pd.notna(r[S_BASE]) else 0
                cards += (
                    f'<div style="display:flex;gap:12px;align-items:center;background:#FFF5F5;'
                    f'border-left:4px solid {DR};border-radius:8px;padding:8px 14px;margin:4px 0">'
                    f'<b style="color:{G1};min-width:90px">#{ordem}</b>'
                    f'<span style="flex:1;font-size:.83rem;color:#333">{texto}</span>'
                    f'<span style="font-size:.72rem;color:{cor};font-weight:700">{bse}</span>'
                    f'<span style="font-size:.72rem;color:{DR};font-weight:700;min-width:110px;text-align:right">{fmt_br(dias)} dias atraso</span></div>'
                )
            st.markdown(cards, unsafe_allow_html=True)
            st.markdown("---")

        # ── Atividades de hoje ──────────────────────────────────────────────
        st.markdown(f'<div style="font-weight:700;color:{G1};font-size:1rem;margin-bottom:6px">📍 Atividades de Hoje ({fmt_br(len(hoje_df))})</div>', unsafe_allow_html=True)
        if hoje_df.empty:
            st.caption("Nenhuma atividade com prazo para hoje.")
        else:
            cards = ""
            for _, r in hoje_df.head(25).iterrows():
                ordem = r.get(S_ORDEM, "—"); texto = str(r.get(S_TEXTO, ""))[:55]
                bse = r.get("_base", ""); cor = COR_BASE.get(bse, G4)
                cards += (
                    f'<div style="display:flex;gap:10px;align-items:center;background:white;'
                    f'border-left:4px solid {cor};border-radius:8px;padding:8px 14px;margin:4px 0;'
                    f'box-shadow:0 1px 4px rgba(0,0,0,.06)">'
                    f'<b style="color:{G1};min-width:90px">#{ordem}</b>{_abc_tag(r)}'
                    f'<span style="flex:1;font-size:.84rem;color:#333">{texto}</span>'
                    f'<span style="font-size:.74rem;color:{cor};font-weight:700">{bse}</span></div>'
                )
            st.markdown(cards, unsafe_allow_html=True)
        st.markdown("---")

        # ── Cronograma (Gantt) — próximos 30 dias ───────────────────────────
        st.markdown(f'<div style="font-weight:700;color:{G1};font-size:1rem;margin-bottom:6px">📊 Cronograma — próximas semanas</div>', unsafe_allow_html=True)
        if mes_df.empty:
            st.caption("Nada programado para os próximos 30 dias.")
        else:
            g = mes_df.head(40).copy()
            ini = g[S_ENT].fillna(hoje) if S_ENT in g.columns else pd.Series([hoje]*len(g), index=g.index)
            ini = ini.where(ini >= hoje, hoje)
            fim = g[S_BASE]
            ini = ini.where(ini < fim, fim - pd.Timedelta(days=1))
            g["_ini"] = ini; g["_fim"] = fim
            g["_lbl"] = "#" + g[S_ORDEM].astype(str) + " · " + g[S_TEXTO].astype(str).str.slice(0, 32)
            figG = px.timeline(g, x_start="_ini", x_end="_fim", y="_lbl",
                               color="_base", color_discrete_map=COR_BASE)
            figG.update_yaxes(autorange="reversed", title="")
            figG.update_xaxes(title="")
            figG.add_vline(x=hoje, line_dash="dash", line_color=DR)
            figG.update_layout(height=max(360, len(g)*24), plot_bgcolor="white",
                               paper_bgcolor="rgba(0,0,0,0)", font_family="Inter",
                               margin=dict(t=10,b=20,l=8,r=8),
                               legend=dict(orientation="h",y=1.02,x=1,xanchor="right",title=""))
            st.plotly_chart(figG, use_container_width=True)
            st.caption("Linha tracejada vermelha = hoje. Mostrando até 40 ordens mais próximas.")
        st.markdown("---")

        # ── Carga por semana ────────────────────────────────────────────────
        st.markdown(f'<div style="font-weight:700;color:{G1};font-size:1rem;margin-bottom:6px">🗓️ Carga de Trabalho por Semana</div>', unsafe_allow_html=True)
        fut = pend[pend[S_BASE] >= hoje].copy()
        if fut.empty:
            st.caption("Sem programação futura no período filtrado.")
        else:
            fut["_sem"] = fut[S_BASE].dt.to_period("W").apply(lambda p: p.start_time)
            dsem = fut.groupby(["_sem","_base"]).size().reset_index(name="Qtd")
            dsem["Semana"] = "Sem " + dsem["_sem"].dt.strftime("%d/%m")
            dsem = dsem.sort_values("_sem")
            figS = px.bar(dsem, x="Semana", y="Qtd", color="_base",
                          barmode="stack", text_auto=True, color_discrete_map=COR_BASE)
            graf_layout(figS, 320)
            figS.update_layout(legend_title="")
            st.plotly_chart(figS, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# DETALHAMENTO POR Nº DE ORDEM
# ════════════════════════════════════════════════════════════════════════════
elif base_nav == "🔍 Detalhamento":
    st.markdown('<p class="sec-title">🔍 Detalhamento de Atividades</p>', unsafe_allow_html=True)

    df_det = get_sap_filtrado()
    cbusca, cinfo = st.columns([2, 3])
    with cbusca:
        num = st.text_input("Buscar nº da ordem", placeholder="Ex: 12345678", key="busca_ordem")
    with cinfo:
        st.markdown(f'<div style="padding-top:28px;color:#888;font-size:.82rem">{fmt_br(len(df_det))} ordens no filtro atual</div>', unsafe_allow_html=True)

    if df_det.empty:
        st.info("Nenhuma ordem disponível.")
    else:
        res = df_det.copy()
        if num.strip():
            res = res[res[S_ORDEM].astype(str).str.contains(num.strip(), na=False)]

        st.caption(f"{fmt_br(len(res))} resultado(s)")
        ABC_COR = {"A":DR,"B":AM,"C":G4}
        for _, r in res.head(40).iterrows():
            ordem  = r.get(S_ORDEM, "—")
            texto  = str(r.get(S_TEXTO, "—"))
            status = str(r.get(S_STATUS, "—"))
            bse    = r.get("_base", "—")
            tipo   = r.get("_tipo", "—")
            abc    = str(r.get(S_ABC, "—")) if S_ABC in r else "—"
            disc   = str(r.get("_disc", "—")) if "_disc" in r else "—"
            centro = str(r.get(S_CENTRO, "—")) if S_CENTRO in r else "—"
            local  = str(r.get(S_LOCAL, "—")) if S_LOCAL in r else "—"
            ent    = r[S_ENT].strftime("%d/%m/%Y")  if S_ENT in r and pd.notna(r[S_ENT])  else "—"
            plan   = r[S_BASE].strftime("%d/%m/%Y") if S_BASE in r and pd.notna(r[S_BASE]) else "—"
            real   = r[S_REAL].strftime("%d/%m/%Y") if S_REAL in r and pd.notna(r[S_REAL]) else "— (em aberto)"
            concl  = pd.notna(r[S_REAL]) if S_REAL in r else False
            badge_c = G3 if concl else "#F9A825"
            badge_t = "✅ Executada" if concl else "⏳ Em aberto"
            cor_b   = COR_BASE.get(bse, G4)
            cor_abc = ABC_COR.get(abc, "#BDBDBD")
            abc_tag = (f'<span style="background:{cor_abc};color:white;padding:2px 9px;'
                       f'border-radius:20px;font-size:.7rem;font-weight:700">Criticidade {abc}</span>') if abc not in ("—","nan") else ""
            tipo_cor = G4 if "PREV" in str(tipo) else AZ2
            card = (
                f'<div style="background:white;border-radius:12px;padding:16px 18px;margin:8px 0;'
                f'box-shadow:0 2px 10px rgba(0,0,0,.08);border-top:3px solid {cor_b}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:8px">'
                f'<span style="font-size:1.1rem;font-weight:800;color:{G1}">Ordem #{ordem}</span>'
                f'<span style="display:flex;gap:6px;align-items:center">{abc_tag}'
                f'<span style="background:{badge_c};color:white;padding:3px 12px;border-radius:20px;font-size:.74rem;font-weight:600">{badge_t}</span></span>'
                f'</div>'
                f'<div style="font-size:.92rem;color:#333;margin-bottom:12px">{texto}</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:16px;font-size:.78rem">'
                f'<div><span style="color:#999">Base:</span> <b style="color:{cor_b}">{bse}</b></div>'
                f'<div><span style="color:#999">Tipo:</span> <b style="color:{tipo_cor}">{tipo}</b></div>'
                f'<div><span style="color:#999">Disciplina:</span> <b>{disc}</b></div>'
                f'<div><span style="color:#999">Centro:</span> <b>{centro}</b></div>'
                f'<div><span style="color:#999">Entrada:</span> <b>{ent}</b></div>'
                f'<div><span style="color:#999">Prazo:</span> <b>{plan}</b></div>'
                f'<div><span style="color:#999">Concluída:</span> <b>{real}</b></div>'
                f'</div>'
                f'<div style="font-size:.72rem;color:#aaa;margin-top:8px">📍 {local}</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)
        if len(res) > 40:
            st.caption(f"+ {fmt_br(len(res)-40)} ordens. Refine a busca pelo número.")

# ════════════════════════════════════════════════════════════════════════════
# VISÃO POR BASE
# ════════════════════════════════════════════════════════════════════════════
else:
    base = base_nav
    cor  = COR_BASE.get(base, G4)
    tabs_list = []
    if mostrar_sap and tem_sap(base): tabs_list.append("📋 Ordens SAP")
    if mostrar_prod and prod_ok:           tabs_list.append("⚙️ Atividades Produtivo")

    if not tabs_list:
        st.warning(f"Nenhum dado disponível para **{base}** na fonte selecionada.")
        st.stop()

    tabs = st.tabs(tabs_list)

    # ── TAB SAP ───────────────────────────────────────────────────────────────
    if "📋 Ordens SAP" in tabs_list:
        with tabs[tabs_list.index("📋 Ordens SAP")]:
            df_s = filtrar_sap(sap_base(base))
            kp   = kpis_sap(df_s) if not df_s.empty else {}

            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("Total",       f"{fmt_br(kp.get('total',0))}")
            c2.metric("Preventivas", f"{fmt_br(kp.get('prev',0))}")
            c3.metric("Corretivas",  f"{fmt_br(kp.get('corr',0))}")
            c4.metric("Executadas",  f"{fmt_br(kp.get('exec_',0))}")
            c5.metric("Abertas",     f"{fmt_br(kp.get('abert',0))}")
            c6.metric("% No Prazo",  f"{kp.get('pct',0)}%")

            st.markdown('<p class="sec-title">Distribuição</p>', unsafe_allow_html=True)
            g1,g2,g3 = st.columns(3)
            with g1: st.plotly_chart(pizza(["Preventivas","Corretivas"],
                [kp.get("prev",0),kp.get("corr",0)],[cor,AZ2],"Tipo"), use_container_width=True)
            ex=kp.get("exec_",0)
            with g2:
                if S_ABC in df_s.columns and not df_s.empty:
                    dabc = df_s[S_ABC].value_counts()
                    ordem_abc = [x for x in ["A","B","C","Sem classif."] if x in dabc.index]
                    dabc = dabc.reindex(ordem_abc)
                    cores = {"A":DR,"B":AM,"C":G4,"Sem classif.":"#BDBDBD"}
                    st.plotly_chart(pizza(list(dabc.index), list(dabc.values),
                        [cores.get(x,"#BDBDBD") for x in dabc.index], "Criticidade"), use_container_width=True)
            with g3: st.plotly_chart(pizza(["Executadas","Abertas"],[ex,kp.get("abert",0)],[cor,"#BDBDBD"],"Execução"), use_container_width=True)

            # Curva S
            st.markdown('<p class="sec-title">Curva S — Planejado × Executado (Acumulado)</p>', unsafe_allow_html=True)
            if not df_s.empty and S_BASE in df_s.columns and S_REAL in df_s.columns:
                st.plotly_chart(curva_s(df_s,S_BASE,df_s.dropna(subset=[S_REAL]),S_REAL), use_container_width=True)

            # Barras mensais
            if not df_s.empty and S_BASE in df_s.columns and "_tipo" in df_s.columns:
                st.markdown('<p class="sec-title">Ordens por Mês</p>', unsafe_allow_html=True)
                dm = (df_s.dropna(subset=[S_BASE])
                      .assign(mes=lambda x: x[S_BASE].dt.to_period("M").astype(str))
                      .groupby(["mes","_tipo"]).size().reset_index(name="Qtd"))
                fig_b = px.bar(dm,x="mes",y="Qtd",color="_tipo",barmode="stack",text_auto=True,
                               color_discrete_sequence=[cor,AZ2])
                graf_layout(fig_b,320)
                st.plotly_chart(fig_b,use_container_width=True)

            # Top serviços
            if not df_s.empty and S_TEXTO in df_s.columns:
                st.markdown('<p class="sec-title">Top 15 Tipos de Serviço</p>', unsafe_allow_html=True)
                top = df_s[S_TEXTO].value_counts().head(15).reset_index()
                top.columns=["Serviço","Qtd"]
                fig_t = px.bar(top,x="Qtd",y="Serviço",orientation="h",text_auto=True,
                               color_discrete_sequence=[cor])
                graf_layout(fig_t,460)
                fig_t.update_layout(yaxis={"categoryorder":"total ascending"})
                st.plotly_chart(fig_t,use_container_width=True)

            with st.expander(f"📋 Ver tabela completa ({fmt_br(len(df_s))} ordens)"):
                st.dataframe(df_s.drop(columns=["_tipo","_base"],errors="ignore"),
                             use_container_width=True, height=360)
                c1,c2 = st.columns(2)
                with c1: st.download_button("⬇️ CSV",   df_s.to_csv(index=False,encoding="utf-8-sig").encode(), f"SAP_{base}.csv")
                with c2:
                    buf=io.BytesIO(); df_s.to_excel(buf,index=False,engine="openpyxl")
                    st.download_button("⬇️ Excel", buf.getvalue(), f"SAP_{base}.xlsx")

    # ── TAB PRODUTIVO ─────────────────────────────────────────────────────────
    if "⚙️ Atividades Produtivo" in tabs_list:
        with tabs[tabs_list.index("⚙️ Atividades Produtivo")]:
            df_p = filtrar_prod(PROD[PROD["_base"]==base])
            kpp  = kpis_prod(df_p) if not df_p.empty else {}

            if df_p.empty:
                st.warning(f"Nenhuma atividade Produtivo para **{base}** com os filtros atuais.")
            else:
                p1,p2,p3,p4,p5 = st.columns(5)
                p1.metric("Total",       f"{fmt_br(kpp['total'])}")
                p2.metric("Finalizadas", f"{fmt_br(kpp['finalizadas'])}")
                p3.metric("Andamento",   f"{fmt_br(kpp['and_'])}")
                p4.metric("A Realizar",  f"{fmt_br(kpp['real'])}")
                p5.metric("% Concluído", f"{kpp['pct']}%")

                st.markdown('<p class="sec-title">Distribuição</p>', unsafe_allow_html=True)
                pp1,pp2,pp3 = st.columns(3)
                with pp1: st.plotly_chart(pizza(["Finalizadas","Em Andamento","A Realizar"],
                    [kpp["finalizadas"],kpp["and_"],kpp["real"]],[G4,AM,"#90CAF9"],"Status"), use_container_width=True)
                with pp2:
                    ts2 = df_p["_tipo_serv"].value_counts().head(5)
                    st.plotly_chart(pizza(ts2.index.tolist(),ts2.values.tolist(),
                        [G4,AM,AZ1,AZ2,ROXO],"Tipo de Serviço"), use_container_width=True)
                with pp3:
                    if P_LOCAL in df_p.columns:
                        loc = df_p[P_LOCAL].value_counts().head(5)
                        st.plotly_chart(pizza(loc.index.tolist(),loc.values.tolist(),
                            px.colors.qualitative.Set2[:len(loc)],"Top Locais"), use_container_width=True)

                # Curva S Produtivo
                st.markdown('<p class="sec-title">Curva S — Planejado × Finalizado (Acumulado)</p>', unsafe_allow_html=True)
                if P_DT_FIM in df_p.columns and P_FIN in df_p.columns:
                    df_fin = df_p[df_p[P_STATUS]=="Finalizada"]
                    st.plotly_chart(curva_s(df_p,P_DT_FIM,df_fin,P_FIN,"Finalizado"), use_container_width=True)

                # Barras por mês
                col_dt = P_FIN if P_FIN in df_p.columns else P_DT_FIM
                if col_dt in df_p.columns:
                    st.markdown('<p class="sec-title">Atividades por Mês</p>', unsafe_allow_html=True)
                    dm3 = (df_p.dropna(subset=[col_dt])
                           .assign(mes=lambda x: x[col_dt].dt.to_period("M").astype(str))
                           .groupby(["mes",P_STATUS]).size().reset_index(name="Qtd"))
                    fig_p = px.bar(dm3,x="mes",y="Qtd",color=P_STATUS,barmode="stack",text_auto=True,
                                   color_discrete_map={"Finalizada":G4,"Em andamento":AM,"A realizar":"#90CAF9"})
                    graf_layout(fig_p,320)
                    st.plotly_chart(fig_p,use_container_width=True)

                with st.expander(f"📋 Tabela ({fmt_br(len(df_p))} atividades)"):
                    cols_v = [c for c in [P_TITULO,P_LOCAL,P_STATUS,P_DT_INI,P_DT_FIM,P_FIN,"_tipo_serv"] if c in df_p.columns]
                    st.dataframe(df_p[cols_v], use_container_width=True, height=360)
                    c1,c2 = st.columns(2)
                    with c1: st.download_button("⬇️ CSV",   df_p.to_csv(index=False,encoding="utf-8-sig").encode(), f"Prod_{base}.csv")
                    with c2:
                        buf=io.BytesIO(); df_p.to_excel(buf,index=False,engine="openpyxl")
                        st.download_button("⬇️ Excel", buf.getvalue(), f"Prod_{base}.xlsx")

# ════════════════════════════════════════════════════════════════════════════
# WIDGET IA FLUTUANTE — canto inferior direito
# ════════════════════════════════════════════════════════════════════════════


