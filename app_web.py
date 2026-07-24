import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    .metric-green { color: #3fb950 !important; }
    .metric-red { color: #f85149 !important; }
    .metric-gold { color: #ffd700 !important; }
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
# 3. FUNÇÕES DE DADOS
# ==========================================
def load_data():
    cols = ["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]
    if not db or 'user_id' not in st.session_state:
        return pd.DataFrame(columns=cols)
    try:
        docs = db.collection("users").document(st.session_state.user_id).collection("trades").order_by("Data").stream()
        data = [doc.to_dict() for doc in docs]
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
            if count >= 10:
                return False, "🚫 Limite FREE atingido (10 trades). Faça upgrade para PRO!"
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
            elif db:
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
                    st.success(f"Bem-vindo! Plano: {user_doc.get('plano', 'free').upper()}")
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos!")
    
    with tab_register:
        email_reg = st.text_input("Email", key="reg_email")
        senha_reg = st.text_input("Senha", type="password", key="reg_senha")
        conf_senha = st.text_input("Confirmar Senha", type="password", key="reg_conf")
        
        if st.button("Criar Conta Grátis", type="primary", use_container_width=True):
            if not email_reg or not senha_reg:
                st.error("Preencha todos os campos!")
            elif senha_reg != conf_senha:
                st.error("Senhas não coincidem!")
            elif len(senha_reg) < 6:
                st.error("Mínimo 6 caracteres!")
            elif db:
                if any(db.collection("users").where("email", "==", email_reg).stream()):
                    st.error("Email já cadastrado!")
                else:
                    db.collection("users").add({
                        "email": email_reg,
                        "senha": senha_reg,
                        "plano": "free",
                        "criado_em": datetime.now(),
                        "ativo": True
                    })
                    st.success("Conta criada! Faça login.")
    
    st.markdown("""
    <div class='disclaimer'>
    ⚠️ <b>AVISO DE RISCO:</b> Esta plataforma é uma ferramenta de análise estatística. 
    Não constitui recomendação de investimento. Trading envolve risco de perda.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()

# ==========================================
# 5. INICIALIZAÇÃO DE SESSÃO
# ==========================================
if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

if 'last_asset' not in st.session_state:
    st.session_state.last_asset = "USDJPY"

# ==========================================
# 6. BARRA LATERAL
# ==========================================
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_email}**")
    
    plano = st.session_state.get("user_plano", "free")
    
    if plano == "free":
        st.markdown("🆓 Plano: **FREE** (até 10 trades)")
        
        st.markdown("""
        <div class='upgrade-banner'>
            <h4 style='color:white; margin:0;'>🚀 Desbloqueie Tudo</h4>
            <p style='color:#e0e0e0; font-size:14px;'>Trades ilimitados + Insights Pro + Análises avançadas</p>
            <b style='color:#ffd700; font-size:22px;'>R$ 29,90/mês</b>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💳 Assinar PRO", use_container_width=True):
            st.link_button("Ir para Pagamento", "https://buy.stripe.com/SEU_LINK_PRO", use_container_width=True)
            st.caption("Pagamento seguro")
    
    elif plano == "pro":
        st.markdown("⭐ Plano: **PRO** (R$ 29,90/mês — Ilimitado)")
        st.success("✅ Todos os recursos desbloqueados!")
    
    elif plano == "lifetime":
        st.markdown("👑 Plano: **LIFETIME** (Acesso Perpétuo)")
        st.success("✅ Todos os recursos desbloqueados!")
    
    st.divider()
    
    st.session_state.capital_inicial = st.number_input("Capital Inicial (USD)", value=20.0)
    st.divider()
    
    st.subheader("💾 Backup Local")
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
# 7. PROCESSAMENTO DE MÉTRICAS BASE
# ==========================================
df = st.session_state.df_trades

for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

loss_df = df[df["Lucro"] < 0]
win_df = df[df["Lucro"] > 0]
n_losses = len(loss_df)
n_wins = len(win_df)
total_trades = len(df)

avg_loss_cash = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if n_losses > 0 else 0
avg_win_cash = win_df["Lucro"].mean() if n_wins > 0 else 0
avg_win_pts = abs(win_df["Saída"] - win_df["Entrada"]).mean() if n_wins > 0 else 0

total_profit = df["Lucro"].sum()
equity = st.session_state.capital_inicial + total_profit
wr = (n_wins / total_trades * 100) if total_trades > 0 else 0
pf = (win_df["Lucro"].sum() / abs(loss_df["Lucro"].sum())) if abs(loss_df["Lucro"].sum()) > 0 else 0

# ==========================================
# 8. MÉTRICAS AVANÇADAS (PRO)
# ==========================================
def calc_drawdown(df, capital_inicial):
    equity_curve = np.cumsum([capital_inicial] + df["Lucro"].tolist())
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - running_max
    max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0
    max_dd_pct = (max_dd / running_max.max() * 100) if running_max.max() > 0 else 0
    return max_dd, max_dd_pct, equity_curve, drawdown

def calc_streak(df):
    if df.empty:
        return 0, 0
    profits = df["Lucro"].values
    max_win_streak, max_loss_streak = 0, 0
    current_win, current_loss = 0, 0
    for p in profits:
        if p > 0:
            current_win += 1
            current_loss = 0
            max_win_streak = max(max_win_streak, current_win)
        elif p < 0:
            current_loss += 1
            current_win = 0
            max_loss_streak = max(max_loss_streak, current_loss)
    return max_win_streak, max_loss_streak

def calc_expectancy(df):
    if df.empty:
        return 0
    return (wr/100 * avg_win_cash) - ((1 - wr/100) * avg_loss_cash)

def calc_r_multiple(df):
    if df.empty:
        return 0
    risk = abs(df["Entrada"] - df["SL"])
    reward = abs(df["Saída"] - df["Entrada"])
    r_mult = (reward / risk).mean() if risk.mean() > 0 else 0
    return r_mult

def calc_recovery_factor(df, capital_inicial):
    max_dd, _, _, _ = calc_drawdown(df, capital_inicial)
    return total_profit / max_dd if max_dd > 0 else 0

def get_best_worst_trade(df):
    if df.empty:
        return None, None
    best = df.loc[df["Lucro"].idxmax()] if n_wins > 0 else None
    worst = df.loc[df["Lucro"].idxmin()] if n_losses > 0 else None
    return best, worst

def get_performance_by_asset(df):
    if df.empty:
        return pd.DataFrame()
    return df.groupby("Ativo").agg(
        Trades=("Lucro", "count"),
        Lucro_Total=("Lucro", "sum"),
        Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
    ).sort_values("Lucro_Total", ascending=False)

def get_performance_by_type(df):
    if df.empty:
        return pd.DataFrame()
    return df.groupby("Tipo").agg(
        Trades=("Lucro", "count"),
        Lucro_Total=("Lucro", "sum"),
        Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100),
        Lucro_Medio=("Lucro", "mean")
    )

max_dd, max_dd_pct, equity_curve, drawdown_series = calc_drawdown(df, st.session_state.capital_inicial)
max_win_streak, max_loss_streak = calc_streak(df)
expectancy = calc_expectancy(df)
r_multiple = calc_r_multiple(df)
recovery_factor = calc_recovery_factor(df, st.session_state.capital_inicial)
best_trade, worst_trade = get_best_worst_trade(df)
perf_by_asset = get_performance_by_asset(df)
perf_by_type = get_performance_by_type(df)

# ==========================================
# 9. DASHBOARD PRINCIPAL
# ==========================================
st.title("📊 Trader Strategy Analytics Pro")

# Linha 1 - Métricas principais
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{wr:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()

# ==========================================
# 10. ABAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Gráficos", "📚 Insights Pro", "📝 Histórico", "➕ Novo Trade"])

# --- TAB 1: GRÁFICOS ---
with tab1:
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(
                y=equity_curve, mode='lines',
                line=dict(color='#58a6ff', width=2),
                fill='tozeroy', fillcolor='rgba(88,166,255,0.1)',
                name='Equity'
            ))
            fig_equity.update_layout(
                title="📈 Crescimento da Conta",
                template="plotly_dark",
                height=400,
                xaxis_title="Trades",
                yaxis_title="Equity ($)"
            )
            st.plotly_chart(fig_equity, use_container_width=True)
        
        with col_b:
            df["Risco_Pts"] = abs(df["Entrada"] - df["SL"])
            st.plotly_chart(
                px.bar(df, y="Risco_Pts", title="⚠️ Risco em Pontos por Trade",
                       color_discrete_sequence=['#f85149'], template="plotly_dark"),
                use_container_width=True
            )
        
        # Gráfico de Drawdown
        if total_trades > 1:
            st.markdown("---")
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                y=drawdown_series, mode='lines',
                line=dict(color='#f85149', width=2),
                fill='tozeroy', fillcolor='rgba(248,81,73,0.2)',
                name='Drawdown'
            ))
            fig_dd.update_layout(
                title="📉 Drawdown Acumulado",
                template="plotly_dark",
                height=300,
                xaxis_title="Trades",
                yaxis_title="Drawdown ($)"
            )
            st.plotly_chart(fig_dd, use_container_width=True)
    else:
        st.info("Adicione trades para ver os gráficos.")

# --- TAB 2: INSIGHTS PRO (BLOQUEADO PARA FREE) ---
with tab2:
    plano = st.session_state.get("user_plano", "free")
    
    if plano == "free":
        st.markdown("""
        <div style='text-align:center; padding:50px; background:linear-gradient(135deg, #161b22 0%, #1c2128 100%); border-radius:12px; border:1px solid #30363d;'>
            <h1>🔒</h1>
            <h3 style='color:#e6edf3;'>Painel PRO Bloqueado</h3>
            <p style='color:#8b949e;'>Desbloqueie análises profissionais por apenas <b style='color:#ffd700;'>R$ 29,90/mês</b></p>
            <div style='display:grid; grid-template-columns:1fr 1fr; gap:10px; text-align:left; max-width:500px; margin:20px auto;'>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Drawdown Máximo & Projeções</div>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Expectancy & R-Multiple</div>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Streaks de Vitórias/Derrotas</div>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Performance por Ativo</div>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Melhor/Pior Trade</div>
                <div style='background:#0d1117; padding:15px; border-radius:8px;'>✅ Histograma de Lucros</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("💳 Desbloquear PRO — R$ 29,90/mês", use_container_width=True):
            st.link_button("Ir para Pagamento", "https://buy.stripe.com/SEU_LINK_PRO", use_container_width=True)
    
    else:
        # ====== PRO / LIFETIME - MOSTRA TUDO ======
        st.header("📊 Análise Estatística Profissional")
        
        # Métricas avançadas em cards
        st.markdown("### 🎯 Métricas de Performance")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("📉 Max Drawdown", f"$ {max_dd:,.2f} ({max_dd_pct:.1f}%)")
        m2.metric("💡 Expectancy", f"$ {expectancy:,.2f}/trade")
        m3.metric("⚖️ R-Multiple", f"{r_multiple:.2f}R")
        m4.metric("🔄 Fator Recup.", f"{recovery_factor:.2f}x")
        m5.metric("📊 Lucro Médio", f"$ {total_profit/total_trades:,.2f}" if total_trades > 0 else "$ 0.00")
        
        st.divider()
        
        # Streaks e Best/Worst
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### 🔥 Streaks")
            st.markdown(f"""
            <div class='insight-card' style='border-left-color:#3fb950;'>
                <h4>✅ Maior Sequência de Vitórias</h4>
                <p style='font-size:24px; color:#3fb950; margin:0;'><b>{max_win_streak} trades</b></p>
            </div>
            <div class='insight-card' style='border-left-color:#f85149;'>
                <h4>❌ Maior Sequência de Derrotas</h4>
                <p style='font-size:24px; color:#f85149; margin:0;'><b>{max_loss_streak} trades</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📉 Análise de Perdas")
            st.markdown(f"""
            <div class='insight-card'>
                <p>Perda média: <b>$ {avg_loss_cash:.2f}</b> | <b>{avg_loss_pts:.3f} pts</b></p>
                <p>Lucro médio: <b>$ {avg_win_cash:.2f}</b> | <b>{avg_win_pts:.3f} pts</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown("### 🏆 Melhor & Pior Trade")
            if best_trade is not None:
                st.markdown(f"""
                <div class='insight-card' style='border-left-color:#3fb950;'>
                    <h4>🥇 Melhor Trade</h4>
                    <p><b>{best_trade.get('Ativo', 'N/A')}</b> | {best_trade.get('Tipo', 'N/A')}</p>
                    <p style='font-size:20px; color:#3fb950; margin:0;'><b>+$ {best_trade.get('Lucro', 0):,.2f}</b></p>
                    <p style='font-size:12px; color:#8b949e; margin:0;'>{best_trade.get('Data', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if worst_trade is not None:
                st.markdown(f"""
                <div class='insight-card' style='border-left-color:#f85149;'>
                    <h4>🥉 Pior Trade</h4>
                    <p><b>{worst_trade.get('Ativo', 'N/A')}</b> | {worst_trade.get('Tipo', 'N/A')}</p>
                    <p style='font-size:20px; color:#f85149; margin:0;'><b>-$ {abs(worst_trade.get('Lucro', 0)):,.2f}</b></p>
                    <p style='font-size:12px; color:#8b949e; margin:0;'>{worst_trade.get('Data', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### 🔮 Projeção (30 Trades)")
            proj = equity + (expectancy * 30)
            st.markdown(f"""
            <div class='insight-card' style='border-left-color:#ffd700;'>
                <p>Capital estimado após 30 trades:</p>
                <p style='font-size:24px; color:#ffd700; margin:0;'><b>$ {proj:,.2f}</b></p>
                <p style='font-size:12px; color:#8b949e;'>Baseado na expectancy atual</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Performance por Ativo
        st.markdown("### 📊 Performance por Ativo")
        if not perf_by_asset.empty:
            st.dataframe(
                perf_by_asset.style.format({
                    "Lucro_Total": "${:,.2f}",
                    "Win_Rate": "{:.1f}%"
                }).background_gradient(subset=["Lucro_Total"], cmap="RdYlGn"),
                use_container_width=True
            )
        else:
            st.info("Sem dados suficientes.")
        
        st.divider()
        
        # Performance por Tipo
        st.markdown("### 📈 Performance por Tipo (Buy vs Sell)")
        if not perf_by_type.empty:
            st.dataframe(
                perf_by_type.style.format({
                    "Lucro_Total": "${:,.2f}",
                    "Win_Rate": "{:.1f}%",
                    "Lucro_Medio": "${:,.2f}"
                }),
                use_container_width=True
            )
        
        st.divider()
        
        # Histograma de Lucros
        st.markdown("### 📊 Distribuição de Lucros")
        if total_trades > 1:
            fig_hist = px.histogram(
                df, x="Lucro", nbins=20,
                title="Histograma de Resultados",
                color_discrete_sequence=['#58a6ff'],
                template="plotly_dark"
            )
            fig_hist.update_layout(height=350, xaxis_title="Lucro ($)", yaxis_title="Frequência")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Adicione mais trades para ver a distribuição.")

# --- TAB 3: HISTÓRICO ---
with tab3:
    st.dataframe(
        df.sort_index(ascending=False).style.format({
            "Entrada": "{:.3f}", "Saída": "{:.3f}",
            "SL": "{:.3f}", "TP": "{:.3f}", "Lucro": "${:.2f}"
        }).background_gradient(subset=["Lucro"], cmap="RdYlGn"),
        use_container_width=True
    )

# --- TAB 4: NOVO TRADE ---
with tab4:
    plano = st.session_state.get("user_plano", "free")
    
    if plano == "free" and len(df) >= 8:
        st.warning(f"⚠️ Você usou {len(df)}/10 trades gratuitos. Faça upgrade para PRO!")
    
    if plano == "free" and len(df) >= 10:
        st.error("🚫 Limite de 10 trades atingido! Faça upgrade para PRO.")
        st.link_button("Assinar PRO — R$ 29,90/mês", "https://buy.stripe.com/SEU_LINK_PRO", use_container_width=True)
        st.stop()
    
    with st.form("add_trade", clear_on_submit=True):
        st.subheader("📝 Registrar Operação")
        ativo = st.text_input("Ativo", value=st.session_state.last_asset)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tipo = st.selectbox("Tipo", ["buy", "sell"])
        with c2:
            vol = st.number_input("Volume", value=0.01, format="%.2f")
        with c3:
            lucro = st.number_input("Lucro (USD)", value=0.0, format="%.2f")
        with c4:
            st.write("")
        
        st.divider()
        
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            p_in = st.number_input("Entrada", value=0.0, format="%.3f")
        with c6:
            p_out = st.number_input("Saída", value=0.0, format="%.3f")
        with c7:
            sl = st.number_input("SL", value=0.0, format="%.3f")
        with c8:
            tp = st.number_input("TP", value=0.0, format="%.3f")
        
        if st.form_submit_button("💾 SALVAR TRADE", use_container_width=True):
            st.session_state.last_asset = ativo
            
            trade_data = {
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ativo": ativo, "Tipo": tipo, "Volume": float(vol),
                "Entrada": float(p_in), "Saída": float(p_out),
                "SL": float(sl), "TP": float(tp), "Lucro": float(lucro), "Obs": ""
            }
            
            st.session_state.df_trades = pd.concat(
                [st.session_state.df_trades, pd.DataFrame(
                    [[trade_data["Data"], ativo, tipo, vol, p_in, p_out, sl, tp, lucro, ""]],
                    columns=df.columns
                )],
                ignore_index=True
            )
            
            if db:
                ok, msg = salvar_trade(trade_data)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("⚠️ Salvo localmente (nuvem offline).")
            st.rerun()

# ==========================================
# 11. RODAPÉ
# ==========================================
st.divider()
st.markdown("""
<div class='disclaimer'>
<b>⚠️ AVISO DE RISCO:</b> Esta plataforma é uma ferramenta de análise estatística. 
Não constitui recomendação de investimento. Trading envolve risco de perda.
</div>
""", unsafe_allow_html=True)
