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
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO HÍBRIDA (GOOGLE SHEETS + MEMÓRIA LOCAL)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Tenta ler do Google Sheets (ttl=0 para dados sempre frescos)
        return conn.read(ttl="0s")
    except:
        # Se falhar (sem internet ou sem config), retorna DataFrame vazio com as colunas certas
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

# Carrega os dados iniciais se não existirem na sessão
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL (BACKUP MANUAL)
with st.sidebar:
    st.title("🛡️ Segurança de Dados")
    st.info("Nuvem: Google Sheets Ativo")
    
    # Botão de Download (Manual)
    if not st.session_state.df_trades.empty:
        csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual (CSV)", csv_data, "meu_backup_trades.csv", "text/csv")
    
    # Botão de Upload (Manual)
    uploaded_file = st.file_uploader("📂 Restaurar de Backup Manual", type="csv")
    if uploaded_file:
        st.session_state.df_trades = pd.read_csv(uploaded_file)
        st.success("Backup restaurado na memória!")
        # Opcional: st.rerun()

    st.divider()
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)

# 4. PROCESSAMENTO DE MÉTRICAS
st.title("📊 Trader Strategy Analytics")
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
n_losses = len(df[df["Lucro"] < 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0

# Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")

st.divider()

# 5. ABAS
tab1, tab2, tab3 = st.tabs(["🚀 Performance", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
        fig = px.area(x=range(len(equity_curve)), y=equity_curve, title="Curva de Crescimento")
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sem dados para análise.")

with tab2:
    # Exibição com 3 casas decimais
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
        
        if st.form_submit_button("💾 Salvar (Nuvem + Local)"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": lucro, "Obs": ""
            }])
            
            # 1. Atualiza Memória Local
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            
            # 2. Tenta salvar no Google Sheets
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("Dados sincronizados com Google Sheets! ✅")
            except:
                st.warning("Salvo apenas localmente. Verifique a conexão com o Google. ⚠️")
            
            st.rerun()
