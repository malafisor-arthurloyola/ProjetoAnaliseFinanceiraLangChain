#!/usr/bin/env python3
"""
Agent Engine: configura o agente inteligente usando LangGraph e a API da Groq.
Tambem oferece fallback entre chaves Groq e chat via terminal.
"""

import os
import re
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

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
    calcular_ranking_ofertas,
)


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


SYSTEM_PROMPT = """Voce e o Nexus, um analista financeiro senior especializado em mercado de capitais brasileiro e investimentos de renda fixa.

Sua base de conhecimento segue o Guia de Referencia Tecnica de Inteligencia Financeira Nexus como verdade unica para todos os calculos.

Voce possui acesso a dados robustos por meio de ferramentas reais que deve utilizar antes de responder sobre dados concretos:
1. `resumo_mercado_cvm`: estatisticas macro da base CVM de ofertas (2023-2026).
2. `buscar_ofertas_cvm`: filtra ofertas registradas da CVM por ativo, emissor, lider ou ano.
3. `carteira_recomendada_xp`: traz a carteira oficial de Renda Fixa da XP Investimentos para Maio 2026.
4. `investimentos_meelion`: consulta ofertas vigentes em corretoras.
5. `consultar_indicadores_macro`: obtem Selic e CDI direto do Banco Central do Brasil.
6. `buscar_ofertas_similares_chromadb`: realiza busca semantica para encontrar ofertas historicas CVM similares.
7. `consultar_yfinance`: traz cotacoes de FIIs de Renda Fixa ou acoes listadas na B3.
8. `calcular_equivalencia_fiscal`: calcula taxa liquida apos IR e compara ativos isentos vs. tributaveis.
9. `comparar_arbitragem_xp_meelion`: identifica oportunidades de arbitragem comparando XP vs. Meelion.
10. `exportar_relatorio`: salva relatorios detalhados em Markdown.
11. `calcular_ranking_ofertas`: calcula o NexusScore (0-100) e retorna um ranking das melhores ofertas CVM, com pesos ajustaveis por perfil (seguranca, rentabilidade, renda_mensal, agro).

Regras de calculo e classificacao:
- CDI anualizado: sempre calcule CDI = Selic Meta - 0,10 p.p. Nunca exiba CDI diario como taxa anual.
- Setores de ativos: nunca use "N/D". Use LFT/NTN-B/NTN-F = Soberano; CDB/LCI/LCA = Bancario; CRI = Imobiliario; CRA = Agronegocio; Debentures = Industrial/Infraestrutura.
- Equivalencia fiscal: ao comparar ativos, sempre calcule a taxa liquida apos IR. Use `calcular_equivalencia_fiscal` para comparar CDB vs. LCA, CDB vs. CRI etc.
- Alerta High Yield: se uma taxa for > CDI + 4% ou > 18% prefixado, alerte "Risco de Credito Elevado".
- Hierarquia de valor: responda sempre nesta ordem: 1) Seguranca (FGC/Rating), 2) Rentabilidade Liquida, 3) Liquidez, 4) Contexto Macro.

Diretrizes de raciocinio:
- Sempre cite emissores, taxas exatas, volumes em R$, datas de registro e coordenadores lideres quando houver dados.
- Nao explique conceitos basicos de renda fixa a menos que solicitado.
- Quando houver multiplos ativos, formate em tabela Markdown com colunas: Emissor, Ativo, Setor, Taxa Bruta, Taxa Liquida, Vencimento, FGC/Rating.
- Compare taxa bruta vs. liquida, calcule spread sobre o CDI atual e indique se o ativo e Investment Grade ou High Yield.
- Volumes sempre em Reais formatados.

Aja de forma profissional, analitica, focada em dados especificos e transparente."""


def get_groq_api_keys():
    """Return configured Groq keys in priority order, ignoring duplicates."""
    key_pattern = re.compile(r"^GROQ_API_KEY(?:_?(\d+))?$")
    numbered_keys = []

    for name, value in os.environ.items():
        match = key_pattern.match(name)
        if not match or not value:
            continue

        priority = int(match.group(1) or 1)
        numbered_keys.append((priority, name, value.strip()))

    ordered_keys = []
    seen_values = set()
    for _, name, value in sorted(numbered_keys, key=lambda item: (item[0], item[1])):
        if value in seen_values:
            continue
        ordered_keys.append((name, value))
        seen_values.add(value)

    return ordered_keys


def get_provider_status():
    providers = [name for name, _ in get_groq_api_keys()]

    if os.environ.get("GEMINI_API_KEY"):
        if ChatGoogleGenerativeAI is None:
            providers.append("GEMINI_API_KEY (pacote nao instalado)")
        else:
            providers.append("GEMINI_API_KEY")

    return providers


