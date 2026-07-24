import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA E TEMA DARK FORÇADO
st.set_page_config(page_title="Trader Strategy Analytics", page_icon="📊", layout="wide")

# CSS para garantir o modo Dark e melhorar o visual dos cards
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre; background-color: #161b22; border-radius: 8px 8px 0 0; gap: 1px; }
    </style>
    """, unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DOS DADOS
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "Lucro", "Obs"
    ])

if 'capital_inicial' not in st.session_state:
    st.session_state.capital_inicial = 20.0

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Risco")
    st.session_state.capital_inicial = st.number_input("Capital Atual (USD)", value=st.session_state.capital_inicial)
    st.divider()
    
    # Exportar/Importar
    if not st.session_state.trades.empty:
        csv = st.session_state.trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup (CSV)", csv, "meus_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("Upload de Backup", type="csv")
    if uploaded_file:
        st.session_state.trades = pd.read_csv(uploaded_file)
        st.rerun()

# 4. PROCESSAMENTO DE MÉTRICAS
st.title("📊 Trader Strategy Analytics")
df = st.session_state.trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins_df = df[df["Lucro"] > 0]
loss_df = df[df["Lucro"] < 0]
total_trades = len(df)
n_wins = len(wins_df)
n_losses = len(loss_df)

wr = (n_wins / total_trades * 100) if total_trades > 0 else 0
avg_win = wins_df["Lucro"].mean() if n_wins > 0 else 0
avg_loss = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 1e-9
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
tab1, tab2, tab3 = st.tabs(["🚀 Análise & Projeção", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if total_trades > 0:
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Gráfico de Equity
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_eq = px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta", labels={'x':'Trades','y':'Capital USD'})
            fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_eq, use_container_width=True)
            
        with col_right:
            # Projeção de Ganhos
            st.subheader("🔮 Projeção (30 dias)")
            # Cálculo de taxa diária aproximada
            trades_por_dia = total_trades / max(len(df["Data"].unique()), 1)
            media_por_trade = total_profit / total_trades
            ganho_diario_estimado = trades_por_dia * media_por_trade
            
            p30 = equity + (ganho_diario_estimado * 30)
            p60 = equity + (ganho_diario_estimado * 60)
            p90 = equity + (ganho_diario_estimado * 90)
            
            st.write(f"Se mantiver o ritmo de **{trades_por_dia:.1f} trades/dia**:")
            st.info(f"📅 30 dias: **$ {p30:,.2f}**")
            st.info(f"📅 60 dias: **$ {p60:,.2f}**")
            st.info(f"📅 90 dias: **$ {p90:,.2f}**")
            
            if profit_factor > 1:
                st.success("Sua estratégia é matematicamente vencedora! 🟢")
            else:
                st.error("Atenção: Estratégia com expectativa negativa. 🔴")

        # Gráfico de Distribuição de Lucros/Perdas
        fig_dist = px.histogram(df, x="Lucro", color=df["Lucro"] > 0, 
                               title="Distribuição de Resultados",
                               color_discrete_map={True: "#3fb950", False: "#f85149"},
                               labels={'Lucro':'Resultado USD', 'count':'Frequência'})
        fig_dist.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.warning("Aguardando dados para gerar análise estratégica.")

with tab2:
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    if st.button("🗑️ Resetar Tudo"):
        st.session_state.trades = pd.DataFrame(columns=df.columns)
        st.rerun()

with tab3:
    with st.form("form_add", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        c1, c2, c3 = st.columns(3)
        ativo = c1.text_input("Ativo (ex: USDJPY)")
        tipo = c2.selectbox("Tipo", ["buy", "sell"])
        lucro = c3.number_input("Resultado Final (USD)", format="%.2f", help="Use negativo para perdas")
        
        obs = st.text_input("Nota Mental (O que aconteceu?)")
        
        if st.form_submit_button("💾 Salvar Trade"):
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Lucro": lucro, "Obs": obs
            }])
            st.session_state.trades = pd.concat([st.session_state.trades, novo], ignore_index=True)
            st.success("Registrado!")
            st.rerun()
