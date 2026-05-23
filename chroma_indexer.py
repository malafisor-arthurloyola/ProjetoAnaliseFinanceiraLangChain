#!/usr/bin/env python3
"""
ChromaDB Indexer — Indexa ofertas da CVM no banco vetorial para busca semântica.

Lê o CSV da Resolução 160 da CVM (2023-2026), converte cada oferta em um
documento textual descritivo e armazena no ChromaDB com embeddings locais.

Uso:
    python chroma_indexer.py

O banco é persistido em ./chroma_db/ e pode ser consultado pelo agente.
"""

import os
import sys
import pandas as pd
import chromadb
from pathlib import Path

# ─── Configuração ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "cvm"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

CSV_FILE = DATA_DIR / "oferta_resolucao_160.csv"

COLLECTION_NAME = "ofertas_cvm_resolucao_160"

# Colunas relevantes para gerar o texto descritivo de cada oferta
COLS_TEXTO = [
    "Nome_Emissor", "Valor_Mobiliario", "Nome_Lider", "Valor_Total_Registrado",
    "Data_Registro", "Data_Encerramento", "Status_Requerimento", "Publico_alvo",
    "Titulo_incentivado", "Titulo_classificado_como_sustentavel", "Tipo_lastro",
    "Regime_distribuicao", "Bookbuilding", "Destinacao_recursos",
    "Descricao_garantias", "Tipo_Oferta",
]

# Colunas usadas como metadados estruturados (filtráveis no ChromaDB)
COLS_META = [
    "Nome_Emissor", "Valor_Mobiliario", "Nome_Lider", "Data_Registro",
    "Status_Requerimento", "Publico_alvo", "Titulo_incentivado",
    "Titulo_classificado_como_sustentavel", "Tipo_Oferta",
    "Valor_Total_Registrado",
]


# ─── Funções ──────────────────────────────────────────────────────────────────

def carregar_csv(caminho: Path) -> pd.DataFrame:
    """Carrega o CSV da CVM e faz limpeza básica."""
    print(f"📂 Carregando {caminho.name}...")
    df = pd.read_csv(caminho, sep=";", encoding="utf-8", on_bad_lines="skip")
    print(f"   → {len(df):,} registros, {len(df.columns)} colunas")
    return df


def gerar_texto_oferta(row: pd.Series) -> str:
    """Converte uma linha do DataFrame em texto descritivo para embedding."""
    partes = []

    emissor = row.get("Nome_Emissor", "N/D")
    tipo = row.get("Valor_Mobiliario", "N/D")
    lider = row.get("Nome_Lider", "N/D")
    valor = row.get("Valor_Total_Registrado")
    data_reg = row.get("Data_Registro", "N/D")
    status = row.get("Status_Requerimento", "N/D")
    publico = row.get("Publico_alvo", "N/D")
    incentivado = row.get("Titulo_incentivado", "N/D")
    sustentavel = row.get("Titulo_classificado_como_sustentavel", "N/D")
    lastro = row.get("Tipo_lastro", "")
    regime = row.get("Regime_distribuicao", "")
    destinacao = row.get("Destinacao_recursos", "")
    garantias = row.get("Descricao_garantias", "")

    # Formatar valor
    if pd.notna(valor) and valor > 0:
        valor_fmt = f"R$ {valor/1e6:.1f} milhões"
    else:
        valor_fmt = "valor não informado"

    incentivado_txt = "Sim" if incentivado == "S" else "Não"
    sustentavel_txt = "Sim" if sustentavel == "S" else "Não"

    partes.append(f"Oferta de {tipo} emitida por {emissor}.")
    partes.append(f"Coordenada por {lider}.")
    partes.append(f"Volume total: {valor_fmt}.")
    partes.append(f"Data de registro: {data_reg}. Status: {status}.")
    partes.append(f"Público-alvo: {publico}.")
    partes.append(f"Título incentivado: {incentivado_txt}. Sustentável (ESG): {sustentavel_txt}.")

    if pd.notna(lastro) and lastro:
        partes.append(f"Tipo de lastro: {lastro}.")
    if pd.notna(regime) and regime:
        partes.append(f"Regime de distribuição: {regime}.")
    if pd.notna(destinacao) and destinacao:
        partes.append(f"Destinação dos recursos: {destinacao}.")
    if pd.notna(garantias) and garantias:
        partes.append(f"Garantias: {garantias}.")

    return " ".join(partes)


