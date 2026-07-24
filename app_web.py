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

# 2. CONEXÃO COM GOOGLE SHEETS (CORREÇÃO DEFINITIVA)
def start_connection():
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            # 1. Pegamos todos os dados dos Secrets
            all_creds = dict(st.secrets["connections"]["gsheets"])
            
            # 2. SEPARAMOS o link da planilha das credenciais de acesso
            # Isso evita o erro de 'unexpected keyword argument spreadsheet'
            spreadsheet_url = all_creds.pop("spreadsheet", None)
            all_creds.pop("type", None) # Remove 'type' para evitar duplicidade
            
            # 3. Limpamos a chave privada
            if "private_key" in all_creds:
                all_creds["private_key"] = all_creds["private_key"].replace("\\n", "\n")
            
            # 4. Iniciamos a conexão apenas com a autenticação
            conn = st.connection("gsheets", type=GSheetsConnection, **all_creds)
            
            # 5. Lemos os dados usando o link que separamos
            df = conn.read(spreadsheet=spreadsheet_url, ttl="0s")
            return df, conn, spreadsheet_url
        else:
            return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None, None
    except Exception as e:
        st.sidebar.error(f"⚠️ Erro de Configuração: {e}")
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]), None, None

df_cloud, conn, sheet_url = start_connection()

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = df_cloud

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if conn is not None: st.success("✅ Conectado à Nuvem")
    else: st.warning("⚠️ Modo Offline")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup Manual", csv_data, "backup_trades.csv", "text/csv")

# 4. PROCESSAMENTO DE MÉTRICAS (EXATAMENTE COMO VOCÊ PEDIU)
df = st.session_state.df_trades
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns: df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Cálculos de Perda e Risco
loss_df = df[df["Lucro"] < 0]
n_losses = len(loss_df)
avg_loss_cash = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 0
# Cálculo de pontos de perda (Entrada - SL)
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if n_losses > 0 else 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

# 5. DASHBOARD
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
            # Gráfico de Risco por Operação
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            st.plotly_chart(px.bar(df, y="Risco_Pts", title="Risco em Pontos por Trade", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else: st.info("Adicione trades para ver os gráficos.")

with tab2:
    st.header("📚 Resumo Detalhado das Métricas")
    if not df.empty:
        st.markdown(f"""
        <div class='insight-card'>
            <h4>📉 Análise de Perdas (Drawdown Médio)</h4>
            <p>Sua perda média em dinheiro é de: <b>$ {avg_loss_cash:.2f}</b></p>
            <p>Sua perda média em pontos é de: <b>{avg_loss_pts:.3f} pts</b></p>
            <p><i>Dica: Se sua perda média em pontos for maior que seu lucro médio, você precisa de um Win Rate muito alto para sobreviver.</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        media_trade = total_profit / len(df)
        p30 = equity + (media_trade * 30)
        st.markdown(f"<div class='insight-card'><h4>🔮 Projeção para os Próximos 30 Trades</h4><p>Estimativa de capital futuro: <b>$ {p30:,.2f}</b>.</p></div>", unsafe_allow_html=True)
    else: st.info("Aguardando dados para gerar o resumo.")

with tab3:
    # Tabela formatada com 3 casas decimais
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab4:
    with st.form("add_trade_pro", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        st.write("**Preços (Precisão de 3 casas)**")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("Stop Loss", value=0.0, format="%.3f")
        tp = r8.number_input("Take Profit", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR TRADE"):
            st.session_state.last_asset = ativo
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ativo": ativo, "Tipo": tipo, "Volume": vol,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp, "Lucro": lucro, "Obs": ""
            }])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            if conn:
                try:
                    conn.update(spreadsheet=sheet_url, data=st.session_state.df_trades)
                    st.success("✅ Salvo na Nuvem!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar na nuvem: {e}")
            else: st.warning("Salvo apenas localmente.")
