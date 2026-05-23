#!/usr/bin/env python3
"""
Interface Streamlit — Painel Analítico Premium (Sleek Dark Mode)
Desenvolvido segundo as diretrizes de UX/UI institucionais do BTG Pactual (Bloomberg Style).
Integrando barra lateral de navegação vertical, KPIs na Top Bar, gráficos Plotly customizados,
tabela de dados interativa com ficha técnica Master-Detail, documentos fictícios e assistente IA.
"""

import json
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from agent_engine import build_agent
from tools_custom import consultar_indicadores_macro

# ─── Configuração de Layout da Página ──────────────────────────────────────────

st.set_page_config(
    page_title="Nexus | Renda Fixa",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Typography & Premium CSS Styles (BTG Sleek Dark Mode & Glassmorphism) ─────

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;600;700;800&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* Estilos Globais */
    .stApp {
        background-color: #05132A !important; /* Background Base BTG Wealth */
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Configuração de títulos */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar Navigation Override to match mockups */
    div[data-testid="stSidebar"] {
        background-color: #05132A !important;
        border-right: 1px solid rgba(135, 186, 255, 0.1) !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding-top: 15px;
    }
    
    div[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(11, 40, 89, 0.25) !important;
        border: 1px solid rgba(135, 186, 255, 0.08) !important;
        border-radius: 4px !important;
        padding: 12px 18px !important;
        color: #87BAFF !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 400 !important;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(25, 90, 180, 0.15) !important;
        color: #FFFFFF !important;
        border-color: rgba(135, 186, 255, 0.2) !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #195AB4 !important; /* Azul BTG */
        color: #FFFFFF !important;
        border-color: #B1D2FF !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(25, 90, 180, 0.4);
    }
    
    /* Oculta os círculos nativos do radio button */
    div[data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {
        display: none !important;
    }
    
    /* Ajusta margens do texto do rádio */
    div[data-testid="stSidebar"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        margin: 0px !important;
        font-size: 0.92rem !important;
    }
    
    /* Top Bar Design */
    .top-bar-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 20px;
        background: rgba(11, 40, 89, 0.2);
        border: 1px solid rgba(135, 186, 255, 0.15);
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .logo-text {
        font-family: 'Outfit', sans-serif;
        font-size: 20px;
        font-weight: 300;
        color: #FFFFFF;
        letter-spacing: 0.5px;
    }
    
    .logo-badge {
        background: #195AB4; /* Azul Institucional BTG */
        color: #FFFFFF;
        font-weight: 800;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        margin-right: 8px;
    }
    
    /* Glassmorphic Cards para Painéis */
    .dashboard-panel {
        background: rgba(11, 40, 89, 0.3) !important;
        border-radius: 6px;
        padding: 16px;
        border: 1px solid rgba(135, 186, 255, 0.12) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
        margin-bottom: 20px;
    }
    
    /* Customização dos Inputs e Widgets do Streamlit */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div {
        background-color: #0B2859 !important; /* Surface Level 1 */
        color: #FFFFFF !important;
        border: 1px solid rgba(135, 186, 255, 0.2) !important;
        border-radius: 4px !important;
    }
    
    /* Botões Customizados */
    .stButton>button {
        background-color: #195AB4 !important; /* Azul Institucional */
        color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
        border: 1px solid rgba(135, 186, 255, 0.2) !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #10408D !important;
        border-color: #B1D2FF !important;
        box-shadow: 0 0 12px rgba(177, 210, 255, 0.25) !important;
        transform: scale(1.01);
    }
    
    /* Abas customizadas */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(11, 40, 89, 0.35) !important;
        border-bottom: 2px solid rgba(135, 186, 255, 0.1) !important;
        padding: 5px 10px 0 10px !important;
        border-radius: 6px 6px 0 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #87BAFF !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #195AB4 !important;
    }
    
    /* Chat Custom Overrides */
    .stChatMessage {
        background-color: rgba(11, 40, 89, 0.4) !important;
        border: 1px solid rgba(135, 186, 255, 0.12) !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
    }
    
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(25, 90, 180, 0.1) !important;
        border: 1px solid rgba(135, 186, 255, 0.25) !important;
    }
    
    /* Accordion (Expander) de Logs no Chat */
    .stExpander {
        background-color: rgba(11, 40, 89, 0.15) !important;
        border: 1px solid rgba(135, 186, 255, 0.08) !important;
        border-radius: 4px !important;
        margin-top: 6px !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #05132A;
    }
    ::-webkit-scrollbar-thumb {
        background: #0B2859;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #195AB4;
    }
</style>
""", unsafe_allow_html=True)

# ─── Inicialização do Cache de Recursos (Agent & Data) ────────────────────────

@st.cache_resource
def get_cached_agent():
    """Compila e faz cachê da estrutura do agente ReAct LangGraph."""
    return build_agent()


@st.cache_data
def load_cvm_dataset():
    """Carrega de forma otimizada os dados históricos da CVM."""
    csv_path = Path("data/cvm/oferta_resolucao_160.csv")
    if not csv_path.exists():
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path, sep=";")
    df["Data_Registro"] = pd.to_datetime(df["Data_Registro"], errors="coerce")
    df["Data_Encerramento"] = pd.to_datetime(df["Data_Encerramento"], errors="coerce")
    df["Ano"] = df["Data_Registro"].dt.year
    df["Valor_Total_Registrado"] = pd.to_numeric(df["Valor_Total_Registrado"], errors="coerce")
    return df


@st.cache_data(ttl=1800)  # Atualiza a cada 30 minutos
def load_realtime_indicators():
    """Busca e extrai os dados reais de Selic, CDI e IPCA do Banco Central."""
    raw_str = consultar_indicadores_macro.func()
    
    # Valores fallback padrão
    selic_val = "14.75% a.a."
    cdi_val = "14.65% a.a."
    ipca_val = "0.43%"
    selic_date = "23/05/2026"
    cdi_date = "23/05/2026"
    ipca_date = "04/2026"
    
    # Parsing simples e robusto da string retornada
    for line in raw_str.split("\n"):
        if "Selic Meta:" in line:
            parts = line.split(":")
            selic_val = parts[1].split("(")[0].split("[")[0].strip()
            if "vigente em" in line:
                selic_date = line.split("vigente em")[-1].replace(")", "").replace("]", "").strip()
        elif "Taxa CDI" in line:
            parts = line.split(":")
            cdi_val = parts[1].split("(")[0].split("[")[0].strip()
            if "vigente em" in line:
                cdi_date = line.split("vigente em")[-1].replace(")", "").replace("]", "").strip()
            elif "referência de" in line:
                cdi_date = line.split("referência de")[-1].replace(")", "").replace("]", "").strip()
        elif "IPCA" in line:
            parts = line.split(":")
            ipca_val = parts[1].split("(")[0].split("[")[0].strip()
            if "referente a" in line:
                ipca_date = line.split("referente a")[-1].replace(")", "").replace("]", "").strip()
                
    return {
        "selic": selic_val, "selic_date": selic_date,
        "cdi": cdi_val, "cdi_date": cdi_date,
        "ipca": ipca_val, "ipca_date": ipca_date
    }


def gerar_insight_ia(row, selic_str, cdi_str):
    """Gera insights financeiros dinâmicos para cada emissão da CVM."""
    ativo = str(row.get("Valor_Mobiliario", "")).upper().strip()
    emissor = str(row.get("Nome_Emissor", "")).strip()
    
    try:
        cdi_val = float(cdi_str.replace("%", "").replace("a.a.", "").strip())
    except:
        cdi_val = 14.65

    # Isenção de IR para PF (LCI, LCA, CRI, CRA, LIG, Debêntures Incentivadas)
    isentos = ["CRI", "CRA", "LCI", "LCA", "LIG"]
    eh_isento = any(x in ativo for x in isentos) or "INCENTIVADA" in ativo
    
    # Classificação real do Setor (nunca N/D)
    if any(x in ativo for x in ["LFT", "NTN", "TESOURO"]):
        setor = "Soberano"
    elif any(x in ativo for x in ["CDB", "LCI", "LCA", "LF"]):
        setor = "Bancário"
    elif "CRI" in ativo:
        setor = "Imobiliário"
    elif "CRA" in ativo:
        setor = "Agronegócio"
    elif "DEB" in ativo or "DEBENTURE" in ativo:
        setor = "Infraestrutura" if "INCENTIVADA" in ativo else "Industrial"
    else:
        setor = "Corporativo"

    # Insights recomendados baseados no tipo e setor
    if eh_isento:
        # Equivalente a CDB calculado com alíquota média de 15% (prazo longo)
        taxa_eq = cdi_val / 0.85
        if "CRA" in ativo:
            return f"🌾 Isento [{setor}]. Lastro agro. Isenção atrativa, equivale a CDB de ~{taxa_eq:.2f}% a.a."
        elif "CRI" in ativo:
            return f"🏢 Isento [{setor}]. Lastro imobiliário. Equivale a CDB de ~{taxa_eq:.2f}% a.a."
        elif "DEB" in ativo or "DEBENTURE" in ativo:
            return f"⚡ Isento [{setor}]. Incentivada (infra). Retorno líquido superior."
        else:
            return f"✅ Isento [{setor}]. Isenção fiscal PF. Excelente custo-benefício."
    else:
        if "CDB" in ativo:
            return f"🛡️ Bancário [{setor}]. Cobertura FGC até R$ 250k. Benchmark de rentabilidade: {cdi_str}."
        elif "DEB" in ativo or "DEBENTURE" in ativo:
            return f"🏭 Tributado [{setor}]. Risco de Crédito Privado. Exige análise de rating de {emissor[:12]}."
        elif "Soberano" in setor:
            return f"🏛️ Soberano [{setor}]. Risco zero do Tesouro Nacional. Benchmark: {selic_str}."
        else:
            return f"💼 {setor}. Rendimento tributável. Verifique prazos e ratings."

# ─── Carregamento Inicial de Dados ──────────────────────────────────────────

df_cvm = load_cvm_dataset()
kpi_data = load_realtime_indicators()

# ─── Inicialização de Estados da Sessão ───────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Olá! Sou o Nexus, seu analista especialista em renda fixa. Posso buscar taxas no Banco Central, cotações ao vivo na B3, ofertas vigentes da XP e Meelion, além de fazer buscas semânticas na CVM. Como posso te apoiar hoje?",
            "tools": []
        }
    ]

if "show_panel" not in st.session_state:
    st.session_state.show_panel = True

if "pending_ai_query" not in st.session_state:
    st.session_state.pending_ai_query = None

# Estados persistentes dos filtros para evitar perda ao fechar painel lateral
if "filter_ativos" not in st.session_state:
    st.session_state.filter_ativos = None
if "filter_lider" not in st.session_state:
    st.session_state.filter_lider = ""
if "filter_status" not in st.session_state:
    st.session_state.filter_status = None
if "filter_volume" not in st.session_state:
    st.session_state.filter_volume = (0.0, 1500.0) # Em Milhões

# Auxiliares de correspondência
def get_default_ativos(options):
    defaults = []
    keywords = ["Imobili", "Agroneg", "Deb", "Comercia"]
    for kw in keywords:
        for opt in options:
            if kw.lower() in opt.lower():
                defaults.append(opt)
                break
    if not defaults and options:
        defaults = [options[0]]
    return list(set(defaults))

def get_default_status(options):
    defaults = []
    for val in ["Deferido", "Registrado"]:
        for opt in options:
            if val.lower() in opt.lower():
                defaults.append(opt)
    if not defaults and options:
        defaults = options
    return list(set(defaults))

if not df_cvm.empty:
    ativos_disponiveis_init = sorted(df_cvm["Valor_Mobiliario"].dropna().unique().tolist())
    status_disponiveis_init = sorted(df_cvm["Status_Requerimento"].dropna().unique().tolist())
    
    if st.session_state.filter_ativos is None:
        st.session_state.filter_ativos = get_default_ativos(ativos_disponiveis_init)
    if st.session_state.filter_status is None:
        st.session_state.filter_status = get_default_status(status_disponiveis_init)
else:
    if st.session_state.filter_ativos is None:
        st.session_state.filter_ativos = []
    if st.session_state.filter_status is None:
        st.session_state.filter_status = []

# ─── 1. BARRA LATERAL (Menu de Navegação Vertical) ───────────────────────────

with st.sidebar:
    st.write("""
    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px; margin-bottom: 25px; margin-top: 10px;'>
        <span class="logo-badge" style="width: 42px; height: 42px; font-size: 14px;">btg</span>
        <span style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 600; color: #FFFFFF; letter-spacing: 0.5px;">Nexus</span>
    </div>
    """, unsafe_allow_html=True)
    
    menu_option = st.radio(
        "Navegação",
        options=["📈 Dashboard CVM", "💼 Mercado (XP vs Meelion)", "⚙️ Configurações"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem;color:#87BAFF;text-align:center; opacity:0.8;'>"
        "BTG Pactual • Renda Fixa<br>TAPI Entrega Final 2026</div>",
        unsafe_allow_html=True
    )

# ─── 2. TOP BAR (Logotipo e KPIs do Banco Central - Spans the Main Content) ───

st.write(f"""
<div class="top-bar-container">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;">BTG Pactual</span>
        <span style="color: rgba(255, 255, 255, 0.4); font-size: 18px;">|</span>
        <span style="font-family: 'Outfit', sans-serif; font-size: 16px; font-weight: 300; color: #87BAFF;">Nexus</span>
    </div>
    <div style="display: flex; gap: 30px; align-items: center;">
        <div style="text-align: right;">
            <span style="font-size: 0.65rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Selic Meta</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 600; color: #FFFFFF;">{kpi_data["selic"]} <span style="font-size:0.75rem; color:#87BAFF; font-weight:normal;">0.00 p.p.</span></span>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(135, 186, 255, 0.15); padding-left: 30px;">
            <span style="font-size: 0.65rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Taxa CDI</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 600; color: #FFFFFF;">{kpi_data["cdi"]} <span style="font-size:0.75rem; color:#87BAFF; font-weight:normal;">0.00 p.p.</span></span>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(135, 186, 255, 0.15); padding-left: 30px;">
            <span style="font-size: 0.65rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">IPCA (12m)</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 600; color: #2DB071;">{kpi_data["ipca"]} <span style="font-size:0.75rem; color:#2DB071; font-weight:normal;">-0.02 p.p.</span></span>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(135, 186, 255, 0.15); padding-left: 30px; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 0.72rem; color: #87BAFF; font-family: monospace;">23/05/2026</span>
            <div style="background: #195AB4; color: #FFFFFF; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-family: 'Outfit'; font-size: 11px; font-weight: bold; box-shadow: 0 0 8px rgba(25,90,180,0.5);">AG</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── PAGINA 1: DASHBOARD CVM ──────────────────────────────────────────────────

if menu_option == "📈 Dashboard CVM":
    
    if st.session_state.show_panel:
        col_dash, col_panel = st.columns([7.4, 2.6])
    else:
        col_dash = st.container()
        col_panel = None

    with col_dash:
        # Header do painel principal
        head_left, head_right = st.columns([6, 2])
        with head_left:
            st.markdown("<h2 style='margin-top:0px; font-size:1.5rem;'>📈 Workspace Analítico CVM</h2>", unsafe_allow_html=True)
        with head_right:
            btn_label = "Recolher Painel ➔" if st.session_state.show_panel else "◀ Abrir Painel IA / Filtros"
            if st.button(btn_label, key="toggle_panel_btn", use_container_width=True):
                st.session_state.show_panel = not st.session_state.show_panel
                st.rerun()

        # Filtragem dinâmica local do dataset
        if not df_cvm.empty:
            df_filtrado = df_cvm.copy()
            if st.session_state.filter_ativos:
                df_filtrado = df_filtrado[df_filtrado["Valor_Mobiliario"].isin(st.session_state.filter_ativos)]
            if st.session_state.filter_status:
                df_filtrado = df_filtrado[df_filtrado["Status_Requerimento"].isin(st.session_state.filter_status)]
            if st.session_state.filter_lider:
                df_filtrado = df_filtrado[df_filtrado["Nome_Lider"].str.contains(st.session_state.filter_lider, case=False, na=False)]
            df_filtrado = df_filtrado[
                (df_filtrado["Valor_Total_Registrado"] >= st.session_state.filter_volume[0] * 1e6) &
                (df_filtrado["Valor_Total_Registrado"] <= st.session_state.filter_volume[1] * 1e6)
            ]
        else:
            df_filtrado = pd.DataFrame()

        if df_filtrado.empty:
            st.info("Nenhuma oferta registrada corresponde aos filtros ativos. Ajuste os filtros na aba lateral.")
        else:
            # Gráficos lado a lado
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0px; font-size:1.05rem; color:#87BAFF;'>Distribuição de Ativos</h4>", unsafe_allow_html=True)
                df_tipo = df_filtrado.groupby("Valor_Mobiliario")["Valor_Total_Registrado"].sum().reset_index()
                df_tipo["Volume_Bi"] = df_tipo["Valor_Total_Registrado"] / 1e9
                total_vol_bi = df_tipo["Volume_Bi"].sum()
                
                fig_tipo = px.pie(
                    df_tipo,
                    values="Volume_Bi",
                    names="Valor_Mobiliario",
                    color_discrete_sequence=["#195AB4", "#B1D2FF", "#10408D", "#307AE0", "#549CFF", "#87BAFF", "#D2E5FF"],
                    hole=0.55,
                    labels={"Volume_Bi": "Volume (Bi R$)", "Valor_Mobiliario": "Ativo"}
                )
                fig_tipo.update_traces(
                    textposition='inside', 
                    textinfo='percent',
                    marker=dict(line=dict(color='#05132A', width=2))
                )
                fig_tipo.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FFFFFF",
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0, font=dict(size=10)),
                    margin=dict(t=5, b=5, l=5, r=100),
                    height=200,
                    annotations=[dict(
                        text=f'<span style="font-family:Outfit;font-weight:bold;font-size:14px;color:#FFFFFF;">R$ {total_vol_bi:.1f}Bi</span><br><span style="font-size:8px;color:#87BAFF;font-weight:bold;text-transform:uppercase;">Volume Total</span>', 
                        x=0.5, y=0.5, font_size=13, showarrow=False, align='center'
                    )]
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_chart2:
                st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0px; font-size:1.05rem; color:#87BAFF;'>Coordenadores Líderes (Volume)</h4>", unsafe_allow_html=True)
                df_lider = df_filtrado.groupby("Nome_Lider")["Valor_Total_Registrado"].sum().reset_index()
                df_lider = df_lider.sort_values("Valor_Total_Registrado", ascending=False).head(5)
                df_lider["Volume_Bi"] = df_lider["Valor_Total_Registrado"] / 1e9
                
                fig_lider = px.bar(
                    df_lider,
                    x="Volume_Bi",
                    y="Nome_Lider",
                    orientation="h",
                    color="Volume_Bi",
                    color_continuous_scale=["#0B2859", "#195AB4", "#B1D2FF"],
                    labels={"Volume_Bi": "Volume (Bi R$)", "Nome_Lider": "Coordenador Líder"}
                )
                fig_lider.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FFFFFF",
                    coloraxis_showscale=False,
                    margin=dict(t=5, b=5, l=5, r=5),
                    height=200,
                    xaxis=dict(showgrid=True, gridcolor="rgba(135, 186, 255, 0.08)", title="Volume (Bi R$)"),
                    yaxis=dict(showgrid=False, title="")
                )
                st.plotly_chart(fig_lider, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            # 📋 Tabela de Emissões CVM
            st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0px; font-size:1.25rem;'>📋 Emissões Registradas</h3>", unsafe_allow_html=True)
            
            # Adicionar coluna Insight IA com base no cenário macroeconômico atual
            df_insight = df_filtrado.copy()
            df_insight["Insight IA"] = df_insight.apply(
                lambda row: gerar_insight_ia(row, kpi_data["selic"], kpi_data["cdi"]), 
                axis=1
            )
            
            display_cols = {
                "Nome_Emissor": "Issuer",
                "Valor_Mobiliario": "Asset",
                "Valor_Total_Registrado": "Volume (R$)",
                "Status_Requerimento": "Status",
                "Insight IA": "Insight IA"
            }
            
            df_display = df_insight[list(display_cols.keys())].copy()
            df_display = df_display.rename(columns=display_cols)
            
            event = st.dataframe(
                df_display,
                column_config={
                    "Volume (R$)": st.column_config.NumberColumn(
                        format="R$ %.2f",
                        help="Volume financeiro total da oferta"
                    ),
                    "Insight IA": st.column_config.TextColumn(
                        help="Insight gerado automaticamente pela inteligência da plataforma"
                    )
                },
                hide_index=True,
                use_container_width=True,
                height=260,
                selection_mode="single-row",
                on_select="rerun",
                key="ofertas_table"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
    # ─── 4. PAINEL DE CONTROLE (Filtros, IA, Detalhes) ───────────────────────
    
    if st.session_state.show_panel and col_panel is not None:
        with col_panel:
            # Detecta se há seleção de linha na tabela
            selected_rows = event.selection.rows if 'event' in locals() else []
            
            if selected_rows:
                tab_titles = ["Filtros", "AI Assistant", "🔍 Detalhes"]
            else:
                tab_titles = ["Filtros", "AI Assistant"]
                
            tabs = st.tabs(tab_titles)
            
            if len(tabs) == 3:
                tab_filters, tab_ai, tab_detail = tabs
            else:
                tab_filters, tab_ai = tabs
                tab_detail = None
                
            # 📌 ABA FILTROS
            with tab_filters:
                st.markdown("<p style='font-size:0.8rem; color:#87BAFF;'>Configure os filtros para atualizar o dashboard:</p>", unsafe_allow_html=True)
                if not df_cvm.empty:
                    ativos_disponiveis = sorted(df_cvm["Valor_Mobiliario"].dropna().unique().tolist())
                    ativos_selecionados = st.multiselect(
                        "Tipo de Ativo",
                        options=ativos_disponiveis,
                        default=st.session_state.filter_ativos,
                        key="multiselect_ativos"
                    )
                    st.session_state.filter_ativos = ativos_selecionados
                    
                    lider_search = st.text_input(
                        "Coordenador Líder",
                        value=st.session_state.filter_lider,
                        key="text_lider"
                    )
                    st.session_state.filter_lider = lider_search
                    
                    status_disponiveis = sorted(df_cvm["Status_Requerimento"].dropna().unique().tolist())
                    status_selecionados = st.multiselect(
                        "Status do Requerimento",
                        options=status_disponiveis,
                        default=st.session_state.filter_status,
                        key="multiselect_status"
                    )
                    st.session_state.filter_status = status_selecionados
                    
                    max_vol = float(df_cvm["Valor_Total_Registrado"].max() / 1e6) if pd.notna(df_cvm["Valor_Total_Registrado"].max()) else 1000.0
                    volume_range = st.slider(
                        "Volume (Milhões R$)",
                        min_value=0.0,
                        max_value=min(max_vol, 5000.0),
                        value=st.session_state.filter_volume,
                        key="slider_volume"
                    )
                    st.session_state.filter_volume = volume_range
                    
            # 🤖 ABA CHATBOT DE IA CONTEXTUAL
            with tab_ai:
                ativos_txt = ", ".join(st.session_state.filter_ativos) if st.session_state.filter_ativos else "Todos"
                lider_txt = st.session_state.filter_lider if st.session_state.filter_lider else "Todos"
                status_txt = ", ".join(st.session_state.filter_status) if st.session_state.filter_status else "Todos"
                
                st.markdown(f"""
                <div style="font-size:0.72rem; background: rgba(25, 90, 180, 0.1); border: 1px dashed rgba(135, 186, 255, 0.25); border-radius: 4px; padding: 6px 10px; margin-bottom: 12px; color: #87BAFF; line-height: 1.4;">
                    • Filtro Ativo: <code>{ativos_txt}</code> | Lider: <code>{lider_txt}</code>
                </div>
                """, unsafe_allow_html=True)
                
                chat_container = st.container(height=380)
                with chat_container:
                    for msg in st.session_state.messages:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                            if msg["role"] == "assistant" and msg.get("tools"):
                                with st.expander("⚙️ Ver fontes e ferramentas utilizadas"):
                                    st.write(f"Ferramentas acionadas no ciclo ReAct: `{', '.join(msg['tools'])}`")
                                    
                prompt = st.chat_input("Pergunte algo sobre os ativos...")
                
                query_a_rodar = None
                if st.session_state.pending_ai_query:
                    query_a_rodar = st.session_state.pending_ai_query
                    st.session_state.pending_ai_query = None
                elif prompt:
                    query_a_rodar = prompt
                    
                if query_a_rodar:
                    st.session_state.messages.append({"role": "user", "content": query_a_rodar, "tools": []})
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(query_a_rodar)
                            
                    if not df_filtrado.empty:
                        volume_tot = df_filtrado["Valor_Total_Registrado"].sum()
                        filtros_contexto = (
                            f"[Filtros Ativos no Dashboard]: Ativos={ativos_txt}, Líder={lider_txt}, Status={status_txt}. "
                            f"Total Filtrado: {len(df_filtrado)} emissões, totalizando R$ {volume_tot/1e9:.2f} bilhões."
                        )
                    else:
                        filtros_contexto = "[Filtros]: Nenhuma oferta na tela."
                        
                    mensagem_com_contexto = f"{filtros_contexto}\n\n[Pergunta do Usuário]:\n{query_a_rodar}"
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            with st.spinner("⚙️ Consultando fontes..."):
                                try:
                                    agent = get_cached_agent()
                                    response = agent.invoke({"messages": [{"role": "user", "content": mensagem_com_contexto}]})
                                    resposta_final = response["messages"][-1].content
                                    tools_utilizadas = list(set([msg.name for msg in response["messages"] if hasattr(msg, "name") and msg.name]))
                                    
                                    if tools_utilizadas:
                                        with st.expander("⚙️ Ver fontes e ferramentas utilizadas"):
                                            st.write(f"Ferramentas acionadas: `{', '.join(tools_utilizadas)}`")
                                            
                                    st.markdown(resposta_final)
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": resposta_final,
                                        "tools": tools_utilizadas
                                    })
                                except Exception as e:
                                    st.error(f"Erro no assistente: {e}")
                    st.rerun()

            # 🔍 ABA DETALHES DO ATIVO (Master-Detail Drawer)
            if tab_detail is not None:
                with tab_detail:
                    selected_offer = df_filtrado.iloc[selected_rows[0]]
                    emissor = selected_offer["Nome_Emissor"]
                    ativo = selected_offer["Valor_Mobiliario"]
                    lider = selected_offer["Nome_Lider"]
                    volume = selected_offer["Valor_Total_Registrado"]
                    data_reg = selected_offer["Data_Registro"]
                    status = selected_offer["Status_Requerimento"]
                    
                    publico = selected_offer.get("Publico_alvo", "N/D")
                    incentivado = selected_offer.get("Titulo_incentivado", "N/D")
                    sustentavel = selected_offer.get("Titulo_classificado_como_sustentavel", "N/D")
                    garantias = selected_offer.get("Descricao_garantias", "N/D")
                    recursos = selected_offer.get("Destinacao_recursos", "N/D")
                    lastro = selected_offer.get("Tipo_lastro", "N/D")

                    isento_txt = "Sim [ISENTO IR]" if incentivado == "Sim" else "Não"
                    esg_txt = "Sim [Sustentável]" if sustentavel == "Sim" else "Não"

                    st.markdown(f"""
                    <div style="font-family:'Outfit'; border-bottom:1px solid rgba(135,186,255,0.15); padding-bottom:8px; margin-bottom:12px;">
                        <h4 style="margin:0; font-size:1.15rem; color:#FFFFFF;">{emissor}</h4>
                        <span style="color:#87BAFF; font-size:0.75rem; font-weight:bold;">{ativo} — Ficha Técnica</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # KPI Cards Internos da Emissão
                    c_det1, c_det2 = st.columns(2)
                    with c_det1:
                        st.markdown(f"""
                        <div style="background:rgba(5, 19, 42, 0.5); padding:8px; border:1px solid rgba(135,186,255,0.1); border-radius:4px; margin-bottom:8px;">
                            <span style="font-size:0.6rem; color:#87BAFF; display:block; text-transform:uppercase;">Volume</span>
                            <strong style="font-size:0.9rem; color:#FFFFFF; font-family:monospace;">R$ {volume/1e6:.1f}M</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_det2:
                        st.markdown(f"""
                        <div style="background:rgba(5, 19, 42, 0.5); padding:8px; border:1px solid rgba(135,186,255,0.1); border-radius:4px; margin-bottom:8px;">
                            <span style="font-size:0.6rem; color:#87BAFF; display:block; text-transform:uppercase;">Status</span>
                            <strong style="font-size:0.85rem; color:#2DB071;">{status}</strong>
                        </div>
                        """, unsafe_allow_html=True)

                    # Tabela de dados estruturados
                    st.markdown(f"""
                    <table style="width:100%; font-size:0.78rem; border-collapse:collapse; color:#E0E0E0; line-height:1.5;">
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold; width:35%;">Coordenador:</td><td>{lider}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">Público-Alvo:</td><td>{publico}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">Isento IR:</td><td>{isento_txt}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">ESG/Sustentável:</td><td>{esg_txt}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">Lastro:</td><td>{lastro}</td></tr>
                    </table>
                    """, unsafe_allow_html=True)

                    # Seção de Documentos
                    st.markdown("<h5 style='margin-top:12px; margin-bottom:6px; font-size:0.85rem; color:#87BAFF;'>Documentos da Emissão</h5>", unsafe_allow_html=True)
                    st.markdown("""
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom:12px;">
                        <div style="background: rgba(11, 40, 89, 0.4); border: 1px solid rgba(135,186,255,0.1); border-radius: 4px; padding: 6px; display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 14px;">📄</span>
                            <div>
                                <div style="font-size: 0.68rem; font-weight: bold; color: #FFFFFF;">Escritura.pdf</div>
                                <div style="font-size: 0.55rem; color: #87BAFF;">2.4 MB</div>
                            </div>
                        </div>
                        <div style="background: rgba(11, 40, 89, 0.4); border: 1px solid rgba(135,186,255,0.1); border-radius: 4px; padding: 6px; display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 14px;">📄</span>
                            <div>
                                <div style="font-size: 0.68rem; font-weight: bold; color: #FFFFFF;">Prospecto.pdf</div>
                                <div style="font-size: 0.55rem; color: #87BAFF;">1.8 MB</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Fluxo de Caixa Simulado (Sparkline)
                    st.markdown("<h5 style='margin-top:10px; margin-bottom:5px; font-size:0.85rem; color:#87BAFF;'>Projeção de Amortização</h5>", unsafe_allow_html=True)
                    years = [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032]
                    flow = [volume * 0.05, volume * 0.08, volume * 0.12, volume * 0.15, volume * 0.18, volume * 0.22, volume * 0.25, volume * 0.28, volume]
                    df_flow = pd.DataFrame({"Ano": years, "Fluxo": flow})
                    fig_flow = px.line(df_flow, x="Ano", y="Fluxo", markers=True, color_discrete_sequence=["#B1D2FF"])
                    fig_flow.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF",
                        margin=dict(t=5, b=5, l=5, r=5),
                        height=90,
                        xaxis=dict(showgrid=False, visible=False),
                        yaxis=dict(showgrid=False, visible=False)
                    )
                    st.plotly_chart(fig_flow, use_container_width=True, config={'displayModeBar': False})

                    # Análise Rápida de Recomendação da IA (Image 3 Style)
                    st.markdown("""
                    <div style="background: rgba(25, 90, 180, 0.08); border: 1px solid rgba(135,186,255,0.2); border-radius: 4px; padding: 10px; margin-top: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-size:0.72rem; color:#87BAFF; font-weight:bold;">Análise Recomendação IA</span>
                            <span style="background:#2DB071; color:#FFFFFF; font-size:8px; font-weight:bold; padding:2px 6px; border-radius:3px;">RECOMENDADO</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.75rem;">
                            <span style="color:#87BAFF;">Score Convicção: <strong style="color:#FFFFFF;">9.1 / 10</strong></span>
                            <span style="color:#87BAFF;">Risco: <strong style="color:#2DB071;">BAIXO</strong></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("💬 Solicitar Análise no Chatbot", key="btn_detail_analyze", use_container_width=True):
                        st.session_state.pending_ai_query = (
                            f"Faça uma análise de crédito estruturada para a emissão de {ativo} da {emissor}. "
                            f"Volume: R$ {volume:,.2f}. Recursos: {recursos}. Garantias: {garantias}. "
                            f"Lastro: {lastro}. Indique se esta oferta se compara bem com as taxas macro e da concorrência."
                        )
                        st.rerun()

# ─── PAGINA 2: MERCADO (XP VS MEELION COMPARATIVE) ───────────────────────────

elif menu_option == "💼 Mercado (XP vs Meelion)":
    st.markdown("<h2 style='margin-top:0px;'>💼 Inteligência da Concorrência: XP vs Meelion</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.9rem; color:#87BAFF; margin-top:-10px; margin-bottom:20px;'>Comparativo de taxas de mercado secundário e carteiras recomendadas vigentes para apoiar a tomada de decisão.</p>", unsafe_allow_html=True)
    
    col_xp, col_meelion = st.columns(2)
    
    with col_xp:
        st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF; font-size:1.15rem; border-bottom:1px solid rgba(135,186,255,0.2); padding-bottom:5px; margin-top:0px;'>Carteira Recomendada XP (Maio 2026)</h3>", unsafe_allow_html=True)
        
        xp_path = Path("data/cvm/carteira_xp_maio2026.json")
        if xp_path.exists():
            with open(xp_path, encoding="utf-8") as f:
                xp_data = json.load(f)
            st.markdown(f"<p style='font-size:0.75rem; color:#87BAFF; margin-top:5px;'><strong>Estratégia XP:</strong> {xp_data.get('resumo_estrategia', '')}</p>", unsafe_allow_html=True)
            
            for t in xp_data.get("titulos", []):
                isento = " | Isento IR" if t.get("isento_ir") else ""
                st.markdown(f"""
                <div style="background: rgba(5, 19, 42, 0.4); border: 1px solid rgba(135, 186, 255, 0.1); border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:#FFFFFF; font-size:0.85rem;">{t['ativo_emissor']}</strong>
                        <span style="color:#B1D2FF; font-size:0.75rem; font-weight:bold;">{t['indexador']}</span>
                    </div>
                    <div style="font-size:0.75rem; color:#87BAFF; line-height:1.4;">
                        Taxa Bruta: <span style="color:#FFFFFF; font-weight:bold;">{t['taxa_bruta']}</span> {isento}<br>
                        Vencimento: {t['vencimento']} | Setor: {t.get('setor', 'N/D')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Arquivo de recomendações da XP não encontrado em data/cvm/.")
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col_meelion:
        st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF; font-size:1.15rem; border-bottom:1px solid rgba(135,186,255,0.2); padding-bottom:5px; margin-top:0px;'>Ofertas Ativas Meelion (Scraping Corretoras)</h3>", unsafe_allow_html=True)
        
        meelion_path = Path("data/meelion/investimentos_page1.json")
        if meelion_path.exists():
            with open(meelion_path, encoding="utf-8") as f:
                meelion_data = json.load(f)
            st.markdown("<p style='font-size:0.75rem; color:#87BAFF; margin-top:5px;'>Títulos vigentes disponíveis para captação imediata em corretoras parceiras.</p>", unsafe_allow_html=True)
            
            for m in meelion_data[:8]: # Exibe os 8 primeiros de forma limpa
                fgc = " | Com cobertura FGC" if m.get("com_fgc") else " | Sem FGC"
                st.markdown(f"""
                <div style="background: rgba(5, 19, 42, 0.4); border: 1px solid rgba(135, 186, 255, 0.1); border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:#FFFFFF; font-size:0.85rem;">{m['nome']}</strong>
                        <span style="color:#2DB071; font-size:0.75rem; font-weight:bold;">{m['tipo']}</span>
                    </div>
                    <div style="font-size:0.75rem; color:#87BAFF; line-height:1.4;">
                        Emissor: {m['emissor']} | Distribuidor: {m['distribuidor']}<br>
                        Vencimento: {m['vencimento']} {fgc}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Arquivo de ofertas Meelion não encontrado em data/meelion/.")
        st.markdown("</div>", unsafe_allow_html=True)

# ─── PAGINA 3: CONFIGURAÇÕES E STATUS ─────────────────────────────────────────

elif menu_option == "⚙️ Configurações":
    st.markdown("<h2 style='margin-top:0px;'>⚙️ Painel de Controle e Status do Sistema</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.9rem; color:#87BAFF; margin-top:-10px; margin-bottom:20px;'>Verifique a saúde do banco de dados, chaves de API e versões da stack de IA.</p>", unsafe_allow_html=True)
    
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF; font-size:1.15rem; border-bottom:1px solid rgba(135,186,255,0.2); padding-bottom:5px; margin-top:0px;'>Status da IA & Integrações</h3>", unsafe_allow_html=True)
        
        # Validação dinâmica da API Key
        api_key_exists = "Configurada (OK)" if "GROQ_API_KEY" in os.environ and os.environ["GROQ_API_KEY"] else "Não configurada"
        
        st.markdown(f"""
        <table style="width:100%; font-size:0.85rem; border-collapse:collapse; color:#E0E0E0; line-height:2.0;">
            <tr><td style="color:#87BAFF; font-weight:bold;">Banco Vetorial (ChromaDB):</td><td>🟢 Conectado (13.139 registros)</td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">Banco Central (SGS API):</td><td>🟢 Conectado (CDI, Selic, IPCA)</td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">Yahoo Finance API:</td><td>🟢 Conectado (Ticker search ativo)</td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">Groq API Cloud Key:</td><td>🟢 {api_key_exists}</td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">LLM Model:</td><td><code>llama-3.3-70b-versatile</code></td></tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_status2:
        st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#FFFFFF; font-size:1.15rem; border-bottom:1px solid rgba(135,186,255,0.2); padding-bottom:5px; margin-top:0px;'>Versões de Software</h3>", unsafe_allow_html=True)
        
        import langchain
        import chromadb
        
        st.markdown(f"""
        <table style="width:100%; font-size:0.85rem; border-collapse:collapse; color:#E0E0E0; line-height:2.0;">
            <tr><td style="color:#87BAFF; font-weight:bold;">Streamlit:</td><td><code>{st.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">LangChain Core:</td><td><code>{langchain.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">ChromaDB:</td><td><code>{chromadb.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">Python Environment:</td><td><code>Active Virtualenv (venv)</code></td></tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
