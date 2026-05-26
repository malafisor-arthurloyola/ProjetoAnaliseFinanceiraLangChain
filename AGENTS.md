# AGENTS.md — Nexus (Renda Fixa Analytics)

## Project Context
- TAPI project for **BTG Pactual** via InteliAcademy (individual)
- Deadline: **25/05/2026** (meta interna), 28/05/2026 (oficial TAPI)
- GitHub: `https://github.com/malafisor-arthurloyola/ProjetoAnaliseFinanceiraLangChain`
- **All 10 development stages are complete** — project is in final/polish state
- Obsidian vault at `C:\Users\Inteli\Documents\BTG informações` is the **source of truth** for context, decisions, and status (contains "Prompt de Resgate" for full agent handoff)

## Entrypoints
- `app.py` — Streamlit dashboard (run: `streamlit run app.py`)
- `agent_engine.py` — terminal chat (run: `python agent_engine.py`, has `main()`)
- `chroma_indexer.py` — index CVM data into ChromaDB (run: `python chroma_indexer.py`)

## Setup
- Virtual env: `ExemploDeCódigoLangChain/venv/Scripts/Activate.ps1`
- `.env` must have `GROQ_API_KEY` (primary) or `GEMINI_API_KEY` (fallback)
- Multiple Groq keys supported: `GROQ_API_KEY`, `GROQ_API_KEY_2`, etc. — fallback on rate limit/429
- Data files expected at `data/cvm/oferta_resolucao_160.csv`, `data/cvm/carteira_xp_maio2026.json`, `data/meelion/investimentos_page1.json`
- ChromaDB persists to `chroma_db/` (gitignored)

## Architecture
- **`app.py`** → Streamlit UI, loads CVM dataset, renders dashboard + chat with `invoke_agent_with_key_fallback`
- **`agent_engine.py`** → builds LangGraph ReAct agent (`create_react_agent`), exposes 11 tools, tries Groq → Gemini on failure
- **`tools_custom.py`** → 11 `@tool` functions: CVM queries, XP portfolio, Meelion scraping, BCB SGS, ChromaDB semantic search, Yahoo Finance, tax equivalence, arbitrage comparison, report export, offer ranking
- **`chroma_indexer.py`** → loads CSV → generates embeddings (`all-MiniLM-L6-v2` via onnxruntime, CPU, offline) → persists to ChromaDB
- **NexusScore** — composite ranking (0-100) computed in `prepare_nexus_dataset()` using `calcular_nexus_score()` from `tools_custom.py`. 6 weighted dimensions: Rentabilidade (30%), Segurança (35%), Fiscal (15%), Porte (10%), Liquidez (5%), ESG (5%). Weights dynamic by intent. Displayed as stars in table and breakdown in detail panel.
- **`calcular_nexus_score()`** (`tools_custom.py:216-238`) now returns `dimensoes` dict with individual dimension scores (0-10 scale) for radar chart rendering.

## UI Redesign (Passos 1-5 completed 26/05/2026)
### Passo 1 — Treemap + Sunburst
- Pie chart replaced with **Treemap** (`px.treemap`, path: Setor → Tipo) in col_chart1
- **Sunburst** added as collapsible expander below charts (Setor → Ativo → Volume)
- Color scale: `["#0B2859", "#195AB4", "#87BAFF", "#B1D2FF"]`

### Passo 2 — Gauge + Radar + Waterfall (Detail Panel)
- **Gauge** (`go.Indicator`, mode gauge+number) shows NexusScore 0-100 with color zones
- **Radar** (`go.Scatterpolar`, 6 axes fixed 0-10) shows dimension breakdown using `calcular_nexus_score().dimensoes`
- **Waterfall** (`go.Waterfall`) shows tax equivalence: Taxa Bruta → IR deduction → Taxa Líquida

### Passo 3 — Sparklines on KPIs
- Top Bar rebuilt with `st.columns` layout; each KPI (Selic, CDI, IPCA) has a **mini sparkline** (`go.Scatter` with fill, height=24px)
- Synthetic 6-point history generated per KPI using `_sparkline_fig()` + `_build_spark_data()`

### Passo 4 — Table Enhancements
- **Pagination**: Top 100 rows by default, checkbox to show all
- **ProgressColumn**: Volume column uses `st.column_config.ProgressColumn` (normalized by max volume)
- **High Yield badge**: "⚡ High Yield" text column shown when Taxa_Bruta > CDI + 4%
- Detail panel `selected_offer` reference remains correct with paginated display

### Passo 5 — CSS Tokens + High Yield Pulse
- CSS custom properties added (`:root`): `--accent-blue`, `--success`, `--danger`, `--font-heading`, etc.
- `@keyframes hyPulse` animation: pulsing border glow on High Yield cards
- `.high-yield-badge` class: styled inline badge tag (red, uppercase)
- `.high-yield-pulse` class applied dynamically to Nexus info card when `is_high_yield` is True
- `div[role="progressbar"]` override for ProgressColumn color

## Key Domain Rules (hardcoded in agent prompt & tools)
- CDI anual = Selic Meta − 0.10 p.p. (never display daily CDI as annual)
- IR regressive table: 22.5% (≤180d), 20% (181-360d), 17.5% (361-720d), 15% (>720d)
- Sector mapping (never return N/D): Soberano, Bancário, Imobiliário, Agronegócio, etc.
- High Yield alert: CDI + 4% or prefixado > 18%
- `agent_engine.py:43-73` has the full system prompt with all rules

## Dependencies
No `requirements.txt` at root; dependencies installed in `ExemploDeCódigoLangChain/venv/` via `ExemploDeCódigoLangChain/requirements.txt`. Key packages: `langchain-groq`, `langchain-google-genai`, `langchain-core`, `langgraph`, `chromadb`, `streamlit`, `pandas`, `bcb`, `yfinance`, `python-dotenv`, `plotly`.

## Critical Prompt Engineering (hard-earned)
- **Especificidade Mandatória**: agent MUST cite real issuers, exact rates, volumes in R$, and lead coordinators. NEVER give generic financial lessons unless explicitly asked.
- When multiple assets returned, format as Markdown tables with: Emissor, Ativo, Setor, Taxa Bruta, Taxa Líquida, Vencimento, FGC/Rating.

## Important
- `ExemploDeCódigoLangChain/` is a **separate educational sub-project** (class material). Its `AGENTS.md` and `opencode.json` are specific to that sub-project, not the root app.
- Streamlit dark theme configured in `.streamlit/config.toml`
- `.env` contains live API keys — never commit or expose
