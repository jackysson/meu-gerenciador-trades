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
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS (HÍBRIDA)
def get_connection():
    try:
        creds = st.secrets["connections"]["gsheets"]
        fixed_key = creds["private_key"].replace("\\n", "\n")
        conn = st.connection("gsheets", type=GSheetsConnection, spreadsheet=creds["spreadsheet"],
                            project_id=creds["project_id"], private_key_id=creds["private_key_id"],
                            private_key=fixed_key, client_email=creds["client_email"], client_id=creds["client_id"])
        return conn.read(ttl="0s"), conn
    except:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None

df_cloud, conn = get_connection()

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = df_cloud

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL (GESTÃO DE DADOS)
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if conn is None:
        st.warning("⚙️ Modo Offline (Backup Manual Ativo)")
    else:
        st.success("☁️ Conectado à Nuvem")
        
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    
    st.subheader("💾 Backup e Restauração")
    # O botão de baixar agora sempre aparece
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Meus Dados (CSV)", csv_data, "meus_trades.csv", "text/csv", help="Clique aqui para salvar seus trades no seu dispositivo.")
    
    uploaded_file = st.file_uploader("📂 Carregar Arquivo de Trades", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Dados carregados com sucesso!")
        except: st.error("Erro ao ler o arquivo.")

# 4. PROCESSAMENTO E MÉTRICAS
current_df = st.session_state.df_trades
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
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not current_df.empty:
        equity_curve = np.cumsum([st.session_state.capital_inicial] + current_df["Lucro"].tolist())
        st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Curva de Crescimento", template="plotly_dark"), use_container_width=True)
    else: st.warning("Adicione trades para ver os gráficos.")

with tab2:
    st.header("📚 Resumo das Estatísticas")
    if not current_df.empty:
        st.markdown(f"<div class='insight-card'><h4>📊 Resumo Operacional</h4><p>Você realizou {len(current_df)} trades. Seu lucro acumulado é de $ {total_profit:,.2f}.</p></div>", unsafe_allow_html=True)
        # Projeção
        media_trade = total_profit / len(current_df)
        p30 = equity + (media_trade * 30)
        st.markdown(f"<div class='insight-card'><h4>🔮 Projeção (Próximos 30 Trades)</h4><p>Se mantiver a performance, seu capital chegará a <b>$ {p30:,.2f}</b>.</p></div>", unsafe_allow_html=True)
    else: st.info("Registre trades para gerar o resumo automático.")

with tab3:
    st.dataframe(current_df.sort_index(ascending=False), use_container_width=True)

with tab4:
    with st.form("add_trade", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        if st.form_submit_button("💾 SALVAR TRADE (ENTER)"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol, "Lucro": lucro}])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            
            if conn is not None:
                try:
                    conn.update(data=st.session_state.df_trades)
                    st.success("✅ SALVO NA NUVEM!")
                    st.rerun()
                except Exception as e: st.error(f"Erro na nuvem: {e}")
            else:
                st.warning("⚠️ Salvo apenas localmente. Baixe o backup antes de sair!")
