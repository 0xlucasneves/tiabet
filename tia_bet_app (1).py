
import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
from pathlib import Path
from streamlit_lottie import st_lottie
import requests

st.set_page_config(page_title="Tia Bet PRO - Painel de Apostas", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #0e1117; color: white; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .title { font-size: 2.5rem; font-weight: 700; text-align: center; margin-bottom: 2rem; }
        .card {
            background-color: #1e222b;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            transition: 0.3s ease;
        }
        .card:hover {
            transform: scale(1.01);
            box-shadow: 0 4px 20px rgba(255, 215, 0, 0.3);
        }
    </style>
""", unsafe_allow_html=True)

aba = st.selectbox("Escolha uma aba", ["📌 Palpite de Hoje", "📊 Painel de Apostas"])

json_path = Path("apostas_reais.json")
if not json_path.exists():
    st.warning("Nenhum histórico de aposta encontrado.")
    st.stop()

with open(json_path, "r", encoding="utf-8") as f:
    dados = json.load(f)

df = pd.DataFrame(dados)
df["data"] = pd.to_datetime(df["data"])

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

if aba == "📌 Palpite de Hoje":
    st.markdown('<div class="title">📌 Palpite de Hoje - Tia Bet</div>', unsafe_allow_html=True)
    hoje = datetime.now().date()
    df_hoje = df[df["data"].dt.date == hoje]

    if df_hoje.empty:
        st.warning("Nenhum palpite registrado para hoje ainda.")
    else:
        destaque = df_hoje.iloc[0]
        col1, col2 = st.columns([1, 2])

        with col1:
            lottie_anim = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_vfppxhqn.json")
            if lottie_anim:
                st_lottie(lottie_anim, height=180, key="palpite")
            else:
                st.warning("⚠️ Não foi possível carregar a animação.")

        with col2:
            st.markdown(f"""
            <div class='card'>
                <h2>🔥 {destaque['tipo']}</h2>
                <h4>⚽ <strong>{destaque['jogo']}</strong> – ⏰ {destaque['horario']}</h4>
                <p><strong>Lado:</strong> <span style='color:#FFD700'>{destaque['lado']}</span> | <strong>Odd:</strong> <span style='color:#FFD700'>{destaque['odd']}</span> | <strong>EV:</strong> <span style='color:#00FF99'>{destaque['ev']}%</span></p>
                <p style='font-style: italic;'>👵 _Esse é o palpite com valor para hoje!_</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='card'>💸 Simule sua entrada:</div>", unsafe_allow_html=True)
        valor = st.number_input("Digite o valor da entrada (R$)", min_value=1.0, value=100.0, step=10.0)
        retorno_total = valor * destaque['odd']
        lucro = retorno_total - valor

        col_sim1, col_sim2 = st.columns(2)
        col_sim1.metric("🔁 Retorno Total", f"R${retorno_total:.2f}")
        col_sim2.metric("📈 Lucro Potencial", f"R${lucro:.2f}")
        st.success("👵 Se bater, hoje tem churrasco pago pela Tia Bet!")

else:
    st.markdown('<div class="title">📊 Painel de Apostas - Tia Bet PRO</div>', unsafe_allow_html=True)
    st.sidebar.title("🎯 Filtros")
    estilo = st.sidebar.selectbox("Estilo de Aposta", sorted(df["tipo"].unique()))
    data_range = st.sidebar.date_input("Período", [])
    ev_min = st.sidebar.slider("Valor Esperado Mínimo (EV)", 0, 50, 10)

    df_filtrado = df[df["tipo"] == estilo]
    if data_range and len(data_range) == 2:
        start, end = data_range
        df_filtrado = df_filtrado[(df_filtrado["data"] >= pd.to_datetime(start)) & (df_filtrado["data"] <= pd.to_datetime(end))]
    df_filtrado = df_filtrado[df_filtrado["ev"] >= ev_min]

    st.markdown("<div class='card'>📈 Estatísticas Gerais</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Total de Apostas", len(df_filtrado))
    col2.metric("💸 Odd Média", f"{df_filtrado['odd'].mean():.2f}")
    col3.metric("📈 EV Médio", f"{df_filtrado['ev'].mean():.2f}%")
    col4.metric("📆 Dias distintos", df_filtrado['data'].dt.date.nunique())

    entrada_fixa = 100
    acertos = df_filtrado[df_filtrado["resultado"] == "Ganho"]
    lucro = (acertos["odd"] * entrada_fixa - entrada_fixa).sum()
    roi = (lucro / (len(df_filtrado) * entrada_fixa)) * 100 if len(df_filtrado) > 0 else 0
    acerto_pct = (len(acertos) / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0

    col5, col6 = st.columns(2)
    col5.metric("🏆 ROI Total", f"{roi:.2f}%")
    col6.metric("✅ Taxa de Acerto", f"{acerto_pct:.1f}%")

    st.markdown("<div class='card'>📊 Resultados das Apostas</div>", unsafe_allow_html=True)
    resultado_count = df_filtrado["resultado"].value_counts().reset_index()
    resultado_count.columns = ["Resultado", "Quantidade"]
    fig_resultado = px.bar(resultado_count, x="Resultado", y="Quantidade", color="Resultado")
    fig_resultado.update_layout(plot_bgcolor='#1e222b', paper_bgcolor='#0e1117', font_color='white')
    st.plotly_chart(fig_resultado, use_container_width=True)

    st.markdown("<div class='card'>📊 EV Diário</div>", unsafe_allow_html=True)
    ev_por_dia = df_filtrado.groupby(df_filtrado['data'].dt.date)["ev"].mean().reset_index()
    ev_chart = px.line(ev_por_dia, x="data", y="ev", title="Evolução do EV Diário", markers=True)
    ev_chart.update_layout(plot_bgcolor='#1e222b', paper_bgcolor='#0e1117', font_color='white')
    st.plotly_chart(ev_chart, use_container_width=True)

    st.markdown("<div class='card'>🔁 Detalhamento das Apostas</div>", unsafe_allow_html=True)
    st.dataframe(df_filtrado.sort_values("data", ascending=False), use_container_width=True)

    st.sidebar.markdown("---")
    if st.sidebar.button("📥 Exportar CSV"):
        df_filtrado.to_csv("apostas_filtradas.csv", index=False)
        st.success("CSV exportado com sucesso!")
