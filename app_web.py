import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO HÍBRIDA
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl="0s")
    except:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Segurança e Risco")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    
    if not st.session_state.df_trades.empty:
        csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual", csv_data, "backup_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Restaurar Backup", type="csv")
    if uploaded_file:
        st.session_state.df_trades = pd.read_csv(uploaded_file)
        st.success("Backup restaurado!")

# 4. PROCESSAMENTO DE MÉTRICAS AVANÇADAS
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
df["Entrada"] = pd.to_numeric(df["Entrada"], errors='coerce').fillna(0)
df["SL"] = pd.to_numeric(df["SL"], errors='coerce').fillna(0)

# Cálculo de Stop Loss em Pontos e Dinheiro Estimado
def calc_sl_metrics(row):
    if row["Entrada"] != 0 and row["SL"] != 0:
        pontos = abs(row["Entrada"] - row["SL"])
        # Para USDJPY, 1 ponto costuma ser 0.001 ou 0.01 dependendo da corretora
        # Aqui calculamos a distância bruta
        dinheiro = pontos * row["Volume"] * 1000.0 # Estimativa de risco financeiro
        return pontos, dinheiro
    return 0, 0

if not df.empty:
    df[["SL_Pontos", "SL_Dinheiro"]] = df.apply(lambda r: pd.Series(calc_sl_metrics(r)), axis=1)
    avg_sl_pts = df[df["SL_Pontos"] > 0]["SL_Pontos"].mean()
    avg_sl_cash = df[df["SL_Dinheiro"] > 0]["SL_Dinheiro"].mean()
else:
    avg_sl_pts = 0
    avg_sl_cash = 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wr = (len(df[df["Lucro"] > 0]) / len(df) * 100) if len(df) > 0 else 0

# 5. LAYOUT DE CARDS
st.title("📊 Trader Strategy Analytics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("🎯 Win Rate", f"{wr:.1f}%")
c3.metric("📉 Risco Médio ($)", f"$ {avg_sl_cash:.2f}")
c4.metric("📏 Risco Médio (Pts)", f"{avg_sl_pts:.3f}")
c5.metric("📈 Lucro Total", f"$ {total_profit:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3 = st.tabs(["🚀 Análise de Risco", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_eq = px.area(x=range(len(equity_curve)), y=equity_curve, title="Curva de Crescimento", labels={'x':'Trades','y':'USD'})
            fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_eq, use_container_width=True)
        
        with col_b:
            # Gráfico de Risco Planejado (SL)
            fig_risk = px.bar(df, x=df.index, y="SL_Dinheiro", title="Risco Financeiro por Trade (Stop Loss $)", color_discrete_sequence=['#f85149'])
            fig_risk.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_risk, use_container_width=True)
            
        st.info(f"💡 Sua relação média de risco é de **$ {avg_sl_cash:.2f}** por operação. Compare isso com seu lucro médio para saber seu Risk/Reward!")
    else:
        st.warning("Sem dados para análise.")

with tab2:
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab3:
    with st.form("add_trade", clear_on_submit=True):
        st.subheader("Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("SL", value=0.0, format="%.3f")
        tp = r8.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 Salvar Trade"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": lucro, "Obs": ""
            }])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("Sincronizado com a Nuvem! ✅")
            except:
                st.warning("Salvo apenas localmente. ⚠️")
            st.rerun()
