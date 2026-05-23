#!/usr/bin/env python3
"""
Interface Streamlit — Painel Analítico Premium (Sleek Dark Mode)
Implementado segundo as diretrizes de UX/UI institucionais do BTG Pactual.
Integrando KPIs globais, gráficos dinâmicos de ofertas primárias CVM,
tabela interativa com vista de detalhe (Master-Detail) e chat ReAct integrado.
"""

import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from agent_engine import build_agent
from tools_custom import consultar_indicadores_macro

# ─── Configuração de Layout da Página ──────────────────────────────────────────

st.set_page_config(
    page_title="Antigravity-BTG | Renda Fixa",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    
    /* Glassmorphic Cards para KPIs */
    .kpi-card {
        background: rgba(11, 40, 89, 0.4) !important; /* Surface Level 1 */
        border-radius: 6px;
        padding: 12px 18px;
        border: 1px solid rgba(135, 186, 255, 0.12) !important;
        border-left: 4px solid #195AB4 !important; /* Primary Accent BTG */
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(135, 186, 255, 0.3) !important;
        transform: translateY(-2px);
    }
    
    .kpi-title {
        font-size: 0.75rem;
        color: #87BAFF; /* Text Secondary */
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 3px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 200; /* Estilo Moderat Thin */
        color: #FFFFFF;
        font-family: 'Outfit', sans-serif;
        line-height: 1.2;
    }
    
    .kpi-date {
        font-size: 0.7rem;
        color: #87BAFF;
        opacity: 0.75;
        margin-top: 3px;
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
        background-color: rgba(25, 90, 180, 0.1) !important; /* Azul escuro com transparência */
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
    selic_val = "10.50%"
    cdi_val = "10.40%"
    ipca_val = "0.38%"
    selic_date = "23/05/2026"
    cdi_date = "21/05/2026"
    ipca_date = "04/2026"
    
    # Parsing simples e robusto da string retornada
    for line in raw_str.split("\n"):
        if "Selic Meta:" in line:
            parts = line.split(":")
            selic_val = parts[1].split("(")[0].strip()
            if "vigente em" in line:
                selic_date = line.split("vigente em")[-1].replace(")", "").strip()
        elif "Taxa CDI" in line:
            parts = line.split(":")
            cdi_val = parts[1].split("(")[0].strip()
            if "referência de" in line:
                cdi_date = line.split("referência de")[-1].replace(")", "").strip()
        elif "IPCA" in line:
            parts = line.split(":")
            ipca_val = parts[1].split("(")[0].strip()
            if "referente a" in line:
                ipca_date = line.split("referente a")[-1].replace(")", "").strip()
                
    return {
        "selic": selic_val, "selic_date": selic_date,
        "cdi": cdi_val, "cdi_date": cdi_date,
        "ipca": ipca_val, "ipca_date": ipca_date
    }

# ─── Carregamento Inicial de Dados ──────────────────────────────────────────

df_cvm = load_cvm_dataset()
kpi_data = load_realtime_indicators()

# ─── Inicialização de Estados da Sessão ───────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Olá! Sou o Antigravity-BTG, seu analista especialista em renda fixa. Posso buscar taxas no Banco Central, cotações ao vivo na B3, ofertas vigentes da XP e Meelion, além de fazer buscas semânticas na CVM. Como posso te apoiar hoje?",
            "tools": []
        }
    ]

if "show_panel" not in st.session_state:
    st.session_state.show_panel = True

if "pending_ai_query" not in st.session_state:
    st.session_state.pending_ai_query = None

# Estados persistentes dos filtros para evitar perda ao fechar painel lateral
if "filter_ativos" not in st.session_state:
    st.session_state.filter_ativos = ["CRI", "CRA", "Debêntures", "Nota Comercial"]
if "filter_lider" not in st.session_state:
    st.session_state.filter_lider = ""
if "filter_status" not in st.session_state:
    st.session_state.filter_status = ["Deferido", "Registrado"]
if "filter_volume" not in st.session_state:
    st.session_state.filter_volume = (0.0, 1500.0) # Em Milhões

# ─── 1. TOP BAR (Logo + KPIs Globais do Banco Central) ────────────────────────

