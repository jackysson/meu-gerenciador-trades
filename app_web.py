import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl="0s")
    except:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    if not st.session_state.df_trades.empty:
        csv = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual", csv, "meus_trades.csv", "text/csv")

# 4. MÉTRICAS
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
n_losses = len(df[df["Lucro"] < 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0

st.title("📊 Trader Strategy Analytics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")

st.divider()

# 5. ABAS
tab1, tab2, tab3 = st.tabs(["🚀 Gráficos", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
        st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento", template="plotly_dark"), use_container_width=True)
    else:
        st.info("Sem dados.")

with tab2:
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

with tab3:
    # VOLTEI COM O FORM PARA O ENTER FUNCIONAR
    with st.form("form_novo_trade", clear_on_submit=True):
        st.subheader("Nova Operação")
        c1, c2, c3, c4 = st.columns(4)
        ativo = c1.text_input("Ativo", value="USDJPY")
        tipo = c2.selectbox("Tipo", ["buy", "sell"])
        vol = c3.number_input("Volume", value=0.01, format="%.2f")
        lucro = c4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        c5, c6, c7, c8 = st.columns(4)
        p_in = c5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = c6.number_input("Saída", value=0.0, format="%.3f")
        sl = c7.number_input("SL", value=0.0, format="%.3f")
        tp = c8.number_input("TP", value=0.0, format="%.3f")
        
        submit = st.form_submit_button("💾 SALVAR OPERAÇÃO (ENTER)")
        
        if submit:
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": lucro, "Obs": ""
            }])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("✅ SALVO NA NUVEM!")
                st.rerun()
            except:
                st.error("❌ ERRO NA NUVEM: Configure os 'Secrets' com a chave JSON do Google.")
                st.warning("Dados salvos apenas nesta sessão.")
