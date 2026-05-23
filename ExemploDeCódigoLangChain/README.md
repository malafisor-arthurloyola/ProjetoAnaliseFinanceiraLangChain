# Aula — Agente de Análise de Ofertas Primárias com LangChain

Material de apoio para a aula sobre construção de agentes inteligentes aplicados ao mercado financeiro brasileiro, utilizando LangChain como framework de orquestração.

## Sobre a Aula

Esta aula demonstra como construir um agente capaz de coletar, consolidar e analisar ofertas primárias de diferentes instituições financeiras (BTG Pactual, XP, Itaú, etc.), identificando padrões e oportunidades relativas entre taxas.

O repositório contém o código-base e os dados que serão utilizados durante a prática.

## O que tem aqui

### 📄 Instruções para Agentes
- **`AGENTS.md`** — Contém as regras e padrões que o agente (IA) deve seguir durante o desenvolvimento, incluindo uso obrigatório do MCP Server do LangChain para consulta à documentação oficial.

### 🔧 Configuração
- **`opencode.json`** — Configuração do MCP Server para acesso à documentação do LangChain diretamente no ambiente.

### 📥 Extração de Dados
- **`src/data_ingestion/download_cvm_ofertas.py`** — Script que baixa e analisa os dados oficiais de Ofertas Públicas de Distribuição da CVM. Durante a aula, vamos rodar esse script ao vivo para mostrar:
  - Download do ZIP da CVM (5.1 MB)
  - Extração de 2 datasets: `oferta_distribuicao.csv` (48.926 registros) e `oferta_resolucao_160.csv` (13.015 registros)
  - Análise das colunas mais relevantes para o projeto
  - Comparação entre instituições líderes (BTG, XP, Itaú, Singulare, etc.)

### 🌐 Scraping com Playwright (Meelion)
- **`src/data_ingestion/scrape_meelion.py`** — Demonstra como contornar bot-protection e extrair dados de um comparador de investimentos real usando Playwright:
  - Abre o Firefox visível
  - Passa a bot-protection do site sem configuração extra
  - Extrai os 9 cards gratuitos: nome, tipo, FGC, emissor, distribuidor, vencimento
  - Salva em `data/meelion/investimentos_page1.json`
  - Comentários no código descrevem evoluções futuras: login, paginação completa (4196 investimentos), filtros via URL e paralelismo assíncrono

### 🤖 Extração com LLM (LangChain + Pydantic)
- **`src/data_ingestion/extract_renda_fixa.py`** — Demonstra como extrair dados estruturados de artigos financeiros usando:
  - **r.jina.ai** para converter páginas web em markdown limpo
  - **Pydantic** para definir o schema de saída (títulos de renda fixa)
  - **`with_structured_output()`** do LangChain para forçar o ChatGroq a retornar JSON validado
  - Resultado: carteira completa com ativo, vencimento, indexador, taxa, duration, isento IR, etc.

### 🤖 Agente LangChain (LangGraph)
- **`src/agents/agent.py`** — Demonstra a anatomia completa de um agente moderno com LangGraph:
  - **Tools** — 4 ferramentas que consultam dados reais (CVM, XP, Meelion)
  - **LLM** — ChatGroq (Llama 3.3 70B) decide qual tool usar e quando parar
  - **`create_react_agent`** — loop ReAct (Reasoning + Acting) do LangGraph
  - Interface de chat interativo no terminal
  - Comentários descrevem evoluções: memória persistente, ChromaDB, Streamlit

### 🔍 Teste de Scraping
- **`scraping-inicial.py`** — Script que testa a acessibilidade de diversas fontes de dados via r.jina.ai (Jina Reader). Útil para entender quais fontes são viáveis para scraping e quais são bloqueadas.

### 1. Configurar ambiente

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Criar arquivo `.env`:
```bash
GROQ_API_KEY=sua_chave_aqui
```

### 3. Rodar os scripts da aula

```bash
# Baixar e analisar dados da CVM
python src/data_ingestion/download_cvm_ofertas.py

# Extrair carteira de renda fixa com LLM (requer GROQ_API_KEY)
python src/data_ingestion/extract_renda_fixa.py

# Scraper Meelion — abre Firefox e extrai investimentos (requer: playwright install firefox)
python src/data_ingestion/scrape_meelion.py

# Agente interativo — chat com os dados reais (requer GROQ_API_KEY)
python src/agents/agent.py

# Testar fontes de scraping
python scraping-inicial.py
```

## Dados Disponíveis

Após rodar o script de extração, os dados ficam em `data/cvm/`:

| Dataset | Registros | Colunas | Período |
|---------|-----------|---------|---------|
| `oferta_distribuicao.csv` | 48.926 | 76 | 1989–2026 |
| `oferta_resolucao_160.csv` | 13.015 | 71 | 2023–2026 |

## Fontes de Dados

| Fonte | Tipo | Status |
|-------|------|--------|
| CVM Dados Abertos | API/CSV | ✅ Funcionando |
| BCB SGS (Selic, IPCA) | API JSON | ✅ Funcionando |
| BCB Relatório Focus | Web | ⚠️ Parcial |
| Meelion | Web (Playwright) | ✅ Funcionando |
| XP / BTG / Itaú | Web | ⚠️ Parcial via r.jina.ai |
| ANBIMA | Web | ⚠️ Parcial |
| B3 | Web/API | ❌ Bloqueado |
| Investing.com | Web | ❌ Bloqueado |

## Stack

| Camada | Tecnologia |
|--------|------------|
| Orquestração | LangChain, LangGraph |
| LLM | ChatGroq (Meta, Mistral via Groq API) |
| Vector Store | ChromaDB |
| Interface | Streamlit |
| Linguagem | Python 3.12+ |

## Estrutura do Repositório

```
├── AGENTS.md                          # Regras para o agente IA
├── opencode.json                      # Configuração MCP
├── scraping-inicial.py                # Teste de fontes de scraping
├── requirements.txt                   # Dependências
├── src/
│   ├── agents/
│   │   └── agent.py                   # Agente ReAct com LangGraph + 4 tools
│   └── data_ingestion/
│       ├── download_cvm_ofertas.py    # Download e análise CVM
│       ├── extract_renda_fixa.py      # Extração com LLM + Pydantic
│       └── scrape_meelion.py          # Scraping com Playwright (Meelion)
├── data/
│   └── cvm/                           # Dados baixados (gerado pelo script)
└── context/
    ├── projeto.md                     # Descrição do projeto base
    ├── scraping-options.md            # Fontes de scraping mapeadas
    └── notes.txt
```

## Documentação

- **`AGENTS.md`** — Regras e instruções para o agente, incluindo uso do MCP LangChain
- **`context/projeto.md`** — Descrição completa do projeto que os alunos vão desenvolver
- **`context/scraping-options.md`** — Fontes de scraping mapeadas e categorizadas
