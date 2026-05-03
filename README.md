# 💰 Finly — Analista Financeiro Pessoal com IA

> Projeto de portfólio | Análise de dados + LLM local (Llama 3.1)

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.1-black)](https://ollama.com)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas)](https://pandas.pydata.org)
[![Plotly](https://img.shields.io/badge/Plotly-interactive-3F4F75?logo=plotly)](https://plotly.com)

---

## O que é o Finly?

O Finly é um analista financeiro pessoal que roda **100% local** — sem mandar seus dados pra nuvem. Você sobe um extrato bancário em CSV e a IA faz o trabalho:

- **Categoriza** cada transação automaticamente usando Llama 3.1
- **Detecta padrões** comportamentais que apps de banco não mostram
- **Prevê** tendências de gasto por categoria
- **Responde perguntas** em linguagem natural sobre os seus dados

---

## Insights descobertos

A análise revelou padrões comportamentais reais nos dados:

| Insight | Detalhe |
|---|---|
| 🛵 Delivery 2.1x mais caro nas sextas | Padrão claro de gasto impulsivo no fim de semana |
| 🛒 Alimentação na 1ª semana custa 2.4x mais | Compra do mês logo após o salário |
| 🎉 Nov/Dez com +29% acima da média | Sazonalidade de fim de ano detectada automaticamente |
| 🚗 Transporte = 29.8% do total | Segunda maior categoria — dado surpreendente |

---

## Tecnologias

| Camada | Tecnologia | Por quê |
|---|---|---|
| LLM local | Ollama + Llama 3.1 | Sem custo, sem limite, 100% privado |
| Interface | Streamlit | Deploy rápido, fácil de demonstrar |
| Análise | Pandas + NumPy | Manipulação e agregação dos dados |
| Visualização | Plotly | Gráficos interativos no browser |
| Notebooks | Jupyter | Documentação do raciocínio analítico |

---

## Funcionalidades

### 📊 Dashboard de categorias
Distribuição de gastos em pizza e barras interativas, com evolução mensal empilhada por categoria.

### 📅 Padrões comportamentais
- Gasto médio por dia da semana e por categoria
- Gasto por semana do mês (detecta o "dia de mercadão")
- Heatmap de intensidade categoria × mês

### 🔍 Detecção de anomalias
Identifica meses onde o gasto fugiu do padrão histórico usando desvio padrão. Sensibilidade ajustável via slider.

### 💬 Chat em linguagem natural
O usuário digita uma pergunta em português → Llama 3.1 gera o código Python → código executa → resposta aparece. Igual ao ChatGPT Advanced Data Analysis, construído do zero.

---

## Como rodar localmente

### Pré-requisitos
- Python 3.10+
- [Ollama](https://ollama.com) instalado com o modelo `llama3.1`

```bash
ollama pull llama3.1
```

### Instalação

```bash
# Clone o repositório
git clone https://github.com/thyfanixs/finly.git
cd finly

# Instale as dependências
pip install streamlit pandas numpy plotly requests

# Rode o app
streamlit run app.py
```

### Formato do CSV

O app aceita qualquer extrato com essas colunas (os nomes podem variar):

```
data,descricao,valor
2024-01-05,iFood - Pizza,55.90
2024-01-06,Posto Shell,120.00
2024-01-07,Supermercado BH,380.00
```

Não tem um extrato real à mão? Use o gerador de dados simulados:

```bash
python gerar_dados.py
# Gera extrato_simulado.csv com 459 transações e padrões comportamentais embutidos
```

---

## Estrutura do projeto

```
finly/
├── app.py                          # App Streamlit principal
├── gerar_dados.py                  # Gerador de dados simulados
├── extrato_simulado.csv            # Dataset de exemplo
├── notebooks/
│   ├── 01_categorizacao.ipynb      # Categorização com Llama 3.1
│   ├── 02_analise_padroes.ipynb    # Análise e visualizações
│   └── 03_chat_linguagem_natural.ipynb  # Motor do chat
└── .gitignore
```

---

## Notebooks

Os notebooks documentam o raciocínio analítico passo a passo:

**01 — Categorização com IA**
Chama o Llama 3.1 em lotes de 10 transações e avalia a acurácia comparando com o gabarito. Resultado: **78.4% de acurácia** com modelo rodando em CPU local.

**02 — Análise de padrões**
Gráficos de padrão por dia da semana, semana do mês, sazonalidade mensal e detecção de anomalias com desvio padrão.

**03 — Chat em linguagem natural**
Pipeline completo: pergunta → prompt engineering → código gerado pelo LLM → execução com `exec()` → resposta em português.

---

## Aprendizados e limitações

**O que funcionou bem:**
- Llama 3.1 categoriza estabelecimentos conhecidos com alta precisão
- O chat em linguagem natural funciona bem para perguntas simples e agregações diretas
- Detecção de anomalias via desvio padrão capturou os meses de fim de ano corretamente

**Limitações honestas:**
- Acurácia de 78.4% — categorias como `casa` (Magazine Luiza, Casas Bahia) confundem o modelo
- O chat falha em perguntas complexas que exigem múltiplas transformações
- Llama 3.1 na CPU é lento (~10-20s por pergunta)

**Próximos passos:**
- [ ] Fine-tuning do prompt de categorização para estabelecimentos brasileiros
- [ ] Adicionar previsão de gastos com Prophet
- [ ] Suporte a múltiplos formatos de extrato (OFX, PDF)

---

## Autora

**Thyfani Xavier**
Analista de Dados em formação

[![GitHub](https://img.shields.io/badge/GitHub-thyfanixs-black?logo=github)](https://github.com/thyfanixs)

---

*Projeto desenvolvido como portfólio de análise de dados com IA generativa.*
