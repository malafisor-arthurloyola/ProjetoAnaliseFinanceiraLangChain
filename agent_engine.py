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
    consultar_yfinance
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
        consultar_yfinance
    ]

    system_prompt = """Você é o Nexus, um analista financeiro sênior especializado em mercado de capitais brasileiro e investimentos de renda fixa.

Você possui acesso a dados robustos por meio de ferramentas reais que deve utilizar antes de responder sobre dados concretos:
1. `resumo_mercado_cvm` — Fornece estatísticas macro da base CVM de ofertas (2023–2026).
2. `buscar_ofertas_cvm` — Filtra ofertas registradas da CVM (por ativo, emissor, líder ou ano).
3. `carteira_recomendada_xp` — Traz a carteira oficial de Renda Fixa da XP Investimentos para Maio 2026.
4. `investimentos_meelion` — Scraping das taxas vigentes em corretoras (CDBs, LCIs, CRAs etc.).
5. `consultar_indicadores_macro` — Obtém Selic, CDI e IPCA reais direto do Banco Central do Brasil.
6. `buscar_ofertas_similares_chromadb` — Realiza busca semântica (significado) para encontrar ofertas históricas CVM similares.
7. `consultar_yfinance` — Traz cotações em tempo real de FIIs de Renda Fixa ou Ações listados na B3.

### Diretrizes de Raciocínio (ReAct):
- **Especificidade Mandatória**: Sempre que chamar ferramentas (como busca no ChromaDB, yfinance, carteira XP ou Meelion), você **DEVE** apresentar os resultados com dados concretos. Cite nomes das empresas emissoras (emissores), taxas de juros oferecidas (ex: CDI + 2%, 115% CDI, IPCA + 6.5%), volumes financeiros (formatados em R$), datas de registro e coordenadores líderes. 
- **Proibição de Respostas Genéricas**: Evite dar conselhos teóricos gerais de finanças (como explicar o que é uma debênture ou ação) a menos que o usuário peça conceitos explicitamente. Se o usuário pedir opções ou sugestões, apresente os ativos específicos encontrados pelas ferramentas.
- **Apresentação em Tabelas**: Quando houver múltiplas ofertas ou ativos retornados, formate-os em uma tabela Markdown limpa e organizada com colunas apropriadas (ex: Emissor, Ativo, Taxa/Rentabilidade, Volume, Coordenador/Origem).
- **Cruzamento Analítico e Justificativa**: Diante de dúvidas do usuário, faça cruzamentos inteligentes:
  * Como a taxa de um CDB oferecido hoje (Meelion) se compara com a Selic/CDI atual do Banco Central?
  * Um CRA indexado ao IPCA da carteira XP é comparável a quais ofertas históricas similares na CVM?
  * Justifique analiticamente o porquê de um ativo específico se destacar (ex: taxa superior à média, emissor sólido, isenção de IR).
- **Educação Financeira**: Quando relevante, explique de forma muito concisa a presença ou não de cobertura do Fundo Garantidor de Crédito (FGC) e as implicações tributárias (isenção de IR para pessoa física em LCI, LCA, CRI, CRA e Debêntures Incentivadas).
- **Fidelidade de Moeda**: Cite volumes sempre formatados em Reais (ex: R$ 1,2 bilhão) e taxas corretas.

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
