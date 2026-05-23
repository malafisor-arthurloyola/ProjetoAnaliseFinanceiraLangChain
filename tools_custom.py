#!/usr/bin/env python3
"""
Tools Customizadas — Ferramentas que o agente inteligente utiliza para analisar
dados da CVM, do Banco Central (SGS), do ChromaDB (busca semântica), da XP, da Meelion e cotações de mercado.
"""

import json
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
    Consulta os indicadores macroeconômicos oficiais do Brasil (Taxa Selic Meta, CDI e IPCA mensal)
    diretamente da API do SGS (Sistema Gerenciador de Séries Temporais) do Banco Central do Brasil.
    Use quando o usuário quiser saber as taxas de juros atuais ou a inflação mais recente para apoiar
    suas análises e comparações de rentabilidade (por exemplo, analisar CDB 110% CDI ou CRA IPCA + 6%).
    """
    try:
        from bcb import sgs
        # Obter dados recentes do Banco Central
        # Séries: 433 (IPCA mensal), 432 (Selic Meta), 12 (CDI diário)
        df = sgs.get({'IPCA': 433, 'Selic_Meta': 432, 'CDI': 12}, start='2025-01-01')
        
        if df.empty:
            raise ValueError("Dataframe retornado pelo Banco Central está vazio.")
            
        # Pegar as últimas taxas válidas
        latest_selic = df['Selic_Meta'].dropna().iloc[-1]
        latest_selic_date = df['Selic_Meta'].dropna().index[-1].strftime('%d/%m/%Y')
        
        latest_ipca = df['IPCA'].dropna().iloc[-1]
        latest_ipca_date = df['IPCA'].dropna().index[-1].strftime('%m/%Y')
        
        latest_cdi = df['CDI'].dropna().iloc[-1]
        latest_cdi_date = df['CDI'].dropna().index[-1].strftime('%d/%m/%Y')
        
        return (
            f"INDICADORES MACROECONÔMICOS (Banco Central do Brasil - SGS):\n"
            f"- Taxa Selic Meta: {latest_selic:.2f}% a.a. (vigente em {latest_selic_date})\n"
            f"- Taxa CDI (Anualizada): {latest_cdi:.2f}% a.a. (referência de {latest_cdi_date})\n"
            f"- IPCA (Variação Mensal): {latest_ipca:.2f}% (referente a {latest_ipca_date})\n\n"
            f"Nota: A Selic e o CDI ancoram os investimentos pós-fixados, enquanto o IPCA baliza o rendimento "
            f"de títulos de inflação (IPCA + spread)."
        )
    except Exception as e:
        # Fallback robusto caso a API de Séries do BCB falhe ou demore
        return (
            f"INDICADORES MACROECONÔMICOS (Valores de Referência Recentes - Fallback):\n"
            f"- Taxa Selic Meta: 10.50% a.a.\n"
            f"- Taxa CDI (Anualizada): 10.40% a.a.\n"
            f"- IPCA (Mensal): 0.38% (acumulado de 12 meses em ~3.93%)\n\n"
            f"Nota: Não foi possível obter os dados ao vivo do Banco Central (SGS) devido a erro de conexão: {str(e)}. "
            f"Os valores acima representam as últimas taxas estimadas de referência de mercado."
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
