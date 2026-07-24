import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide" )

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 15px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Tenta ler os dados da nuvem
        data = conn.read(ttl="0s")
        return data
    except Exception as e:
        # Se falhar, cria um banco de dados vazio na memória
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

# Carregar dados para a sessão
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    
    st.divider()
    # Backup Manual (Sempre bom ter!)
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup Manual (CSV)", csv_data, "meus_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Restaurar de Backup", type="csv")
    if uploaded_file:
        st.session_state.df_trades = pd.read_csv(uploaded_file)
        st.success("Dados carregados na memória!")

# 4. CÁLCULOS
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins_df = df[df["Lucro"] > 0]
loss_df = df[df["Lucro"] < 0]
n_wins = len(wins_df)
n_losses = len(loss_df)
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
profit_factor = (wins_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0

# 5. CARDS DE MÉTRICAS (VOLTARAM VITÓRIAS E DERROTAS)
st.title("📊 Trader Strategy Analytics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{profit_factor:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            fig_dist = px.histogram(df, x="Lucro", color=df["Lucro"] > 0, title="Distribuição de Resultados", color_discrete_map={True: "#3fb950", False: "#f85149"}, template="plotly_dark")
            st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.warning("Sem dados para análise.")

with tab2:
    st.header("📚 Resumo Estratégico")
    if not df.empty:
        st.markdown(f"<div class='insight-card'><h4>Saúde: {'Vencedora 🟢' if profit_factor > 1 else 'Alerta 🔴'}</h4><p>Seu Profit Factor é {profit_factor:.2f}.</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-card'><h4>Ritmo de Ganhos</h4><p>Seu lucro médio por trade é de $ {(total_profit/len(df)):,.2f}.</p></div>", unsafe_allow_html=True)
    else:
        st.info("Aguardando trades...")

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({"Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"}), use_container_width=True)
    if st.button("🗑️ Limpar Tudo (CUIDADO)"):
        st.session_state.df_trades = pd.DataFrame(columns=df.columns)
        try: conn.update(data=st.session_state.df_trades); st.rerun()
        except: st.error("Erro ao limpar na nuvem.")

with tab4:
    st.subheader("Registrar Operação")
    # Removido o st.form para permitir salvamento mais fluido
    c1, c2, c3, c4 = st.columns(4)
    ativo = c1.text_input("Ativo", value="USDJPY")
    tipo = c2.selectbox("Tipo", ["buy", "sell"])
    vol = c3.number_input("Volume", value=0.01, format="%.2f")
    lucro = c4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
    
    st.write("---")
    c5, c6, c7, c8 = st.columns(4)
    p_in = c5.number_input("Entrada", value=0.0, format="%.3f")
    p_out = c6.number_input("Saída", value=0.0, format="%.3f")
    sl = c7.number_input("SL", value=0.0, format="%.3f")
    tp = c8.number_input("TP", value=0.0, format="%.3f")
    
    if st.button("💾 SALVAR TRADE (Clique ou Enter)"):
        novo = pd.DataFrame([{
            "Data": datetime.now().strftime("%Y-%m-%d"),
            "Ativo": ativo, "Tipo": tipo, "Volume": vol,
            "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
            "Lucro": lucro, "Obs": ""
        }])
        
        # Atualiza Memória
        st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
        
        # Tenta Gravar no Google
        try:
            conn.update(data=st.session_state.df_trades)
            st.success("✅ SALVO NA NUVEM COM SUCESSO!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ ERRO AO SALVAR NA NUVEM: Verifique os 'Secrets' no Streamlit Cloud.")
            st.warning("Os dados estão salvos apenas nesta sessão. Baixe o backup manual!")
