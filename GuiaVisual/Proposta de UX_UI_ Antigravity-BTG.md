# Proposta de UX/UI: Antigravity-BTG

A plataforma Antigravity-BTG, focada em análise avançada de Renda Fixa e inteligência de mercado, exige uma interface que transmita autoridade, precisão e sofisticação. O layout atual, dividido rigidamente entre Dashboard e Chatbot, compromete a experiência do usuário ao criar um ambiente visualmente poluído e apertado. 

Para elevar o produto ao padrão institucional premium do BTG Pactual, propomos uma reformulação completa baseada nos princípios de design de terminais financeiros modernos (como o Bloomberg Terminal, mas com estética contemporânea) e nas diretrizes visuais oficiais do banco.

## 1. Design System & Estética Premium (Sleek Dark Mode)

O "Sleek Dark Mode" é ideal para plataformas financeiras de uso contínuo, pois reduz a fadiga visual e destaca dados críticos através de contraste intencional. A paleta foi construída a partir do Brand Book oficial do BTG Pactual, adaptada para um ambiente escuro.

### Paleta de Cores Institucional (Dark Theme)

A paleta utiliza os tons oficiais do BTG Pactual como base, invertendo a polaridade para criar um ambiente escuro sofisticado.

| Token Semântico | Cor (Hex) | Uso Principal |
| :--- | :--- | :--- |
| **Background Base** | `#05132A` | Fundo principal da aplicação (Azul Escuro BTG Wealth). |
| **Surface Level 1** | `#0B2859` | Fundo de painéis, cards e modais (Glassmorphism leve). |
| **Surface Level 2** | `#10408D` | Elementos em destaque, cabeçalhos de tabelas. |
| **Primary Accent** | `#195AB4` | Botões primários, links, indicadores de seleção (Azul Institucional BTG). |
| **Secondary Accent** | `#B1D2FF` | Destaques sutis, ícones ativos (Azul Claro BTG Asset). |
| **Text Primary** | `#FFFFFF` | Textos principais, valores de KPIs, títulos. |
| **Text Secondary** | `#87BAFF` | Rótulos, legendas, textos de apoio. |
| **Success (Positive)** | `#2DB071` | Variações positivas, botões de confirmação. |
| **Danger (Negative)** | `#E83E48` | Variações negativas, alertas, erros. |
| **Warning (Alert)** | `#E8B73D` | Avisos, status pendentes. |

### Tipografia e Hierarquia

A tipografia oficial do BTG Pactual é a **Moderat**. Para a plataforma Antigravity-BTG, a hierarquia tipográfica deve focar na legibilidade de dados densos.

| Nível | Estilo (Moderat) | Tamanho / Peso | Uso |
| :--- | :--- | :--- | :--- |
| **Display** | Moderat Thin | 32px / 100 | Valores grandes de KPIs (ex: 10,50%). |
| **Heading 1** | Moderat Light | 24px / 300 | Títulos de seções principais (ex: "Análise de Renda Fixa"). |
| **Heading 2** | Moderat Regular | 18px / 400 | Títulos de cards e painéis. |
| **Body** | Moderat Regular | 14px / 400 | Textos gerais, descrições. |
| **Data / Numbers** | Moderat Mono | 13px / 400 | Valores em tabelas, grids de dados (alinhamento tabular). |
| **Labels** | Moderat Bold | 12px / 700 | Cabeçalhos de tabelas, rótulos de gráficos. |

### Estilo Visual (Glassmorphism & Bordas)

Para modernizar a interface sem perder a seriedade, aplicamos princípios sutis de *Glassmorphism*:
- **Bordas**: Arredondamento leve (Radius 4px a 8px) para suavizar a interface sem parecer lúdico.
- **Superfícies**: Cards com fundo translúcido (`rgba(11, 40, 89, 0.6)`) e desfoque de fundo (`backdrop-filter: blur(12px)`).
- **Divisórias**: Linhas finas e sutis (`rgba(255, 255, 255, 0.1)`) para separar conteúdos sem criar caixas pesadas.

## 2. Reorganização do Grid (Wireframe Conceitual)

O problema atual é a divisão 50/50 entre Dashboard e Chatbot. A solução é adotar um layout assimétrico e expansível, priorizando os dados (75%) e mantendo o Chatbot como uma camada de assistência contextual (25%), que pode ser recolhida ou expandida.

### Estrutura do Layout (Grid)

A tela será dividida em três zonas principais:

