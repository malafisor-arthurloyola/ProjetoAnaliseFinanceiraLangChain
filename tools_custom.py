#!/usr/bin/env python3
"""
Tools Customizadas — Ferramentas que o agente inteligente utiliza para analisar
dados da CVM, do Banco Central (SGS), do ChromaDB (busca semântica), da XP, da Meelion e cotações de mercado.
"""

import json
import math
import os
import unicodedata
import warnings
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from langchain_core.tools import tool

# ─── Configurações e Caminhos de Dados ────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Carrega variáveis do arquivo .env (chave Groq, etc.)
load_dotenv(PROJECT_ROOT / ".env")

# ─── Carrega Bases de Dados locais (Cachê em Memória) ──────────────────────────

try:
    cvm_csv_path = DATA_DIR / "cvm" / "oferta_resolucao_160.csv"
    if cvm_csv_path.exists():
        _df_cvm = pd.read_csv(cvm_csv_path, sep=";")
        _df_cvm["Data_Registro"] = pd.to_datetime(_df_cvm["Data_Registro"], errors="coerce")
        _df_cvm["Ano"] = _df_cvm["Data_Registro"].dt.year
    else:
        _df_cvm = pd.DataFrame()
except Exception as e:
    print(f"Aviso ao carregar base CVM: {e}")
    _df_cvm = pd.DataFrame()

try:
    xp_json_path = DATA_DIR / "cvm" / "carteira_xp_maio2026.json"
    if xp_json_path.exists():
        with open(xp_json_path, encoding="utf-8") as f:
            _carteira_xp = json.load(f)
    else:
        _carteira_xp = {}
except Exception as e:
    print(f"Aviso ao carregar carteira XP: {e}")
    _carteira_xp = {}

try:
    meelion_json_path = DATA_DIR / "meelion" / "investimentos_page1.json"
    if meelion_json_path.exists():
        with open(meelion_json_path, encoding="utf-8") as f:
            _meelion = json.load(f)
    else:
        _meelion = []
except Exception as e:
    print(f"Aviso ao carregar dados Meelion: {e}")
    _meelion = []


# ─── Funções Utilitárias ──────────────────────────────────────────────────────

