#!/usr/bin/env python3
"""
Agent Engine — Configura o agente inteligente usando LangGraph e a API da Groq.
Conecta as ferramentas customizadas e define as diretrizes de raciocínio lógico.
"""

import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langgraph.prebuilt import create_react_agent

from tools_custom import (
    resumo_mercado_cvm,
    buscar_ofertas_cvm,
    carteira_recomendada_xp,
    investimentos_meelion,
    consultar_indicadores_macro,
    buscar_ofertas_similares_chromadb,
    consultar_yfinance,
    calcular_equivalencia_fiscal,
    comparar_arbitragem_xp_meelion,
    exportar_relatorio,
)

# ─── Configurações ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent

# Garante o carregamento do .env local
load_dotenv(PROJECT_ROOT / ".env")


def build_agent():
    """
    Constrói e retorna o agente inteligente ReAct com a stack de IA:
    - LLM: Llama 3.3 70B (Groq)
    - Graph: React Agent (LangGraph)
    - Tools: CVM, BCB, ChromaDB, XP, Meelion, yfinance
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Chave de API 'GROQ_API_KEY' não encontrada no arquivo .env.\n"
            "Por favor, configure sua chave no arquivo .env na raiz do projeto."
        )

    # Llama 3.3 70B Versatile da Groq
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        api_key=api_key
    )

    # Ferramentas integradas para o agente utilizar
    tools = [
        resumo_mercado_cvm,
        buscar_ofertas_cvm,
        carteira_recomendada_xp,
        investimentos_meelion,
        consultar_indicadores_macro,
        buscar_ofertas_similares_chromadb,
        consultar_yfinance,
        calcular_equivalencia_fiscal,
        comparar_arbitragem_xp_meelion,
        exportar_relatorio,
    ]

    system_prompt = """Você é o Nexus, um analista financeiro sênior especializado em mercado de capitais brasileiro e investimentos de renda fixa.

Sua base de conhecimento segue o **Guia de Referência Técnica de Inteligência Financeira Nexus** como Verdade Única para todos os cálculos.

Você possui acesso a dados robustos por meio de ferramentas reais que deve utilizar antes de responder sobre dados concretos:
1. `resumo_mercado_cvm` — Estatísticas macro da base CVM de ofertas (2023–2026).
2. `buscar_ofertas_cvm` — Filtra ofertas registradas da CVM (por ativo, emissor, líder ou ano).
3. `carteira_recomendada_xp` — Traz a carteira oficial de Renda Fixa da XP Investimentos para Maio 2026.
4. `investimentos_meelion` — Scraping das taxas vigentes em corretoras (CDBs, LCIs, CRAs etc.).
5. `consultar_indicadores_macro` — Obtém Selic e CDI reais direto do Banco Central do Brasil.
6. `buscar_ofertas_similares_chromadb` — Realiza busca semântica para encontrar ofertas históricas CVM similares.
7. `consultar_yfinance` — Traz cotações em tempo real de FIIs de Renda Fixa ou Ações listados na B3.
8. `calcular_equivalencia_fiscal` — Motor de Equivalência Fiscal: calcula taxa líquida após IR e compara ativos isentos vs. tributáveis.
9. `comparar_arbitragem_xp_meelion` — Identifica oportunidades de arbitragem comparando XP vs. Meelion.
10. `exportar_relatorio` — Escreve e salva relatórios detalhados em formato Markdown em arquivo físico local.

### Regras de Cálculo e Classificação (Guia de Referência Técnica — VERDADE Única):
- **CDI Anualizado:** SEMPRE calcule CDI = Selic Meta - 0,10 p.p. Nunca exiba o CDI diário (~0,05%) como taxa anual.
- **Setores de Ativos:** NUNCA use 'N/D'. Use: LFT/NTN-B/NTN-F = Soberano; CDB/LCI/LCA = Bancário; CRI = Imobiliário; CRA = Agronegócio; Debêntures = Industrial/Infraestrutura.
- **Equivalência Fiscal:** Ao comparar ativos, SEMPRE calcule a taxa líquida após IR. Use `calcular_equivalencia_fiscal` para comparar CDB vs. LCA, CDB vs. CRI, etc.
- **Alerta High Yield:** Se uma taxa for > CDI + 4% ou > 18% prefixado, OBRIGATORIAMENTE alerte 'Risco de Crédito Elevado'.
- **Hierarquia de Valor do Especialista:** Responda sempre nesta ordem: 1) Segurança (FGC/Rating), 2) Rentabilidade Líquida, 3) Liquidez, 4) Contexto Macro.

### Diretrizes de Raciocínio (ReAct):
- **Especificidade Mandatória:** Sempre cite emissores, taxas exatas, volumes em R$, datas de registro e coordenadores líderes.
- **Proibição de Respostas Genéricas:** Não explique conceitos básicos de renda fixa a menos que solicitado. Apresente ativos específicos com dados.
- **Apresentação em Tabelas:** Quando houver múltiplos ativos, formate em tabela Markdown com colunas: Emissor, Ativo, Setor, Taxa Bruta, Taxa Líquida, Vencimento, FGC/Rating.
- **Cruzamento Analítico:** Compare sempre taxa bruta vs. líquida. Calcule o spread sobre o CDI atual. Indique se o ativo é Investment Grade ou High Yield.
- **Educação Financeira Contextual:** Mencione FGC, tributação e spread sobre Tesouro apenas quando relevante para a dúvida.
- **Fidelidade de Moeda:** Volumes sempre em Reais formatados (ex: R$ 1,2 bilhão).

Aja de forma extremamente profissional, analítica, focada em dados específicos e transparente."""

    return create_react_agent(llm, tools, prompt=system_prompt)


# ─── Script para Teste Rápido do Agente via Terminal ──────────────────────────

def main():
    print("=" * 70)
    print("  Teste do Agente Inteligente Nexus")
    print("=" * 70)
    
    try:
        agent = build_agent()
        print("✅ Agente construído com sucesso!")
        
        pergunta = "Qual é a taxa Selic Meta atual no Banco Central e quais são 3 títulos recomendados pela XP?"
        print(f"\n💬 Testando pergunta: '{pergunta}'")
        
        for step in agent.stream(
            {"messages": [{"role": "user", "content": pergunta}]},
            stream_mode="updates",
        ):
            if "tools" in step:
                for msg in step["tools"]["messages"]:
                    print(f"\n🔧 [Chama Tool: {msg.name}]")
                    print(f"   Resultado (resumido): {msg.content[:250]}...")
            
            if "agent" in step:
                last_msg = step["agent"]["messages"][-1]
                if last_msg.content:
                    print(f"\n🤖 Resposta Final do Agente:\n{last_msg.content}")
                    
    except Exception as e:
        print(f"❌ Erro ao inicializar o agente: {e}")


if __name__ == "__main__":
    main()