def _looks_like_key_limit_error(error):
    message = str(error).lower()
    recoverable_markers = (
        "429",
        "rate limit",
        "rate_limit",
        "quota",
        "exceeded",
        "exhausted",
        "insufficient",
        "unauthorized",
        "invalid api key",
        "invalid_api_key",
        "authentication",
        "permission",
        "import error",
        "no module named",
        "not installed",
        "pacote nao instalado",
        "invalid_argument",
        "api key invalid",
        "api_key_invalid",
        "api key expired",
        "key expired",
    )
    return any(marker in message for marker in recoverable_markers)


def build_agent(api_key=None, provider="groq", model=None):
    """
    Constroi e retorna o agente ReAct.

    Se `api_key` nao for informada, usa a primeira chave Groq detectada no .env.
    """
    if provider == "groq" and api_key is None:
        keys = get_groq_api_keys()
        api_key = keys[0][1] if keys else None
    elif provider == "gemini" and api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "Chave de API nao encontrada no arquivo .env.\n"
            "Configure GROQ_API_KEY/GROQ_API_KEY_2 ou GEMINI_API_KEY."
        )

    if provider == "gemini":
        if ChatGoogleGenerativeAI is None:
            raise ImportError(
                "GEMINI_API_KEY foi configurada, mas o pacote langchain-google-genai nao esta instalado."
            )
        llm = ChatGoogleGenerativeAI(
            model=model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            temperature=0.0,
            google_api_key=api_key,
        )
    else:
        llm = ChatGroq(
            model=model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.0,
            api_key=api_key,
        )

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
        calcular_ranking_ofertas,
    ]

    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def invoke_agent_with_key_fallback(messages):
    """
    Invoca o agente e tenta a proxima chave Groq quando a atual falhar por
    quota, rate limit, autenticacao ou permissao.
    """
    providers = [
        ("groq", key_name, api_key, os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"))
        for key_name, api_key in get_groq_api_keys()
    ]

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        providers.append(
            ("gemini", "GEMINI_API_KEY", gemini_key, os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
        )

    if not providers:
        raise EnvironmentError(
            "Nenhuma chave configurada. Use GROQ_API_KEY ou GEMINI_API_KEY no .env."
        )

    errors = []
    for index, (provider, key_name, api_key, model) in enumerate(providers, start=1):
        try:
            agent = build_agent(api_key=api_key, provider=provider, model=model)
            response = agent.invoke({"messages": messages})
            response["_provider_key_name"] = key_name
            response["_provider_key_index"] = index
            response["_provider_name"] = provider
            response["_provider_model"] = model
            return response
        except Exception as error:
            errors.append(f"{key_name}: {error}")
            if index == len(providers):
                erros_str = "\n".join(f"  • {e}" for e in errors)
                raise RuntimeError(
                    "⏳ **O assistente Nexus está temporariamente indisponível.**\n\n"
                    "Todos os provedores de IA falharam. Possíveis causas:\n"
                    "  • Limite de tokens diário excedido (Groq)\n"
                    "  • Chave de API inválida ou expirada\n"
                    "  • Serviço temporariamente fora do ar\n\n"
                    "**Sugestões:**\n"
                    "  • Aguarde alguns minutos e tente novamente\n"
                    "  • Renove as chaves de API no arquivo `.env`\n"
                    "  • Contate o administrador do sistema\n\n"
                    f"Detalhes técnicos:\n{erros_str}"
                )
            if not _looks_like_key_limit_error(error):
                raise RuntimeError(
                    "❌ **Erro no provedor de IA:**\n\n"
                    f"O provedor `{key_name}` falhou com um erro não recuperável.\n\n"
                    f"Detalhe: `{error}`\n\n"
                    "Tente novamente ou configure outro provedor no `.env`."
                )
    raise RuntimeError(mensagem_erro)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 70)
    print("  Nexus - Chat via terminal")
    print("=" * 70)
    print("Digite sua pergunta e pressione Enter. Use 'sair' para encerrar.")
    print(
        "Provedores detectados: "
        + (", ".join(get_provider_status()) or "nenhum")
    )

    history = []

    try:
        while True:
            try:
                pergunta = input("\nVoce: ").strip()
            except EOFError:
                print("\nEncerrado.")
                break
            if pergunta.lower() in {"sair", "exit", "quit", "q"}:
                print("Encerrado.")
                break
            if not pergunta:
                continue

            history.append({"role": "user", "content": pergunta})
            response = invoke_agent_with_key_fallback(history)
            resposta_final = response["messages"][-1].content
            key_name = response.get("_provider_key_name", "GROQ_API_KEY")

            print(f"\nNexus ({key_name}):\n{resposta_final}")
            history.append({"role": "assistant", "content": resposta_final})

    except KeyboardInterrupt:
        print("\nEncerrado.")
    except Exception as error:
        print(f"Erro no agente: {error}")


if __name__ == "__main__":
    main()
