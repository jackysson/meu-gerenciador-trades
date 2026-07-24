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
    st.title("🛡️ Gestão de Risco")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    
    if not st.session_state.df_trades.empty:
        csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual", csv_data, "backup_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Restaurar Backup", type="csv")
    if uploaded_file:
        st.session_state.df_trades = pd.read_csv(uploaded_file)
        st.success("Backup restaurado!")

# 4. PROCESSAMENTO DE MÉTRICAS
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
df["Entrada"] = pd.to_numeric(df["Entrada"], errors='coerce').fillna(0)
df["SL"] = pd.to_numeric(df["SL"], errors='coerce').fillna(0)

def calc_sl_metrics(row):
    if row["Entrada"] != 0 and row["SL"] != 0:
        pontos = abs(row["Entrada"] - row["SL"])
        dinheiro = pontos * row["Volume"] * 1000.0
        return pontos, dinheiro
    return 0, 0

if not df.empty:
    df[["SL_Pontos", "SL_Dinheiro"]] = df.apply(lambda r: pd.Series(calc_sl_metrics(r)), axis=1)
    avg_sl_pts = df[df["SL_Pontos"] > 0]["SL_Pontos"].mean()
    avg_sl_cash = df[df["SL_Dinheiro"] > 0]["SL_Dinheiro"].mean()
    total_profit = df["Lucro"].sum()
    wins_df = df[df["Lucro"] > 0]
    loss_df = df[df["Lucro"] < 0]
    wr = (len(wins_df) / len(df) * 100)
    profit_factor = (wins_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0
else:
    avg_sl_pts = avg_sl_cash = total_profit = wr = profit_factor = 0

equity = st.session_state.capital_inicial + total_profit

# 5. HEADER E CARDS
st.title("📊 Trader Strategy Analytics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("🎯 Win Rate", f"{wr:.1f}%")
c3.metric("📉 Risco Médio ($)", f"$ {avg_sl_cash:.2f}")
c4.metric("📈 Profit Factor", f"{profit_factor:.2f}")
c5.metric("💵 Lucro Total", f"$ {total_profit:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.bar(df, x=df.index, y="SL_Dinheiro", title="Risco Planejado (Stop Loss $)", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else:
        st.warning("Sem dados para análise.")

with tab2:
    st.header("📚 Resumo das Estatísticas")
    if not df.empty:
        # Insight 1: Saúde da Conta
        status_pf = "Vencedora 🟢" if profit_factor > 1 else "Em Alerta 🔴"
        st.markdown(f"""<div class='insight-card'>
            <h4>💹 Saúde da Estratégia: {status_pf}</h4>
            <p>Seu <b>Profit Factor</b> é de {profit_factor:.2f}. Isso significa que para cada $ 1,00 perdido, você ganha $ {profit_factor:.2f}. 
            Valores acima de 1.5 indicam uma estratégia muito sólida.</p>
        </div>""", unsafe_allow_html=True)

        # Insight 2: Gerenciamento de Risco
        st.markdown(f"""<div class='insight-card'>
            <h4>📉 Gerenciamento de Risco</h4>
            <p>Seu risco médio por operação é de <b>$ {avg_sl_cash:.2f}</b> ({avg_sl_pts:.3f} pontos). 
            Mantenha este valor sob controle para evitar que uma única perda apague vários dias de lucro.</p>
        </div>""", unsafe_allow_html=True)

        # Insight 3: Win Rate vs Lucratividade
        st.markdown(f"""<div class='insight-card'>
            <h4>🎯 Win Rate ({wr:.1f}%)</h4>
            <p>Sua taxa de acerto atual indica que você acerta {wr:.1f} de cada 100 trades. 
            Lembre-se: o lucro real vem da combinação entre acertar mais e ganhar mais do que perde quando acerta.</p>
        </div>""", unsafe_allow_html=True)

        # Insight 4: Projeção
        trades_por_dia = len(df) / max(len(df["Data"].unique()), 1)
        media_por_trade = total_profit / len(df)
        p30 = equity + (trades_por_dia * media_por_trade * 30)
        st.markdown(f"""<div class='insight-card'>
            <h4>🔮 Projeção de Futuro</h4>
            <p>Mantendo o ritmo atual de <b>{trades_por_dia:.1f} trades/dia</b>, sua projeção para os próximos 30 dias é de <b>$ {p30:,.2f}</b>.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("Registre alguns trades para gerar o resumo automático.")

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({"Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"}), use_container_width=True)

with tab4:
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
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol, "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp, "Lucro": lucro, "Obs": ""}])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("Sincronizado na Nuvem! ✅")
            except:
                st.warning("Salvo localmente. ⚠️")
            st.rerun()
