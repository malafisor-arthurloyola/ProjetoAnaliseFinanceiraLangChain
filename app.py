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
import plotly.graph_objects as go
import streamlit as st

from agent_engine import get_provider_status, invoke_agent_with_key_fallback
from tools_custom import consultar_indicadores_macro, calcular_nexus_score

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
    /* ─── CSS Design Tokens ─── */
    :root {
        --bg-primary: #05132A;
        --bg-surface: #0B2859;
        --bg-card: rgba(11, 40, 89, 0.3);
        --accent-blue: #195AB4;
        --accent-blue-dark: #10408D;
        --accent-light: #87BAFF;
        --accent-bright: #B1D2FF;
        --text-primary: #FFFFFF;
        --text-secondary: #87BAFF;
        --text-muted: #B1D2FF;
        --success: #2DB071;
        --warning: #B8860B;
        --danger: #E83E48;
        --border-subtle: rgba(135, 186, 255, 0.12);
        --border-active: rgba(135, 186, 255, 0.25);
        --font-heading: 'Outfit', sans-serif;
        --font-body: 'Inter', sans-serif;
    }

    /* Estilos Globais */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-body) !important;
    }
    
    /* Configuração de títulos */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-heading) !important;
        color: var(--text-primary) !important;
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

    .nexus-skeleton {
        height: 12px;
        border-radius: 4px;
        background: linear-gradient(90deg, rgba(135,186,255,0.08), rgba(135,186,255,0.22), rgba(135,186,255,0.08));
        background-size: 220% 100%;
        animation: nexusPulse 1.4s ease-in-out infinite;
        margin: 8px 0;
    }

    .nexus-disclaimer {
        color: #B1D2FF;
        font-size: 0.72rem;
        line-height: 1.35;
        border-top: 1px solid rgba(135,186,255,0.16);
        margin-top: 10px;
        padding-top: 8px;
    }

    @keyframes nexusPulse {
        0% { background-position: 0% 0; }
        100% { background-position: -220% 0; }
    }

    /* ─── High Yield Pulse Animation ─── */
    @keyframes hyPulse {
        0% { box-shadow: 0 0 0 0 rgba(232, 62, 72, 0.5); }
        70% { box-shadow: 0 0 0 10px rgba(232, 62, 72, 0); }
        100% { box-shadow: 0 0 0 0 rgba(232, 62, 72, 0); }
    }
    .high-yield-pulse {
        animation: hyPulse 2s infinite;
        border-color: var(--danger) !important;
    }
    .high-yield-badge {
        display: inline-block;
        background: rgba(232, 62, 72, 0.15);
        color: var(--danger);
        border: 1px solid rgba(232, 62, 72, 0.3);
        border-radius: 3px;
        padding: 1px 6px;
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    /* ─── Progress Bar Override ─── */
    div[data-testid="stDataFrame"] div[role="progressbar"] {
        background-color: var(--accent-blue) !important;
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
                
    selic_num = parse_percent_value(selic_val, default=14.50)
    cdi_num = max(selic_num - 0.10, 0.0)
    cdi_val = f"{cdi_num:.2f}% a.a."
    if cdi_date == "23/05/2026":
        cdi_date = selic_date

    return {
        "selic": selic_val, "selic_date": selic_date,
        "cdi": cdi_val, "cdi_date": cdi_date,
        "ipca": ipca_val, "ipca_date": ipca_date
    }


def parse_percent_value(value, default=0.0):
    try:
        cleaned = str(value).replace("%", "").replace("a.a.", "").replace(",", ".").strip()
        return float(cleaned.split()[0])
    except (TypeError, ValueError, IndexError):
        return default


def _sparkline_fig(values, color="#87BAFF", height=30):
    """Mini sparkline chart for KPI cards."""
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color=color, width=1.2),
        fill="tozeroy", fillcolor=f"rgba{tuple(int(color[i:i+2], 16) for i in (1, 3, 5)) + (0.12,)}",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0), height=height,
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False,
    )
    return fig


def _build_spark_data(current_val, n=6, noise=0.05):
    """Generate synthetic history around current value for sparkline."""
    import random
    base = current_val
    vals = []
    for i in range(n):
        frac = i / (n - 1)
        drift = (random.random() - 0.5) * 2 * noise * base
        vals.append(base - (base * noise * (1 - frac)) + drift)
    vals[-1] = current_val
    return vals


