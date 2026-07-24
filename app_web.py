import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Trader Analytics (Persistente)", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
# Nota: Você precisará configurar as credenciais no Streamlit Cloud (veja instruções abaixo)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Tenta ler a planilha. Se estiver vazia, retorna o esqueleto
        return conn.read(ttl="0s")
    except:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

df = load_data()

# Inicialização de memória local
if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"
if 'capital_inicial' not in st.session_state:
    st.session_state.capital_inicial = 20.0

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Risco")
    st.session_state.capital_inicial = st.number_input("Capital Atual (USD)", value=st.session_state.capital_inicial)
    st.divider()
    st.info("💡 Seus dados estão sendo salvos automaticamente no Google Sheets.")
    
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Local (CSV)", csv, "backup_trades.csv", "text/csv")

# 4. PROCESSAMENTO DE MÉTRICAS
st.title("📊 Trader Strategy Analytics (Google Cloud)")
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins_df = df[df["Lucro"] > 0]
loss_df = df[df["Lucro"] < 0]
total_trades = len(df)
n_wins = len(wins_df)
n_losses = len(loss_df)

wr = (n_wins / total_trades * 100) if total_trades > 0 else 0
profit_factor = (wins_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0

# 5. LAYOUT DE CARDS
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{profit_factor:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3 = st.tabs(["🚀 Análise & Projeção", "📝 Histórico", "➕ Registrar Operação"])

with tab1:
    if total_trades > 0:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_eq = px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta")
            fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_eq, use_container_width=True)
            
        with col_right:
            st.subheader("🔮 Projeção (30 dias)")
            media_por_trade = total_profit / total_trades
            p30 = equity + (media_por_trade * 30) # Estimativa simples
            st.info(f"📅 Estimativa 30 dias: **$ {p30:,.2f}**")
    else:
        st.warning("Aguardando dados para análise.")

with tab2:
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab3:
    with st.form("form_add", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
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
        
        if st.form_submit_button("💾 Salvar no Google Sheets"):
            st.session_state.last_asset = ativo
            novo_trade = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": lucro, "Obs": ""
            }])
            
            # Atualiza a planilha
            df_atualizado = pd.concat([df, novo_trade], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("Salvo com sucesso na nuvem!")
            st.rerun()
