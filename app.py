#!/usr/bin/env python3
"""
Interface Streamlit — Painel Analítico Premium (Sleek Dark Mode)
Integrando estatísticas, gráficos interativos de ofertas primárias CVM,
e chat inteligente com o agente ReAct Antigravity-BTG.
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
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Typography & Premium CSS Styles (Sleek Dark Mode + Glassmorphism) ────────

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* Estilos Globais */
    .stApp {
        background: linear-gradient(135deg, #0a0c10 0%, #121620 100%);
        color: #f0f3f8;
        font-family: 'Inter', sans-serif;
    }
    
    /* Neon glowing headers */
    .neon-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        color: #00f2fe;
        text-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
        margin-bottom: 0px;
    }
    
    .subtitle {
        font-family: 'Outfit', sans-serif;
        color: #8c9cb2;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 25px;
    }
    
    /* Sidebar premium styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 12, 16, 0.95) !important;
        border-right: 1px solid rgba(0, 242, 254, 0.15) !important;
    }
    
    /* Glassmorphic Cards para KPIs */
    .kpi-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 15px 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid #00f2fe;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        margin-bottom: 10px;
    }
    
    .kpi-title {
        font-size: 0.85rem;
        color: #8c9cb2;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #00f2fe;
        font-family: 'Outfit', monospace;
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.3);
    }
    
    .kpi-date {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 3px;
    }
    
    /* Chat premium overrides */
    .stChatMessage {
        border-radius: 10px !important;
        margin-bottom: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(0, 242, 254, 0.03) !important;
        border: 1px solid rgba(0, 242, 254, 0.1) !important;
    }
    
    /* Scrollbar override */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0c10;
    }
    ::-webkit-scrollbar-thumb {
        background: #1c2333;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00f2fe;
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
    df["Ano"] = df["Data_Registro"].dt.year
    df["Valor_Total_Registrado"] = pd.to_numeric(df["Valor_Total_Registrado"], errors="coerce")
    return df


@st.cache_data(ttl=1800)  # Atualiza a cada 30 minutos
def load_realtime_indicators():
    """Busca e extrai os dados reais de Selic, CDI e IPCA do Banco Central."""
    raw_str = consultar_indicadores_macro()
    
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

# ─── Sidebar — Filtros do Dashboard ──────────────────────────────────────────

st.sidebar.markdown("<h2 style='color:#00f2fe;font-family:Outfit;margin-bottom:5px;'>⚡ Filtros Rápidos</h2>", unsafe_allow_html=True)
st.sidebar.write("Refine as estatísticas e atualize o painel dinamicamente:")

if not df_cvm.empty:
    # 1. Filtro Tipo de Ativo
    ativos_disponiveis = sorted(df_cvm["Valor_Mobiliario"].dropna().unique().tolist())
    ativos_selecionados = st.sidebar.multiselect(
        "Tipo de Ativo Renda Fixa",
        options=ativos_disponiveis,
        default=["CRI", "CRA", "Debêntures", "Nota Comercial"] if all(x in ativos_disponiveis for x in ["CRI", "CRA", "Debêntures", "Nota Comercial"]) else [ativos_disponiveis[0]]
    )

    # 2. Filtro Líder da Distribuição (Pesquisa de texto)
    liders_disponiveis = sorted(df_cvm["Nome_Lider"].dropna().unique().tolist())
    lider_search = st.sidebar.text_input("Buscar Coordenador Líder (ex: BTG)", "")

    # 3. Filtro Status do Requerimento
    status_disponiveis = sorted(df_cvm["Status_Requerimento"].dropna().unique().tolist())
    status_selecionados = st.sidebar.multiselect(
        "Status do Requerimento",
        options=status_disponiveis,
        default=["Deferido", "Registrado"] if all(x in status_disponiveis for x in ["Deferido", "Registrado"]) else status_disponiveis
    )

    # 4. Filtro Faixa de Volume (Milhões de R$)
    max_vol = float(df_cvm["Valor_Total_Registrado"].max() / 1e6) if pd.notna(df_cvm["Valor_Total_Registrado"].max()) else 1000.0
    volume_range = st.sidebar.slider(
        "Volume Registrado (Milhões de R$)",
        min_value=0.0,
        max_value=min(max_vol, 5000.0), # Travar em R$ 5 bilhões para escala visual
        value=(0.0, min(max_vol, 1500.0))
    )

    # Aplicar filtros no DataFrame local
    df_filtrado = df_cvm.copy()
    
    if ativos_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Valor_Mobiliario"].isin(ativos_selecionados)]
        
    if status_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Status_Requerimento"].isin(status_selecionados)]
        
    if lider_search:
        df_filtrado = df_filtrado[df_filtrado["Nome_Lider"].str.contains(lider_search, case=False, na=False)]
        
    df_filtrado = df_filtrado[
        (df_filtrado["Valor_Total_Registrado"] >= volume_range[0] * 1e6) &
        (df_filtrado["Valor_Total_Registrado"] <= volume_range[1] * 1e6)
    ]
else:
    df_filtrado = pd.DataFrame()

# Rodapé da sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:0.8rem;color:#64748b;text-align:center;'>"
    "Antigravity-BTG • Sistema Analítico Avançado<br>"
    "Dados CVM atualizados até 2026</div>",
    unsafe_allow_html=True
)

# ─── Estrutura Principal da Tela (Cabeçalho e KPIs) ──────────────────────────

st.markdown("<h1 class='neon-title'>⚡ Antigravity-BTG</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Painel Avançado de Distribuição de Renda Fixa & Agente ReAct Inteligente</p>", unsafe_allow_html=True)

# Linha de Indicadores Macro (KPI Cards com Glassmorphism)
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Taxa Selic Meta</div>
        <div class="kpi-value">{kpi_data["selic"]}</div>
        <div class="kpi-date">Vigência: {kpi_data["selic_date"]} (Banco Central)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Taxa CDI de Referência</div>
        <div class="kpi-value">{kpi_data["cdi"]}</div>
        <div class="kpi-date">Data: {kpi_data["cdi_date"]} (Banco Central)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #39ff14;">
        <div class="kpi-title">IPCA (Inflação Mensal)</div>
        <div class="kpi-value" style="color:#39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.3);">{kpi_data["ipca"]}</div>
        <div class="kpi-date">Referência: {kpi_data["ipca_date"]} (Banco Central)</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Corpo de Layout de 2 Colunas (Painel Analítico vs. AI Agent Chat) ───────

col_dash, col_chat = st.columns([3, 2])

# ── Coluna Esquerda: Visualização Gráfica & Tabela ────────────────────────────
with col_dash:
    st.markdown("<h3 style='font-family:Outfit;color:#f0f3f8;margin-bottom:15px;'>📈 Inteligência do Painel (Dashboard)</h3>", unsafe_allow_html=True)
    
    if df_filtrado.empty:
        st.info("Nenhuma oferta registrada corresponde aos filtros ativos. Tente relaxar as restrições na barra lateral.")
    else:
        # 1. Gráficos Plotly em abas
        tab_tipo, tab_lider = st.tabs(["Distribuição por Tipo de Ativo", "Maiores Líderes de Distribuição"])
        
        with tab_tipo:
            df_tipo = df_filtrado.groupby("Valor_Mobiliario")["Valor_Total_Registrado"].sum().reset_index()
            df_tipo["Volume_Bi"] = df_tipo["Valor_Total_Registrado"] / 1e9
            
            fig_tipo = px.pie(
                df_tipo,
                values="Volume_Bi",
                names="Valor_Mobiliario",
                color_discrete_sequence=px.colors.sequential.Ales,
                hole=0.4,
                labels={"Volume_Bi": "Volume (Bi R$)", "Valor_Mobiliario": "Ativo"}
            )
            fig_tipo.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f0f3f8",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=10, b=10, l=10, r=10),
                height=280
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
                color_continuous_scale="Cividis",
                labels={"Volume_Mi": "Volume (Milhões R$)", "Nome_Lider": "Coordenador Líder"}
            )
            fig_lider.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f0f3f8",
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=280
            )
            st.plotly_chart(fig_lider, use_container_width=True)
            
        # 2. Tabela de dados Interativa
        st.markdown("<h4 style='font-family:Outfit;color:#00f2fe;margin-top:20px;margin-bottom:10px;'>📋 Detalhes das Ofertas Selecionadas</h4>", unsafe_allow_html=True)
        
        # Otimizar colunas para exibição amigável
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
        
        st.dataframe(
            df_display,
            column_config={
                "Volume (R$)": st.column_config.NumberColumn(
                    format="R$ %.2f",
                    help="Volume financeiro total da oferta registrado na CVM"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )

# ── Coluna Direita: Agente Inteligente Chat ───────────────────────────────────
with col_chat:
    st.markdown("<h3 style='font-family:Outfit;color:#00f2fe;margin-bottom:15px;'>🤖 Analista Financeiro ReAct (IA)</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.85rem;color:#8c9cb2;margin-bottom:15px;line-height:1.3;'>"
        "Faça análises complexas sobre renda fixa. O agente possui memória interna "
        "e acessa dinamicamente as ferramentas de CVM, BCB, ChromaDB e XP.</div>",
        unsafe_allow_html=True
    )
    
    # Inicializa histórico de mensagens na sessão
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Olá! Sou o Antigravity-BTG, seu analista especialista em renda fixa. Posso buscar taxas no Banco Central, cotações ao vivo na B3, ofertas vigentes da XP e Meelion, além de fazer buscas semânticas na CVM. Como posso te apoiar hoje?"}
        ]
        
    # Renderiza mensagens anteriores do chat
    chat_container = st.container(height=480)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    # Caixa de entrada para novas interações
    if prompt := st.chat_input("Ex: CDBs pós-fixados Meelion estão atraentes comparados à Selic?"):
        # Adiciona e renderiza mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
                
        # Constrói o contexto dinâmico dos filtros ativos no painel
        if not df_filtrado.empty:
            ativo_txt = ", ".join(ativos_selecionados) if ativos_selecionados else "Todos"
            lider_txt = lider_search if lider_search else "Todos"
            status_txt = ", ".join(status_selecionados) if status_selecionados else "Todos"
            volume_tot = df_filtrado["Valor_Total_Registrado"].sum()
            
            filtros_contexto = (
                f"[Filtros Ativos na Tela do Usuário]:\n"
                f"- Tipos de Ativo: {ativo_txt}\n"
                f"- Coordenador Líder buscado: {lider_txt}\n"
                f"- Status da Oferta: {status_txt}\n"
                f"- Total de Ofertas Filtradas: {len(df_filtrado)}\n"
                f"- Volume Financeiro das Ofertas Filtradas: R$ {volume_tot/1e9:.2f} bilhões\n"
                f"Use estes filtros como orientação se o usuário se referir a 'estes dados', 'painel' ou 'ofertas visíveis'."
            )
        else:
            filtros_contexto = "[Filtros Ativos na Tela]: Nenhuma oferta atende aos filtros atuais."

        # Passa a pergunta com o contexto embarcado de forma invisível para o usuário
        mensagem_com_contexto = f"{filtros_contexto}\n\n[Pergunta do Usuário]:\n{prompt}"
        
        # Invoca o agente ReAct e exibe a resposta
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🔧 Pensando e consultando ferramentas..."):
                    try:
                        agent = get_cached_agent()
                        # Executa chamada ao grafo do LangGraph
                        response = agent.invoke({"messages": [{"role": "user", "content": mensagem_com_contexto}]})
                        
                        # Extrai a resposta final do LLM
                        resposta_final = response["messages"][-1].content
                        
                        # Rastreia as tools chamadas no processo para exibição
                        tools_chamadas = []
                        for msg in response["messages"]:
                            if hasattr(msg, "name") and msg.name:
                                tools_chamadas.append(msg.name)
                                
                        if tools_chamadas:
                            st.markdown(
                                f"<div style='font-size:0.75rem;color:#00f2fe;font-family:monospace;margin-bottom:8px;'>"
                                f"🔧 Chamadas de Ferramentas: {', '.join(set(tools_chamadas))}</div>",
                                unsafe_allow_html=True
                            )
                            
                        st.markdown(resposta_final)
                        st.session_state.messages.append({"role": "assistant", "content": resposta_final})
                    except Exception as e:
                        st.error(f"Erro ao analisar com a IA: {e}")