st.write(f"""
<div class="top-bar-container">
    <div style="display: flex; align-items: center;">
        <span class="logo-badge">btg</span>
        <span class="logo-text">pactual <span style="font-weight: 600; color: #B1D2FF;">antigravity</span></span>
    </div>
    <div style="display: flex; gap: 30px; align-items: center;">
        <div style="text-align: right;">
            <span style="font-size: 0.7rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Taxa Selic Meta</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 300; color: #FFFFFF;">{kpi_data["selic"]}</span>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(135, 186, 255, 0.15); padding-left: 30px;">
            <span style="font-size: 0.7rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Taxa CDI</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 300; color: #FFFFFF;">{kpi_data["cdi"]}</span>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(135, 186, 255, 0.15); padding-left: 30px;">
            <span style="font-size: 0.7rem; color: #87BAFF; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">IPCA Mensal</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 600; color: #2DB071;">{kpi_data["ipca"]}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── 2. GRID PRINCIPAL (Workspace vs Painel de Controle) ─────────────────────

if st.session_state.show_panel:
    col_dash, col_panel = st.columns([7.2, 2.8])
else:
    col_dash = st.container()
    col_panel = None

# ─── 3. WORKSPACE (Dashboard de Dados & Gráficos) ────────────────────────────

with col_dash:
    # Cabeçalho do Workspace com botão recolhível
    head_left, head_right = st.columns([6, 2])
    with head_left:
        st.markdown("<h2 style='margin-top:0px; font-size:1.6rem;'>📈 Workspace Analítico</h2>", unsafe_allow_html=True)
    with head_right:
        btn_label = "Recolher Painel ➔" if st.session_state.show_panel else "◀ Abrir Painel IA / Filtros"
        if st.button(btn_label, key="toggle_panel_btn", use_container_width=True):
            st.session_state.show_panel = not st.session_state.show_panel
            st.rerun()
            
    # Mensagem se o processo do IA colocou uma query de análise
    if st.session_state.pending_ai_query:
        st.info("🔄 Consulta gerada com sucesso! Clique na aba **Assistente IA** no painel lateral para ver a resposta detalhada.")

    # Processamento de Filtros (aplicável mesmo se o painel estiver recolhido)
    if not df_cvm.empty:
        df_filtrado = df_cvm.copy()
        
        # Filtro Tipo de Ativo
        if st.session_state.filter_ativos:
            df_filtrado = df_filtrado[df_filtrado["Valor_Mobiliario"].isin(st.session_state.filter_ativos)]
            
        # Filtro Status
        if st.session_state.filter_status:
            df_filtrado = df_filtrado[df_filtrado["Status_Requerimento"].isin(st.session_state.filter_status)]
            
        # Filtro Coordenador Líder
        if st.session_state.filter_lider:
            df_filtrado = df_filtrado[df_filtrado["Nome_Lider"].str.contains(st.session_state.filter_lider, case=False, na=False)]
            
        # Filtro de Volume (Milhões)
        df_filtrado = df_filtrado[
            (df_filtrado["Valor_Total_Registrado"] >= st.session_state.filter_volume[0] * 1e6) &
            (df_filtrado["Valor_Total_Registrado"] <= st.session_state.filter_volume[1] * 1e6)
        ]
    else:
        df_filtrado = pd.DataFrame()

    if df_filtrado.empty:
        st.info("Nenhuma oferta registrada corresponde aos filtros ativos. Tente relaxar as restrições na aba de Filtros.")
    else:
        # Seção de Gráficos em Abas
        tab_tipo, tab_lider = st.tabs(["Distribuição por Tipo de Ativo", "Maiores Líderes de Distribuição"])
        
        with tab_tipo:
            df_tipo = df_filtrado.groupby("Valor_Mobiliario")["Valor_Total_Registrado"].sum().reset_index()
            df_tipo["Volume_Bi"] = df_tipo["Valor_Total_Registrado"] / 1e9
            
            fig_tipo = px.pie(
                df_tipo,
                values="Volume_Bi",
                names="Valor_Mobiliario",
                color_discrete_sequence=["#195AB4", "#B1D2FF", "#10408D", "#307AE0", "#549CFF", "#87BAFF", "#D2E5FF"],
                hole=0.45,
                labels={"Volume_Bi": "Volume (Bi R$)", "Valor_Mobiliario": "Ativo"}
            )
            fig_tipo.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                marker=dict(line=dict(color='#05132A', width=2))
            )
            fig_tipo.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FFFFFF",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                margin=dict(t=10, b=10, l=10, r=10),
                height=260
            )
            st.plotly_chart(fig_tipo, use_container_width=True)
            
        with tab_lider:
            df_lider = df_filtrado.groupby("Nome_Lider")["Valor_Total_Registrado"].sum().reset_index()
            df_lider = df_lider.sort_values("Valor_Total_Registrado", ascending=False).head(8)
            df_lider["Volume_Mi"] = df_lider["Valor_Total_Registrado"] / 1e6
            
            fig_lider = px.bar(
                df_lider,
                x="Volume_Mi",
                y="Nome_Lider",
                orientation="h",
                color="Volume_Mi",
                color_continuous_scale=["#0B2859", "#195AB4", "#B1D2FF"],
                labels={"Volume_Mi": "Volume (Milhões R$)", "Nome_Lider": "Coordenador Líder"}
            )
            fig_lider.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FFFFFF",
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                xaxis=dict(showgrid=True, gridcolor="rgba(135, 186, 255, 0.1)"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_lider, use_container_width=True)
            
        # 📋 Tabela de Dados Interativa com Detalhes (Master-Detail)
        st.markdown("<h3 style='margin-top:20px; font-size:1.4rem;'>📋 Tabela de Ofertas CVM</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:#87BAFF; margin-top:-10px; margin-bottom:10px;'>Selecione uma linha abaixo para ver a ficha técnica e analisar os ativos com o IA.</p>", unsafe_allow_html=True)
        
        display_cols = {
            "Nome_Emissor": "Emissor",
            "Valor_Mobiliario": "Ativo",
            "Nome_Lider": "Coordenador Líder",
            "Valor_Total_Registrado": "Volume (R$)",
            "Data_Registro": "Registro",
            "Status_Requerimento": "Status"
        }
        
        df_display = df_filtrado[list(display_cols.keys())].copy()
        df_display["Data_Registro"] = df_display["Data_Registro"].dt.strftime("%d/%m/%Y")
        df_display = df_display.rename(columns=display_cols)
        
        # Renderiza a tabela habilitando seleção de linha única
        event = st.dataframe(
            df_display,
            column_config={
                "Volume (R$)": st.column_config.NumberColumn(
                    format="R$ %.2f",
                    help="Volume financeiro total da oferta registrado na CVM"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=280,
            selection_mode="single-row",
            on_select="rerun",
            key="ofertas_table"
        )
        
        # Lógica de exibição de Ficha Técnica (Master-Detail) se linha for selecionada
        selected_rows = event.selection.rows
        if selected_rows:
            row_idx = selected_rows[0]
            # Recuperar registro original correspondente (usando iloc)
            selected_offer = df_filtrado.iloc[row_idx]
            
            emissor = selected_offer["Nome_Emissor"]
            ativo = selected_offer["Valor_Mobiliario"]
            lider = selected_offer["Nome_Lider"]
            volume = selected_offer["Valor_Total_Registrado"]
            data_reg = selected_offer["Data_Registro"]
            status = selected_offer["Status_Requerimento"]
            
            # Detalhes ricos (colunas extras do CSV)
            publico = selected_offer.get("Publico_alvo", "N/D")
            incentivado = selected_offer.get("Titulo_incentivado", "N/D")
            sustentavel = selected_offer.get("Titulo_classificado_como_sustentavel", "N/D")
            garantias = selected_offer.get("Descricao_garantias", "N/D")
            recursos = selected_offer.get("Destinacao_recursos", "N/D")
            lastro = selected_offer.get("Tipo_lastro", "N/D")
            
            # Formatação de texto isento
            isento_badge = "<span style='background:#2DB071; color:#FFFFFF; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:3px;'>ISENTO IR</span>" if incentivado == "Sim" else ""
            sustentavel_badge = "<span style='background:#B1D2FF; color:#05132A; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:3px; margin-left:5px;'>ESG</span>" if sustentavel == "Sim" else ""
            
            # Card do Master-Detail
            st.markdown(f"""
            <div style="background: rgba(11, 40, 89, 0.45); border: 1px solid #195AB4; border-radius: 6px; padding: 18px; margin-top: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(135,186,255,0.18); padding-bottom:8px; margin-bottom:12px;">
                    <h4 style="margin:0; font-family:'Outfit',sans-serif; color:#FFFFFF; font-size:1.1rem; display:flex; align-items:center; gap:8px;">
                        🔍 Ficha Técnica: {emissor} {isento_badge} {sustentavel_badge}
                    </h4>
                    <span style="background:#195AB4; color:#FFFFFF; font-size:11px; font-weight:bold; padding:3px 10px; border-radius:4px; text-transform:uppercase; font-family:'Outfit';">{ativo}</span>
                </div>
                <table style="width:100%; border-collapse:collapse; font-size:0.85rem; color:#FFFFFF; line-height: 1.6;">
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold; width:25%;">Emissor:</td><td style="padding:4px 0;">{emissor}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Coordenador Líder:</td><td style="padding:4px 0;">{lider}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Volume da Oferta:</td><td style="padding:4px 0; font-family:monospace; font-weight:bold; color:#B1D2FF;">R$ {volume:,.2f}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Data de Registro:</td><td style="padding:4px 0;">{data_reg.strftime('%d/%m/%Y') if pd.notna(data_reg) else 'N/D'}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Status CVM:</td><td style="padding:4px 0;"><span style="color:#2DB071; font-weight:bold;">{status}</span></td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Público-Alvo:</td><td style="padding:4px 0;">{publico}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Tipo de Lastro:</td><td style="padding:4px 0;">{lastro}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Garantias da Emissão:</td><td style="padding:4px 0; line-height:1.4; font-style:italic; color:#dcdcdc;">{garantias}</td></tr>
                    <tr><td style="padding:4px 0; color:#87BAFF; font-weight:bold;">Destinação dos Recursos:</td><td style="padding:4px 0; line-height:1.4; color:#dcdcdc;">{recursos}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de ação integrado para mandar dados da oferta para a IA analisar
            if st.button(f"💬 Solicitar Análise de IA para {emissor}", key="btn_trigger_ai", use_container_width=True):
                st.session_state.pending_ai_query = (
                    f"Faça uma análise de crédito estruturada para a emissão de {ativo} da empresa {emissor}, "
                    f"coordenada por {lider}. O volume registrado é de R$ {volume:,.2f}. "
                    f"Lastro: {lastro}. Público-alvo: {publico}. Isento de IR: {incentivado}. "
                    f"Garantias descritas: {garantias}. Destinação dos recursos: {recursos}. "
                    f"Comente sobre a solidez e nos diga se essa taxa de emissão tende a ser atrativa perante o cenário macro."
                )
                st.rerun()

# ─── 4. PAINEL DE CONTROLE (Filtros & Chatbot com IA) ────────────────────────

if st.session_state.show_panel and col_panel is not None:
    with col_panel:
        st.markdown("<h3 style='margin-top:0px; font-size:1.3rem;'>⚡ Painel de Controle</h3>", unsafe_allow_html=True)
        tab_filters, tab_ai = st.tabs(["Filtros Rápidos", "🤖 Assistente IA"])
        
        # 📌 ABA FILTROS RÁPIDOS
        with tab_filters:
            st.markdown("<p style='font-size:0.82rem; color:#87BAFF;'>Configure os filtros para atualizar a tela e os dados fornecidos à IA:</p>", unsafe_allow_html=True)
            
            if not df_cvm.empty:
                # 1. Filtro Tipo de Ativo
                ativos_disponiveis = sorted(df_cvm["Valor_Mobiliario"].dropna().unique().tolist())
                ativos_selecionados = st.multiselect(
                    "Tipo de Ativo Renda Fixa",
                    options=ativos_disponiveis,
                    default=st.session_state.filter_ativos,
                    key="multiselect_ativos"
                )
                st.session_state.filter_ativos = ativos_selecionados
                
                # 2. Filtro Líder da Distribuição
                lider_search = st.text_input(
                    "Coordenador Líder (ex: BTG, XP)",
                    value=st.session_state.filter_lider,
                    key="text_lider"
                )
                st.session_state.filter_lider = lider_search
                
                # 3. Filtro Status
                status_disponiveis = sorted(df_cvm["Status_Requerimento"].dropna().unique().tolist())
                status_selecionados = st.multiselect(
                    "Status do Requerimento",
                    options=status_disponiveis,
                    default=st.session_state.filter_status,
                    key="multiselect_status"
                )
                st.session_state.filter_status = status_selecionados
                
                # 4. Filtro de Volume (Slider)
                max_vol = float(df_cvm["Valor_Total_Registrado"].max() / 1e6) if pd.notna(df_cvm["Valor_Total_Registrado"].max()) else 1000.0
                volume_range = st.slider(
                    "Volume (Milhões de R$)",
                    min_value=0.0,
                    max_value=min(max_vol, 5000.0),
                    value=st.session_state.filter_volume,
                    key="slider_volume"
                )
                st.session_state.filter_volume = volume_range
            else:
                st.write("Base de dados indisponível para carregar filtros.")
                
        # 🤖 ABA CHATBOT DE IA CONTEXTUAL (RAG)
        with tab_ai:
            # Pílulas visuais de contexto ativo
            ativos_txt = ", ".join(st.session_state.filter_ativos) if st.session_state.filter_ativos else "Todos"
            lider_txt = st.session_state.filter_lider if st.session_state.filter_lider else "Todos"
            status_txt = ", ".join(st.session_state.filter_status) if st.session_state.filter_status else "Todos"
            
            st.markdown(f"""
            <div style="font-size:0.75rem; background: rgba(25, 90, 180, 0.1); border: 1px dashed rgba(135, 186, 255, 0.25); border-radius: 4px; padding: 6px 10px; margin-bottom: 12px; color: #87BAFF; line-height: 1.4;">
                <strong>🎯 Filtros do Painel Sincronizados com a IA:</strong><br>
                • Ativos: <code>{ativos_txt}</code><br>
                • Líder: <code>{lider_txt}</code><br>
                • Status: <code>{status_txt}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Container de Rolagem do Chat
            chat_container = st.container(height=420)
            
            # Renderiza mensagens anteriores do chat
            with chat_container:
                for idx, msg in enumerate(st.session_state.messages):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        # Renderiza ferramentas acionadas no expander se houver histórico gravado
                        if msg["role"] == "assistant" and msg.get("tools"):
                            with st.expander("⚙️ Ver fontes e ferramentas utilizadas"):
                                st.write(f"Ferramentas acionadas no ciclo ReAct: `{', '.join(msg['tools'])}`")
            
            # Captura a caixa de texto
            prompt = st.chat_input("Ex: Quais CRIs do setor imobiliário estão ativos?")
            
            # Se houver clique no botão de ação da tabela (Master-Detail) ou digitação manual
            query_a_rodar = None
            if st.session_state.pending_ai_query:
                query_a_rodar = st.session_state.pending_ai_query
                st.session_state.pending_ai_query = None # Reseta
            elif prompt:
                query_a_rodar = prompt
                
            if query_a_rodar:
                # Mostra no chat a mensagem do usuário
                st.session_state.messages.append({"role": "user", "content": query_a_rodar, "tools": []})
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(query_a_rodar)
                
                # Monta contexto dinâmico de filtros ativos para guiar a IA
                if not df_filtrado.empty:
                    volume_tot = df_filtrado["Valor_Total_Registrado"].sum()
                    filtros_contexto = (
                        f"[Filtros Ativos no Dashboard do Usuário]:\n"
                        f"- Tipos de Ativo: {ativos_txt}\n"
                        f"- Coordenador Líder: {lider_txt}\n"
                        f"- Status da Oferta: {status_txt}\n"
                        f"- Total de Ofertas Filtradas: {len(df_filtrado)}\n"
                        f"- Volume Financeiro Filtrado: R$ {volume_tot/1e9:.2f} bilhões\n"
                        f"Se o usuário mencionar 'esses dados', 'este painel' ou 'ativos na tela', guie-se por esse contexto."
                    )
                else:
                    filtros_contexto = "[Filtros Ativos]: Nenhuma oferta corresponde aos filtros atuais."
                
                mensagem_com_contexto = f"{filtros_contexto}\n\n[Pergunta do Usuário]:\n{query_a_rodar}"
                
                # Invoca o agente
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("⚙️ Consultando ferramentas e comparando dados..."):
                            try:
                                agent = get_cached_agent()
                                response = agent.invoke({"messages": [{"role": "user", "content": mensagem_com_contexto}]})
                                
                                resposta_final = response["messages"][-1].content
                                
                                # Extrai as tools utilizadas
                                tools_utilizadas = []
                                for msg in response["messages"]:
                                    if hasattr(msg, "name") and msg.name:
                                        tools_utilizadas.append(msg.name)
                                
                                # Limpa duplicatas
                                tools_utilizadas = list(set(tools_utilizadas))
                                
                                # Renderiza ferramentas utilizadas em accordion
                                if tools_utilizadas:
                                    with st.expander("⚙️ Ver fontes e ferramentas utilizadas"):
                                        st.write(f"Ferramentas acionadas no ciclo ReAct: `{', '.join(tools_utilizadas)}`")
                                
                                st.markdown(resposta_final)
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": resposta_final,
                                    "tools": tools_utilizadas
                                })
                            except Exception as e:
                                st.error(f"Erro ao analisar com a IA: {e}")
                st.rerun()
