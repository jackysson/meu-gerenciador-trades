import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    .insight-title { color: #58a6ff; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO HÍBRIDA (GOOGLE SHEETS + LOCAL)
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

# 3. BARRA LATERAL (BACKUP E GESTÃO)
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    st.subheader("💾 Backup de Segurança")
    if not st.session_state.df_trades.empty:
        csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Backup Manual (CSV)", csv_data, "meu_backup_trades.csv", "text/csv")
    uploaded_file = st.file_uploader("📂 Restaurar de Backup", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Backup carregado na memória!")
        except: st.error("Arquivo inválido.")

# 4. PROCESSAMENTO DE MÉTRICAS AVANÇADAS
df = st.session_state.df_trades
df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
df["Entrada"] = pd.to_numeric(df["Entrada"], errors='coerce').fillna(0)
df["SL"] = pd.to_numeric(df["SL"], errors='coerce').fillna(0)

def calc_risk(row):
    if row["Entrada"] != 0 and row["SL"] != 0:
        pts = abs(row["Entrada"] - row["SL"])
        cash = pts * row["Volume"] * 1000.0
        return pts, cash
    return 0, 0

if not df.empty:
    df[["SL_Pts", "SL_Cash"]] = df.apply(lambda r: pd.Series(calc_risk(r)), axis=1)
    avg_sl_pts = df[df["SL_Pts"] > 0]["SL_Pts"].mean()
    avg_sl_cash = df[df["SL_Cash"] > 0]["SL_Cash"].mean()
    total_profit = df["Lucro"].sum()
    wins_df = df[df["Lucro"] > 0]
    loss_df = df[df["Lucro"] < 0]
    n_wins, n_losses = len(wins_df), len(loss_df)
    wr = (n_wins / len(df) * 100)
    pf = (wins_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0
else:
    avg_sl_pts = avg_sl_cash = total_profit = n_wins = n_losses = wr = pf = 0

equity = st.session_state.capital_inicial + total_profit

# 5. HEADER E CARDS DE MÉTRICAS
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# 6. ABAS PRINCIPAIS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(x=range(len(equity_curve)), y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.bar(df, x=df.index, y="SL_Cash", title="Risco Planejado ($)", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else: st.warning("Sem dados para análise.")

with tab2:
    st.header("📚 Resumo Inteligente da Estratégia")
    if not df.empty:
        # Saúde da Estratégia
        st.markdown(f"""<div class='insight-card'><div class='insight-title'>💹 Saúde: {'Vencedora 🟢' if pf > 1 else 'Em Alerta 🔴'}</div>
            <p>Seu <b>Profit Factor</b> é de {pf:.2f}. Isso indica que para cada $1 perdido, você ganha ${pf:.2f}. Acima de 1.5 é o ideal para traders profissionais.</p></div>""", unsafe_allow_html=True)
        
        # Gerenciamento de Risco
        st.markdown(f"""<div class='insight-card'><div class='insight-title'>📉 Gerenciamento de Risco</div>
            <p>Seu risco médio por operação é de <b>$ {avg_sl_cash:.2f}</b> ({avg_sl_pts:.3f} pontos). Monitore se esse valor não está aumentando desproporcionalmente ao seu capital.</p></div>""", unsafe_allow_html=True)
        
        # Análise de Taxa de Acerto
        st.markdown(f"""<div class='insight-card'><div class='insight-title'>🎯 Eficiência (Win Rate: {wr:.1f}%)</div>
            <p>Você tem <b>{n_wins} vitórias</b> e <b>{n_losses} derrotas</b>. Lembre-se que no USDJPY, a consistência é mais importante do que acertar todos os trades.</p></div>""", unsafe_allow_html=True)
        
        # Projeção Futura
        media_por_trade = total_profit / len(df)
        p30 = equity + (media_por_trade * 30)
        st.markdown(f"""<div class='insight-card'><div class='insight-title'>🔮 Projeção de Futuro (30 dias)</div>
            <p>Mantendo o ritmo atual, sua projeção de capital para os próximos 30 trades é de <b>$ {p30:,.2f}</b>.</p></div>""", unsafe_allow_html=True)
    else: st.info("Registre alguns trades para gerar o resumo automático.")

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({"Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"}), use_container_width=True)
    if st.button("🗑️ Limpar Tudo (Nuvem + Local)"):
        st.session_state.df_trades = pd.DataFrame(columns=df.columns)
        try: conn.update(data=st.session_state.df_trades); st.rerun()
        except: st.error("Erro ao limpar na nuvem.")

with tab4:
    with st.form("add_trade", clear_on_submit=True):
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
        if st.form_submit_button("💾 SALVAR TRADE (ENTER)"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{"Data": datetime.now().strftime("%Y-%m-%d"), "Ativo": ativo, "Tipo": tipo, "Volume": vol, "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp, "Lucro": lucro, "Obs": ""}])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("✅ SALVO NA NUVEM!")
                st.rerun()
            except: st.error("❌ ERRO NA NUVEM: Verifique os Secrets.")
