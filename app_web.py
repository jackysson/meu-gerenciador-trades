import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

# Estilo visual profissional
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
# Versão simplificada para evitar erros de argumentos inesperados
def start_connection():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # O link da planilha será lido automaticamente dos Secrets
        df = conn.read(ttl="0s")
        return df, conn
    except Exception as e:
        st.sidebar.error(f"Erro de Configuração: {e}")
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None

df_cloud, conn = start_connection()

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = df_cloud

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if conn is not None:
        st.success("✅ Conectado à Nuvem")
    else:
        st.warning("⚠️ Modo Offline (Verifique os Secrets)")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup Manual", csv_data, "backup_trades.csv", "text/csv")

# 4. PROCESSAMENTO DE MÉTRICAS (TODAS AS FUNÇÕES SOLICITADAS)
df = st.session_state.df_trades
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns: df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins_df = df[df["Lucro"] > 0]
loss_df = df[df["Lucro"] < 0]
n_wins, n_losses = len(wins_df), len(loss_df)
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
pf = (wins_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0

# 5. DASHBOARD PRINCIPAL
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            # Risco em dinheiro (Entrada - SL)
            df["Risco_Cash"] = abs(df["Entrada"] - df["SL"]) * df["Volume"] * 1000
            st.plotly_chart(px.bar(df, y="Risco_Cash", title="Risco por Operação ($)", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else: st.info("Adicione trades para visualizar.")

with tab2:
    st.header("📚 Resumo Estratégico")
    if not df.empty:
        st.markdown(f"<div class='insight-card'><h4>Saúde da Estratégia: {'Vencedora 🟢' if pf > 1 else 'Alerta 🔴'}</h4><p>Seu Profit Factor atual é de {pf:.2f}.</p></div>", unsafe_allow_html=True)
        media_trade = total_profit / len(df)
        p30 = equity + (media_trade * 30)
        st.markdown(f"<div class='insight-card'><h4>🔮 Projeção (30 Trades)</h4><p>Estimativa de capital futuro: <b>$ {p30:,.2f}</b>.</p></div>", unsafe_allow_html=True)
    else: st.info("Aguardando dados para gerar resumo.")

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab4:
    with st.form("add_trade_vfinal", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        st.write("**Preços (3 casas decimais)**")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("SL", value=0.0, format="%.3f")
        tp = r8.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR TRADE"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp, "Lucro": lucro, "Obs": ""
            }])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            if conn:
                try:
                    conn.update(data=st.session_state.df_trades)
                    st.success("✅ Salvo na Nuvem!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar na nuvem: {e}")
            else: st.warning("Salvo apenas localmente.")