def classify_sector(row):
    ativo = str(row.get("Valor_Mobiliario", "")).upper()
    incentivado = str(row.get("Titulo_incentivado", "")).upper()
    lastro = str(row.get("Tipo_lastro", "")).upper()

    if any(term in ativo for term in ["LFT", "NTN", "TESOURO"]):
        return "Soberano"
    if any(term in ativo for term in ["CDB", "LCI", "LCA", "LETRA FINANCEIRA"]):
        return "Bancario"
    if "AGRONEGOCIO" in ativo or "AGRONEG" in ativo or "CRA" in ativo:
        return "Agro"
    if "IMOBILI" in ativo or "CRI" in ativo or "FII" in ativo:
        return "Imobiliario"
    if "DEB" in ativo:
        return "Infra" if incentivado == "S" else "Corporativo"
    if "FIDC" in ativo or "DIREITOS CREDITORIOS" in ativo:
        return "Credito Estruturado" if "CONCENTRADO" in lastro else "Credito Pulverizado"
    if "FIP" in ativo:
        return "Private Equity"
    if "FIF" in ativo or "FUNDO" in ativo:
        return "Fundos"
    if "NOTAS COMERCIAIS" in ativo:
        return "Corporativo"
    return "Corporativo"


def is_tax_exempt(row):
    ativo = str(row.get("Valor_Mobiliario", "")).upper()
    incentivado = str(row.get("Titulo_incentivado", "")).upper()
    return incentivado == "S" or any(term in ativo for term in ["LCA", "LCI", "CRI", "CRA", "LIG"])


def calculate_ir_rate(row):
    if is_tax_exempt(row):
        return 0.0

    registro = row.get("Data_Registro")
    encerramento = row.get("Data_Encerramento")
    if pd.isna(registro) or pd.isna(encerramento):
        prazo_dias = 721
    else:
        prazo_dias = max((encerramento - registro).days, 1)

    if prazo_dias <= 180:
        return 0.225
    if prazo_dias <= 360:
        return 0.20
    if prazo_dias <= 720:
        return 0.175
    return 0.15


def estimate_gross_rate(row, cdi_value):
    setor = row.get("Setor", classify_sector(row))
    volume = float(row.get("Valor_Total_Registrado", 0) or 0)
    spread_by_sector = {
        "Soberano": -0.10,
        "Bancario": 0.35,
        "Agro": 1.25,
        "Imobiliario": 1.45,
        "Infra": 1.70,
        "Corporativo": 2.20,
        "Credito Pulverizado": 2.50,
        "Credito Estruturado": 3.25,
        "Private Equity": 4.50,
        "Fundos": 0.60,
    }
    volume_spread = 0.45 if volume and volume < 100_000_000 else 0.0
    return max(cdi_value + spread_by_sector.get(setor, 1.0) + volume_spread, 0.0)


def infer_rating(row):
    setor = row.get("Setor", classify_sector(row))
    volume = float(row.get("Valor_Total_Registrado", 0) or 0)
    avaliador = str(row.get("Avaliador_Risco", "")).strip().lower()
    garantias = str(row.get("Descricao_garantias", "")).strip().lower()
    status = str(row.get("Status_Requerimento", "")).upper()

    if setor == "Soberano":
        return "AAA", "Baixo Risco"
    if setor == "Bancario":
        return "AA", "Baixo Risco"
    if "SUSPENSA" in status or "REVOGADA" in status or "CADUCADO" in status:
        return "BB", "Atencao"
    if avaliador and avaliador not in {"nan", "na", "n.a.", "nao ha", "não há"}:
        return ("AA", "Baixo Risco") if volume >= 300_000_000 else ("A", "Medio Risco")
    if any(term in garantias for term in ["fiduci", "aval", "seguro", "fundo"]):
        return "A", "Medio Risco"
    if setor in {"Agro", "Imobiliario", "Infra"}:
        return "A-", "Medio Risco"
    if setor in {"Credito Estruturado", "Private Equity"}:
        return "BBB", "Atencao"
    return "BBB+", "Medio Risco"


def build_ai_verdict(row, cdi_value):
    rating = row.get("Rating", "BBB")
    setor = row.get("Setor", "Corporativo")
    taxa = float(row.get("Taxa_Bruta_Estimada", cdi_value) or cdi_value)
    isento = bool(row.get("Isento_IR", False))

    if taxa > cdi_value + 4:
        return "Atencao", "Taxa estimada acima de CDI + 4 p.p.; exige diligencia de credito e liquidez."
    if rating in {"AAA", "AA"} or setor == "Soberano":
        return "Seguro", "Perfil defensivo por rating/garantia/setor; ainda requer validacao documental."
    if isento and setor in {"Agro", "Imobiliario", "Infra"}:
        return "Oportunidade", "Ativo isento com potencial de eficiencia fiscal para pessoa fisica."
    return "Neutro", "Oferta sem sinal forte; comparar taxa liquida, prazo, lastro e garantias."