def gerar_metadados(row: pd.Series) -> dict:
    """Extrai metadados estruturados de uma linha para filtros no ChromaDB."""
    meta = {}
    for col in COLS_META:
        val = row.get(col)
        if pd.notna(val):
            # ChromaDB aceita apenas str, int, float, bool nos metadados
            if isinstance(val, (int, float)):
                meta[col] = val
            else:
                meta[col] = str(val)
    return meta


def indexar_no_chromadb(df: pd.DataFrame):
    """Cria a coleção no ChromaDB e indexa todos os registros."""
    print(f"\n🧠 Inicializando ChromaDB em {CHROMA_DIR}...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Deletar coleção antiga se existir (para reindexação limpa)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"   🗑️  Coleção anterior '{COLLECTION_NAME}' removida.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Ofertas CVM Resolução 160 (2023-2026)"}
    )
    print(f"   ✅ Coleção '{COLLECTION_NAME}' criada.")

    # Gerar documentos e metadados
    print(f"\n📝 Gerando documentos descritivos para {len(df):,} ofertas...")
    documentos = []
    metadados = []
    ids = []

    for idx, row in df.iterrows():
        texto = gerar_texto_oferta(row)
        meta = gerar_metadados(row)
        doc_id = f"cvm_r160_{idx}"

        documentos.append(texto)
        metadados.append(meta)
        ids.append(doc_id)

    # Inserir em batches de 500 (ChromaDB tem limite por operação)
    BATCH_SIZE = 500
    total_batches = (len(documentos) + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n📥 Indexando {len(documentos):,} documentos em {total_batches} batches...")
    for i in range(0, len(documentos), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        fim = min(i + BATCH_SIZE, len(documentos))
        collection.add(
            documents=documentos[i:fim],
            metadatas=metadados[i:fim],
            ids=ids[i:fim],
        )
        print(f"   Batch {batch_num}/{total_batches}: {fim - i} documentos indexados ({fim:,}/{len(documentos):,})")

    print(f"\n✅ Indexação completa! {collection.count():,} documentos no ChromaDB.")
    return collection


def testar_busca(collection):
    """Executa uma busca de teste para validar a indexação."""
    print(f"\n🔍 Teste de busca semântica...")

    queries = [
        "debêntures de energia elétrica",
        "CRI de crédito imobiliário com garantia",
        "ofertas do BTG Pactual em 2025",
    ]

    for query in queries:
        results = collection.query(query_texts=[query], n_results=3)
        print(f"\n   Query: \"{query}\"")
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            emissor = meta.get("Nome_Emissor", "?")
            tipo = meta.get("Valor_Mobiliario", "?")
            data = meta.get("Data_Registro", "?")
            print(f"   {i+1}. [{tipo}] {emissor} ({data})")
            print(f"      {doc[:120]}...")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  ChromaDB Indexer — Ofertas CVM Resolução 160")
    print("=" * 70)

    if not CSV_FILE.exists():
        print(f"\n❌ Arquivo não encontrado: {CSV_FILE}")
        print("   Execute primeiro o script de download da CVM.")
        sys.exit(1)

    df = carregar_csv(CSV_FILE)
    collection = indexar_no_chromadb(df)
    testar_busca(collection)

    print(f"\n{'=' * 70}")
    print(f"  ✅ Base vetorial pronta em: {CHROMA_DIR.absolute()}")
    print(f"  📊 Total de documentos: {collection.count():,}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