1. **Top Bar (KPIs e Contexto)**: Fixa no topo, compacta.
2. **Main Workspace (Dashboard)**: Área central expansível.
3. **Side Panel (Filtros e Chatbot)**: Painel lateral direito, com abas.

#### Wireframe Conceitual

| Top Bar (Altura: 64px) |
| :--- |
| **Logo Antigravity-BTG** \| **KPIs Globais**: Selic: 10,50% • CDI: 10,40% • IPCA: 4,50% \| **Perfil/Config** |

| Main Workspace (Largura: 75% -> 100%) | Side Panel (Largura: 25% -> 0%) |
| :--- | :--- |
| **Área de Gráficos (Topo)**<br>• Gráfico de Pizza (Distribuição)<br>• Gráfico de Barras (Líderes)<br><br>**Área de Dados (Base)**<br>• Tabela de Ofertas CVM (Emissor, Ativo, Volume)<br>• *Paginação e Controles de Exportação* | **Tabs: [ Filtros ] [ Assistente IA ]**<br><br>*(Se Aba Filtros)*<br>• Tipo de Ativo<br>• Coordenador Líder<br>• Status<br>• Faixa de Volume<br><br>*(Se Aba Assistente IA)*<br>• Histórico de Chat<br>• *Indicador: "Lendo filtros atuais..."*<br>• Input de Texto |

### Estratégias de Otimização de Espaço

- **Painel Lateral Colapsável**: O painel direito (Filtros/Chat) pode ser recolhido, expandindo o Dashboard para 100% da tela quando o usuário precisar focar apenas nos dados.
- **Abas (Tabs) no Painel Lateral**: Em vez de ter Filtros e Chatbot competindo por espaço, eles compartilham o mesmo painel lateral através de abas. O Chatbot "sabe" quais filtros estão ativos, eliminando a necessidade de vê-los simultaneamente o tempo todo.
- **Tabelas Densas**: Utilizar a fonte Moderat Mono e reduzir o *padding* vertical das células para exibir mais linhas sem necessidade de rolagem excessiva.

## 3. Micro-interações e Fluxo

A excelência de uma plataforma premium reside nos detalhes de interação, garantindo que o usuário compreenda o que o sistema está fazendo sem interrupções bruscas.

### Detalhes de uma Oferta Selecionada (Tabela)

Em vez de abrir um modal (que bloqueia a visão do resto do dashboard) ou redirecionar para outra página, propomos o padrão de **Master-Detail via Drawer ou Expandable Row**:

- **Expandable Row (Linha Expansível)**: Ao clicar em uma linha da tabela CVM, ela se expande verticalmente, revelando um sub-painel com detalhes completos da oferta (documentos, histórico, análise da IA específica para aquele ativo).
- **Side Drawer (Gaveta Lateral)**: Alternativamente, clicar na linha abre uma "gaveta" sobreposta ao lado direito da tabela (deslizando da direita para a esquerda), contendo os detalhes profundos, mantendo a tabela visível ao fundo.

### Transparência da IA (Logs de Execução)

Para mostrar que a IA está rodando ferramentas (buscando na CVM, XP, Meelion) sem poluir o chat:

- **Indicadores de Status Inline**: Quando a IA está processando, exibir uma mensagem sutil em itálico e com opacidade reduzida acima do indicador de digitação. Ex: `⚙️ Consultando base de dados da CVM...`
- **Accordion de Logs**: Após a resposta da IA, incluir um pequeno componente expansível (accordion) no final do balão de mensagem: `[+] Ver fontes e ferramentas utilizadas`. Se o usuário clicar, ele vê o log técnico (útil para auditoria e confiança).

### Consciência de Contexto (Filtros e Chat)

É crucial que o usuário saiba que o Chatbot está considerando os filtros aplicados no Dashboard:

- **Pílulas de Contexto (Context Pills)**: No topo da interface do Chatbot, exibir pequenas "pílulas" visuais mostrando os filtros ativos. Ex: `[Ativo: CRA] [Status: Aberta]`.
- **Mensagem de Abertura Dinâmica**: Quando o usuário abre a aba do Chatbot, a IA pode iniciar com uma mensagem contextual: *"Vejo que você está analisando ofertas de CRA abertas. Como posso ajudar com esses dados?"*
- **Sincronização Visual**: Se a IA sugerir uma mudança de filtro via chat, os botões de filtro na aba correspondente devem piscar sutilmente (highlight) para indicar que foram atualizados pelo assistente.
