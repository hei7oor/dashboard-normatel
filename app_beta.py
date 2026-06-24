import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai as genai_sdk
import json, io, base64, os, re, time
from datetime import datetime, date

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Normatel — Dashboard (BETA)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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

/* ── Esconde label do botão recolher sidebar ──── */
[data-testid="stSidebarCollapseButton"] span {{ display:none; }}
[data-testid="stSidebarCollapseButton"] svg  {{ fill: white !important; }}
button[kind="headerNoPadding"] {{ background:transparent !important; border:none; }}

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

S_ORDEM = "Ordem";  S_STATUS = "Status sistema"; S_TEXTO = "Texto breve"
S_ENT   = "Data de entrada"; S_BASE = "Data-base fim"; S_REAL = "Dt.real fim"

P_TITULO = "Título"; P_STATUS = "Status"; P_LOCAL = "Cliente ou Local"
P_CRIADA = "Quando foi criada"; P_INIC = "Quando foi iniciada"
P_FIN    = "Quando foi finalizada"; P_DT_FIM = "Data e hora final"
P_DT_INI = "Data e hora inicial"; P_FORM = "Formulário"

MAPA = {
    "sap": {
        "UTGSUL": ["UTGSUL","utgsul"],
        "TIMS":   ["TIMS","tims"],
        "UTGC":   ["UTGC","utgc"],
    },
    "prod": {
        "realizar":    ["REALIZAR","A REALIZAR"],
        "andamento":   ["ANDAMENTO","EM ANDAMENTO"],
        "finalizadas": ["FINALIZADAS","FINALIZADA"],
    }
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

@st.cache_data(show_spinner=False)
def ler_sap(caminho):
    xl = pd.ExcelFile(caminho, engine="openpyxl")
    resultado = {}
    for aba in xl.sheet_names:
        df = xl.parse(aba)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")
        if df.empty or S_ORDEM not in df.columns: continue
        for col in [S_ENT, S_BASE, S_REAL]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        resultado[aba] = df
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
    sap  = {b:{} for b in BASES_SAP}
    prod = {"realizar":None,"andamento":None,"finalizadas":None}
    log  = []
    for base, padroes in MAPA["sap"].items():
        c = encontrar_arquivo(PASTA, padroes)
        if c:
            try:
                abas = ler_sap(c)
                if abas:
                    sap[base] = abas
                    tot = sum(len(d) for d in abas.values())
                    log.append((base, tot, "sap"))
            except: pass
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

# ── Gemini key ───────────────────────────────────────────────────────────────
try:    GEM_KEY = st.secrets["GEMINI_API_KEY"]
except: GEM_KEY = ""
if "chat"        not in st.session_state: st.session_state.chat = []
if "chat_aberto" not in st.session_state: st.session_state.chat_aberto = False

# ════════════════════════════════════════════════════════════════════════════
# DADOS COMBINADOS
# ════════════════════════════════════════════════════════════════════════════
def sap_base(base):
    frames = []
    for aba, df in sap_data[base].items():
        tmp = df.copy(); tmp["_tipo"] = aba.upper(); frames.append(tmp)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

prod_all_frames = [df for df in prod_data.values() if df is not None]
PROD = pd.concat(prod_all_frames, ignore_index=True) if prod_all_frames else pd.DataFrame()

sap_ok  = [b for b in BASES_SAP if sap_data[b]]
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
# SIDEBAR — FILTROS INTELIGENTES (sem upload)
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Cabeçalho compacto
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:6px 2px 12px">
      <div style="font-size:1.15rem">⚙️</div>
      <div style="font-size:.95rem;font-weight:800;color:white;letter-spacing:.5px">FILTROS</div>
    </div>""", unsafe_allow_html=True)

    # ── 1. Período ────────────────────────────────────────────────────────────
    st.markdown("### 📅 Período")
    periodo = st.date_input("", value=(dt_min, dt_max),
                            min_value=dt_min, max_value=dt_max,
                            format="DD/MM/YYYY",
                            key="periodo_global", label_visibility="collapsed")
    if len(periodo) == 2:
        p_ini, p_fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
    else:
        p_ini, p_fim = pd.Timestamp(dt_min), pd.Timestamp(dt_max)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 2. Base ───────────────────────────────────────────────────────────────
    st.markdown("### 🏭 Bases")
    bases_disp = sap_ok if sap_ok else ["UTGSUL","TIMS","UTGC"]
    bases_sel  = st.multiselect("", bases_disp, default=bases_disp,
                                placeholder="Todas as bases",
                                key="bases_sel", label_visibility="collapsed")
    if not bases_sel:
        bases_sel = bases_disp   # se vazio → mostra todas

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 3. Fonte de dados ─────────────────────────────────────────────────────
    st.markdown("### 📊 Fonte de Dados")
    fonte = st.radio("", ["SAP + Produtivo","Apenas SAP","Apenas Produtivo"],
                     key="fonte_sel", label_visibility="collapsed")
    mostrar_sap  = fonte != "Apenas Produtivo"
    mostrar_prod = fonte != "Apenas SAP"

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 4. Tipo de ordem (SAP) ────────────────────────────────────────────────
    if mostrar_sap:
        st.markdown("### 🔧 Tipo de Ordem")
        tipos_ord = st.multiselect("", ["PREVENTIVAS","CORRETIVAS"],
                                   default=["PREVENTIVAS","CORRETIVAS"],
                                   placeholder="Todos os tipos",
                                   key="tipos_ord", label_visibility="collapsed")
        if not tipos_ord:
            tipos_ord = ["PREVENTIVAS","CORRETIVAS"]

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── 5. Status Produtivo ───────────────────────────────────────────────────
    if mostrar_prod and prod_ok:
        st.markdown("### ⚙️ Status das Atividades")
        status_prod = st.multiselect("",
                                     ["A realizar","Em andamento","Finalizada"],
                                     default=["A realizar","Em andamento","Finalizada"],
                                     placeholder="Todos os status",
                                     key="status_prod", label_visibility="collapsed")
        if not status_prod:
            status_prod = ["A realizar","Em andamento","Finalizada"]

        st.markdown("### 🛠️ Tipo de Serviço")
        tipos_serv = sorted(PROD["_tipo_serv"].unique().tolist())
        serv_sel = st.multiselect("", tipos_serv, default=tipos_serv,
                                  placeholder="Todos os serviços",
                                  key="serv_sel", label_visibility="collapsed")
        if not serv_sel:
            serv_sel = tipos_serv

        st.markdown("<hr>", unsafe_allow_html=True)

    # ── 6. Busca livre ────────────────────────────────────────────────────────
    st.markdown("### 🔍 Busca Livre")
    busca = st.text_input("", placeholder="Pesquisar serviço, local...",
                          key="busca_geral", label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Botão recarregar ──────────────────────────────────────────────────────
    if st.button("🔄  Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # Status de carga
    if _log:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### ✅ Dados Carregados")
        for nome, qtd, tipo in _log:
            icone = "📋" if tipo == "sap" else "⚙️"
            st.markdown(f"<small>{icone} <b>{nome}</b>: {qtd:,} registros</small>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
logo_src = LOGO_WHITE or LOGO_COLOR
logo_tag = f'<div class="norm-header-logo"><img src="data:image/png;base64,{logo_src}"></div>' if logo_src else ""

st.markdown(f"""
<div class="norm-header">
  {logo_tag}
  <div class="norm-header-text">
    <h1>Dashboard de Planejamento <span style="background:#F9A825;color:#1B5E20;font-size:.7rem;padding:2px 10px;border-radius:12px;vertical-align:middle;font-weight:800;letter-spacing:.5px">BETA</span></h1>
    <p>Gestão Integrada de Manutenção &nbsp;·&nbsp; SAP PM + Produtivo &nbsp;·&nbsp; UTGSUL &nbsp;·&nbsp; TIMS &nbsp;·&nbsp; UTGC</p>
  </div>
  <div class="norm-header-info">
    <span class="label">Contrato</span>
    <span class="value">{CONTRATO}</span>
    <span class="label" style="margin-top:8px">Atualizado em</span>
    <span class="value">{HOJE.strftime('%d/%m/%Y')}</span>
    <span class="label" style="margin-top:4px">Período filtrado</span>
    <span class="value" style="font-size:.78rem">{p_ini.strftime('%d/%m/%y')} – {p_fim.strftime('%d/%m/%y')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

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
    pct = round((exec_-atr)/exec_*100,1) if exec_>0 else 0
    return dict(total=total,prev=prev,corr=corr,exec_=exec_,abert=abert,atraso=atr,pct=pct)

def kpis_prod(df):
    total = len(df)
    fin   = int((df[P_STATUS]=="Finalizada").sum()) if P_STATUS in df.columns else 0
    and_  = int((df[P_STATUS]=="Em andamento").sum()) if P_STATUS in df.columns else 0
    real  = int((df[P_STATUS]=="A realizar").sum()) if P_STATUS in df.columns else 0
    return dict(total=total, finalizadas=fin, and_=and_, real=real,
                pct=round(fin/total*100,1) if total>0 else 0,
                fin_perc=round(fin/total*100,1) if total>0 else 0,
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

    respostas = {}

    # 0 — Resumo geral
    linhas = []
    for b in bases:
        d = r[b]
        linhas.append(f"**{b}:** {d.get('total',0):,} ordens · {d.get('exec_perc',0):.0f}% executadas · {d.get('atrasadas',0)} atrasadas")
    if prod_r:
        linhas.append(f"**Produtivo:** {prod_r.get('total',0):,} atividades · {prod_r.get('fin_perc',0):.0f}% finalizadas")
    respostas[0] = "\n\n".join(linhas) if linhas else "Sem dados carregados."

    # 1 — Ordens atrasadas
    linhas = []
    for b in bases:
        at = r[b].get("atrasadas", 0)
        tot = max(r[b].get("total", 1), 1)
        linhas.append(f"**{b}:** {at:,} atrasadas ({at/tot*100:.1f}% do total)")
    respostas[1] = "\n\n".join(linhas) if linhas else "Sem dados SAP."

    # 2 — Preventivas vs Corretivas
    linhas = []
    for b in bases:
        prev = r[b].get("preventivas", 0); corr = r[b].get("corretivas", 0)
        linhas.append(f"**{b}:** {prev:,} preventivas · {corr:,} corretivas")
    respostas[2] = "\n\n".join(linhas) if linhas else "Sem dados SAP."

    # 3 — Melhor desempenho
    if bases:
        melhor = max(bases, key=lambda b: r[b].get("exec_perc", 0))
        pior   = min(bases, key=lambda b: r[b].get("exec_perc", 0))
        respostas[3] = (f"🥇 **{melhor}** lidera com {r[melhor].get('exec_perc',0):.0f}% de execução "
                        f"({r[melhor].get('total',0):,} ordens).\n\n"
                        f"⚠️ **{pior}** precisa de atenção: {r[pior].get('exec_perc',0):.0f}% executado "
                        f"e {r[pior].get('atrasadas',0)} atrasadas.")
    else:
        respostas[3] = "Sem dados SAP."

    # 4 — Status Produtivo
    if prod_r:
        respostas[4] = (f"**Total:** {prod_r.get('total',0):,} atividades\n\n"
                        f"✅ **Finalizadas:** {prod_r.get('finalizadas',0):,} ({prod_r.get('fin_perc',0):.0f}%)\n\n"
                        f"🔄 **Em andamento:** {prod_r.get('andamento',0):,}\n\n"
                        f"📋 **A realizar:** {prod_r.get('realizar',0):,}")
    else:
        respostas[4] = "Nenhum dado do Produtivo carregado."

    return respostas

# Pré-calcula respostas uma única vez por sessão (recalcula se filtros mudaram)
_cache_key = str(p_ini) + str(p_fim) + str(bases_sel) + str(tipos_ord)
if st.session_state.get("_ia_cache_key") != _cache_key:
    st.session_state["_ia_respostas"] = _calcular_respostas_ia()
    st.session_state["_ia_cache_key"] = _cache_key

_IA_RESPOSTAS = st.session_state["_ia_respostas"]

_IA_PERGUNTAS = [
    ("📊", "Resumo geral"),
    ("⏰", "Ordens atrasadas"),
    ("🔧", "Preventivas vs Corretivas"),
    ("🏆", "Melhor desempenho"),
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
        if not sap_data.get(b): continue
        df = sap_base(b); df["_base"] = b
        frames.append(filtrar_sap(df))
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()

# ════════════════════════════════════════════════════════════════════════════
# NAVEGAÇÃO: BASE
# ════════════════════════════════════════════════════════════════════════════
nav_opts = ["🌐 Visão Geral"] + (bases_sel if bases_sel else sap_ok) + ["🔍 Detalhamento"]
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
        c1.metric("Total Ordens",   f"{kp.get('total',0):,}")
        c2.metric("Preventivas",    f"{kp.get('prev',0):,}")
        c3.metric("Corretivas",     f"{kp.get('corr',0):,}")
        c4.metric("Executadas",     f"{kp.get('exec_',0):,}")
        c5.metric("Abertas",        f"{kp.get('abert',0):,}")
        c6.metric("% No Prazo",     f"{kp.get('pct',0)}%",
                  delta=f"-{kp.get('atraso',0)} atrasadas", delta_color="inverse")

        pg1,pg2,pg3 = st.columns(3)
        bases_v = [b for b in (bases_sel or sap_ok) if sap_data.get(b)]
        with pg1:
            vals=[len(filtrar_sap(sap_base(b))) for b in bases_v]
            st.plotly_chart(pizza(bases_v,vals,[COR_BASE.get(b,G4) for b in bases_v],
                "Ordens por Base"), use_container_width=True)
        with pg2:
            st.plotly_chart(pizza(["Preventivas","Corretivas"],[kp.get("prev",0),kp.get("corr",0)],
                [G4,AZ2],"Tipo de Ordem"), use_container_width=True)
        with pg3:
            ex=kp.get("exec_",0); atr=kp.get("atraso",0)
            st.plotly_chart(pizza(["No Prazo","Atrasadas"],[ex-atr,atr],
                [G4,DR],"Pontualidade"), use_container_width=True)

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

    # ── KPIs Produtivo ────────────────────────────────────────────────────────
    if mostrar_prod and prod_ok:
        df_p = filtrar_prod(PROD)
        kpp  = kpis_prod(df_p)

        st.markdown('<p class="sec-title">⚙️ Produtivo — Atividades de Campo</p>', unsafe_allow_html=True)
        p1,p2,p3,p4,p5 = st.columns(5)
        p1.metric("Total Atividades", f"{kpp['total']:,}")
        p2.metric("Finalizadas",      f"{kpp['finalizadas']:,}")
        p3.metric("Em Andamento",     f"{kpp['and_']:,}")
        p4.metric("A Realizar",       f"{kpp['real']:,}")
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
# DETALHAMENTO POR Nº DE ORDEM
# ════════════════════════════════════════════════════════════════════════════
elif base_nav == "🔍 Detalhamento":
    st.markdown('<p class="sec-title">🔍 Detalhamento de Atividades</p>', unsafe_allow_html=True)

    df_det = get_sap_filtrado()
    cbusca, cinfo = st.columns([2, 3])
    with cbusca:
        num = st.text_input("Buscar nº da ordem", placeholder="Ex: 12345678", key="busca_ordem")
    with cinfo:
        st.markdown(f'<div style="padding-top:28px;color:#888;font-size:.82rem">{len(df_det):,} ordens no filtro atual</div>', unsafe_allow_html=True)

    if df_det.empty:
        st.info("Nenhuma ordem disponível.")
    else:
        res = df_det.copy()
        if num.strip():
            res = res[res[S_ORDEM].astype(str).str.contains(num.strip(), na=False)]

        st.caption(f"{len(res):,} resultado(s)")
        for _, r in res.head(40).iterrows():
            ordem  = r.get(S_ORDEM, "—")
            texto  = str(r.get(S_TEXTO, "—"))
            status = str(r.get(S_STATUS, "—"))
            bse    = r.get("_base", "—")
            tipo   = r.get("_tipo", "—")
            ent    = r[S_ENT].strftime("%d/%m/%Y")  if S_ENT in r and pd.notna(r[S_ENT])  else "—"
            plan   = r[S_BASE].strftime("%d/%m/%Y") if S_BASE in r and pd.notna(r[S_BASE]) else "—"
            real   = r[S_REAL].strftime("%d/%m/%Y") if S_REAL in r and pd.notna(r[S_REAL]) else "— (em aberto)"
            concl  = pd.notna(r[S_REAL]) if S_REAL in r else False
            badge_c = G3 if concl else "#F9A825"
            badge_t = "✅ Executada" if concl else "⏳ Em aberto"
            cor_b   = COR_BASE.get(bse, G4)
            card = (
                f'<div style="background:white;border-radius:12px;padding:16px 18px;margin:8px 0;'
                f'box-shadow:0 2px 10px rgba(0,0,0,.08);border-top:3px solid {cor_b}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
                f'<span style="font-size:1.1rem;font-weight:800;color:{G1}">Ordem #{ordem}</span>'
                f'<span style="background:{badge_c};color:white;padding:3px 12px;border-radius:20px;font-size:.74rem;font-weight:600">{badge_t}</span>'
                f'</div>'
                f'<div style="font-size:.92rem;color:#333;margin-bottom:12px">{texto}</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:18px;font-size:.78rem">'
                f'<div><span style="color:#999">Base:</span> <b style="color:{cor_b}">{bse}</b></div>'
                f'<div><span style="color:#999">Tipo:</span> <b>{tipo}</b></div>'
                f'<div><span style="color:#999">Status SAP:</span> <b>{status}</b></div>'
                f'<div><span style="color:#999">Entrada:</span> <b>{ent}</b></div>'
                f'<div><span style="color:#999">Prazo:</span> <b>{plan}</b></div>'
                f'<div><span style="color:#999">Concluída:</span> <b>{real}</b></div>'
                f'</div></div>'
            )
            st.markdown(card, unsafe_allow_html=True)
        if len(res) > 40:
            st.caption(f"+ {len(res)-40} ordens. Refine a busca pelo número.")

# ════════════════════════════════════════════════════════════════════════════
# VISÃO POR BASE
# ════════════════════════════════════════════════════════════════════════════
else:
    base = base_nav
    cor  = COR_BASE.get(base, G4)
    tabs_list = []
    if mostrar_sap and sap_data.get(base): tabs_list.append("📋 Ordens SAP")
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
            c1.metric("Total",       f"{kp.get('total',0):,}")
            c2.metric("Preventivas", f"{kp.get('prev',0):,}")
            c3.metric("Corretivas",  f"{kp.get('corr',0):,}")
            c4.metric("Executadas",  f"{kp.get('exec_',0):,}")
            c5.metric("Abertas",     f"{kp.get('abert',0):,}")
            c6.metric("% No Prazo",  f"{kp.get('pct',0)}%",
                      delta=f"-{kp.get('atraso',0)} atrasadas", delta_color="inverse")

            st.markdown('<p class="sec-title">Distribuição</p>', unsafe_allow_html=True)
            g1,g2,g3 = st.columns(3)
            with g1: st.plotly_chart(pizza(["Preventivas","Corretivas"],
                [kp.get("prev",0),kp.get("corr",0)],[cor,AZ2],"Tipo"), use_container_width=True)
            ex=kp.get("exec_",0); atr=kp.get("atraso",0)
            with g2: st.plotly_chart(pizza(["No Prazo","Atrasadas"],[ex-atr,atr],[G4,DR],"Pontualidade"), use_container_width=True)
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

            with st.expander(f"📋 Ver tabela completa ({len(df_s):,} ordens)"):
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
                p1.metric("Total",       f"{kpp['total']:,}")
                p2.metric("Finalizadas", f"{kpp['finalizadas']:,}")
                p3.metric("Andamento",   f"{kpp['and_']:,}")
                p4.metric("A Realizar",  f"{kpp['real']:,}")
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

                with st.expander(f"📋 Tabela ({len(df_p):,} atividades)"):
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


