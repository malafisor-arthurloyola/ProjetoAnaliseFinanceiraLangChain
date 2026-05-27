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
- [x] **Etapa 3: Ingestão e Estruturação de Dados**
  - Integração do script da CVM para processar ofertas públicas.
  - Setup do scraping/coleta de ofertas vigentes do mercado secundário/primário (XP Investimentos e Meelion) salvas em JSON.
  - Configuração do repositório Git e sincronização com o GitHub.
- [x] **Etapa 4: Construção da Base Vetorial (ChromaDB)**
  - Criação do script `chroma_indexer.py` para carregar as ofertas da CVM.
  - Teste de embeddings locais (`all-MiniLM-L6-v2` via onnxruntime) e correção de tratamento de exceções do ChromaDB.
  - Execução inicial da indexação em lotes de 500 concluída no background.
- [x] **Etapa 5: Implementação do Agente Inteligente (LangChain / LangGraph)**
  - Criação do agente ReAct para receber as perguntas do usuário, pesquisar dados via tools e responder.
  - Implementação das tools: busca de ofertas da CVM, dados macroeconômicos do BCB, equivalência fiscal, arbitragem XP/Meelion e exportação de relatórios.
- [x] **Etapa 6: Desenvolvimento da Interface Visual (Streamlit)**
  - Construção do dashboard interativo com filtros.
  - Integração de gráficos Plotly da evolução de taxas e tabelas.
  - Caixa de chat integrada para o usuário conversar diretamente com o agente de IA.
  - Adição da coluna de "Insight IA" na tabela de emissões CVM gerando avaliações dinâmicas macro.
- [x] **Etapa 7: Testes, Refinamento e Documentação Final**
  - Testes ponta a ponta e finalização do relatório de entrega com base no novo design de UX e nas diretrizes do Guia de Referência Técnica.

---

## 2. Arquitetura da Plataforma e Fluxo de Dados

A plataforma Nexus foi desenhada de forma modular e altamente integrada, visando performance, facilidade de auditoria técnica e governança. O fluxo de dados e controle entre os componentes da plataforma segue a arquitetura descrita abaixo:

```mermaid
graph TD
    User([Usuário]) -->|Filtra UI / Chat| App[app.py - Streamlit Premium UI]
    App -->|Sincroniza Contexto| Agent[agent_engine.py - LangGraph Agent]
    Agent -->|Consome API| BCB[Banco Central SGS - Selic/CDI/IPCA]
    Agent -->|Busca Semântica| Chroma[ChromaDB - ofertas_cvm_resolucao_160]
    Agent -->|Consulta Cotações| YF[Yahoo Finance - yfinance]
    Agent -->|Filtro Rígido| CSV[Data CVM - Pandas CSV]
    Agent -->|Recomendações XP| XP[XP Portfolio JSON]
    Agent -->|Ofertas Ativas| Meelion[Meelion Scraping JSON]
    ChromaIndexer[chroma_indexer.py] -->|Gera Embeddings locais| Chroma
    CSV -->|Alimenta| ChromaIndexer
```

---

## 3. Decisões Metodológicas Adotadas

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

A inteligência da plataforma Nexus é suportada por uma arquitetura híbrida de modelos de linguagem natural (LLM) e representação vetorial (embeddings):

- **LLM Principal: `llama-3.3-70b-versatile` (via Groq API)**
  - Escolhido por sua alta velocidade de inferência e capacidade avançada de raciocínio lógico em cenários complexos (ReAct). Ele analisa as chamadas de ferramentas e formata as respostas baseando-se estritamente nas regras do *Guia de Referência Técnica Nexus*.
  - Configurado com `temperature=0.0` para maximizar a precisão e consistência dos cálculos matemáticos e reduzir o risco de alucinações.
- **Modelo de Embeddings: `all-MiniLM-L6-v2` (Execução Local via ONNX)**
  - Utilizado no script `chroma_indexer.py` para converter os textos descritivos das ofertas da CVM em vetores de 384 dimensões e persistir no ChromaDB.
  - Permite busca semântica em tempo real de forma totalmente local, sem custos de API por token.

---

## 5. Resultados Obtidos e Regras de Negócio Implementadas

A plataforma Nexus foi validada com sucesso e atende a todos os requisitos de inteligência e auditoria exigidos por especialistas:

1. **CDI Anualizado Realista no Cabeçalho e Chat:**
   - O cálculo foi corrigido para refletir a lógica macroeconômica brasileira: `CDI = Selic Meta - 0.10 p.p.`.
   - Isso evita a exibição do CDI diário como se fosse anualizado e garante que os indicadores de rentabilidade no dashboard (KPI do topo) e no chatbot estejam perfeitamente alinhados com o mercado de capitais brasileiro.
2. **Mapeamento Automático de Setores Reais (Sem "N/D"):**
   - Implementação de um motor de mapeamento dinâmico que atribui setores reais de mercado a todos os ativos e emissores: LFT/NTN = *Soberano*, CDB/LCI/LCA = *Bancário*, CRI = *Imobiliário*, CRA = *Agronegócio*, Debêntures = *Infraestrutura* ou *Industrial*.
