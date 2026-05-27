# Especificações Mestre: Nexus - Inteligência Financeira & UX Pro Max

Este documento é a especificação definitiva para a implementação da plataforma Nexus. Ele combina a inteligência financeira baseada em dados reais com as melhores práticas de UX para investidores.

---

## 1. Arquitetura de Informação e Visualização (Grid de Dados)

### 1.1. Tabela de Ofertas (Dashboard CVM)
A tabela deve ser limpa, focada em **ativos ativos**. Ofertas encerradas devem ser movidas para uma aba de "Histórico".

| Coluna | Regra de Negócio / Inteligência | Elemento de UX |
| :--- | :--- | :--- |
| **Ativo** | Nome do ativo + Ícone (CRA, CDB, etc.) | Link para detalhes do emissor. |
| **Taxa Líquida** | **Cálculo de Gross-up (Equivalência Fiscal)**. Mostrar o ganho real após IR. | **Destaque Visual (Verde/Bold)**. |
| **Rating** | Nota de crédito (AAA, AA, etc.) | Badges coloridos (Verde: Baixo Risco, Vermelho: Alto). |
| **Volume** | Valor total da oferta e % captado. | Barra de progresso discreta. |
| **Veredito IA** | Categoria do Insight (Oportunidade, Seguro, Atenção). | Ícone de lâmpada com Tooltip explicativo. |
| **Ação** | Trigger para o Nexus AI Assistant. | Botão "Analisar com Nexus". |

---

## 2. Inteligência Financeira e Cálculos (Backend)

### 2.1. O Motor de Mercado
*   **CDI Dinâmico:** O sistema deve calcular o CDI como `(Selic Meta - 0.10)`. Exibir sempre em base anual (Ex: 14.40% a.a.).
*   **Normalização de Setores:** Mapear automaticamente ativos para setores reais (Soberano, Bancário, Agro, Infra, Imobiliário). Eliminar o "N/D".
*   **Cálculo de IR:** Aplicar a tabela regressiva automaticamente baseada na data de vencimento do ativo.

---

## 3. UX de Navegação e Filtros Inteligentes

### 3.1. Botões de Atalho (Filtros de Intenção)
Substituir a complexidade técnica por botões de objetivo no topo da página:
*   **🛡️ Máxima Segurança:** Filtra Rating AAA e Emissores com FGC.
*   **💰 Renda Mensal:** Filtra FIIs e Fundos de Infra com pagamentos periódicos.
*   **🚀 Super Rentabilidade:** Filtra ativos High Yield (Taxa > CDI + 4%).
*   **🌱 Foco no Agro:** Filtra LCAs e CRAs (Isentos).

### 3.2. Estados de Carregamento (Skeleton Screens)
Enquanto a IA processa os PDFs dos prospectos, exibir um esqueleto da interface com mensagens de progresso:
*   *"Lendo prospecto de 300 páginas..."*
*   *"Calculando prêmio de risco..."*
*   *"Cruzando com Relatório Focus..."*

---

## 4. Integração com o Chatbot Nexus

O chatbot não deve ser genérico. Ele deve operar em 3 níveis:
1.  **Nível de Oferta:** Quando aberto a partir de uma linha da tabela, ele já inicia com: *"Analisando a Debênture da Empresa X. O cenário para este setor é positivo devido a..."*
2.  **Nível de Arbitragem:** Na aba de Mercado, ele deve ser capaz de dizer: *"A taxa da Meelion para este CRA está 1.2% acima da XP para o mesmo risco. Recomendo olhar o emissor."*
3.  **Nível de Cenário:** Responder perguntas como: *"O que acontece com minha carteira se a inflação subir?"*

---

## 5. Governança e Disclaimer
Todas as análises geradas pela IA devem conter o disclaimer:
> *"Esta análise é gerada por inteligência artificial (Nexus AI) e tem caráter informativo. Não constitui recomendação de investimento. Consulte seu assessor financeiro."*
