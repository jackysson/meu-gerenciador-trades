import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from google.cloud import firestore
from google.oauth2 import service_account

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==========================================
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO COM FIREBASE FIRESTORE
# ==========================================

@st.cache_resource
def get_firestore_client():
    """Conecta ao Firestore usando as secrets do Streamlit Cloud"""
    try:
        secrets = st.secrets["firebase"]
        
        creds = service_account.Credentials.from_service_account_info({
            "type": secrets["type"],
            "project_id": secrets["project_id"],
            "private_key_id": secrets["private_key_id"],
            "private_key": secrets["private_key"],
            "client_email": secrets["client_email"],
            "client_id": secrets["client_id"],
            "auth_uri": secrets["auth_uri"],
            "token_uri": secrets["token_uri"],
        })
        
        client = firestore.Client(credentials=creds, project=secrets["project_id"])
        return client, None
    except Exception as e:
        return None, str(e)

db, error_msg = get_firestore_client()

# ==========================================
# 3. FUNÇÕES DE LEITURA E ESCRITA
# ==========================================

def load_data():
    """Lê todos os trades do Firestore"""
    cols = ["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]
    
    if not db:
        return pd.DataFrame(columns=cols)
    
    try:
        docs = db.collection("trades").order_by("Data").stream()
        data = []
        for doc in docs:
            data.append(doc.to_dict())
        
        if data:
            df = pd.DataFrame(data)
            # Garante que todas as colunas existam
            for col in cols:
                if col not in df.columns:
                    df[col] = None
            return df[cols]
        
        return pd.DataFrame(columns=cols)
    except Exception as e:
        st.error(f"Erro ao ler do Firestore: {e}")
        return pd.DataFrame(columns=cols)

def salvar_trade(dados):
    """Salva um trade no Firestore"""
    if not db:
        return False, "Banco não conectado"
    
    try:
        db.collection("trades").add(dados)
        return True, "✅ Salvo na Nuvem (Firestore)!"
    except Exception as e:
        return False, f"❌ Erro ao salvar: {e}"

# ==========================================
# 4. INICIALIZAÇÃO DE SESSÃO
# ==========================================

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# ==========================================
# 5. BARRA LATERAL
# ==========================================

with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    
    if db:
        st.success("✅ Firestore Conectado")
    else:
        st.warning("⚠️ Modo Offline")
        if error_msg:
            st.error(f"Detalhe: {error_msg}")
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    
    st.subheader("💾 Backup Local")
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Meus Dados (CSV)", csv_data, "meus_trades.csv", "text/csv")
    
    uploaded_file = st.file_uploader("📂 Carregar Backup", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Backup carregado!")
        except:
            st.error("Erro no arquivo.")
    
    if st.button("🔄 Sincronizar com Nuvem"):
        st.session_state.df_trades = load_data()
        st.rerun()

# ==========================================
# 6. PROCESSAMENTO DE MÉTRICAS
# ==========================================

df = st.session_state.df_trades

for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

loss_df = df[df["Lucro"] < 0]
n_losses = len(loss_df)
avg_loss_cash = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if n_losses > 0 else 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
n_wins = len(df[df["Lucro"] > 0])
wr = (n_wins / len(df) * 100) if len(df) > 0 else 0
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) \
     if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

# ==========================================
# 7. DASHBOARD PRINCIPAL
# ==========================================

st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# ==========================================
# 8. ABAS
# ==========================================

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights & Resumo", "📝 Histórico", "➕ Novo Trade"])

# --- ABA 1: GRÁFICOS ---
with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(
                px.area(y=equity_curve, title="Crescimento da Conta", template="plotly_dark"),
                use_container_width=True
            )
        with col_b:
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            st.plotly_chart(
                px.bar(df, y="Risco_Pts", title="Risco em Pontos por Trade",
                       color_discrete_sequence=['#f85149'], template="plotly_dark"),
                use_container_width=True
            )
    else:
        st.info("Adicione trades para ver os gráficos.")

# --- ABA 2: INSIGHTS ---
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
        st.markdown(
            f"<div class='insight-card'><h4>🔮 Projeção (30 Trades)</h4>"
            f"<p>Capital estimado: <b>$ {p30:,.2f}</b>.</p></div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Aguardando dados.")

# --- ABA 3: HISTÓRICO ---
with tab3:
    st.dataframe(
        df.sort_index(ascending=False).style.format({
            "Entrada": "{:.3f}", "Saída": "{:.3f}",
            "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
        }),
        use_container_width=True
    )

# --- ABA 4: NOVO TRADE ---
with tab4:
    with st.form("add_trade_vfinal", clear_on_submit=True):
        st.subheader("Registrar Operação")
        r1, r2, r3, r4 = st.columns(4)
        ativo = r1.text_input("Ativo", value=st.session_state.last_asset)
        tipo = r2.selectbox("Tipo", ["buy", "sell"])
        vol = r3.number_input("Volume", value=0.01, format="%.2f")
        lucro = r4.number_input("Lucro Final (USD)", value=0.0, format="%.2f")
        
        st.write("---")
        
        r5, r6, r7, r8 = st.columns(4)
        p_in = r5.number_input("Entrada", value=0.0, format="%.3f")
        p_out = r6.number_input("Saída", value=0.0, format="%.3f")
        sl = r7.number_input("SL", value=0.0, format="%.3f")
        tp = r8.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR TRADE"):
            st.session_state.last_asset = ativo
            
            # Dados no formato do Firestore (dicionário)
            trade_data = {
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ativo": ativo,
                "Tipo": tipo,
                "Volume": float(vol),
                "Entrada": float(p_in),
                "Saída": float(p_out),
                "SL": float(sl),
                "TP": float(tp),
                "Lucro": float(lucro),
                "Obs": ""
            }
            
            # Adiciona ao DataFrame local
            nova_linha = [
                trade_data["Data"], ativo, tipo, vol, p_in, p_out, sl, tp, lucro, ""
            ]
            st.session_state.df_trades = pd.concat(
                [st.session_state.df_trades, pd.DataFrame([nova_linha], columns=df.columns)],
                ignore_index=True
            )
            
            # Salva no Firestore
            if db:
                sucesso, msg = salvar_trade(trade_data)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("⚠️ Salvo apenas localmente (nuvem desconectada).")
            
            st.rerun()
