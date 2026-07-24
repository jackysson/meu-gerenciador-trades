import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO PARA CONSERTAR A CHAVE E CONECTAR
def get_connection():
    try:
        # Tenta pegar os dados dos secrets
        creds = st.secrets["connections"]["gsheets"]
        
        # O SEGREDO: Vamos limpar a chave privada manualmente aqui no código
        raw_key = creds["private_key"]
        fixed_key = raw_key.replace("\\n", "\n") # Troca o texto \n por uma quebra de linha real
        
        # Criar uma conexão manual mais robusta
        conn = st.connection("gsheets", 
                            type=GSheetsConnection,
                            spreadsheet=creds["spreadsheet"],
                            project_id=creds["project_id"],
                            private_key_id=creds["private_key_id"],
                            private_key=fixed_key,
                            client_email=creds["client_email"],
                            client_id=creds["client_id"])
        
        return conn.read(ttl="0s"), conn
    except Exception as e:
        st.sidebar.warning(f"⚙️ Modo Offline (Backup Manual Ativo)")
        # Se falhar, retorna vazio para não travar o app
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None

df_cloud, conn = get_connection()

# Inicializa o dataframe na sessão
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = df_cloud

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    if not st.session_state.df_trades.empty:
        csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual", csv_data, "backup_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Restaurar Backup", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Backup carregado!")
        except: st.error("Arquivo inválido.")

# 4. PROCESSAMENTO
current_df = st.session_state.df_trades
# Garantir colunas básicas
for col in ["Lucro", "Entrada", "SL", "Volume"]:
    if col not in current_df.columns: current_df[col] = 0

current_df["Lucro"] = pd.to_numeric(current_df["Lucro"], errors='coerce').fillna(0)
total_profit = current_df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins = len(current_df[current_df["Lucro"] > 0])
losses = len(current_df[current_df["Lucro"] < 0])
wr = (wins / len(current_df) * 100) if len(current_df) > 0 else 0

# 5. DASHBOARD
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", wins)
c3.metric("❌ Derrotas", losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")

st.divider()

# 6. ABAS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not current_df.empty:
        equity_curve = np.cumsum([st.session_state.capital_inicial] + current_df["Lucro"].tolist())
        st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento", template="plotly_dark"), use_container_width=True)
    else: st.warning("Sem dados.")

with tab2:
    st.header("📚 Resumo Inteligente")
    if not current_df.empty:
        st.markdown(f"<div class='insight-card'><h4>Ritmo de Ganhos</h4><p>Seu lucro total é de $ {total_profit:,.2f}.</p></div>", unsafe_allow_html=True)
    else: st.info("Registre trades para ver os insights.")

with tab3:
    st.dataframe(current_df.sort_index(ascending=False), use_container_width=True)

with tab4:
    with st.form("add_trade", clear_on_submit=True):
        st.subheader("Registrar Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        if st.form_submit_button("💾 SALVAR TRADE"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol, "Lucro": lucro}])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            
            if conn is not None:
                try:
                    conn.update(data=st.session_state.df_trades)
                    st.success("✅ SALVO NA NUVEM!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao sincronizar: {e}")
            else:
                st.warning("⚠️ Dados salvos apenas nesta sessão (Modo Offline).")