def normalize_text(s: str) -> str:
    """Normaliza strings para remover acentos e facilitar buscas textuais."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


# ─── Mapeamento de Setores (Guia de Referência Técnica — Regra 2.2) ─────────
# Nunca exibir N/D para ativos padronizados

SETOR_MAP = {
    "LFT": "Soberano (Tesouro Nacional)",
    "NTN-B": "Soberano (Tesouro Nacional)",
    "NTN-F": "Soberano (Tesouro Nacional)",
    "TESOURO": "Soberano (Tesouro Nacional)",
    "CDB": "Bancário/Financeiro",
    "LCI": "Bancário/Financeiro",
    "LCA": "Bancário/Financeiro",
    "LCD": "Bancário/Financeiro",
    "CRI": "Imobiliário",
    "CRA": "Agronegócio",
    "DEBENTURE": "Industrial/Infraestrutura",
    "DEBÊNTURE": "Industrial/Infraestrutura",
    "FIDC": "Crédito Privado",
    "FII": "Imobiliário",
    "CPR": "Agronegócio",
    "CCP": "Agronegócio",
}

# Alíquotas IR regressivas (tabela definitiva)
ALIQUOTAS_IR = [
    (180, 0.225),   # até 180 dias: 22,5%
    (360, 0.200),   # 181 a 360 dias: 20%
    (720, 0.175),   # 361 a 720 dias: 17,5%
    (99999, 0.150), # acima de 720 dias: 15%
]


def get_setor(nome_ativo: str) -> str:
    """Retorna o setor do ativo com base no mapeamento padronizado. Nunca retorna N/D."""
    nome_upper = nome_upper = str(nome_ativo).upper()
    for chave, setor in SETOR_MAP.items():
        if chave in nome_upper:
            return setor
    return "Crédito Privado"


def get_aliquota_ir(dias_corridos: int) -> float:
    """Retorna a alíquota de IR com base no prazo em dias corridos."""
    for limite, aliquota in ALIQUOTAS_IR:
        if dias_corridos <= limite:
            return aliquota
    return 0.15


def calcular_taxa_liquida(taxa_bruta_pct: float, dias_corridos: int = 720) -> float:
    """Calcula a taxa líquida após IR para ativos tributáveis.
    
    Args:
        taxa_bruta_pct: Taxa bruta em % ao ano (ex: 14.0 para 14%)
        dias_corridos: Prazo do investimento em dias corridos (padrão 720 = IR de 17,5%)
    Returns:
        Taxa líquida em % ao ano
    """
    aliquota = get_aliquota_ir(dias_corridos)
    return taxa_bruta_pct * (1 - aliquota)


def alerta_high_yield(taxa_str: str, cdi_anual: float = 14.40) -> str:
    """Verifica se uma taxa indica risco de crédito elevado (High Yield).
    
    Critério (Guia Técnico 2.1): taxa > CDI + 4% ou prefixado > 18%
    """
    try:
        t = str(taxa_str).upper()
        # Detecta formato CDI+X%
        if "CDI" in t and "+" in t:
            spread_str = t.split("+")[-1].replace("%", "").strip()
            spread = float(spread_str)
            if spread >= 4.0:
                return f"⚠️ HIGH YIELD — Spread CDI+{spread:.1f}% indica Risco de Crédito Elevado. Verifique o rating do emissor."
        # Detecta prefixado
        elif "%" in t and "CDI" not in t and "IPCA" not in t:
            valor_str = t.replace("%", "").replace("A.A.", "").strip()
            valor = float(valor_str)
            if valor >= 18.0:
                return f"⚠️ HIGH YIELD — Taxa prefixada de {valor:.1f}% a.a. indica Risco de Crédito Elevado."
    except Exception:
        pass
    return ""


# ─── NexusScore Scoring Engine ────────────────────────────────────────────────

PESOS_INTENT = {
    "padrao":     {"rentabilidade": 0.30, "seguranca": 0.35, "fiscal": 0.15, "porte": 0.10, "liquidez": 0.05, "esg": 0.05},
    "seguranca":  {"rentabilidade": 0.15, "seguranca": 0.45, "fiscal": 0.10, "porte": 0.10, "liquidez": 0.15, "esg": 0.05},
    "rentabilidade": {"rentabilidade": 0.45, "seguranca": 0.10, "fiscal": 0.15, "porte": 0.10, "liquidez": 0.10, "esg": 0.10},
    "renda_mensal": {"rentabilidade": 0.25, "seguranca": 0.10, "fiscal": 0.15, "porte": 0.10, "liquidez": 0.30, "esg": 0.10},
    "agro":       {"rentabilidade": 0.25, "seguranca": 0.15, "fiscal": 0.20, "porte": 0.10, "liquidez": 0.10, "esg": 0.20},
}


def _normalizar_rating(rating_str: str) -> float:
    mapa = {"AAA": 10.0, "AA": 8.5, "A": 7.0, "A-": 6.0, "BBB+": 5.5, "BBB": 4.5, "BB": 3.0, "B": 1.5, "CCC": 0.5}
    return mapa.get(str(rating_str).strip().upper(), 3.0)


def _fgc_bonus(setor: str) -> float:
    return 1.5 if str(setor).strip().lower() in ("bancario", "bancário", "bancario/financeiro") else 0.0


def _score_rentabilidade(taxa_liquida: float, cdi_atual: float) -> float:
    if cdi_atual <= 0:
        return 5.0
    return min((taxa_liquida / cdi_atual) * 5, 10.0)


def _score_seguranca(rating_str: str, setor: str) -> float:
    return min(_normalizar_rating(rating_str) + _fgc_bonus(setor), 10.0)


def _score_fiscal(isento: bool, aliquota_ir: float) -> float:
    if isento:
        return 10.0
    if aliquota_ir <= 0.15:
        return 7.0
    if aliquota_ir <= 0.175:
        return 5.0
    return 3.0


def _score_porte(volume: float) -> float:
    if pd.isna(volume) or volume <= 0:
        return 3.0
    return min(max((math.log10(max(volume, 1)) - 5) * 2, 1.0), 10.0)


def _score_liquidez(setor: str) -> float:
    setor_lower = str(setor).strip().lower()
    if "soberano" in setor_lower:
        return 9.0
    if "bancario" in setor_lower or "bancário" in setor_lower:
        return 7.0
    if "imobiliario" in setor_lower or "imobiliário" in setor_lower:
        return 5.0
    return 4.0


def _score_esg(titulo_sustentavel: str) -> float:
    return 10.0 if str(titulo_sustentavel).strip().upper() == "S" else 5.0


def calcular_nexus_score(taxa_liquida: float, cdi_atual: float, rating: str, setor: str, isento: bool, aliquota_ir: float, volume: float, titulo_sustentavel: str = "", intent: str = "padrao") -> dict:
    pesos = PESOS_INTENT.get(intent, PESOS_INTENT["padrao"])
    scores = {
        "rentabilidade": _score_rentabilidade(taxa_liquida, cdi_atual),
        "seguranca": _score_seguranca(rating, setor),
        "fiscal": _score_fiscal(isento, aliquota_ir),
        "porte": _score_porte(volume),
        "liquidez": _score_liquidez(setor),
        "esg": _score_esg(titulo_sustentavel),
    }
    final = sum(scores[k] * pesos[k] for k in pesos) * 10
    if taxa_liquida > cdi_atual + 4:
        final = max(final - 20, 0)
    if final >= 80:
        label = "Excelente"
    elif final >= 60:
        label = "Bom"
    elif final >= 40:
        label = "Regular"
    else:
        label = "Atencao"
    stars = min(max(round(final / 20), 1), 5)
    return {"score": round(final, 1), "label": label, "stars": stars, "dimensoes": {k: round(v, 1) for k, v in scores.items()}}


# ─── Definição das Tools ──────────────────────────────────────────────────────

@tool
def resumo_mercado_cvm() -> str:
    """
    Retorna um resumo geral do mercado de ofertas primárias registradas na CVM
    (Resolução 160, de 2023 a 2026): total de ofertas, volume financeiro registrado,
    breakdown por tipo de ativo (CRI, CRA, Debêntures, FIDC, etc.) e ranking dos 
    maiores bancos/líderes de distribuição.
    Use quando o usuário pedir uma visão macro do mercado de capitais brasileiro.
    """
    if _df_cvm.empty:
        return "A base de ofertas da CVM está vazia ou não pôde ser carregada."
        
    total = len(_df_cvm)
    volume = _df_cvm["Valor_Total_Registrado"].sum() / 1e9

    por_tipo = (
        _df_cvm.groupby("Valor_Mobiliario")["Valor_Total_Registrado"]
        .agg(qtd="count", volume_bi=lambda x: x.sum() / 1e9)
        .sort_values("volume_bi", ascending=False)
        .head(8)
    )

    por_lider = (
        _df_cvm.groupby("Nome_Lider")["Valor_Total_Registrado"]
        .agg(qtd="count", volume_bi=lambda x: x.sum() / 1e9)
        .sort_values("volume_bi", ascending=False)
        .head(6)
    )

    por_ano = (
        _df_cvm.groupby("Ano")["Valor_Total_Registrado"]
        .agg(qtd="count", volume_bi=lambda x: x.sum() / 1e9)
        .sort_index()
    )

    return (
        f"RESUMO MERCADO CVM (Resolução 160 — 2023 a 2026)\n"
        f"Total de ofertas registradas: {total:,}\n"
        f"Volume total acumulado: R$ {volume:.1f} bilhões\n\n"
        f"Por tipo de ativo (top 8):\n{por_tipo.to_string()}\n\n"
        f"Por líder de distribuição (top 6):\n{por_lider.to_string()}\n\n"
        f"Por ano:\n{por_ano.to_string()}"
    )


@tool
def buscar_ofertas_cvm(tipo: str = "", lider: str = "", ano: int = 0, limite: int = 10) -> str:
    """
    Busca ofertas primárias na base da CVM com filtros opcionais.
    Use quando o usuário quiser encontrar registros ou listar ofertas por regras estritas.

    Parâmetros:
        tipo  — tipo de ativo (ex: 'Debêntures', 'CRI', 'CRA', 'FIDC', 'FII').
                Busca parcial, case-insensitive.
        lider — nome do banco líder (ex: 'BTG', 'XP', 'Itaú', 'Bradesco').
                Busca parcial, case-insensitive.
        ano   — ano de registro (ex: 2024, 2025). 0 = todos os anos.
        limite — número máximo de resultados (padrão: 10).
    """
    if _df_cvm.empty:
        return "A base de ofertas da CVM está vazia ou não pôde ser carregada."
        
    df = _df_cvm.copy()

    if tipo:
        df = df[df["Valor_Mobiliario"].map(str).map(normalize_text).str.contains(normalize_text(tipo), case=False, na=False)]
    if lider:
        df = df[df["Nome_Lider"].map(str).map(normalize_text).str.contains(normalize_text(lider), case=False, na=False)]
    if ano:
        df = df[df["Ano"] == ano]

    if df.empty:
        return "Nenhuma oferta encontrada com os filtros informados."

    cols = ["Data_Registro", "Valor_Mobiliario", "Nome_Emissor", "Nome_Lider",
            "Valor_Total_Registrado", "Status_Requerimento"]
    resultado = df[cols].sort_values("Data_Registro", ascending=False).head(limite)
    resultado = resultado.copy()
    resultado["Valor_Total_Registrado"] = resultado["Valor_Total_Registrado"].apply(
        lambda v: f"R$ {v/1e6:.1f}M" if pd.notna(v) and v > 0 else "N/D"
    )
    resultado["Data_Registro"] = resultado["Data_Registro"].dt.strftime("%d/%m/%Y")

    return (
        f"Encontradas {len(df):,} ofertas (exibindo as {min(limite, len(df))} mais recentes):\n\n"
        + resultado.to_string(index=False)
    )


@tool
def carteira_recomendada_xp() -> str:
    """
    Retorna a carteira recomendada de Renda Fixa da XP Investimentos para Maio 2026,
    incluindo nome do ativo, emissor, indexador, taxas bruta e gross-up, vencimento,
    isenção de Imposto de Renda e observações técnicas.
    Use quando o usuário quiser saber as recomendações oficiais e análises da XP.
    """
    if not _carteira_xp:
        return "Carteira de recomendações da XP não disponível."
        
    c = _carteira_xp
    linhas = [
        f"CARTEIRA RECOMENDADA XP — {c.get('data_referencia', 'Maio 2026')}",
        f"Instituição: {c.get('instituicao', 'XP Investimentos')}",
        f"Estratégia: {c.get('resumo_estrategia', '')}",
        f"Fonte: {c.get('fonte_url', '')}",
        f"\n{len(c.get('titulos', []))} títulos recomendados:",
    ]
    for i, t in enumerate(c.get("titulos", []), 1):
        ir = " [ISENTO IR]" if t.get("isento_ir") else ""
        gross = f" | Gross-up: {t['taxa_gross_up']}" if t.get("taxa_gross_up") else ""
        linhas.append(
            f"\n  {i}. {t['ativo_emissor']}{ir}\n"
            f"     Indexador: {t['indexador']} | Taxa: {t['taxa_bruta']}{gross}\n"
            f"     Vencimento: {t['vencimento']} | Setor: {t.get('setor', 'N/D')}"
        )
    return "\n".join(linhas)


@tool
def investimentos_meelion() -> str:
    """
    Retorna os títulos de renda fixa disponíveis no mercado primário e secundário 
    obtidos via scraping do comparador de investimentos Meelion (dados de Maio 2026).
    Retorna emissor, distribuidor, tipo de ativo, rentabilidade, vencimento e se possui 
    cobertura do Fundo Garantidor de Créditos (FGC).
    Use quando o usuário quiser saber o que está efetivamente sendo oferecido nas corretoras.
    """
    if not _meelion:
        return "Dados de investimentos vigentes do Meelion não disponíveis."
        
    linhas = [f"OFERTAS DE RENDIMENTOS MEELION ({len(_meelion)} resultados):"]
    for i, inv in enumerate(_meelion, 1):
        fgc = "Com cobertura FGC" if inv.get("com_fgc") else "Sem FGC (Risco Emissor)"
        linhas.append(
            f"\n  {i}. {inv['nome']}\n"
            f"     Tipo: {inv['tipo']} | {fgc}\n"
            f"     Emissor: {inv['emissor']} | Distribuidor: {inv['distribuidor']}\n"
            f"     Vencimento: {inv['vencimento']} | Taxa/Rentabilidade: {inv.get('rentabilidade', 'N/D')}"
        )
    return "\n".join(linhas)


@tool
def consultar_indicadores_macro() -> str:
    """
    Consulta os indicadores macroeconômicos oficiais do Brasil (Taxa Selic Meta, CDI Anualizado e IPCA mensal)
    diretamente da API do SGS (Sistema Gerenciador de Séries Temporais) do Banco Central do Brasil.

    REGRA (Guia de Referência Técnica 1.1): O CDI anualizado é calculado como Selic Meta - 0,10 p.p.
    Nunca exibir o CDI diário (~0.05%) como taxa anual.

    Use quando o usuário quiser saber as taxas de juros atuais ou a inflação mais recente para apoiar
    suas análises e comparações de rentabilidade (por exemplo, analisar CDB 110% CDI ou CRA IPCA + 6%).
    """
    try:
        from bcb import sgs
        # Séries: 433 (IPCA mensal), 432 (Selic Meta)
        # Não usamos a série 12 (CDI diário) para evitar exibir taxa diária como anual
        df = sgs.get({'IPCA': 433, 'Selic_Meta': 432}, start='2025-01-01')
        
        if df.empty:
            raise ValueError("Dataframe retornado pelo Banco Central está vazio.")
            
        # Pegar a Selic Meta mais recente
        latest_selic = df['Selic_Meta'].dropna().iloc[-1]
        latest_selic_date = df['Selic_Meta'].dropna().index[-1].strftime('%d/%m/%Y')
        
        latest_ipca = df['IPCA'].dropna().iloc[-1]
        latest_ipca_date = df['IPCA'].dropna().index[-1].strftime('%m/%Y')
        
        # REGRA DE OURO (Guia 1.1): CDI anual = Selic Meta - 0.10 p.p.
        cdi_anual = round(latest_selic - 0.10, 2)
        
        # IPCA acumulado estimado (12 meses = mensal * 12 como proxy rápido)
        ipca_12m_estimado = round(latest_ipca * 12, 2)
        
        return (
            f"INDICADORES MACROECONÔMICOS (Banco Central do Brasil - SGS):\n"
            f"- Taxa Selic Meta: {latest_selic:.2f}% a.a. (vigente em {latest_selic_date})\n"
            f"- Taxa CDI (Anualizada): {cdi_anual:.2f}% a.a. [= Selic - 0,10 p.p., base 252 dias úteis]\n"
            f"- IPCA (Variação Mensal): {latest_ipca:.2f}% (referente a {latest_ipca_date})\n"
            f"- IPCA Acumulado Estimado (12m): ~{ipca_12m_estimado:.2f}%\n\n"
            f"Nota: O CDI âncora investimentos pós-fixados. Um CDB de 110% CDI rende ~{cdi_anual * 1.10:.2f}% a.a. bruto. "
            f"Para títulos IPCA+, o spread real sobre a inflação deve ser analisado separadamente."
        )
    except Exception as e:
        # Fallback com CDI corrigido (Selic 14.75% - 0.10 = 14.65% CDI, referência Mai/2026)
        selic_fallback = 14.75
        cdi_fallback = round(selic_fallback - 0.10, 2)
        return (
            f"INDICADORES MACROECONÔMICOS (Valores de Referência — Fallback Mai/2026):\n"
            f"- Taxa Selic Meta: {selic_fallback:.2f}% a.a.\n"
            f"- Taxa CDI (Anualizada): {cdi_fallback:.2f}% a.a. [= Selic - 0,10 p.p.]\n"
            f"- IPCA (Mensal): ~0.43% (acumulado 12m estimado: ~5.16%)\n\n"
            f"Nota: Não foi possível obter dados ao vivo do BCB (SGS): {str(e)}. "
            f"Os valores acima são estimativas de referência de mercado de Mai/2026."
        )


@tool
def buscar_ofertas_similares_chromadb(query: str, limite: int = 5) -> str:
    """
    Busca ofertas primárias históricas registradas na CVM por similaridade semântica (significado) no ChromaDB.
    Use quando o usuário quiser encontrar emissões parecidas com um determinado tipo, emissor, ou setor
    (ex: 'debêntures de saneamento', 'CRIs com garantia real do setor de logística', 'ofertas do BTG').

    Parâmetros:
        query  - a frase de busca semântica em linguagem natural (ex: 'debênture de energia com boa taxa')
        limite - quantidade máxima de ofertas similares a retornar (padrão: 5)
    """
    try:
        import chromadb
        if not CHROMA_DIR.exists():
            return "O banco vetorial do ChromaDB ainda não foi inicializado."
            
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        
        # Verificar se a coleção existe
        colecoes = [c.name for c in client.list_collections()]
        if "ofertas_cvm_resolucao_160" not in colecoes:
            return "Nenhuma coleção de ofertas da CVM foi indexada no ChromaDB ainda."
            
        collection = client.get_collection("ofertas_cvm_resolucao_160")
        
        results = collection.query(query_texts=[query], n_results=limite)
        
        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            return "Nenhuma oferta similar encontrada no banco vetorial."
            
        linhas = [f"OFERTAS SIMILARES ENCONTRADAS NO CHROMADB (Busca Semântica por: '{query}'):"]
        
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            emissor = meta.get("Nome_Emissor", "N/D")
            tipo = meta.get("Valor_Mobiliario", "N/D")
            data = meta.get("Data_Registro", "N/D")
            lider = meta.get("Nome_Lider", "N/D")
            status = meta.get("Status_Requerimento", "N/D")
            valor = meta.get("Valor_Total_Registrado")
            
            if valor:
                try:
                    valor_val = float(valor)
                    valor_fmt = f"R$ {valor_val/1e6:.1f}M" if valor_val > 0 else "N/D"
                except (ValueError, TypeError):
                    valor_fmt = str(valor)
            else:
                valor_fmt = "N/D"
                
            linhas.append(
                f"\n  {i}. [{tipo}] {emissor}\n"
                f"     Coordenador Líder: {lider} | Registro: {data} | Status: {status} | Volume: {valor_fmt}\n"
                f"     Descrição Analítica: {doc}"
            )
            
        return "\n".join(linhas)
    except Exception as e:
        return f"Erro ao realizar busca semântica no ChromaDB: {str(e)}"


@tool
def consultar_yfinance(ticker: str) -> str:
    """
    Consulta informações financeiras e cotação atual de ativos negociados na B3 (como Ações, FIIs de Renda Fixa ou ETFs)
    através do Yahoo Finance.
    Use quando o usuário pedir o preço atual de tela de um FII de renda fixa listado ou de uma debênture listada no mercado.

    Parâmetros:
        ticker - o símbolo do ativo no Yahoo Finance. Para ações e FIIs da B3, utilize o sufixo '.SA' (ex: 'MXRF11.SA', 'KNIP11.SA', 'VALE3.SA').
    """
    try:
        import yfinance as yf
        
        # Correção amigável de sufixo para ativos brasileiros
        ticker_search = ticker.strip().upper()
        if len(ticker_search) >= 5 and ticker_search[0].isalpha() and ticker_search[4].isdigit() and not ticker_search.endswith(".SA"):
            ticker_search += ".SA"
            
        ativo = yf.Ticker(ticker_search)
        info = ativo.info
        
        if not info or ('regularMarketPrice' not in info and 'previousClose' not in info):
            # Tentar sem o sufixo .SA caso tenha falhado
            if ticker_search != ticker.upper():
                ativo = yf.Ticker(ticker.upper())
                info = ativo.info
                ticker_search = ticker.upper()
                
        if not info or ('regularMarketPrice' not in info and 'previousClose' not in info):
            return f"Não foi possível obter dados para o ticker '{ticker}'. Certifique-se de que o símbolo está correto (ex: 'MXRF11' ou 'KNIP11')."
            
        nome = info.get("longName", info.get("shortName", ticker_search))
        preco = info.get("regularMarketPrice", info.get("previousClose", 0.0))
        fechamento_anterior = info.get("previousClose", 0.0)
        variacao = ((preco - fechamento_anterior) / fechamento_anterior * 100) if fechamento_anterior > 0 else 0.0
        moeda = info.get("currency", "BRL")
        
        dy = info.get("dividendYield")
        dy_txt = f"{dy * 100:.2f}%" if dy else "N/D"
        
        resumo = info.get("longBusinessSummary", "")
        resumo_txt = f"\n     Perfil do Fundo/Empresa: {resumo[:160]}..." if resumo else ""
        
        return (
            f"COTAÇÃO DE MERCADO (Yahoo Finance) — {ticker_search}:\n"
            f"- Ativo: {nome}\n"
            f"- Preço Atual: {moeda} {preco:.2f}\n"
            f"- Variação Diária: {variacao:+.2f}%\n"
            f"- Dividend Yield (LTM): {dy_txt}"
            f"{resumo_txt}"
        )
    except Exception as e:
        return f"Erro ao consultar o Yahoo Finance para o ticker '{ticker}': {str(e)}"


@tool
def calcular_equivalencia_fiscal(taxa_bruta: float, tipo_ativo: str, prazo_dias: int = 720) -> str:
    """
    Motor de Equivalência Fiscal — Calcula e compara a rentabilidade líquida de ativos com IR
    versus ativos isentos, permitindo uma comparação justa 'maçã com maçã'.

    REGRA (Guia de Referência Técnica 1.2): Ativos isentos de IR (LCI, LCA, CRI, CRA, Debêntures
    Incentivadas) não pagam Imposto de Renda para Pessoa Física. Já CDB, Debêntures Comuns e
    Tesouro Direto seguem tabela regressiva: 22,5% (até 180d), 20% (181-360d), 17,5% (361-720d),
    15% (acima de 720d).

    Use quando o usuário quiser comparar retornos entre ativos com tributações diferentes.

    Parâmetros:
        taxa_bruta  - taxa bruta do ativo em % ao ano (ex: 14.0 para 14% a.a.)
        tipo_ativo  - tipo do ativo (ex: 'CDB', 'LCA', 'CRI', 'CRA', 'Debênture Incentivada')
        prazo_dias  - prazo do investimento em dias corridos (padrão: 720 dias = alíquota 17,5%)
    """
    tipo_upper = tipo_ativo.upper().strip()
    setor = get_setor(tipo_upper)

    # Ativos isentos de IR para PF
    ISENTOS = {"LCI", "LCA", "CRI", "CRA", "LIG"}
    eh_isento = any(isento in tipo_upper for isento in ISENTOS)
    eh_isento = eh_isento or "INCENTIVADA" in tipo_upper or "DEBENTURE INCENTIVADA" in tipo_upper

    aliquota = get_aliquota_ir(prazo_dias)
    taxa_liquida = taxa_bruta if eh_isento else calcular_taxa_liquida(taxa_bruta, prazo_dias)

    # Gerar tabela de comparação para todos os prazos
    comparacoes = []
    for dias, aliq in ALIQUOTAS_IR:
        prazo_label = {180: "Curto (<180d)", 360: "Médio (181-360d)", 720: "Longo (361-720d)", 99999: "Muito Longo (>720d)"}[dias]
        liq = taxa_bruta if eh_isento else taxa_bruta * (1 - aliq)
        comparacoes.append(f"  {prazo_label}: {taxa_bruta:.2f}% bruto → {liq:.2f}% líquido (alíq. {aliq*100:.1f}%)")

    # Alerta de High Yield
    alerta = alerta_high_yield(f"{taxa_bruta}%")

    tributacao_txt = "ISENTO de IR (PF)" if eh_isento else f"Tributado — Alíquota {aliquota*100:.1f}% (prazo {prazo_dias}d)"

    linhas = [
        f"MOTOR DE EQUIVALÊNCIA FISCAL — {tipo_ativo.upper()} | Setor: {setor}",
        f"Taxa Bruta Informada: {taxa_bruta:.2f}% a.a.",
        f"Tributação: {tributacao_txt}",
        f"Taxa Líquida (prazo {prazo_dias}d): {taxa_liquida:.2f}% a.a.",
        f"",
        f"Comparativo por prazo (ativo {'isento' if eh_isento else 'tributável'}):",
    ] + comparacoes

    if alerta:
        linhas.append(f"\n{alerta}")

    linhas.append(
        f"\nInsight: Para ser equivalente a este {tipo_ativo} de {taxa_bruta:.2f}% bruto, "
        f"um ativo ISENTO precisaria render apenas {taxa_liquida:.2f}% — "
        f"qualquer LCA/CRI acima disso é matematicamente superior para o investidor PF."
    )

    return "\n".join(linhas)


@tool
def comparar_arbitragem_xp_meelion() -> str:
    """
    Identificação de Oportunidades de Arbitragem — Compara automaticamente as taxas dos ativos
    da carteira recomendada pela XP Investimentos com os investimentos vigentes do Meelion,
    e destaca a 'Melhor Oportunidade do Dia' baseada em Rentabilidade Líquida / Risco.

    REGRA (Guia de Referência Técnica 4): Ativos isentos de IR têm rentabilidade líquida real
    superior a ativos tributados com taxa nominal equivalente. A análise cruza ambas as listas.

    Use quando o usuário quiser descobrir qual plataforma (XP ou Meelion/corretoras) oferece
    a melhor oportunidade atual, ou ao perguntar sobre 'arbitragem', 'melhor investimento do dia',
    ou 'onde investir agora'.
    """
    if not _carteira_xp or not _meelion:
        return "Dados insuficientes: é necessário ter as listas da XP e do Meelion carregadas."

    linhas = ["🔍 ANÁLISE DE ARBITRAGEM — XP Investimentos vs. Meelion (Corretoras)"]
    linhas.append("=" * 60)

    # Processar XP
    linhas.append("\n📌 CARTEIRA XP INVESTIMENTOS (Mai/2026):")
    xp_items = []
    for t in _carteira_xp.get("titulos", []):
        nome = t.get("ativo_emissor", "N/D")
        indexador = t.get("indexador", "")
        taxa_str = t.get("taxa_bruta", "N/D")
        gross_up = t.get("taxa_gross_up", "")
        isento = t.get("isento_ir", False)
        venc = t.get("vencimento", "N/D")
        setor = get_setor(nome)
        alerta = alerta_high_yield(taxa_str)
        ir_txt = "✅ ISENTO IR" if isento else "⚠️ Com IR"
        gross_txt = f" | Gross-up: {gross_up}" if gross_up else ""
        xp_items.append({
            "nome": nome, "taxa": taxa_str, "isento": isento,
            "gross_up": gross_up, "venc": venc, "setor": setor
        })
        linhas.append(f"  • {nome} [{setor}] — {indexador} {taxa_str}{gross_txt} | Venc: {venc} | {ir_txt}")
        if alerta:
            linhas.append(f"    {alerta}")

    # Processar Meelion
    linhas.append("\n📌 OFERTAS MEELION (Corretoras — Mai/2026):")
    meelion_items = []
    for inv in _meelion:
        nome = inv.get("nome", "N/D")
        tipo = inv.get("tipo", "N/D")
        taxa_str = inv.get("tipo", inv.get("rentabilidade", "N/D"))
        emissor = inv.get("emissor", "N/D")
        venc = inv.get("vencimento", "N/D")
        fgc = inv.get("com_fgc", False)
        setor = get_setor(tipo)
        fgc_txt = "🛡️ FGC" if fgc else "⚡ Sem FGC"
        alerta = alerta_high_yield(taxa_str)
        meelion_items.append({
            "nome": nome, "tipo": tipo, "taxa": taxa_str,
            "emissor": emissor, "venc": venc, "fgc": fgc, "setor": setor
        })
        linhas.append(f"  • {nome} [{setor}] — {emissor} | Venc: {venc} | {fgc_txt}")
        if alerta:
            linhas.append(f"    {alerta}")

    # Conclusão de Arbitragem
    linhas.append("\n" + "=" * 60)
    linhas.append("🏆 INSIGHT DE ARBITRAGEM:")
    linhas.append(
        "  Compare as taxas brutas vs. líquidas: ativos ISENTOS de IR (LCA, CRA, CRI, LCI) da "
        "XP precisam render MENOS que um CDB tributado para entregar o mesmo resultado líquido.\n"
        "  Regra rápida: LCA de 13% a.a. ISENTO ≈ CDB de ~15,3% tributado (alíq. 15%, prazo >720d).\n"
        "  Priorize: 1) Segurança (FGC ou Rating), 2) Rentabilidade Líquida, 3) Liquidez."
    )

    return "\n".join(linhas)


@tool
def exportar_relatorio(conteudo_markdown: str, nome_arquivo: str = "relatorio_investimento_nexus.md") -> str:
    """
    Exportação de Relatórios Sob Demanda — Escreve e salva um relatório formatado em Markdown
    em um arquivo físico local na raiz do projeto.

    Use quando o usuário solicitar explicitamente o salvamento de arquivos/relatórios (ex: 'salve um relatório',
    'exporte essa análise', 'gere um arquivo md com esse resumo').

    Parâmetros:
        conteudo_markdown - conteúdo formatado em Markdown a ser salvo no arquivo.
        nome_arquivo      - nome do arquivo de destino (padrão: 'relatorio_investimento_nexus.md').
    """
    try:
        import os
        filename = os.path.basename(nome_arquivo)
        if not filename.endswith(".md") and not filename.endswith(".txt"):
            filename += ".md"
            
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(conteudo_markdown)
            
        return f"Sucesso: Relatório salvo localmente em '{filepath}'."
    except Exception as e:
        return f"Erro ao exportar o relatório: {str(e)}"


@tool
def calcular_ranking_ofertas(intent: str = "padrao", tipo: str = "", limite: int = 10) -> str:
    """
    Calcula o NexusScore e retorna o ranking das melhores ofertas da base CVM.
    O NexusScore (0-100) pondera Rentabilidade Líquida, Segurança/Rating, Eficiência Fiscal,
    Porte do Emissor, Liquidez e ESG, com pesos ajustáveis por perfil de investidor.

    Parâmetros:
        intent — perfil do investidor: 'padrao', 'seguranca', 'rentabilidade', 'renda_mensal', 'agro'
        tipo   — filtrar por tipo de ativo (opcional, ex: 'Debêntures', 'CRI', 'CDB')
        limite — quantidade de resultados no ranking (padrão: 10)
    """
    if _df_cvm.empty:
        return "A base de ofertas CVM está vazia. Execute chroma_indexer.py primeiro."

    # Obter CDI atual
    indicadores = consultar_indicadores_macro.func()
    cdi_atual = 14.65
    for line in indicadores.split("\n"):
        if "CDI (Anualizada)" in line:
            try:
                cdi_str = line.split(":")[1].split("%")[0].strip()
                cdi_atual = float(cdi_str.replace(",", "."))
            except (ValueError, IndexError):
                pass

    df = _df_cvm.copy()
    if tipo:
        df = df[df["Valor_Mobiliario"].map(str).map(normalize_text).str.contains(normalize_text(tipo), case=False, na=False)]

    if df.empty:
        return "Nenhuma oferta encontrada com os filtros informados."

    # Enriquecer dados e calcular score
    resultados = []
    for _, row in df.iterrows():
        setor = get_setor(str(row.get("Valor_Mobiliario", "")))
        ativo_upper = str(row.get("Valor_Mobiliario", "")).upper()
        prazo_dias = 721
        try:
            data_reg = pd.to_datetime(row.get("Data_Registro"), errors="coerce")
            data_enc = pd.to_datetime(row.get("Data_Encerramento"), errors="coerce")
            if pd.notna(data_reg) and pd.notna(data_enc):
                prazo_dias = max((data_enc - data_reg).days, 1)
        except Exception:
            pass
        aliquota = get_aliquota_ir(prazo_dias)
        eh_isento = any(x in ativo_upper for x in ["LCI", "LCA", "CRI", "CRA", "LIG"]) or "INCENTIVADA" in ativo_upper

        spread_map = {"Soberano (Tesouro Nacional)": -0.10, "Bancário/Financeiro": 0.35, "Imobiliário": 1.25, "Agronegócio": 1.25, "Industrial/Infraestrutura": 1.70, "Crédito Privado": 2.20}
        spread = spread_map.get(setor, 1.0)
        taxa_bruta = cdi_atual + spread
        volume = float(row.get("Valor_Total_Registrado", 0) or 0)
        if volume > 0 and volume < 100_000_000:
            taxa_bruta += 0.45
        taxa_liquida = taxa_bruta * (1 - aliquota) if not eh_isento else taxa_bruta

        rating_map = {"Soberano (Tesouro Nacional)": "AAA", "Bancário/Financeiro": "AA", "Imobiliário": "A-", "Agronegócio": "A-", "Industrial/Infraestrutura": "BBB+", "Crédito Privado": "BBB"}
        rating = rating_map.get(setor, "BBB+")
        if volume >= 300_000_000:
            rating = "AA"
        elif volume >= 100_000_000:
            rating = "A"

        sust = str(row.get("Titulo_classificado_como_sustentavel", ""))

        score = calcular_nexus_score(taxa_liquida, cdi_atual, rating, setor, eh_isento, aliquota, volume, sust, intent)

        resultados.append({
            "score": score["score"], "stars": score["stars"], "label": score["label"],
            "emissor": row.get("Nome_Emissor", "N/D"), "tipo": row.get("Valor_Mobiliario", "N/D"),
            "setor": setor, "taxa_bruta": round(taxa_bruta, 2), "taxa_liquida": round(taxa_liquida, 2),
            "rating": rating, "volume": volume, "isento": eh_isento,
        })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    top = resultados[:limite]

    linhas = [
        f"🏆 RANKING NEXUSSCORE — Perfil: {intent.upper()} | CDI: {cdi_atual:.2f}%",
        f"Total de ofertas analisadas: {len(resultados):,}",
    ]
    for i, r in enumerate(top, 1):
        estrelas = "⭐" * r["stars"] + "☆" * (5 - r["stars"])
        ir_txt = "ISENTO" if r["isento"] else "Tributado"
        volume_txt = f" | Volume: R$ {r['volume']/1e6:.1f}M" if r['volume'] > 0 else ""
        linhas.append(
            f"\n  {i}. {estrelas} ({r['score']}/100) — {r['label']}\n"
            f"     {r['tipo']} — {r['emissor']} [{r['setor']}]\n"
            f"     Taxa: {r['taxa_bruta']:.2f}% bruta → {r['taxa_liquida']:.2f}% líquida | Rating: {r['rating']} | {ir_txt}{volume_txt}"
        )

    return "\n".join(linhas)
