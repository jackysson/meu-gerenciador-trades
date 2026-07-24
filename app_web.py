import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

# Estilo Visual Dark Moderno
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS (MÉTODO JSON BRUTO) ---
def get_gspread_client():
    try:
        # Puxa o JSON inteiro de um único segredo para evitar erro de PEM
        json_string = st.secrets["google_service_account_json"]
        creds_dict = json.loads(json_string)
        
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
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

# Inicializar dados na sessão
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    if client_sheet:
        st.success("✅ Nuvem Conectada")
    else:
        st.warning("⚠️ Modo Offline (Verifique os Secrets)")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    
    st.subheader("💾 Backup Manual")
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Meus Dados (CSV)", csv_data, "meus_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Carregar Backup", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Dados carregados com sucesso!")
        except: st.error("Erro ao ler o arquivo.")
    
    if st.button("🔄 Sincronizar com Nuvem"):
        st.session_state.df_trades = load_data()
        st.rerun()

# --- PROCESSAMENTO DE MÉTRICAS ---
df = st.session_state.df_trades

# Garantir que todas as colunas existam
cols = ["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]
for c in cols:
    if c not in df.columns: df[c] = 0

# Converter para numérico
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Métricas de Perda e Risco
loss_df = df[df["Lucro"] < 0]
n_losses = len(loss_df)
avg_loss_cash = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if n_losses > 0 else 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

# --- DASHBOARD PRINCIPAL ---
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            fig_growth = px.area(y=equity_curve, title="Curva de Crescimento da Conta", template="plotly_dark")
            fig_growth.update_traces(line_color='#58a6ff')
            st.plotly_chart(fig_growth, use_container_width=True)
        with col_b:
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            fig_risk = px.bar(df, y="Risco_Pts", title="Risco em Pontos por Operação", color_discrete_sequence=['#f85149'], template="plotly_dark")
            st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.info("Adicione trades para visualizar os gráficos.")

with tab2:
    st.header("📚 Resumo Estratégico Detalhado")
    if not df.empty:
        st.markdown(f"""
        <div class='insight-card'>
            <h4>📉 Análise de Perdas e Risco</h4>
            <p>Sua perda média em dinheiro é de: <b>$ {avg_loss_cash:.2f}</b></p>
            <p>Sua perda média em pontos é de: <b>{avg_loss_pts:.3f} pts</b></p>
            <p><i>Diagnóstico: {'Sua gestão de risco está saudável.' if avg_loss_cash < (total_profit/len(df) if len(df)>0 else 1) else 'Cuidado: Suas perdas médias estão altas em relação aos ganhos.'}</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        media_trade = total_profit / len(df)
        p30 = equity + (media_trade * 30)
        st.markdown(f"""
        <div class='insight-card'>
            <h4>🔮 Projeção para os Próximos 30 Trades</h4>
            <p>Mantendo a performance atual, seu capital estimado será de: <b>$ {p30:,.2f}</b></p>
            <p>Expectativa Matemática por Trade: <b>$ {media_trade:.2f}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='insight-card'>
            <h4>💹 Saúde da Estratégia</h4>
            <p>Profit Factor: <b>{pf:.2f}</b></p>
            <p>Status: <b>{'ESTRATÉGIA VENCEDORA 🟢' if pf > 1 else 'ESTRATÉGIA EM ALERTA 🔴'}</b></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aguardando dados para gerar o resumo estatístico.")

with tab3:
    st.subheader("📝 Histórico de Operações")
    # Tabela formatada com 3 casas decimais para preços e 2 para lucro
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab4:
    with st.form("add_trade_final", clear_on_submit=True):
        st.subheader("➕ Registrar Nova Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume (Lote)", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        st.write("**Preços (Precisão de 3 casas decimais)**")
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Preço Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Preço Saída", value=0.0, format="%.3f")
        sl = r7.number_input("Stop Loss", value=0.0, format="%.3f")
        tp = r8.number_input("Take Profit", value=0.0, format="%.3f")
        
        obs = st.text_input("Observações")
        
        if st.form_submit_button("💾 SALVAR NO HISTÓRICO"):
            st.session_state.last_asset = ativo
            nova_linha = [
                datetime.now().strftime("%Y-%m-%d %H:%M"), ativo, tipo, vol,
                p_in, p_out, sl, tp, lucro, obs
            ]
            
            # Adicionar localmente primeiro
            novo_df = pd.DataFrame([dict(zip(cols, nova_linha))])
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo_df], ignore_index=True)
            
            # Tentar salvar na nuvem
            if client_sheet:
                try:
                    client_sheet.append_row(nova_linha)
                    st.success("✅ Salvo na Nuvem e no Histórico!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar na nuvem: {e}")
            else:
                st.warning("⚠️ Salvo apenas localmente (Nuvem desconectada).")
                st.rerun()
