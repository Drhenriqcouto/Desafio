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
    """
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
    """,
    unsafe_allow_html=True
)


def brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


def carregar_dados():
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)

        df["data_prevista"] = pd.to_datetime(
            df["data_prevista"],
            errors="coerce"
        ).dt.date

        df["data_pagamento"] = df["data_pagamento"].fillna("").astype(str)
        df["pago"] = df["pago"].astype(bool)
        df["valor_previsto"] = df["valor_previsto"].astype(float)
        df["valor_pago"] = df["valor_pago"].astype(float)
        df["observacao"] = df["observacao"].fillna("").astype(str)

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


def registrar_deposito(df, deposito_num, valor_pago, data_pagamento, observacao):
    idx = df.index[df["deposito_num"] == deposito_num][0]

    df.loc[idx, "valor_pago"] = float(valor_pago)
    df.loc[idx, "pago"] = True
    df.loc[idx, "data_pagamento"] = data_pagamento.strftime("%Y-%m-%d")
    df.loc[idx, "observacao"] = str(observacao)

    salvar_dados(df)

    return df


def desfazer_deposito(df, deposito_num):
    idx = df.index[df["deposito_num"] == deposito_num][0]

    df.loc[idx, "valor_pago"] = 0.0
    df.loc[idx, "pago"] = False
    df.loc[idx, "data_pagamento"] = ""
    df.loc[idx, "observacao"] = ""

    salvar_dados(df)

    return df


def gerar_painel_250_valores(df):
    html = """
    <div style="
        display:grid;
        grid-template-columns:repeat(10, 1fr);
        gap:8px;
        margin-top:15px;
    ">
    """

    for _, row in df.iterrows():
        numero = int(row["deposito_num"])
        valor = brl(row["valor_previsto"])

        if row["pago"]:
            cor = "#5CFF7D"
            texto = "#111214"
            status = "Pago"
        else:
            cor = "#ff4d6d"
            texto = "white"
            status = "Não pago"

        html += f"""
        <div title="{status} • {valor}"
            style="
            background:{cor};
            color:{texto};
            border-radius:14px;
            padding:12px;
            min-height:70px;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            font-weight:700;
            box-shadow:0px 4px 12px rgba(0,0,0,0.25);
            ">
            <div style="font-size:13px;">#{numero}</div>
            <div style="font-size:17px;margin-top:4px;">{valor}</div>
        </div>
        """

    html += "</div>"

    return html


df = carregar_dados()
df = recalcular_acumulados(df)

total_pago = df["valor_pago"].sum()
qtd_pagos = int(df["pago"].sum())
progresso_financeiro = total_pago / META_FINAL
progresso_depositos = qtd_pagos / TOTAL_DEPOSITOS
valor_restante = META_FINAL - total_pago
atrasados = int((df["status"] == "Atrasado").sum())

proximo = df[df["pago"] == False].head(1)

if len(proximo) > 0:
    prox_num = int(proximo.iloc[0]["deposito_num"])
    prox_valor = float(proximo.iloc[0]["valor_previsto"])
    prox_data = proximo.iloc[0]["data_prevista"]
else:
    prox_num = "-"
    prox_valor = 0
    prox_data = "-"


st.sidebar.markdown("## 💰 Desafio 250")
st.sidebar.caption("Painel de depósitos semanais")

menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Registrar depósito",
        "Tabela de registros",
        "Exportar dados",
        "Configurações"
    ]
)

st.sidebar.markdown("---")
st.sidebar.metric("Meta final", brl(META_FINAL))
st.sidebar.metric("Depósitos feitos", f"{qtd_pagos}/250")
st.sidebar.progress(progresso_financeiro)


