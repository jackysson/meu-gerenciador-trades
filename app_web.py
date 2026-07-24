import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
st.set_page_config(page_title="Gerenciador de Trades Pro", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DOS DADOS
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Data Abertura", "Ativo", "Bilhete", "Tipo", "Volume",
        "Preço Entrada", "S/L", "T/P", "Data Fechamento",
        "Preço Fechamento", "Lucro", "Mudança %", "Observação"
    ])

if 'capital_inicial' not in st.session_state:
    st.session_state.capital_inicial = 20.0

# 3. BARRA LATERAL
with st.sidebar:
    st.title("⚙️ Configurações")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=st.session_state.capital_inicial)
    st.divider()
    
    # Upload/Download
    uploaded_file = st.file_uploader("Importar Histórico (CSV)", type="csv")
    if uploaded_file:
        try:
            df_up = pd.read_csv(uploaded_file)
            st.session_state.trades = df_up
            st.success("Dados carregados!")
        except: st.error("Erro ao ler arquivo.")
    
    if not st.session_state.trades.empty:
        csv = st.session_state.trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Dados (CSV)", csv, "meus_trades.csv", "text/csv")

# 4. DASHBOARD DE ESTATÍSTICAS (CARDS)
st.title("📈 Gerenciador de Trades Pro")

df = st.session_state.trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins = len(df[df["Lucro"] > 0])
losses = len(df[df["Lucro"] < 0])
wr = (wins / len(df) * 100) if len(df) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Equity Atual", f"$ {equity:,.2f}")
c2.metric("Lucro Total", f"$ {total_profit:,.2f}", delta=f"{total_profit:,.2f}")
c3.metric("Win Rate", f"{wr:.1f}%")
c4.metric("Total Trades", len(df))

# 5. ABAS PRINCIPAIS
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Visual", "📝 Lista de Trades", "➕ Registrar Operação"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            # Curva de Equity
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_eq = px.area(x=range(len(equity_curve)), y=equity_curve, title="Curva de Patrimônio", labels={'x':'Trades','y':'USD'})
            fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_eq, use_container_width=True)
        
        with col_b:
            # Win Rate Pie
            fig_pie = px.pie(values=[wins, losses], names=['Wins', 'Losses'], title="Win Rate", color_discrete_sequence=['#3fb950', '#f85149'], hole=0.4)
            fig_pie.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Barras de Lucro
        fig_bar = px.bar(df, x=df.index, y="Lucro", color="Lucro", color_continuous_scale=['#f85149', '#3fb950'], title="Resultado por Operação")
        fig_bar.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Registre trades para ver os gráficos.")

with tab2:
    st.dataframe(df, use_container_width=True)
    if st.button("Limpar Histórico"):
        st.session_state.trades = pd.DataFrame(columns=df.columns)
        st.rerun()

with tab3:
    with st.form("add_trade", clear_on_submit=True):
        ca, cb, cc = st.columns(3)
        ativo = ca.text_input("Ativo")
        tipo = cb.selectbox("Tipo", ["buy", "sell"])
        vol = cc.number_input("Volume", value=0.01)
        
        cd, ce, cf = st.columns(3)
        p_in = cd.number_input("Preço Entrada", format="%.5f")
        p_out = ce.number_input("Preço Fechamento", format="%.5f")
        lucro_manual = cf.number_input("Lucro (USD)", format="%.2f")
        
        obs = st.text_input("Observação")
        
        if st.form_submit_button("💾 Salvar Operação"):
            novo = pd.DataFrame([{
                "Data Abertura": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Preço Entrada": p_in, "Preço Fechamento": p_out, 
                "Lucro": lucro_manual, "Observação": obs
            }])
            st.session_state.trades = pd.concat([st.session_state.trades, novo], ignore_index=True)
            st.success("Trade salvo!")
            st.rerun()
