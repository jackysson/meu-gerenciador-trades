import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

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

# 2. CONEXÃO DIRETA E ESTÁVEL (GOOGLE SHEETS)
def get_gspread_client():
    try:
        # Puxa os dados dos Secrets
        info = st.secrets["gcp_service_account"]
        creds_dict = {
            "type": info["type"],
            "project_id": info["project_id"],
            "private_key_id": info["private_key_id"],
            "private_key": info["private_key"].replace("\\n", "\n"),
            "client_email": info["client_email"],
            "client_id": info["client_id"],
            "auth_uri": info["auth_uri"],
            "token_uri": info["token_uri"],
            "auth_provider_x509_cert_url": info["auth_provider_x509_cert_url"],
            "client_x509_cert_url": info["client_x509_cert_url"]
        }
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope )
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo link
        sheet = client.open_by_url(st.secrets["spreadsheet_url"]).sheet1
        return sheet
    except Exception as e:
        st.sidebar.error(f"Erro de Conexão: {e}")
        return None

client_sheet = get_gspread_client()

def load_data():
    if client_sheet:
        try:
            data = client_sheet.get_all_records()
            if not data:
                return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])
            return pd.DataFrame(data)
        except:
            return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])
    return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

# Inicializa dados
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if client_sheet: st.success("✅ Nuvem Conectada")
    else: st.warning("⚠️ Modo Offline")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Backup (CSV)", csv_data, "meus_trades.csv", "text/csv")
    
    if st.button("🔄 Sincronizar Agora"):
        st.session_state.df_trades = load_data()
        st.rerun()

# 4. PROCESSAMENTO DE MÉTRICAS (TUDO O QUE VOCÊ PEDIU)
df = st.session_state.df_trades
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns: df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Métricas de Perda
loss_df = df[df["Lucro"] < 0]
avg_loss_cash = abs(loss_df["Lucro"].mean()) if len(loss_df) > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if len(loss_df) > 0 else 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wins = len(df[df["Lucro"] > 0])
losses = len(df[df["Lucro"] < 0])
wr = (wins / len(df) * 100) if len(df) > 0 else 0
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

# 5. DASHBOARD
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", wins)
c3.metric("❌ Derrotas", losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# 6. ABAS
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            st.plotly_chart(px.bar(df, y="Risco_Pts", title="Risco em Pontos por Trade", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else: st.info("Sem dados.")

with tab2:
    st.header("📚 Resumo Estatístico")
    if not df.empty:
        st.markdown(f"""
        <div class='insight-card'>
            <h4>📉 Análise de Perdas</h4>
            <p>Perda média em dinheiro: <b>$ {avg_loss_cash:.2f}</b></p>
            <p>Perda média em pontos: <b>{avg_loss_pts:.3f} pts</b></p>
        </div>
        """, unsafe_allow_html=True)
        media_trade = total_profit / len(df)
        p30 = equity + (media_trade * 30)
        st.markdown(f"<div class='insight-card'><h4>🔮 Projeção (30 Trades)</h4><p>Capital estimado: <b>$ {p30:,.2f}</b>.</p></div>", unsafe_allow_html=True)

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab4:
    with st.form("add_trade_final", clear_on_submit=True):
        st.subheader("Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value="USDJPY")
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("SL", value=0.0, format="%.3f")
        tp = r8.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR NO HISTÓRICO"):
            nova_linha = [
                datetime.now().strftime("%Y-%m-%d"), ativo, tipo, vol,
                p_in, p_out, sl, tp, lucro, ""
            ]
            if client_sheet:
                try:
                    client_sheet.append_row(nova_linha)
                    st.success("✅ Salvo na Nuvem!")
                    st.session_state.df_trades = load_data()
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.warning("Offline: Dados não salvos.")
