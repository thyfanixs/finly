import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finly — Analista Financeiro Pessoal",
    page_icon="💰",
    layout="wide"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO     = "llama3.1"

CATEGORIAS_VALIDAS = [
    "alimentação", "delivery", "transporte", "lazer",
    "saúde", "vestuário", "educação", "casa", "outros"
]

CORES_CATEGORIAS = {
    "alimentação": "#636EFA",
    "delivery":    "#EF553B",
    "transporte":  "#00CC96",
    "lazer":       "#AB63FA",
    "saúde":       "#FFA15A",
    "vestuário":   "#19D3F3",
    "educação":    "#FF6692",
    "casa":        "#B6E880",
    "outros":      "#FECB52",
}

# ── FUNÇÕES DE IA ─────────────────────────────────────────────────────────────
def ollama_disponivel():
    try:
        r = requests.get("http://localhost:11434", timeout=3)
        return True
    except:
        return False


def categorizar_lote(descricoes):
    lista = "\n".join([f"{i+1}. {d}" for i, d in enumerate(descricoes)])
    prompt = (
        "Voce e um sistema de categorizacao de gastos pessoais brasileiro.\n"
        f"Categorize cada transacao usando EXATAMENTE uma das categorias: {', '.join(CATEGORIAS_VALIDAS)}\n\n"
        f"Transacoes:\n{lista}\n\n"
        f"Responda APENAS com JSON: {{\"categorias\": [\"cat1\", \"cat2\", ...]}}\n"
        f"A lista deve ter exatamente {len(descricoes)} itens."
    )
    payload = {
        "model": MODELO, "prompt": prompt, "stream": False,
        "format": "json", "options": {"temperature": 0, "num_predict": 200}
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    texto = r.json()["response"].strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    cats = json.loads(texto)["categorias"]
    cats = [c if c in CATEGORIAS_VALIDAS else "outros" for c in cats]
    while len(cats) < len(descricoes):
        cats.append("outros")
    return cats[:len(descricoes)]


def categorizar_df(df):
    descricoes    = df["descricao"].tolist()
    categorias    = []
    tamanho_lote  = 10
    total_lotes   = (len(descricoes) + tamanho_lote - 1) // tamanho_lote

    barra    = st.progress(0, text="Categorizando com IA...")
    status   = st.empty()

    for i in range(0, len(descricoes), tamanho_lote):
        lote     = descricoes[i : i + tamanho_lote]
        num_lote = i // tamanho_lote + 1
        try:
            cats = categorizar_lote(lote)
            categorias.extend(cats)
        except Exception as e:
            categorias.extend(["outros"] * len(lote))
        pct = num_lote / total_lotes
        barra.progress(pct, text=f"Categorizando... lote {num_lote}/{total_lotes}")

    barra.empty()
    status.empty()
    df["categoria"] = categorias
    return df


def enriquecer_df(df):
    df["data"]         = pd.to_datetime(df["data"])
    df["dia_semana"]   = df["data"].dt.day_name(locale="pt_BR").str.capitalize()
    df["mes"]          = df["data"].dt.month
    df["mes_nome"]     = df["data"].dt.strftime("%b").str.capitalize()
    df["semana_do_mes"]= ((df["data"].dt.day - 1) // 7) + 1
    df["ano_mes"]      = df["data"].dt.to_period("M").astype(str)
    return df


def gerar_codigo_chat(pergunta, df):
    cats = str(sorted(df["categoria"].unique()))
    n    = len(df)
    prompt = (
        "# Contexto\n"
        f"Existe um DataFrame chamado df JA CARREGADO com {n} linhas.\n"
        "Colunas: data(datetime), descricao(str), valor(float), categoria(str),\n"
        "         mes(int 1-12), mes_nome(str), dia_semana(str), semana_do_mes(int), ano_mes(str)\n"
        f"Categorias: {cats}\n\n"
        "# Regras OBRIGATORIAS\n"
        "1. NAO escreva import. NAO crie um novo df. NAO redefina df.\n"
        "2. Use apenas df, pd e np que ja existem.\n"
        "3. Termine com print() mostrando a resposta em portugues.\n"
        "4. Escreva APENAS o codigo, sem texto, sem markdown.\n\n"
        f"# Pergunta\n{pergunta}\n\n"
        "# Codigo:\n"
    )
    payload = {
        "model": MODELO, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "num_predict": 250}
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    codigo = r.json()["response"].strip()
    codigo = codigo.replace("```python", "").replace("```", "").strip()
    linhas = []
    for linha in codigo.split("\n"):
        if any(p in linha for p in ["import ", "df = pd.DataFrame", "df = {", "df=pd.DataFrame"]):
            continue
        linhas.append(linha)
    return "\n".join(linhas).strip()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💰 Finly")
    st.caption("Analista financeiro pessoal com IA")
    st.divider()

    arquivo = st.file_uploader(
        "Suba seu extrato (.csv)",
        type=["csv"],
        help="CSV com colunas: data, descricao, valor"
    )

    st.divider()
    st.caption("Formato esperado do CSV:")
    st.code("data,descricao,valor\n2024-01-05,iFood,55.90\n2024-01-06,Posto Shell,120.00")

    st.divider()
    status_ollama = ollama_disponivel()
    if status_ollama:
        st.success("Ollama rodando", icon="✅")
    else:
        st.error("Ollama offline", icon="❌")
        st.caption("Abra o app Ollama e tente novamente.")


# ── TELA INICIAL ──────────────────────────────────────────────────────────────
if arquivo is None:
    st.title("💰 Finly")
    st.subheader("Seu analista financeiro pessoal com IA")
    st.write("")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Categorização", "IA local", "Llama 3.1")
    col2.metric("Privacidade", "100%", "sem nuvem")
    col3.metric("Insights", "automáticos", "comportamentais")
    col4.metric("Chat", "linguagem natural", "pergunte aos dados")

    st.write("")
    st.info("Suba seu extrato CSV na barra lateral para começar.", icon="👈")
    st.stop()


# ── CARREGA E PROCESSA ────────────────────────────────────────────────────────
@st.cache_data
def processar(arquivo_bytes, nome):
    import io
    df = pd.read_csv(io.BytesIO(arquivo_bytes))
    df.columns = df.columns.str.lower().str.strip()

    # Aceita variações de nome de coluna
    for col in ["data", "date"]:
        if col in df.columns:
            df.rename(columns={col: "data"}, inplace=True)
            break
    for col in ["descricao", "description", "historico", "memo"]:
        if col in df.columns:
            df.rename(columns={col: "descricao"}, inplace=True)
            break
    for col in ["valor", "value", "amount", "debito"]:
        if col in df.columns:
            df.rename(columns={col: "valor"}, inplace=True)
            break

    df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["data", "descricao", "valor"])
    df = df[df["valor"] > 0]  # só débitos
    return df

arquivo_bytes = arquivo.read()
df_raw = processar(arquivo_bytes, arquivo.name)

# Verifica se já tem categoria ou precisa categorizar
if "categoria" not in df_raw.columns:
    if not ollama_disponivel():
        st.error("Ollama offline. Abra o app Ollama para categorizar as transações.")
        st.stop()
    with st.spinner("Categorizando transações com Llama 3.1..."):
        df_raw = categorizar_df(df_raw.copy())

df = enriquecer_df(df_raw.copy())

ORDEM_DIAS   = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
                "Sexta-feira", "Sábado", "Domingo"]
ORDEM_MESES  = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]


# ── ABAS ──────────────────────────────────────────────────────────────────────
aba1, aba2, aba3, aba4 = st.tabs([
    "📊 Visão geral",
    "📅 Padrões comportamentais",
    "🔍 Anomalias",
    "💬 Chat com os dados"
])


# ── ABA 1: VISÃO GERAL ────────────────────────────────────────────────────────
with aba1:
    st.header("Visão geral")

    gasto_total  = df["valor"].sum()
    media_mensal = df.groupby("ano_mes")["valor"].sum().mean()
    n_transacoes = len(df)
    ticket_medio = df["valor"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gasto total", f"R$ {gasto_total:,.2f}")
    c2.metric("Média mensal", f"R$ {media_mensal:,.2f}")
    c3.metric("Transações", n_transacoes)
    c4.metric("Ticket médio", f"R$ {ticket_medio:,.2f}")

    st.divider()

    por_cat = (
        df.groupby("categoria")["valor"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "total", "count": "qtd"})
        .sort_values("total", ascending=False)
        .reset_index()
    )
    por_cat["percentual"] = por_cat["total"] / por_cat["total"].sum() * 100

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.pie(
            por_cat, values="total", names="categoria",
            hole=0.4, title="Distribuição por categoria",
            color="categoria",
            color_discrete_map=CORES_CATEGORIAS
        )
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.bar(
            por_cat, x="total", y="categoria", orientation="h",
            title="Total por categoria (R$)",
            color="categoria", color_discrete_map=CORES_CATEGORIAS,
            text=por_cat["total"].apply(lambda x: f"R$ {x:,.0f}")
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Evolução mensal")
    mensal = df.groupby(["ano_mes", "categoria"])["valor"].sum().reset_index()
    fig3 = px.bar(
        mensal, x="ano_mes", y="valor", color="categoria",
        title="Gasto por mês e categoria",
        color_discrete_map=CORES_CATEGORIAS,
        labels={"valor": "Total (R$)", "ano_mes": "Mês"}
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── ABA 2: PADRÕES ────────────────────────────────────────────────────────────
with aba2:
    st.header("Padrões comportamentais")
    st.caption("Onde e quando você gasta mais — insights que apps de banco não mostram.")

    cats_foco = ["delivery", "lazer", "transporte", "alimentação"]
    cats_disponiveis = [c for c in cats_foco if c in df["categoria"].unique()]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Por dia da semana")
        por_dia = (
            df[df["categoria"].isin(cats_disponiveis)]
            .groupby(["dia_semana", "categoria"])["valor"]
            .mean().reset_index()
        )
        fig = px.bar(
            por_dia, x="dia_semana", y="valor", color="categoria",
            barmode="group",
            category_orders={"dia_semana": ORDEM_DIAS},
            color_discrete_map=CORES_CATEGORIAS,
            labels={"valor": "Média (R$)", "dia_semana": ""}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Insight automático
        if "delivery" in df["categoria"].unique():
            delivery_dia = df[df["categoria"] == "delivery"].groupby("dia_semana")["valor"].mean()
            if len(delivery_dia) > 1:
                pico = delivery_dia.idxmax()
                ratio = delivery_dia.max() / delivery_dia.min()
                st.info(f"💡 Delivery é **{ratio:.1f}x** mais caro na **{pico}**")

    with col2:
        st.subheader("Por semana do mês")
        por_semana = (
            df[df["categoria"].isin(cats_disponiveis)]
            .groupby(["semana_do_mes", "categoria"])["valor"]
            .mean().reset_index()
        )
        fig2 = px.line(
            por_semana, x="semana_do_mes", y="valor", color="categoria",
            markers=True, color_discrete_map=CORES_CATEGORIAS,
            labels={"valor": "Média (R$)", "semana_do_mes": "Semana do mês"}
        )
        fig2.update_xaxes(
            tickvals=[1,2,3,4],
            ticktext=["1ª semana","2ª semana","3ª semana","4ª semana"]
        )
        st.plotly_chart(fig2, use_container_width=True)

        if "alimentação" in df["categoria"].unique():
            alim = df[df["categoria"] == "alimentação"].groupby("semana_do_mes")["valor"].mean()
            if len(alim) > 1:
                s_pico = alim.idxmax()
                outras = alim.drop(s_pico).mean()
                ratio  = alim.max() / outras
                st.info(f"💡 Alimentação na **{s_pico}ª semana** é **{ratio:.1f}x** mais cara")

    st.subheader("Heatmap — categoria x mês")
    pivot = (
        df.groupby(["categoria", "mes_nome"])["valor"]
        .sum().reset_index()
        .pivot(index="categoria", columns="mes_nome", values="valor")
        .fillna(0)
    )
    meses_presentes = [m for m in ORDEM_MESES if m in pivot.columns]
    pivot = pivot[meses_presentes]
    fig3 = px.imshow(
        pivot, color_continuous_scale="Blues",
        labels={"color": "Total R$"},
        title="Intensidade de gasto por categoria e mês"
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── ABA 3: ANOMALIAS ──────────────────────────────────────────────────────────
with aba3:
    st.header("Detecção de anomalias")
    st.caption("Meses onde o gasto fugiu do padrão histórico.")

    total_mes = df.groupby("ano_mes")["valor"].sum().reset_index()
    total_mes.columns = ["mes", "total"]

    media  = total_mes["total"].mean()
    desvio = total_mes["total"].std()

    sensibilidade = st.slider(
        "Sensibilidade da detecção",
        min_value=1.0, max_value=3.0, value=1.5, step=0.1,
        help="Menor = detecta mais anomalias. Maior = só casos extremos."
    )
    limite = media + sensibilidade * desvio
    total_mes["anomalia"] = total_mes["total"] > limite

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=total_mes["mes"],
        y=total_mes["total"],
        marker_color=["#EF553B" if a else "#636EFA" for a in total_mes["anomalia"]],
        name="Gasto mensal"
    ))
    fig.add_hline(y=limite, line_dash="dash", line_color="orange",
                  annotation_text=f"Limite (R$ {limite:,.0f})")
    fig.add_hline(y=media, line_dash="dot", line_color="green",
                  annotation_text=f"Média (R$ {media:,.0f})")
    fig.update_layout(
        title="Gasto mensal — meses anômalos em vermelho",
        xaxis_title="Mês", yaxis_title="Total (R$)", height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    anomalias = total_mes[total_mes["anomalia"]]
    if len(anomalias) > 0:
        st.warning(f"**{len(anomalias)} mês(es) anômalo(s) detectado(s):**")
        for _, row in anomalias.iterrows():
            pct = (row["total"] - media) / media * 100
            st.write(f"- **{row['mes']}**: R$ {row['total']:,.2f} ({pct:+.1f}% acima da média)")

        # Detalha o pior mês
        pior = anomalias.loc[anomalias["total"].idxmax()]
        st.subheader(f"Detalhes de {pior['mes']}")
        df_pior = df[df["ano_mes"] == pior["mes"]]
        por_cat_pior = df_pior.groupby("categoria")["valor"].sum().sort_values(ascending=False)
        fig2 = px.bar(
            por_cat_pior.reset_index(),
            x="categoria", y="valor",
            title=f"O que pesou em {pior['mes']}",
            color="categoria", color_discrete_map=CORES_CATEGORIAS,
            labels={"valor": "Total (R$)"}
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.success("Nenhum mês anômalo detectado com essa sensibilidade.")


# ── ABA 4: CHAT ───────────────────────────────────────────────────────────────
with aba4:
    st.header("Chat com os dados")
    st.caption("Pergunte qualquer coisa sobre seus gastos em português.")

    if not ollama_disponivel():
        st.error("Ollama offline. Abra o app Ollama para usar o chat.")
        st.stop()

    # Inicializa histórico
    if "historico" not in st.session_state:
        st.session_state.historico = []

    # Sugestões rápidas
    st.write("**Sugestões:**")
    sugestoes = [
        "Quanto gastei com delivery?",
        "Qual meu maior gasto?",
        "Qual categoria cresceu mais no segundo semestre?",
        "Qual dia da semana gasto mais?"
    ]
    cols = st.columns(len(sugestoes))
    for i, sug in enumerate(sugestoes):
        if cols[i].button(sug, key=f"sug_{i}"):
            st.session_state.pergunta_rapida = sug

    st.divider()

    # Exibe histórico
    for msg in st.session_state.historico:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input do usuário
    pergunta_input = st.chat_input("Faça uma pergunta sobre seus gastos...")

    # Pega pergunta (digitada ou sugestão)
    pergunta = pergunta_input
    if hasattr(st.session_state, "pergunta_rapida"):
        pergunta = st.session_state.pergunta_rapida
        del st.session_state.pergunta_rapida

    if pergunta:
        # Mostra pergunta
        with st.chat_message("user"):
            st.write(pergunta)
        st.session_state.historico.append({"role": "user", "content": pergunta})

        # Gera e executa o código
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    codigo = gerar_codigo_chat(pergunta, df)

                    # Captura o print() como string
                    import io, sys
                    captura = io.StringIO()
                    sys.stdout = captura
                    exec(codigo, {"df": df, "pd": pd, "np": np, "print": print})
                    sys.stdout = sys.__stdout__
                    resposta = captura.getvalue().strip()

                    if resposta:
                        st.write(resposta)
                        with st.expander("Ver código gerado"):
                            st.code(codigo, language="python")
                        st.session_state.historico.append({
                            "role": "assistant", "content": resposta
                        })
                    else:
                        st.warning("O modelo não retornou uma resposta. Tente reformular a pergunta.")

                except Exception as e:
                    sys.stdout = sys.__stdout__
                    st.error(f"Erro: {e}")
