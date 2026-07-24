import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

# 2. CONEXÃO COM GOOGLE SHEETS
def get_connection():
    try:
        # Puxa as configurações dos Secrets
        creds = st.secrets["connections"]["gsheets"]
        fixed_key = creds["private_key"].replace("\\n", "\n")
        
        conn = st.connection("gsheets", 
                            type=GSheetsConnection,
                            spreadsheet=creds["spreadsheet"],
                            project_id=creds["project_id"],
                            private_key_id=creds["private_key_id"],
                            private_key=fixed_key,
                            client_email=creds["client_email"],
                            client_id=creds["client_id"])
        
        df = conn.read(ttl="0s")
        return df, conn
    except Exception as e:
        # Se falhar, avisa o erro exato na barra lateral
        st.sidebar.error(f"Erro de Conexão: {e}")
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None

df_cloud, conn = get_connection()

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = df_cloud

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if conn is not None:
        st.success("✅ Conectado à Nuvem")
    else:
        st.warning("⚠️ Modo Offline (Backup Ativo)")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup Manual", csv_data, "meus_trades.csv", "text/csv")

# 4. MÉTRICAS E DASHBOARD (VERSÃO COMPLETA)
df = st.session_state.df_trades
# Garantir colunas numéricas
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns: df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
n_losses = len(df[df["Lucro"] < 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

# ABAS
t1, t2, t3, t4 = st.tabs(["🚀 Gráficos", "📚 Insights", "📝 Histórico", "➕ Novo Trade"])

with t1:
    if not df.empty:
        equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
        st.plotly_chart(px.area(y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
    else: st.info("Sem dados.")

with t2:
    if not df.empty:
        st.markdown(f"<div style='background-color:#161b22;padding:20px;border-radius:10px;border-left:5px solid #58a6ff;'><h4>Resumo Estratégico</h4><p>Sua estratégia tem um Profit Factor de {pf:.2f}. Projeção para 30 trades: $ {(equity + (total_profit/len(df)*30)):,.2f}</p></div>", unsafe_allow_html=True)

with t3:
    st.dataframe(df.sort_index(ascending=False).style.format({"Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"}), use_container_width=True)

with t4:
    with st.form("add_trade_vfinal", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value="USDJPY")
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("SL", value=0.0, format="%.3f")
        tp = r8.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR TRADE"):
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol, "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp, "Lucro": lucro, "Obs": ""}])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            if conn:
                try:
                    conn.update(data=st.session_state.df_trades)
                    st.success("✅ Salvo na Nuvem!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.warning("Salvo apenas localmente.")
