# 📝 Relatório de Desenvolvimento — Agente Inteligente de Ofertas Primárias (BTG Pactual)

Este documento registra o processo de desenvolvimento, decisões técnicas e metodológicas, fontes de dados, modelos e resultados obtidos na construção do Agente Inteligente de Análise e Contextualização de Ofertas Primárias.

---

## 1. Etapas de Desenvolvimento

Abaixo está o cronograma e o status das etapas planejadas para a entrega expressa do projeto:

- [x] **Etapa 1: Alinhamento de Conceitos e Arquitetura**
  - Entendimento do TAPI, mapeamento dos conceitos financeiros e das ferramentas de IA/Web.
  - Setup do cofre Obsidian Zettelkasten para persistência de conhecimento.
- [x] **Etapa 2: Configuração de Ambiente e Dependências**
  - Criação do ambiente virtual (`venv`) e instalação dos pacotes necessários (`streamlit`, `chromadb`, `python-bcb`, `yfinance`, `langchain-community`, `langchain-chroma`).
- [ ] **Etapa 3: Ingestão e Estruturação de Dados**
  - Integração do script da CVM para baixar e processar ofertas públicas.
  - Setup do scraping/coleta de ofertas vigentes de mercado.
  - Conexão com a API do Banco Central (SGS) para obter IPCA, Selic e CDI.
- [ ] **Etapa 4: Construção da Base Vetorial (ChromaDB)**
  - Armazenamento das emissões passadas e setup de busca semântica para encontrar comparativos históricos.
- [ ] **Etapa 5: Implementação do Agente Inteligente (LangChain / LangGraph)**
  - Criação do agente ReAct para receber as perguntas do usuário, pesquisar dados via tools e responder.
  - Implementação das tools: busca de ofertas da CVM, dados macroeconômicos do BCB e comparativos no ChromaDB.
- [ ] **Etapa 6: Desenvolvimento da Interface Visual (Streamlit)**
  - Construção do dashboard interativo com filtros.
  - Integração de gráficos Plotly da evolução de taxas e tabelas st-aggrid.
  - Caixa de chat integrada para o usuário conversar diretamente com o agente de IA.
- [ ] **Etapa 7: Testes, Refinamento e Documentação Final**
  - Testes ponta a ponta e finalização do relatório de entrega.

---

## 2. Decisões Metodológicas Adotadas

### 2.1. Arquitetura do Agente: ReAct (Reasoning + Acting)
Optou-se pelo padrão **ReAct** utilizando a biblioteca **LangGraph**. Esse padrão permite que o modelo (LLM) decida dinamicamente qual ferramenta usar, analise o resultado retornado por ela, reformule seu raciocínio e decida o próximo passo. Isso é crucial para responder perguntas complexas do tipo: *"Como as taxas de CDB indexadas ao IPCA mudaram após a última decisão do Copom sobre a taxa Selic?"*

### 2.2. Armazenamento e Recuperação Semântica (ChromaDB)
Para comparar ofertas novas com ofertas passadas, usamos o **ChromaDB**. Ao invés de fazer buscas exatas (ex: buscar apenas por texto exato do nome da empresa), o ChromaDB nos permite fazer buscas semânticas (ex: buscar "empresas de saneamento com perfil de risco similar").

### 2.3. Coleta Híbrida de Dados
- **Dados Históricos e Oficiais:** CVM Dados Abertos (CSV/ZIP).
- **Dados de Mercado Atuais (Scraping):** Playwright para simular navegação real e extrair taxas do Meelion.
- **Dados Macroeconômicos:** python-bcb direto da API oficial do Banco Central.

### 2.4. Uso de Skills/Ferramentas Prontas da Comunidade (LangChain Community)
Para evitar "reinventar a roda" e garantir estabilidade e agilidade (dado o prazo reduzido), decidimos integrar ferramentas consagradas do ecossistema LangChain e bibliotecas de mercado:
- **`python-bcb`:** Wrapper oficial para a API de Séries Temporais (SGS) do Banco Central, garantindo dados confiáveis de Selic, CDI e IPCA.
- **`yfinance` (Yahoo Finance):** Para consultas rápidas de índices de mercado (como o Ibovespa, dólar) e comportamento de FIIs de Renda Fixa ou Debêntures listadas.
- **`DuckDuckGoSearchRun` ou `Jina Reader`:** Para permitir que o agente busque notícias macroeconômicas de última hora na internet e converta páginas de portais de notícias em Markdown limpo para o LLM interpretar.

### 2.5. Layout e Interface Unificada (Streamlit)
Adotou-se um layout de tela única no Streamlit: os filtros, gráficos interativos (Plotly) e a tabela (AgGrid) ficam no topo/esquerda, enquanto o chat com a IA fica na lateral/baixo. Isso permite que o usuário veja os dados reais e pergunte diretamente sobre eles ao mesmo tempo.

### 2.6. Integração do Contexto de UI com a IA
A IA receberá os filtros selecionados na interface do usuário (UI) como contexto de sistema em cada mensagem. Assim, se o usuário filtrar "CDB" e perguntar "Por que essas taxas estão altas?", a IA saberá exatamente sobre quais CDBs o usuário está falando.

### 2.7. Geração de Relatórios Sob Demanda
Embora o foco seja o chat interativo, o agente será equipado com a capacidade de exportar relatórios analíticos formatados (Markdown/TXT) caso o usuário explicitamente solicite no chat.

### 2.8. Estética Visual: Sleek Dark Mode
Para garantir um visual moderno e "Premium", o painel utilizará um tema escuro (Dark Mode) com elementos visuais sofisticados, neons e efeito translúcido (glassmorphism) nos componentes.

### 2.9. Gestão de Conhecimento com Obsidian (Zettelkasten)
Como salvaguarda contra esgotamento de tokens ou reinicialização de sessões de IA, foi estruturado um cofre Obsidian local (`C:\Users\Inteli\Documents\BTG informações`) seguindo o método Zettelkasten de notas atômicas interligadas.
- **MOC (Map of Content)**: Serve como índice de entrada do cofre.
- **Notas Atômicas**: Criadas com metadados estruturados (YAML) e links bidirecionais (`[[Conceito]]`), cobrindo desde Renda Fixa, CVM e Indexadores até decisões técnicas de arquitetura (LangChain, ChromaDB, Streamlit).
- **Objetivo**: Garantir que todo o contexto de desenvolvimento e conceitos de negócios permaneça persistido e de fácil leitura para o desenvolvedor humano e agentes de IA assistentes.

---

## 3. Fontes de Dados Utilizadas

| Fonte | Tipo de Acesso | Dados Extraídos | Frequência de Atualização |
|-------|----------------|-----------------|---------------------------|
| **CVM (Dados Abertos)** | CSV / ZIP Download | Histórico de ofertas de distribuição de debêntures, CRIs, CRAs e notas comerciais. | Diária (oficial) |
| **Banco Central (SGS)** | API JSON (python-bcb) | Taxas históricas da Selic, IPCA mensal e CDI. | Diária / Mensal |
| **Meelion** | Web Scraping (Playwright) | Ofertas vigentes de Renda Fixa de mercado secundário/primário em corretoras. | Tempo real / Sob demanda |

---

## 4. Modelos Implementados

*Esta seção será detalhada após a definição dos prompts do agente e a escolha do modelo da Groq (ex: Llama 3.3 70B).*

---

## 5. Resultados Obtidos

*Esta seção descreverá o comportamento do sistema final, incluindo capturas de tela do dashboard Streamlit e exemplos de perguntas respondidas com sucesso pelo agente.*
