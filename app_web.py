import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA E TEMA DARK
st.set_page_config(page_title="Trader Strategy Analytics", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DOS DADOS E MEMÓRIA
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"
    ])

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

if 'capital_inicial' not in st.session_state:
    st.session_state.capital_inicial = 20.0

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Risco")
    st.session_state.capital_inicial = st.number_input("Capital Atual (USD)", value=st.session_state.capital_inicial)
    st.divider()
    
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
tab1, tab2, tab3 = st.tabs(["🚀 Análise & Projeção", "📝 Histórico Completo", "➕ Registrar Operação"])

with tab1:
    if total_trades > 0:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_eq = px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta", labels={'x':'Trades','y':'Capital USD'})
            fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_eq, use_container_width=True)
            
        with col_right:
            st.subheader("🔮 Projeção (30 dias)")
            trades_por_dia = total_trades / max(len(df["Data"].unique()), 1)
            media_por_trade = total_profit / total_trades
            ganho_diario_estimado = trades_por_dia * media_por_trade
            p30 = equity + (ganho_diario_estimado * 30)
            st.info(f"📅 Estimativa 30 dias: **$ {p30:,.2f}**")
            if profit_factor > 1: st.success("Estratégia Vencedora! 🟢")
            else: st.error("Expectativa Negativa. 🔴")
    else:
        st.warning("Aguardando dados para análise.")

with tab2:
    # Formatação de colunas para 3 casas decimais na exibição
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)
    
    if st.button("🗑️ Resetar Tudo"):
        st.session_state.trades = pd.DataFrame(columns=df.columns)
        st.rerun()

with tab3:
    with st.form("form_add", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        
        row1_1, row1_2, row1_3, row1_4 = st.columns(4)
        # Usa o 'last_asset' como valor padrão
        ativo = row1_1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = row1_2.selectbox("Tipo", ["buy", "sell"])
        vol = row1_3.number_input("Volume/Lote", value=0.01, format="%.2f")
        lucro_manual = row1_4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        st.write("**Pontos de Preço (Precisão de 3 casas)**")
        row2_1, row2_2, row2_3, row2_4 = st.columns(4)
        p_in = row2_1.number_input("Preço Entrada", value=0.0, format="%.3f")
        p_out = row2_2.number_input("Preço Saída", value=0.0, format="%.3f")
        sl = row2_3.number_input("Stop Loss", value=0.0, format="%.3f")
        tp = row2_4.number_input("Take Profit", value=0.0, format="%.3f")
        
        obs = st.text_input("Observação")
        
        if st.form_submit_button("💾 Salvar Trade"):
            # Atualiza o último ativo usado para a próxima vez
            st.session_state.last_asset = ativo
            
            final_lucro = lucro_manual
            if final_lucro == 0 and p_in != 0 and p_out != 0:
                diff = (p_out - p_in) if tipo == "buy" else (p_in - p_out)
                final_lucro = diff * vol * 1000.0 
            
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": final_lucro, "Obs": obs
            }])
            st.session_state.trades = pd.concat([st.session_state.trades, novo], ignore_index=True)
            st.success(f"Trade de {ativo} registrado!")
            st.rerun()