3. **Motor de Equivalência Fiscal:**
   - Implementação da ferramenta `calcular_equivalencia_fiscal` que calcula a alíquota regressiva do Imposto de Renda (22,5% a 15%) com base no prazo de dias informado pelo usuário e calcula a taxa líquida anualizada.
   - Isso permite fazer comparações justas de rentabilidade entre ativos isentos (CRI, CRA, LCA, LCI) e ativos tributados (CDB, Tesouro).
4. **Alerta de Crédito Elevado (High Yield Guardrails):**
   - Criação de um filtro de risco no chatbot e no dashboard que dispara alertas de "Risco de Crédito Elevado (High Yield)" sempre que uma taxa ofertada excede `CDI + 4.0%` ou taxa prefixada acima de `18.0% a.a.`.
5. **Ferramenta de Arbitragem XP vs. Meelion:**
   - Ferramenta que cruza as ofertas vigentes em tempo real da carteira recomendada da XP com as taxas do mercado secundário do Meelion e identifica a melhor oportunidade de investimento com base na relação Risco/Retorno.
6. **Exportação de Relatórios Sob Demanda:**
   - A ferramenta `exportar_relatorio` permite que o agente salve análises detalhadas solicitadas via chat em arquivos físicos locais (`.md` ou `.txt`) na raiz do projeto, viabilizando o uso prático de relatórios em reuniões executivas.
7. **NexusScore — Sistema de Ranqueamento de Ofertas:**
   - Implementado um score composto (0-100) que pondera 6 dimensões: Rentabilidade Líquida (30%), Segurança/Rating (35%), Eficiência Fiscal (15%), Porte do Emissor (10%), Liquidez Potencial (5%) e ESG (5%).
   - Os pesos são dinâmicos conforme o perfil do investidor (Máxima Segurança, Super Rentabilidade, Renda Mensal, Foco no Agro), ajustando-se automaticamente ao intent selecionado no dashboard.
   - Inclui tratamento de outliers (penalidade de -20 pts para taxas acima de CDI + 4%) e normalização de rating (AAA→BB) com bônus FGC.
   - Exibido na tabela como estrelas (⭐) e no painel de detalhes como score numérico com badge contextual.
   - Nova ferramenta `calcular_ranking_ofertas` exposta ao agente LangGraph para responder perguntas como "qual a melhor oferta?".
   - `calcular_nexus_score()` retorna `dimensoes` dict com scores individuais (0-10) para renderização do radar chart.

8. **UI Redesign Completo (26/05/2026):**
   - **Passo 1 — Treemap + Sunburst**: Gráfico de pizza substituído por Treemap (Setor → Tipo) e Sunburst adicionado como expansor.
   - **Passo 2 — Gauge + Radar + Waterfall**: Painel de detalhes agora exibe gauge do NexusScore, radar das 6 dimensões e waterfall de equivalência fiscal.
   - **Passo 3 — Sparklines em KPIs**: Top Bar reconstruída com `st.columns`; cada KPI (Selic, CDI, IPCA) inclui mini sparkline Plotly.
   - **Passo 4 — Tabela com Paginação + Badges**: Top 100 ofertas por padrão com toggle "mostrar todas"; coluna Volume usa `ProgressColumn`; coluna "High Yield" com badge ⚡.
   - **Passo 5 — CSS Tokens + High Yield Pulse**: Variáveis CSS customizadas (`--accent-blue`, `--success`, `--danger`); animação `hyPulse` em cards de alta rentabilidade; classe `.high-yield-badge` para tags inline.

---

## 6. Indagações e Senso Crítico do Usuário

Este projeto é fruto de uma co-criação activa, caracterizada por importantes direcionamentos técnicos e de segurança estabelecidos pelo usuário. Registramos abaixo os principais pontos levantados, que serviram como princípios orientadores para o desenvolvimento seguro e estruturado:

### 6.1. Governança e Versionamento incremental (Git/GitHub)
- **Direcionamento**: O usuário determinou explicitamente que o código do projeto seja hospedado no repositório público `malafisor-arthurloyola/ProjetoAnaliseFinanceiraLangChain.git` e que cada etapa de desenvolvimento seja commitada de forma incremental ao ser concluída.
- **Impacto**: Isso impede a perda de progresso, facilita a auditoria do código por terceiros e garante as melhores práticas corporativas de CI/CD e versionamento.

### 6.2. Autonomia do Agente vs. Aprovisionamento de Credenciais
- **Direcionamento**: O usuário indagou ativamente sobre como a IA obteria as credenciais de execução da API da Groq (perguntando se deveria fornecê-las ou se o agente faria de forma autônoma) e forneceu sua chave pessoal da Groq (`gsk_...`) de maneira estruturada no `.env`.
- **Impacto**: Garantiu o fornecimento imediato de poder computacional sem interrupções por limites de cota da API, estabelecendo o uso de um modelo altamente sofisticado (`llama-3.3-70b-versatile`).