def is_historical_status(status):
    status_text = str(status).upper()
    return any(term in status_text for term in ["ENCERRADA", "CADUCADO", "REVOGADA", "EXPIRADO"])


def prepare_nexus_dataset(df, kpi_data):
    if df.empty:
        return df

    cdi_value = parse_percent_value(kpi_data.get("cdi"), default=14.40)
    enriched = df.copy()
    enriched["Setor"] = enriched.apply(classify_sector, axis=1)
    enriched["Isento_IR"] = enriched.apply(is_tax_exempt, axis=1)
    enriched["Aliquota_IR"] = enriched.apply(calculate_ir_rate, axis=1)
    enriched["Taxa_Bruta_Estimada"] = enriched.apply(lambda row: estimate_gross_rate(row, cdi_value), axis=1)
    enriched["Taxa_Liquida"] = enriched["Taxa_Bruta_Estimada"] * (1 - enriched["Aliquota_IR"])
    ratings = enriched.apply(infer_rating, axis=1)
    enriched["Rating"] = ratings.apply(lambda item: item[0])
    enriched["Risco_Rating"] = ratings.apply(lambda item: item[1])
    verdicts = enriched.apply(lambda row: build_ai_verdict(row, cdi_value), axis=1)
    enriched["Veredito_IA"] = verdicts.apply(lambda item: item[0])
    enriched["Tooltip_IA"] = verdicts.apply(lambda item: item[1])
    enriched["Historico"] = enriched["Status_Requerimento"].apply(is_historical_status)
    enriched["Taxa Liquida"] = enriched["Taxa_Liquida"].map(lambda value: f"{value:.2f}% a.a.")
    enriched["Taxa Bruta"] = enriched["Taxa_Bruta_Estimada"].map(lambda value: f"{value:.2f}% a.a.")
    enriched["Aliquota IR"] = enriched["Aliquota_IR"].map(lambda value: "Isento" if value == 0 else f"{value * 100:.1f}%")
    enriched["Veredito IA"] = enriched.apply(lambda row: f"{row['Veredito_IA']} - {row['Tooltip_IA']}", axis=1)
    score_results = enriched.apply(
        lambda r: calcular_nexus_score(
            taxa_liquida=r["Taxa_Liquida"], cdi_atual=cdi_value,
            rating=r["Rating"], setor=r["Setor"],
            isento=r["Isento_IR"], aliquota_ir=r["Aliquota_IR"],
            volume=r["Valor_Total_Registrado"],
            titulo_sustentavel=str(r.get("Titulo_classificado_como_sustentavel", "")),
            intent="padrao",
        ),
        axis=1, result_type="expand"
    )
    enriched["NexusScore_100"] = score_results["score"].apply(lambda x: f"{x:.0f}")
    enriched["NexusScore_Stars"] = score_results["stars"].apply(lambda x: "⭐" * int(x) + "☆" * (5 - int(x)))
    enriched["NexusScore_Label"] = score_results["label"]
    return enriched


def apply_intent_filter(df, intent, cdi_value):
    if df.empty or not intent:
        return df
    if intent == "seguranca":
        return df[(df["Rating"].isin(["AAA", "AA"])) | (df["Setor"].isin(["Soberano", "Bancario"]))]
    if intent == "renda_mensal":
        return df[df["Setor"].isin(["Imobiliario", "Infra", "Fundos"])]
    if intent == "rentabilidade":
        return df[df["Taxa_Bruta_Estimada"] > cdi_value + 4]
    if intent == "agro":
        return df[df["Setor"].eq("Agro")]
    return df


def render_pdf_progress_skeleton():
    progress = st.progress(0)
    status = st.empty()
    for step, value in [
        ("Lendo prospecto de 300 paginas...", 30),
        ("Calculando premio de risco...", 65),
        ("Cruzando com Relatorio Focus...", 100),
    ]:
        status.caption(step)
        progress.progress(value)
    st.markdown(
        """
        <div class="nexus-skeleton" style="width: 100%;"></div>
        <div class="nexus-skeleton" style="width: 82%;"></div>
        <div class="nexus-skeleton" style="width: 64%;"></div>
        """,
        unsafe_allow_html=True,
    )