if menu == "Dashboard":
    st.markdown(
        '<p class="big-title">Projeto 31.375</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Desafio dos 250 depósitos semanais, começando em R$ 1,00 e terminando em R$ 250,00.</p>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total acumulado</div>
                <div class="metric-value">{brl(total_pago)}</div>
                <div class="small-text">de {brl(META_FINAL)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Próximo depósito</div>
                <div class="metric-value">{brl(prox_valor)}</div>
                <div class="small-text">Depósito nº {prox_num} • {prox_data}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Progresso financeiro</div>
                <div class="metric-value">{progresso_financeiro * 100:.1f}%</div>
                <div class="small-text">faltam {brl(valor_restante)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Status geral</div>
                <div class="metric-value">{qtd_pagos}/250</div>
                <div class="small-text">{atrasados} depósitos atrasados</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### Progresso do desafio")
    st.progress(progresso_depositos)

    st.markdown("### Painel dos 250 depósitos")
    st.markdown(gerar_painel_250_valores(df), unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])

    with c1:
        fig = px.line(
            df,
            x="deposito_num",
            y=["acumulado_previsto", "acumulado_pago"],
            labels={
                "deposito_num": "Depósito",
                "value": "Valor acumulado",
                "variable": "Tipo"
            },
            title="Evolução acumulada: previsto x realizado"
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=430,
            legend_title_text=""
        )

        st.plotly_chart(fig, use_container_width=True)

    with c2:
        resumo_status = df["status"].value_counts().reset_index()
        resumo_status.columns = ["status", "quantidade"]

        fig2 = px.pie(
            resumo_status,
            names="status",
            values="quantidade",
            title="Distribuição dos depósitos",
            hole=0.55
        )

        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=430
        )

        st.plotly_chart(fig2, use_container_width=True)


elif menu == "Registrar depósito":
    st.markdown(
        '<p class="big-title">Registrar depósito</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Marque cada depósito como concluído para manter seu histórico salvo.</p>',
        unsafe_allow_html=True
    )

    aba1, aba2 = st.tabs(["Registrar novo depósito", "Editar ou desfazer depósito"])

    with aba1:
        pendentes = df[df["pago"] == False]["deposito_num"].tolist()

        if pendentes:
            deposito_num = st.selectbox(
                "Escolha o depósito",
                pendentes,
                format_func=lambda x: f"Depósito {x} - {brl(float(x))}"
            )

            valor_pago = st.number_input(
                "Valor pago",
                min_value=0.0,
                value=float(deposito_num),
                step=1.0
            )

            data_pagamento = st.date_input(
                "Data do pagamento",
                value=date.today()
            )

            observacao = st.text_area(
                "Observação",
                placeholder="Ex.: pago via PIX, caixinha, CDB..."
            )

            if st.button("Salvar depósito"):
                df = registrar_deposito(
                    df,
                    deposito_num,
                    valor_pago,
                    data_pagamento,
                    observacao
                )

                st.success("Depósito registrado com sucesso!")
                st.rerun()

        else:
            st.success("Todos os 250 depósitos foram concluídos.")

    with aba2:
        todos = df["deposito_num"].tolist()

        deposito_editar = st.selectbox(
            "Escolha um depósito",
            todos,
            format_func=lambda x: f"Depósito {x}"
        )

        registro = df[df["deposito_num"] == deposito_editar].iloc[0]

        st.write("Status atual:", registro["status"])
        st.write("Valor previsto:", brl(registro["valor_previsto"]))
        st.write("Valor pago:", brl(registro["valor_pago"]))
        st.write("Data de pagamento:", registro["data_pagamento"])

        novo_valor = st.number_input(
            "Novo valor pago",
            min_value=0.0,
            value=float(registro["valor_pago"]),
            step=1.0
        )

        nova_data = st.date_input(
            "Nova data de pagamento",
            value=date.today()
        )

        nova_obs = st.text_area(
            "Nova observação",
            value=str(registro["observacao"])
        )

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Atualizar registro"):
                df = registrar_deposito(
                    df,
                    deposito_editar,
                    novo_valor,
                    nova_data,
                    nova_obs
                )

                st.success("Registro atualizado!")
                st.rerun()

        with col_b:
            if st.button("Desfazer depósito"):
                df = desfazer_deposito(df, deposito_editar)

                st.success("Depósito desfeito.")
                st.rerun()


elif menu == "Tabela de registros":
    st.markdown(
        '<p class="big-title">Tabela de registros</p>',
        unsafe_allow_html=True
    )

    filtro = st.multiselect(
        "Filtrar por status",
        options=["Pago", "Pendente", "Atrasado"],
        default=["Pago", "Pendente", "Atrasado"]
    )

    df_visivel = df[df["status"].isin(filtro)].copy()

    st.dataframe(
        df_visivel,
        use_container_width=True,
        hide_index=True
    )


elif menu == "Exportar dados":
    st.markdown(
        '<p class="big-title">Exportar dados</p>',
        unsafe_allow_html=True
    )

    csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

    st.download_button(
        label="Baixar CSV dos registros",
        data=csv_data,
        file_name="depositos_250.csv",
        mime="text/csv"
    )

    excel_path = DATA_DIR / "depositos_250.xlsx"

    try:
        df.to_excel(excel_path, index=False)

        with open(excel_path, "rb") as file:
            st.download_button(
                label="Baixar Excel dos registros",
                data=file,
                file_name="depositos_250.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception:
        st.info("Para exportar Excel, instale o pacote openpyxl.")


elif menu == "Configurações":
    st.markdown(
        '<p class="big-title">Configurações</p>',
        unsafe_allow_html=True
    )

    st.warning("Cuidado: esta área altera seus registros salvos.")

    if st.button("Recriar arquivo do desafio"):
        if CSV_PATH.exists():
            os.remove(CSV_PATH)

        st.success("Arquivo recriado. Recarregando...")
        st.rerun()

    st.markdown("### Local do arquivo salvo")
    st.code(str(CSV_PATH))