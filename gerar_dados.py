import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta
import random

fake = Faker("pt_BR")
random.seed(42)
np.random.seed(42)

# ── 1. CATEGORIAS E ESTABELECIMENTOS ──────────────────────────────────────────
# Cada categoria tem: nome, lista de estabelecimentos, gasto médio, desvio padrão
CATEGORIAS = {
    "alimentação": {
        "estabelecimentos": [
            "Supermercado BH", "Mercado Extra", "Atacadão", "Padaria Central",
            "Açougue do João", "Hortifruti Verde"
        ],
        "media": 180, "desvio": 60,
    },
    "delivery": {
        "estabelecimentos": [
            "iFood - McDonald's", "iFood - Pizza Hut", "iFood - Sushi Now",
            "Rappi - Burger King", "iFood - Frango Assado", "Rappi - Açaí Brasil"
        ],
        "media": 55, "desvio": 20,
    },
    "transporte": {
        "estabelecimentos": [
            "Posto Shell", "Posto Ipiranga", "Uber", "99 Taxi",
            "BHBUS Recarga", "Estacionamento Central"
        ],
        "media": 120, "desvio": 40,
    },
    "lazer": {
        "estabelecimentos": [
            "Cinemark BH", "Spotify", "Netflix", "Steam Store",
            "Bar do Zé", "Boate Floresta", "Cinema Show"
        ],
        "media": 80, "desvio": 35,
    },
    "saúde": {
        "estabelecimentos": [
            "Farmácia Araújo", "Drogaria Pacheco", "Clínica Saúde Total",
            "Academia Smart Fit", "Laboratório Hermes"
        ],
        "media": 150, "desvio": 80,
    },
    "vestuário": {
        "estabelecimentos": [
            "Renner", "C&A", "Zara", "Hering Store", "Nike Store"
        ],
        "media": 200, "desvio": 90,
    },
    "educação": {
        "estabelecimentos": [
            "Udemy", "Alura", "Amazon Livros", "Livraria Cultura",
            "Coursera"
        ],
        "media": 80, "desvio": 40,
    },
    "casa": {
        "estabelecimentos": [
            "Leroy Merlin", "Casas Bahia", "Magazine Luiza",
            "Tok&Stok", "Eletro Shopping"
        ],
        "media": 250, "desvio": 150,
    },
}

# ── 2. PADRÕES COMPORTAMENTAIS INTENCIONAIS ───────────────────────────────────
# Estes padrões vão aparecer nos insights de IA — isso é o coração do projeto!

def fator_dia_semana(dia: int, categoria: str) -> float:
    """Multiplica o valor base dependendo do dia da semana (0=segunda, 6=domingo)."""
    if categoria == "delivery" and dia in (4, 5):   # sexta e sábado: +80%
        return 1.8
    if categoria == "lazer" and dia in (5, 6):       # sábado e domingo: +120%
        return 2.2
    if categoria == "transporte" and dia in (0, 1, 2, 3, 4):  # dias úteis: +30%
        return 1.3
    return 1.0

def fator_semana_mes(semana: int, categoria: str) -> float:
    """Multiplica dependendo da semana do mês (1 a 4+)."""
    if categoria == "alimentação" and semana == 1:   # compra do mês na 1ª semana
        return 2.0
    if categoria == "vestuário" and semana in (1, 2): # logo após o salário
        return 1.5
    return 1.0

def fator_mes(mes: int, categoria: str) -> float:
    """Sazonalidade mensal."""
    if categoria == "lazer" and mes == 12:           # dezembro: festas
        return 1.6
    if categoria == "vestuário" and mes in (1, 7):   # liquidações
        return 1.8
    if categoria == "saúde" and mes in (6, 7):       # inverno: gripes
        return 1.5
    return 1.0

# ── 3. GERAÇÃO DAS TRANSAÇÕES ─────────────────────────────────────────────────
transacoes = []

data_inicio = date(2024, 1, 1)
data_fim    = date(2024, 12, 31)

# Quantas transações por categoria por mês (distribuição realista)
N_POR_CATEGORIA_MES = {
    "alimentação": (4, 8),   # de 4 a 8 visitas ao mercado por mês
    "delivery":    (6, 16),  # de 6 a 16 pedidos por mês
    "transporte":  (8, 20),
    "lazer":       (2, 6),
    "saúde":       (0, 3),
    "vestuário":   (0, 2),
    "educação":    (0, 2),
    "casa":        (0, 2),
}


for mes in range(1, 13):
    for categoria, config in CATEGORIAS.items():
        n_min, n_max = N_POR_CATEGORIA_MES[categoria]
        n_transacoes = random.randint(n_min, n_max)

        for _ in range(n_transacoes):
            # Escolhe um dia aleatório dentro do mês
            dia_do_mes = random.randint(1, 28)
            try:
                data = date(2024, mes, dia_do_mes)
            except ValueError:
                data = date(2024, mes, 28)

            dia_semana = data.weekday()
            semana_mes = (dia_do_mes - 1) // 7 + 1

            # Valor base + fatores comportamentais
            valor_base = abs(np.random.normal(config["media"], config["desvio"]))
            valor = (
                valor_base
                * fator_dia_semana(dia_semana, categoria)
                * fator_semana_mes(semana_mes, categoria)
                * fator_mes(mes, categoria)
            )
            valor = round(max(valor, 5.0), 2)  # mínimo R$5

            estabelecimento = random.choice(config["estabelecimentos"])

            transacoes.append({
                "data":          data,
                "descricao":     estabelecimento,
                "valor":         valor,
                "categoria":     categoria,          # verdade — usaremos pra avaliar a IA
                "dia_semana":    data.strftime("%A"),
                "semana_do_mes": semana_mes,
                "mes":           mes,
            })

# ── 4. SALVAR ─────────────────────────────────────────────────────────────────
df = pd.DataFrame(transacoes).sort_values("data").reset_index(drop=True)

# Versão "crua" — só o que o usuário teria num extrato real (sem categoria)
extrato = df[["data", "descricao", "valor"]].copy()
extrato.to_csv("/home/claude/extrato_simulado.csv", index=False)

# Versão completa — com todas as colunas, para validação no notebook
df.to_csv("/home/claude/dados_completos.csv", index=False)

# ── 5. RESUMO ─────────────────────────────────────────────────────────────────
print(f"Total de transações geradas: {len(df)}")
print(f"Período: {df['data'].min()} → {df['data'].max()}")
print(f"Gasto total no ano: R$ {df['valor'].sum():,.2f}")
print()
print("Transações por categoria:")
print(df.groupby("categoria")["valor"].agg(["count", "sum"]).rename(
    columns={"count": "qtd", "sum": "total_R$"}
).round(2).to_string())
print()
print("Primeiras 5 linhas do extrato (o que o usuário vê):")
print(extrato.head())
