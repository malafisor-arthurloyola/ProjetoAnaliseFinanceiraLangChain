---
sidebar_position: 1
sidebar_label: Fontes de Estudo
title: Fontes de Estudo
---

# Fontes de Estudo

Recursos de estudo para as tecnologias utilizadas no projeto do BTG Pactual para fazer um agente inteligente de análise e contextualização de ofertas primárias.

As ferramentas estão organizadas em duas categorias: principais, que formam o núcleo do sistema, e complementares, que estendem suas capacidades em áreas específicas.

---

## Ferramentas Principais

### LangChain

Parte central do projeto: orquestra o agente, conecta o modelo de linguagem às ferramentas de coleta e análise, e gerencia a memória vetorial para recuperação semântica de comparáveis históricos.

#### Documentação

- [Visão geral](https://docs.langchain.com/oss/python/langchain/overview) — Arquitetura do framework e como seus componentes se conectam.
- [Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart) — Primeira aplicação funcional passo a passo. **Ponto de partida recomendado.**
- [Agents](https://python.langchain.com/docs/concepts/agents/) — Como criar agentes que tomam decisões e encadeiam ações de forma autônoma.
- [Tools](https://python.langchain.com/docs/concepts/tools/) — Integração do agente com funções externas como scraping, APIs e bancos de dados.
- [GitHub oficial](https://github.com/langchain-ai/langchain) — Código-fonte e exemplos prontos para explorar.

#### Vídeos

- [LangChain IA](https://www.youtube.com/watch?v=7L0MnVu1KEo) — Introdução.
- [Tutorial básico](https://www.youtube.com/watch?v=nXynNB6XzAM) — Guia direto ao ponto para primeiros contatos.
- [Criando Agentes de IA](https://www.youtube.com/watch?v=jnEmWGmXx8Y) — Implementação prática de agentes com ferramentas customizadas.
- [Curso COMPLETO LangChain](https://www.youtube.com/watch?v=S98c7uxCluA) — Do básico ao avançado, cobrindo todos os componentes principais.

---

### Streamlit

Interface do projeto: o dashboard interativo que permite ao usuário explorar diferenças de taxas por instituição, filtrar por tipo de ativo, indexador e período, e visualizar os insights gerados pelo agente.

#### Documentação

- [Documentação principal](https://docs.streamlit.io/) — Central da ferramenta com todos os guias disponíveis.
- [Get Started](https://docs.streamlit.io/get-started) — Primeiro app funcional em minutos. **Ponto de partida recomendado.**
- [API Reference](https://docs.streamlit.io/develop/api-reference) — Catálogo completo de componentes disponíveis (gráficos, tabelas, filtros, etc.).
- [Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state) — Gerenciamento de estado entre interações do usuário — necessário para filtros dinâmicos no dashboard.
- [Cache Data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data) — Otimização de performance para evitar reprocessar dados a cada interação.
- [GitHub oficial](https://github.com/streamlit/streamlit) — Código-fonte e exemplos.

#### Vídeos

- [Streamlit em 10 min](https://www.youtube.com/watch?v=zxA97KcUm1Q) — Introdução rápida aos conceitos essenciais.
- [Dashboard em 30 min](https://www.youtube.com/watch?v=0lYBYYHBT5k) — Criação prática de um dashboard completo.
- [Alternativa ao Power BI](https://www.youtube.com/watch?v=P6E_Kts9pxE) — Como construir dashboards analíticos com Python puro.
- [Dashboards profissionais](https://www.youtube.com/watch?v=M5xz2PS_RsE) — Layouts avançados e boas práticas de apresentação.
- [Curso completo](https://www.youtube.com/watch?v=TRvmAzXUUfg) — Conteúdo aprofundado para ir além do básico.

---

## Ferramentas Complementares

### Playwright

Usado em conjunto com o LangChain para a coleta automatizada de dados em plataformas que não disponibilizam APIs públicas.

- [Introdução](https://playwright.dev/python/docs/intro) — Setup e primeiros scripts.
- [Locators](https://playwright.dev/python/docs/locators) — Seleção de elementos da página.
- [Codegen](https://playwright.dev/python/docs/codegen) — Gera código automaticamente a partir da navegação gravada.
- [Automação Python](https://www.youtube.com/watch?v=1NNMzL4W8ws) — Tutorial prático focado em Python.

---

### Plotly

Usado dentro do Streamlit para gerar os gráficos interativos do dashboard.

- [Plotly Express](https://plotly.com/python/plotly-express/) — API simplificada para criação rápida de visualizações.
- [Time Series](https://plotly.com/python/time-series/) — Gráficos de séries temporais, aplicável à evolução das taxas no projeto.
- [Criar gráficos](https://www.youtube.com/watch?v=_hCkW5Zli_k) — Tutorial direto e prático.

---

### python-bcb

Usado junto ao LangChain para coletar indicadores macroeconômicos do Banco Central (Selic, IPCA, CDI, câmbio).

- [Documentação oficial](https://wilsonfreitas.github.io/python-bcb/) — Guia completo com todos os módulos disponíveis.
- [SGS — Séries Temporais](https://wilsonfreitas.github.io/python-bcb/sgs.html) — Como buscar séries como IPCA, Selic e CDI em um DataFrame pandas.
- [Catálogo SGS (BCB)](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries) — Encontre o código numérico de qualquer indicador disponível.
- [Coletando Dados Do Banco Central Usando o Python](https://www.youtube.com/watch?v=7MYWTp_TZNU) — Introdução prática ao SGS.

---

### st-aggrid

Extensão do Streamlit para tabelas interativas com filtragem, ordenação e seleção de linhas.

- [GitHub oficial](https://github.com/PablocFonseca/streamlit-aggrid) — Código-fonte e exemplos de uso.
- [Documentação oficial](https://streamlit-aggrid.readthedocs.io/en/docs/) — Referência da API do `AgGrid` e do `GridOptionsBuilder`.
- [Streamlit Ag-Grid Tutorial — Select Rows, Drilldown & Plotly Charts](https://www.youtube.com/watch?v=9NsNXNMwmK8) — Demonstração com integração direta ao Plotly.