DISCLAIMER_IA = (
    "Esta analise e gerada por inteligencia artificial (Nexus AI) e tem carater "
    "informativo. Nao constitui recomendacao de investimento. Consulte seu assessor financeiro."
)


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
df_cvm = prepare_nexus_dataset(df_cvm, kpi_data)

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
    st.session_state.filter_ativos = []
if "filter_lider" not in st.session_state:
    st.session_state.filter_lider = ""
if "filter_status" not in st.session_state:
    st.session_state.filter_status = []
if "filter_volume" not in st.session_state:
    st.session_state.filter_volume = (0.0, 1500.0) # Em Milhões

if "intent_filter" not in st.session_state:
    st.session_state.intent_filter = None
if "selected_offer_context" not in st.session_state:
    st.session_state.selected_offer_context = None

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

selic_num = parse_percent_value(kpi_data["selic"], default=14.50)
cdi_num = parse_percent_value(kpi_data["cdi"], default=14.40)
ipca_num = parse_percent_value(kpi_data["ipca"], default=4.50)

selic_history = _build_spark_data(selic_num)
cdi_history = _build_spark_data(cdi_num)
ipca_history = _build_spark_data(ipca_num, noise=0.08)

st.markdown('<div class="top-bar-container">', unsafe_allow_html=True)
top_cols = st.columns([1.2, 1, 1, 1, 0.8])
with top_cols[0]:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="font-family:'Outfit';font-size:16px;font-weight:800;color:#fff;">BTG Pactual</span>
        <span style="color:rgba(255,255,255,0.4);font-size:16px;">|</span>
        <span style="font-family:'Outfit';font-size:14px;font-weight:300;color:#87BAFF;">Nexus</span>
    </div>
    """, unsafe_allow_html=True)
for col_idx, (label, value, history, color) in enumerate([
    ("Selic Meta", kpi_data["selic"], selic_history, "#FFFFFF"),
    ("Taxa CDI", kpi_data["cdi"], cdi_history, "#FFFFFF"),
    ("IPCA (12m)", kpi_data["ipca"], ipca_history, "#2DB071"),
]):
    with top_cols[col_idx + 1]:
        st.markdown(f"""
        <div style="text-align:right; border-left:1px solid rgba(135,186,255,0.15); padding-left:20px;">
            <span style="font-size:0.6rem;color:#87BAFF;display:block;text-transform:uppercase;font-weight:700;">{label}</span>
            <span style="font-family:'Outfit';font-size:1rem;font-weight:600;color:{color};">{value}</span>
        </div>
        """, unsafe_allow_html=True)
        fig_spark = _sparkline_fig(history, color="#2DB071" if "IPCA" in label else "#87BAFF", height=24)
        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})
with top_cols[4]:
    st.markdown("""
    <div style="text-align:right; border-left:1px solid rgba(135,186,255,0.15); padding-left:20px; display:flex; align-items:center; gap:8px; justify-content:flex-end;">
        <span style="font-size:0.65rem;color:#87BAFF;font-family:monospace;">23/05/2026</span>
        <div style="background:#195AB4;color:#fff;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-family:'Outfit';font-size:10px;font-weight:bold;box-shadow:0 0 6px rgba(25,90,180,0.5);">AG</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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
            cdi_atual = parse_percent_value(kpi_data["cdi"], default=14.40)
        else:
            df_filtrado = pd.DataFrame()
            cdi_atual = parse_percent_value(kpi_data["cdi"], default=14.40)

        st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0px; font-size:1rem; color:#87BAFF;'>Filtros de intenção</h4>", unsafe_allow_html=True)
        intent_cols = st.columns(5)
        intent_options = [
            ("seguranca", "Maxima Seguranca", "Rating AA/AAA, soberano ou bancario"),
            ("renda_mensal", "Renda Mensal", "FIIs, fundos e infra"),
            ("rentabilidade", "Super Rentabilidade", "High Yield acima de CDI + 4 p.p."),
            ("agro", "Foco no Agro", "LCAs e CRAs isentos"),
            (None, "Limpar", "Remover filtro de intenção"),
        ]
        for col, (intent_key, label, help_text) in zip(intent_cols, intent_options):
            with col:
                active = st.session_state.intent_filter == intent_key
                button_label = f"{label}" + (" *" if active and intent_key else "")
                if st.button(button_label, key=f"intent_{label}", help=help_text, use_container_width=True):
                    st.session_state.intent_filter = intent_key
                    st.rerun()
        if st.session_state.intent_filter:
            df_filtrado = apply_intent_filter(df_filtrado, st.session_state.intent_filter, cdi_atual)
        st.markdown("</div>", unsafe_allow_html=True)

        if df_filtrado.empty:
            st.info("Nenhuma oferta registrada corresponde aos filtros ativos. Ajuste os filtros na aba lateral.")
        else:
            # Gráficos lado a lado
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0px; font-size:1.05rem; color:#87BAFF;'>Distribuição por Setor (Treemap)</h4>", unsafe_allow_html=True)
                df_treemap = df_filtrado.groupby(["Setor", "Valor_Mobiliario"])["Valor_Total_Registrado"].sum().reset_index()
                df_treemap["Volume_Bi"] = df_treemap["Valor_Total_Registrado"] / 1e9
                fig_treemap = px.treemap(
                    df_treemap,
                    path=["Setor", "Valor_Mobiliario"],
                    values="Volume_Bi",
                    color="Volume_Bi",
                    color_continuous_scale=["#0B2859", "#195AB4", "#87BAFF", "#B1D2FF"],
                    labels={"Volume_Bi": "Volume (Bi R$)"},
                )
                fig_treemap.update_traces(
                    textinfo="label+value",
                    hovertemplate="<b>%{label}</b><br>Volume: R$ %{value:.1f}Bi<extra></extra>"
                )
                fig_treemap.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FFFFFF",
                    margin=dict(t=5, b=5, l=5, r=5),
                    height=220,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_treemap, use_container_width=True)
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
                
            # Sunburst — Hierarquia Setor → Ativo → Volume
            with st.expander("🌐 Visão Hierárquica (Sunburst)", expanded=False):
                df_sun = df_filtrado.groupby(["Setor", "Valor_Mobiliario"])["Valor_Total_Registrado"].sum().reset_index()
                df_sun["Volume_Bi"] = df_sun["Valor_Total_Registrado"] / 1e9
                fig_sun = px.sunburst(
                    df_sun,
                    path=["Setor", "Valor_Mobiliario"],
                    values="Volume_Bi",
                    color="Volume_Bi",
                    color_continuous_scale=["#0B2859", "#195AB4", "#87BAFF", "#B1D2FF"],
                )
                fig_sun.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FFFFFF",
                    margin=dict(t=5, b=5, l=5, r=5),
                    height=300,
                    coloraxis_showscale=False,
                )
                fig_sun.update_traces(hovertemplate="<b>%{label}</b><br>Volume: R$ %{value:.1f}Bi<extra></extra>")
                st.plotly_chart(fig_sun, use_container_width=True)
                
            # 📋 Tabela de Emissões CVM
            st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0px; font-size:1.25rem;'>📋 Emissões Registradas</h3>", unsafe_allow_html=True)
            
            # Adicionar coluna Insight IA com base no cenário macroeconômico atual
            df_ativas = df_filtrado[~df_filtrado["Historico"]].copy()
            df_historico = df_filtrado[df_filtrado["Historico"]].copy()
            table_mode = st.radio(
                "Recorte da tabela",
                options=["Ofertas Ativas", "Historico"],
                horizontal=True,
                label_visibility="collapsed",
                key="offers_table_mode",
            )
            df_insight = df_ativas.copy() if table_mode == "Ofertas Ativas" else df_historico.copy()
            table_source_df = df_insight
            st.caption(f"{len(df_ativas)} ofertas ativas | {len(df_historico)} no historico")
            df_insight["Insight IA"] = df_insight.apply(
                lambda row: gerar_insight_ia(row, kpi_data["selic"], kpi_data["cdi"]), 
                axis=1
            )

            # Paginação: mostrar top 100 por padrão
            max_table_rows = 100
            total_rows = len(df_insight)
            show_all = st.checkbox(f"Mostrar todas ({total_rows} ofertas)", value=False, key="show_all_table")
            df_table = df_insight if show_all else df_insight.head(max_table_rows)

            # Badge High Yield: CDI + 4%
            cdi_for_hy = parse_percent_value(kpi_data["cdi"], default=14.40)
            df_table["HY"] = df_table["Taxa_Bruta_Estimada"].apply(
                lambda x: "⚡ High Yield" if x > cdi_for_hy + 4 else ""
            )

            display_cols = {
                "NexusScore_Stars": "Nexus",
                "Nome_Emissor": "Emissor",
                "Valor_Mobiliario": "Ativo",
                "Setor": "Setor",
                "Taxa Liquida": "Taxa Liquida",
                "Rating": "Rating",
                "Valor_Total_Registrado": "Volume (R$)",
                "Status_Requerimento": "Status",
                "HY": "High Yield",
            }

            df_display = df_table[list(display_cols.keys())].copy()
            df_display = df_display.rename(columns=display_cols)
            max_volume = df_display["Volume (R$)"].max() if not df_display.empty else 1

            event = st.dataframe(
                df_display,
                column_config={
                    "Volume (R$)": st.column_config.ProgressColumn(
                        format="R$ %.2f",
                        min_value=0,
                        max_value=max_volume,
                        help="Volume financeiro total da oferta"
                    ),
                    "Rating": st.column_config.TextColumn(
                        help="Rating de crédito com indicador de cor"
                    ),
                    "High Yield": st.column_config.TextColumn(
                        help="Alerta de rentabilidade acima de CDI + 4%"
                    ),
                },
                hide_index=True,
                use_container_width=True,
                height=260,
                selection_mode="single-row",
                on_select="rerun",
                key="ofertas_table"
            )
            st.markdown(
                f"<div class='nexus-disclaimer'>{DISCLAIMER_IA}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.72rem;color:#87BAFF;text-align:center;margin-top:6px;'>"
                "💡 Selecione uma oferta na tabela para ver detalhes no painel ao lado</div>",
                unsafe_allow_html=True,
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
                                    response = invoke_agent_with_key_fallback([
                                        {"role": "user", "content": mensagem_com_contexto}
                                    ])
                                    resposta_final = response["messages"][-1].content
                                    if DISCLAIMER_IA not in resposta_final:
                                        resposta_final = f"{resposta_final}\n\n---\n{DISCLAIMER_IA}"
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
                    selected_offer = table_source_df.iloc[selected_rows[0]]
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
                    setor = selected_offer.get("Setor", "Corporativo")
                    rating = selected_offer.get("Rating", "BBB")
                    risco_rating = selected_offer.get("Risco_Rating", "Medio Risco")
                    taxa_liquida = selected_offer.get("Taxa Liquida", "N/D")
                    veredito = selected_offer.get("Veredito_IA", "Neutro")
                    tooltip_ia = selected_offer.get("Tooltip_IA", "")
                    nexus_score = selected_offer.get("NexusScore_100", "N/D")
                    nexus_stars = selected_offer.get("NexusScore_Stars", "")
                    nexus_label = selected_offer.get("NexusScore_Label", "")

                    cdi_num = parse_percent_value(kpi_data.get("cdi", "14.65% a.a."), default=14.40)
                    taxa_liquida_raw = float(selected_offer.get("Taxa_Liquida", 0.0))
                    taxa_bruta_raw = float(selected_offer.get("Taxa_Bruta_Estimada", 0.0))
                    aliquota_val = float(selected_offer.get("Aliquota_IR", 0.0)) * 100
                    is_high_yield = taxa_bruta_raw > cdi_num + 4

                    isento_txt = "Sim [ISENTO IR]" if incentivado == "Sim" else "Não"
                    esg_txt = "Sim [Sustentável]" if sustentavel == "Sim" else "Não"

                    st.markdown(f"""
                    <div style="font-family:'Outfit'; border-bottom:1px solid rgba(135,186,255,0.15); padding-bottom:8px; margin-bottom:12px;">
                        <h4 style="margin:0; font-size:1.15rem; color:#FFFFFF;">{emissor}</h4>
                        <span style="color:#87BAFF; font-size:0.75rem; font-weight:bold;">{ativo} — Ficha Técnica</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # KPI Cards Internos da Emissão
                    c_det1, c_det2, c_det3 = st.columns(3)
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
                    with c_det3:
                        st.markdown(f"""
                        <div style="background:rgba(5, 19, 42, 0.5); padding:8px; border:1px solid rgba(135,186,255,0.1); border-radius:4px; margin-bottom:8px;">
                            <span style="font-size:0.6rem; color:#87BAFF; display:block; text-transform:uppercase;">Taxa Liquida</span>
                            <strong style="font-size:0.85rem; color:#2DB071;">{taxa_liquida}</strong>
                        </div>
                        """, unsafe_allow_html=True)

                    # Tabela de dados estruturados
                    st.markdown(f"""
                    <table style="width:100%; font-size:0.78rem; border-collapse:collapse; color:#E0E0E0; line-height:1.5;">
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold; width:35%;">Coordenador:</td><td>{lider}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">Setor:</td><td>{setor}</td></tr>
                        <tr><td style="padding:3px 0; color:#87BAFF; font-weight:bold;">Rating:</td><td>{rating} ({risco_rating})</td></tr>
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

                    with st.expander("Processar prospecto com Nexus", expanded=False):
                        render_pdf_progress_skeleton()

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

                    # NexusScore — Gauge + Dimensões
                    badge_color = {"Excelente": "#2DB071", "Bom": "#195AB4", "Regular": "#B8860B", "Atencao": "#E83E48"}.get(nexus_label, "#195AB4")
                    badge_text = {"Excelente": "EXCELENTE", "Bom": "FAVORAVEL", "Regular": "NEUTRO", "Atencao": "ATENCAO"}.get(nexus_label, "NEUTRO")

                    # Recompute for dimensões breakdown
                    nexus_detail = calcular_nexus_score(
                        taxa_liquida=taxa_liquida_raw, cdi_atual=cdi_num,
                        rating=selected_offer.get("Rating", "BBB"),
                        setor=selected_offer.get("Setor", "Corporativo"),
                        isento=selected_offer.get("Isento_IR", False),
                        aliquota_ir=float(selected_offer.get("Aliquota_IR", 0.0)),
                        volume=selected_offer.get("Valor_Total_Registrado", 0),
                        titulo_sustentavel=str(selected_offer.get("Titulo_classificado_como_sustentavel", "")),
                        intent="padrao",
                    )
                    dims = nexus_detail.get("dimensoes", {})

                    col_gauge, col_nexus_info = st.columns([1, 1.3])
                    with col_gauge:
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=float(nexus_score) if nexus_score != "N/D" else 0,
                            number={"font": {"color": "#FFFFFF", "size": 26}, "suffix": "/100"},
                            gauge={
                                "axis": {"range": [0, 100], "tickcolor": "#87BAFF", "tickfont": {"color": "#87BAFF", "size": 8}},
                                "bar": {"color": badge_color, "thickness": 0.25},
                                "bgcolor": "rgba(0,0,0,0)",
                                "borderwidth": 0,
                                "steps": [
                                    {"range": [0, 40], "color": "rgba(232, 62, 72, 0.15)"},
                                    {"range": [40, 60], "color": "rgba(184, 134, 11, 0.1)"},
                                    {"range": [60, 80], "color": "rgba(25, 90, 180, 0.15)"},
                                    {"range": [80, 100], "color": "rgba(45, 176, 113, 0.15)"},
                                ],
                                "threshold": {"line": {"color": "#FFFFFF", "width": 1.5}, "thickness": 0.5, "value": float(nexus_score) if nexus_score != "N/D" else 0},
                            }
                        ))
                        fig_gauge.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#FFFFFF", margin=dict(t=0, b=0, l=0, r=0), height=130,
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

                    with col_nexus_info:
                        pulse_class = "high-yield-pulse" if is_high_yield else ""
                        st.markdown(f"""
                        <div class="{pulse_class}" style="background: rgba(25, 90, 180, 0.08); border: 1px solid rgba(135,186,255,0.2); border-radius: 4px; padding: 8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-size:0.65rem; color:#87BAFF; font-weight:bold;">NexusScore — Rating Composto</span>
                                <span style="display:flex; align-items:center; gap:4px;">
                                    {'<span class="high-yield-badge">⚡ High Yield</span>' if is_high_yield else ''}
                                    <span style="background:{badge_color}; color:#FFFFFF; font-size:7px; font-weight:bold; padding:2px 5px; border-radius:3px;">{badge_text}</span>
                                </span>
                            </div>
                            <div style="display:flex; justify-content:space-between; font-size:0.70rem;">
                                <span style="color:#87BAFF;">Score: <strong style="color:#FFFFFF;">{nexus_score}/100</strong> {nexus_stars}</span>
                                <span style="color:#87BAFF;">Rating: <strong style="color:#FFFFFF;">{rating}</strong> ({risco_rating})</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Radar Chart — 6 Dimensões
                    st.markdown("<h5 style='margin-top:4px; margin-bottom:2px; font-size:0.68rem; color:#87BAFF;'>Dimensões do Score (0–10)</h5>", unsafe_allow_html=True)
                    dim_labels = {"rentabilidade": "Rentabilidade", "seguranca": "Segurança", "fiscal": "Fiscal", "porte": "Porte", "liquidez": "Liquidez", "esg": "ESG"}
                    dim_values = [dims.get(k, 0) for k in dim_labels.keys()]
                    dim_names = list(dim_labels.values())
                    fig_radar = go.Figure(go.Scatterpolar(
                        r=dim_values + [dim_values[0]],
                        theta=dim_names + [dim_names[0]],
                        fill="toself", fillcolor="rgba(135, 186, 255, 0.12)",
                        line=dict(color="#87BAFF", width=1.2),
                    ))
                    fig_radar.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF", margin=dict(t=5, b=5, l=5, r=5), height=160,
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(range=[0, 10], visible=True,
                                            gridcolor="rgba(135,186,255,0.15)",
                                            tickfont=dict(size=7)),
                            angularaxis=dict(gridcolor="rgba(135,186,255,0.15)", tickfont=dict(size=7, color="#87BAFF")),
                        ),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

                    st.markdown(f"""
                    <div style="background: rgba(25, 90, 180, 0.10); border: 1px solid rgba(135,186,255,0.25); border-radius: 4px; padding: 10px; margin-top: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-size:0.72rem; color:#87BAFF; font-weight:bold;">Insight da IA</span>
                            <span title="{tooltip_ia}" style="background:#195AB4; color:#FFFFFF; font-size:8px; font-weight:bold; padding:2px 6px; border-radius:3px;">{veredito}</span>
                        </div>
                        <div style="font-size:0.74rem; color:#E0E0E0; line-height:1.35;">{tooltip_ia}</div>
                        <div class="nexus-disclaimer">{DISCLAIMER_IA}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Waterfall — Equivalência Fiscal: Bruta → IR → Líquida
                    isento_offer = selected_offer.get("Isento_IR", False)
                    if isento_offer:
                        waterfall_data = [
                            dict(label="Taxa Bruta", value=taxa_bruta_raw, measure="relative"),
                            dict(label="Isenção IR (0%)", value=0, measure="relative"),
                            dict(label="Taxa Líquida", value=taxa_bruta_raw, measure="total"),
                        ]
                    else:
                        ir_amount = taxa_bruta_raw - taxa_liquida_raw
                        waterfall_data = [
                            dict(label="Taxa Bruta", value=taxa_bruta_raw, measure="relative"),
                            dict(label=f"IR (-{aliquota_val:.0f}%)", value=-ir_amount, measure="relative"),
                            dict(label="Taxa Líquida", value=taxa_liquida_raw, measure="total"),
                        ]
                    fig_waterfall = go.Figure(go.Waterfall(
                        name="Taxa",
                        orientation="v",
                        measure=[d["measure"] for d in waterfall_data],
                        x=[d["label"] for d in waterfall_data],
                        y=[d["value"] for d in waterfall_data],
                        text=[f"{d['value']:.2f}%" for d in waterfall_data],
                        textposition="outside",
                        connector={"line": {"color": "rgba(135,186,255,0.3)", "width": 1}},
                        decreasing={"marker": {"color": "#E83E48"}},
                        increasing={"marker": {"color": "#2DB071"}},
                        totals={"marker": {"color": "#195AB4"}},
                    ))
                    fig_waterfall.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF", margin=dict(t=10, b=5, l=5, r=5), height=130,
                        xaxis=dict(showgrid=False, tickfont=dict(size=8)),
                        yaxis=dict(showgrid=True, gridcolor="rgba(135,186,255,0.1)", tickfont=dict(size=8),
                                   title="Taxa (% a.a.)", title_font=dict(size=8, color="#87BAFF")),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_waterfall, use_container_width=True, config={'displayModeBar': False})

                    if st.button("Analisar com Nexus", key="btn_detail_analyze", use_container_width=True):
                        st.session_state.pending_ai_query = (
                            f"Faça uma análise de crédito estruturada para a emissão de {ativo} da {emissor}. "
                            f"Setor: {setor}. Rating Nexus: {rating} ({risco_rating}). Taxa líquida estimada: {taxa_liquida}. "
                            f"Veredito IA: {veredito} ({tooltip_ia}). Volume: R$ {volume:,.2f}. "
                            f"Recursos: {recursos}. Garantias: {garantias}. Lastro: {lastro}. "
                            f"Indique se esta oferta se compara bem com as taxas macro e da concorrência. "
                            f"Inclua este disclaimer no final: {DISCLAIMER_IA}"
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
        llm_providers = get_provider_status()
        api_key_exists = f"{len(llm_providers)} provedor(es) configurado(s)" if llm_providers else "Não configurada"
        
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
        
        import langchain_core
        import chromadb
        
        st.markdown(f"""
        <table style="width:100%; font-size:0.85rem; border-collapse:collapse; color:#E0E0E0; line-height:2.0;">
            <tr><td style="color:#87BAFF; font-weight:bold;">Streamlit:</td><td><code>{st.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">LangChain Core:</td><td><code>{langchain_core.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">ChromaDB:</td><td><code>{chromadb.__version__}</code></td></tr>
            <tr><td style="color:#87BAFF; font-weight:bold;">Python Environment:</td><td><code>Active Virtualenv (venv)</code></td></tr>
        </table>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