### 6.3. Segurança Extrema em Downloads e Dependências
- **Direcionamento**: O usuário questionou com rigor: *"Você tomou cuidado com a segurança, né? Baixou apenas coisas seguras, certo?"*
- **Impacto**: Elevou a exigência de conformidade do projeto. Fomos instados a validar a procedência de cada biblioteca instalada e de cada endpoint consumido. O inventário de segurança do projeto é 100% oficial e auditável (CVM Dados Abertos para dados governamentais, CDNs oficiais da Microsoft para o Playwright, PyPI oficial para pacotes Python e APIs verificadas para o Jina Reader).

### 6.4. Blindagem do Conhecimento Contra Limitações Técnicas de Contexto
- **Direcionamento**: O usuário exigiu a anotação contínua do progresso no cofre Obsidian (via Zettelkasten) e a criação de um **Prompt de Resgate** para restauração imediata do contexto da sessão.
- **Impacto**: Esta medida mitiga uma das principais vulnerabilidades dos agentes de IA de hoje — o esquecimento decorrente do esgotamento de janelas de contexto (tokens) ou encerramento abrupto da sessão. O cofre Obsidian atua como uma "memória RAM externa" que permite a qualquer agente de IA ou desenvolvedor parceiro restabelecer o trabalho em minutos.

### 6.5. Senso Crítico sobre Respostas Genéricas vs. Especificidade de Dados
- **Direcionamento**: O usuário apontou que as respostas do chatbot eram excessivamente teóricas e didáticas (explicando conceitos de debêntures e ações de forma enciclopédica), em vez de detalhar as ofertas e ativos reais indexados no banco vetorial da CVM. Ele questionou: *"não é possível que você indexou 13.000 itens e não consegue me dar informações específicas"*.
- **Impacto**: Reformulamos imediatamente o prompt de sistema do agente ReAct para impor **Especificidade Mandatória**. A IA agora é proibida de dar respostas genéricas teóricas sobre finanças, a menos que solicitado. Ela é instruída a apresentar dados tabulares em Markdown legível com o nome do emissor, taxas exatas, volumes financeiros, datas de registro e coordenadores líderes.

### 6.6. Estética do Dashboard (UX/UI) e Fluxo de Design Co-criativo
- **Direcionamento**: O usuário manifestou descontentamento com a organização visual inicial da plataforma ("achei bagunçado o jeito que as informações estão no site"). Ele propôs uma metodologia ágil: gerar um prompt de requisitos UX/UI detalhado sobre o que é esperado do site, utilizá-lo para obter a resposta de uma IA especialista em UX/UI, e retornar os padrões definidos para que eu possa implementá-los na interface final.
- **Impacto**: Aprovamos essa metodologia corporativa de design de interface (UX/UI). Criamos uma especificação funcional detalhada sobre as capacidades e dados da aplicação para que a IA de UX desenhe um layout limpo, intuitivo e com foco em usabilidade de nível premium, minimizando o retrabalho técnico e maximizando a experiência do usuário.

---

Este relatório reflete a evolução contínua da aplicação alinhada ao rigor metodológico e controle de qualidade do usuário.olvedor parceiro restabelecer o trabalho em minutos.

Essas contribuições representam a aplicação prática do **senso crítico e governança** de TI, assegurando que o produto final seja seguro, transparente e de altíssimo nível.

---

## 7. Refatoração de Diretório e Robustez (27/05/2026)

### 7.1. Reorganização da Estrutura de Pastas
Realizada migração para estrutura modular padronizada, isolando o código-fonte em `src/` e a documentação em `docs/`:

| Antes | Depois |
|-------|--------|
| `app.py`, `agent_engine.py`, `tools_custom.py`, `chroma_indexer.py` (raiz) | `src/app.py`, `src/agent_engine.py`, `src/tools_custom.py`, `src/chroma_indexer.py` |
| `README.md`, `AGENTS.md`, `relatorio_*.md` (raiz) | `docs/README.md`, `docs/AGENTS.md`, `docs/relatorio_*.md` |
| `Estudos/` (raiz) | `docs/Estudos/` |
| `GuiaVisual/` (raiz) | `design/GuiaVisual/` |
| `ExemploDeCódigoLangChain/` (raiz) | Removido (código legado) |
| `lixo/` (raiz) | Removido |
| — | `.env.example` (template seguro) |
| — | `requirements.txt` (dependências centralizadas) |

### 7.2. Fallback Automático Groq → Gemini
Implementado sistema de fallback transparente no `agent_engine.py`:
- **Provedor Primário**: Groq (`llama-3.3-70b-versatile`) — alta velocidade de inferência.
- **Fallback**: Google Gemini (`gemini-2.0-flash`) — ativado automaticamente se a chave Groq falhar (rate limit, cota excedida, erro de rede).
- **Status Visível na UI**: O dashboard exibe qual provedor está ativo via `get_provider_status()`.

### 7.3. Tratamento de Erros Amigável
Mensagens de erro no chat foram substituídas por respostas compreensíveis para o usuário final, ocultando tracebacks técnicos e orientando o próximo passo.
