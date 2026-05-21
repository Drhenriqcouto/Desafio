import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date, timedelta
import os

st.set_page_config(
    page_title="Desafio 250 Depósitos",
    page_icon="💰",
    layout="wide"
)

DATA_DIR = Path("dados_desafio_250")
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "depositos_250.csv"

META_FINAL = sum(range(1, 251))
TOTAL_DEPOSITOS = 250

st.markdown(
    '''
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #1d2b28 0%, #111214 35%, #0b0c0f 100%);
        color: white;
    }

    section[data-testid="stSidebar"] {
        background-color: #111214;
        border-right: 1px solid #2e3438;
    }

    .metric-card {
        background: linear-gradient(145deg, #1b1d22, #121418);
        border: 1px solid #2b3136;
        border-radius: 22px;
        padding: 24px;
        min-height: 145px;
        box-shadow: 0px 10px 35px rgba(0,0,0,0.35);
    }

    .metric-title {
        color: #a9b0b5;
        font-size: 15px;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #5CFF7D;
        font-size: 31px;
        font-weight: 800;
    }

    .small-text {
        color: #c9d0d4;
        font-size: 13px;
    }

    .big-title {
        font-size: 34px;
        font-weight: 900;
        color: white;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #aeb7bd;
        font-size: 16px;
        margin-top: -8px;
    }

    div[data-testid="stButton"] > button {
        border-radius: 14px;
        border: 0px;
        background-color: #5CFF7D;
        color: #111214;
        font-weight: bold;
        padding: 0.65rem 1rem;
    }
    </style>
    ''',
    unsafe_allow_html=True
)


def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False)


def carregar_dados():

    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)

        df["data_prevista"] = pd.to_datetime(
            df["data_prevista"],
            errors="coerce"
        ).dt.date

        df["data_pagamento"] = pd.to_datetime(
            df["data_pagamento"],
            errors="coerce"
        ).dt.date

        df["pago"] = df["pago"].astype(bool)

        return df

    hoje = date.today()

    linhas = []

    for i in range(1, TOTAL_DEPOSITOS + 1):

        linhas.append({
            "deposito_num": i,
            "semana": i,
            "data_prevista": hoje + timedelta(weeks=i - 1),
            "valor_previsto": float(i),
            "valor_pago": 0.0,
            "pago": False,
            "data_pagamento": "",
            "observacao": ""
        })

    df = pd.DataFrame(linhas)

    salvar_dados(df)

    return df


def recalcular_acumulados(df):

    df = df.sort_values("deposito_num").copy()

    df["acumulado_previsto"] = df["valor_previsto"].cumsum()

    df["acumulado_pago"] = df["valor_pago"].cumsum()

    def status_linha(row):

        if row["pago"]:
            return "Pago"

        if row["data_prevista"] < date.today():
            return "Atrasado"

        return "Pendente"

    df["status"] = df.apply(status_linha, axis=1)

    return df


def registrar_deposito(
        df,
        deposito_num,
        valor_pago,
        data_pagamento,
        observacao
):

    idx = df.index[df["deposito_num"] == deposito_num][0]

    df.loc[idx, "valor_pago"] = float(valor_pago)

    df.loc[idx, "pago"] = True

    df.loc[idx, "data_pagamento"] = data_pagamento

    df.loc[idx, "observacao"] = observacao

    salvar_dados(df)

    return df


df = carregar_dados()

df = recalcular_acumulados(df)

total_pago = df["valor_pago"].sum()

qtd_pagos = int(df["pago"].sum())

progresso = total_pago / META_FINAL

proximo = df[df["pago"] == False].head(1)

if len(proximo) > 0:

    prox_num = int(proximo.iloc[0]["deposito_num"])

    prox_valor = float(proximo.iloc[0]["valor_previsto"])

else:

    prox_num = "-"

    prox_valor = 0


st.sidebar.markdown("## 💰 Desafio 250")

menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Registrar depósito",
        "Tabela"
    ]
)

if menu == "Dashboard":

    st.markdown(
        '<p class="big-title">Projeto 31.375</p>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">
                    Total acumulado
                </div>

                <div class="metric-value">
                    {brl(total_pago)}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">
                    Próximo depósito
                </div>

                <div class="metric-value">
                    {brl(prox_valor)}
                </div>

                <div class="small-text">
                    Depósito nº {prox_num}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f'''
            <div class="metric-card">
                <div class="metric-title">
                    Progresso
                </div>

                <div class="metric-value">
                    {progresso*100:.1f}%
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    st.progress(progresso)

    fig = px.line(
        df,
        x="deposito_num",
        y=["acumulado_previsto", "acumulado_pago"],
        title="Evolução acumulada"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

elif menu == "Registrar depósito":

    pendentes = df[df["pago"] == False]["deposito_num"].tolist()

    deposito_num = st.selectbox(
        "Escolha o depósito",
        pendentes,
        format_func=lambda x: f"Depósito {x} - {brl(float(x))}"
    )

    valor_pago = st.number_input(
        "Valor pago",
        value=float(deposito_num)
    )

    data_pagamento = st.date_input(
        "Data do pagamento",
        value=date.today()
    )

    observacao = st.text_area(
        "Observação"
    )

    if st.button("Salvar depósito"):

        registrar_deposito(
            df,
            deposito_num,
            valor_pago,
            data_pagamento,
            observacao
        )

        st.success("Depósito registrado!")

        st.rerun()

elif menu == "Tabela":

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )