import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from google.cloud import firestore
from google.oauth2 import service_account

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #58a6ff !important; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
    .insight-card { background-color: #1c2128; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
    .disclaimer { background-color: #3d1f00; border: 1px solid #ff8c00; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 12px; color: #ff8c00; }
    .upgrade-banner { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FIRESTORE CLIENT
# ==========================================
@st.cache_resource
def get_firestore_client():
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

db, db_error = get_firestore_client()

# ==========================================
# 3. FUNÇÕES DE DADOS (DEFINIR ANTES DE USAR)
# ==========================================
def load_data():
    cols = ["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]
    if not db:
        return pd.DataFrame(columns=cols)
    
    try:
        docs = db.collection("users").document(st.session_state.user_id).collection("trades").order_by("Data").stream()
        data = []
        for doc in docs:
            data.append(doc.to_dict())
        
        if data:
            df = pd.DataFrame(data)
            for col in cols:
                if col not in df.columns:
                    df[col] = None
            return df[cols]
        return pd.DataFrame(columns=cols)
    except:
        return pd.DataFrame(columns=cols)

def salvar_trade(dados):
    if not db:
        return False, "Banco não conectado"
    
    plano = st.session_state.get("user_plano", "free")
    if plano == "free":
        try:
            docs = db.collection("users").document(st.session_state.user_id).collection("trades").stream()
            count = sum(1 for _ in docs)
            if count >= 50:
                return False, "🚫 Limite FREE atingido (50 trades). Faça upgrade para PRO!"
        except:
            pass
    
    try:
        db.collection("users").document(st.session_state.user_id).collection("trades").add(dados)
        return True, "✅ Salvo na Nuvem!"
    except Exception as e:
        return False, f"❌ Erro: {e}"

# ==========================================
# 4. TELA DE LOGIN
# ==========================================
def login_screen():
    st.markdown("<h1 style='text-align:center;'>📊 Trader Analytics Pro</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#8b949e;'>Gestão Profissional de Trades</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_login, tab_register = st.tabs(["🔑 Entrar", "🆕 Criar Conta"])
    
    with tab_login:
        email_login = st.text_input("Email", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            if not email_login or not senha_login:
                st.error("Preencha email e senha!")
            else:
                if db:
                    users_ref = db.collection("users").where("email", "==", email_login).stream()
                    user_doc = None
                    for doc in users_ref:
                        user_doc = doc.to_dict()
                        user_doc["id"] = doc.id
                        break
                    
                    if user_doc and user_doc.get("senha") == senha_login:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email_login
                        st.session_state.user_plano = user_doc.get("plano", "free")
                        st.session_state.user_id = user_doc["id"]
                        st.success(f"Bem-vindo, {email_login}! Plano: {user_doc.get('plano', 'free').upper()}")
                        st.rerun()
                    else:
                        st.error("Email ou senha incorretos!")
                else:
                    st.error("Banco de dados desconectado!")
    
    with tab_register:
        email_reg = st.text_input("Email", key="reg_email")
        senha_reg = st.text_input("Senha", type="password", key="reg_senha")
        conf_senha = st.text_input("Confirmar Senha", type="password", key="reg_conf")
        
        if st.button("Criar Conta Grátis", type="primary", use_container_width=True):
            if not email_reg or not senha_reg:
                st.error("Preencha todos os campos!")
            elif senha_reg != conf_senha:
                st.error("As senhas não coincidem!")
            elif len(senha_reg) < 6:
                st.error("Senha deve ter pelo menos 6 caracteres!")
            else:
                if db:
                    existing = db.collection("users").where("email", "==", email_reg).stream()
                    if any(existing):
                        st.error("Este email já está cadastrado!")
                    else:
                        db.collection("users").add({
                            "email": email_reg,
                            "senha": senha_reg,
                            "plano": "free",
                            "criado_em": datetime.now(),
                            "ativo": True
                        })
                        st.success("Conta criada! Faça login.")
                else:
                    st.error("Banco de dados desconectado!")
    
    st.markdown("""
    <div class='disclaimer'>
    ⚠️ <b>AVISO DE RISCO:</b> Esta plataforma é uma ferramenta de análise estatística. 
    Não constitui recomendação de investimento. Trading envolve risco de perda.
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# Verifica login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()

# ==========================================
# 5. INICIALIZAÇÃO DE SESSÃO (AGORA AQUI - ANTES DA SIDEBAR!)
# ==========================================
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# ==========================================
# 6. BARRA LATERAL (AGORA df_trades EXISTE!)
# ==========================================
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_email}**")
    
    plano = st.session_state.get("user_plano", "free")
    if plano == "free":
        st.markdown("🆓 Plano: **FREE** (até 50 trades)")
        st.markdown("""
        <div class='upgrade-banner'>
            <h4 style='color:white; margin:0;'>🚀 Upgrade para PRO</h4>
            <p style='color:#e0e0e0; font-size:14px;'>Trades ilimitados + métricas avançadas</p>
            <b style='color:#ffd700; font-size:20px;'>R$ 49/mês</b>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 Assinar PRO", use_container_width=True):
            st.link_button("Ir para Pagamento", "https://buy.stripe.com/SEU_LINK_AQUI", use_container_width=True)
    else:
        st.markdown("⭐ Plano: **PRO** (Ilimitado)")
    
    st.divider()
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    
    st.subheader("💾 Backup Local")
    # AGORA FUNCIONA POIS df_trades JÁ FOI CRIADO!
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV", csv_data, "meus_trades.csv", "text/csv", use_container_width=True)
    
    uploaded_file = st.file_uploader("📂 Carregar Backup", type="csv")
    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Backup carregado!")
        except:
            st.error("Erro no arquivo.")
    
    if st.button("🔄 Sincronizar Nuvem", use_container_width=True):
        st.session_state.df_trades = load_data()
        st.rerun()
    
    st.divider()
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# 7. PROCESSAMENTO DE MÉTRICAS
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
pf = (df[df["Lucro"] > 0]["Lucro"].sum() / abs(df[df["Lucro"] < 0]["Lucro"].sum())) if abs(df[df["Lucro"] < 0]["Lucro"].sum()) > 0 else 0

# ==========================================
# 8. DASHBOARD
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
# 9. ABAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights", "📝 Histórico", "➕ Novo Trade"])

with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            equity_curve = np.cumsum([st.session_state.capital_inicial] + df["Lucro"].tolist())
            st.plotly_chart(px.area(y=equity_curve, title="Crescimento da Conta", template="plotly_dark"), use_container_width=True)
        with col_b:
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            st.plotly_chart(px.bar(df, y="Risco_Pts", title="Risco em Pontos", color_discrete_sequence=['#f85149'], template="plotly_dark"), use_container_width=True)
    else:
        st.info("Adicione trades para ver gráficos.")

with tab2:
    st.header("📚 Resumo Estatístico")
    if not df.empty:
        st.markdown(f"""
        <div class='insight-card'>
            <h4>📉 Análise de Perdas</h4>
            <p>Perda média: <b>$ {avg_loss_cash:.2f}</b> | <b>{avg_loss_pts:.3f} pts</b></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aguardando dados.")

with tab3:
    st.dataframe(df.sort_index(ascending=False).style.format({
        "Entrada": "{:.3f}", "Saída": "{:.3f}", "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "{:.2f}"
    }), use_container_width=True)

with tab4:
    if st.session_state.get("user_plano") == "free" and len(df) >= 45:
        st.warning(f"⚠️ Você usou {len(df)}/50 trades gratuitos. Faça upgrade para PRO!")
    
    with st.form("add_trade", clear_on_submit=True):
        st.subheader("Registrar Operação")
        r1, r2, 
