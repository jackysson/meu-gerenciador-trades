import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from urllib.parse import quote
from google.cloud import firestore
from google.oauth2 import service_account

# =========================================================
# CONFIGURAÇÕES IMPORTANTES - ALTERE AQUI
# =========================================================

# URL pública real do seu aplicativo Streamlit
URL_APP = "https://SEU-APP.streamlit.app"

# Seu perfil do Instagram
URL_INSTAGRAM = "https://www.instagram.com/SEU_USUARIO/"

# Link de pagamento do plano PRO - Stripe, Mercado Pago, Kiwify etc.
LINK_PAGAMENTO_PRO = "https://buy.stripe.com/SEU_LINK_PRO"

# Limite do plano gratuito
LIMITE_TRADES_FREE = 10

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Trader Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0d1117;
        color: #e6edf3;
    }

    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: #58a6ff !important;
    }

    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }

    .insight-card {
        background-color: #1c2128;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #58a6ff;
        margin-bottom: 15px;
    }

    .disclaimer {
        background-color: #3d1f00;
        border: 1px solid #ff8c00;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 12px;
        color: #ffcc80;
    }

    .upgrade-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }

    .share-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-top: 10px;
    }

    .pro-lock-card {
        text-align: center;
        padding: 45px;
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border-radius: 12px;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO COM FIRESTORE / FIREBASE
# =========================================================

@st.cache_resource
def get_firestore_client():
    """Cria conexão com o Firestore usando Streamlit Secrets."""
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

        client = firestore.Client(
            credentials=creds,
            project=secrets["project_id"]
        )

        return client, None

    except Exception as e:
        return None, str(e)


db, db_error = get_firestore_client()

# =========================================================
# 3. FUNÇÕES DE DADOS
# =========================================================

COLUNAS_TRADES = [
    "Data", "Ativo", "Tipo", "Volume",
    "Entrada", "Saída", "SL", "TP",
    "Lucro", "Obs"
]


def load_data():
    """Busca os trades do usuário atual no Firestore."""
    if not db or "user_id" not in st.session_state:
        return pd.DataFrame(columns=COLUNAS_TRADES)

    try:
        docs = (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .order_by("Data")
            .stream()
        )

        data = [doc.to_dict() for doc in docs]

        if not data:
            return pd.DataFrame(columns=COLUNAS_TRADES)

        df = pd.DataFrame(data)

        for col in COLUNAS_TRADES:
            if col not in df.columns:
                df[col] = None

        return df[COLUNAS_TRADES]

    except Exception:
        return pd.DataFrame(columns=COLUNAS_TRADES)


def contar_trades_usuario():
    """Conta trades do usuário no Firestore."""
    if not db:
        return 0

    try:
        docs = (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .stream()
        )

        return sum(1 for _ in docs)

    except Exception:
        return 0


def salvar_trade(dados):
    """Salva trade e aplica limite para plano Free."""
    if not db:
        return False, "Banco de dados não conectado."

    plano = st.session_state.get("user_plano", "free")

    # Apenas plano Free tem limite
    if plano == "free":
        quantidade = contar_trades_usuario()

        if quantidade >= LIMITE_TRADES_FREE:
            return (
                False,
                f"🚫 Limite Free atingido ({LIMITE_TRADES_FREE} trades). "
                "Faça upgrade para o plano PRO!"
            )

    try:
        (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .add(dados)
        )

        return True, "✅ Trade salvo na nuvem com sucesso!"

    except Exception as e:
        return False, f"❌ Erro ao salvar trade: {e}"


# =========================================================
# 4. LOGIN E CRIAÇÃO DE CONTA
# =========================================================

def login_screen():
    st.markdown(
        "<h1 style='text-align:center;'>📊 Trader Analytics Pro</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h3 style='text-align:center; color:#8b949e;'>"
        "Gestão Profissional de Trades"
        "</h3>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    tab_login, tab_register = st.tabs(["🔑 Entrar", "🆕 Criar Conta"])

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------
    with tab_login:
        email_login = st.text_input("E-mail", key="login_email")
        senha_login = st.text_input(
            "Senha",
            type="password",
            key="login_senha"
        )

        if st.button(
            "Entrar na Plataforma",
            type="primary",
            use_container_width=True
        ):
            if not email_login or not senha_login:
                st.error("Preencha o e-mail e a senha.")

            elif not db:
                st.error(f"Banco desconectado: {db_error}")

            else:
                users_ref = (
                    db.collection("users")
                    .where("email", "==", email_login.strip().lower())
                    .stream()
                )

                user_doc = None

                for doc in users_ref:
                    user_doc = doc.to_dict()
                    user_doc["id"] = doc.id
                    break

                if user_doc and user_doc.get("senha") == senha_login:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_login.strip().lower()
                    st.session_state.user_id = user_doc["id"]
                    st.session_state.user_plano = user_doc.get("plano", "free")

                    # Limpa dados antigos da sessão de outro login
                    if "df_trades" in st.session_state:
                        del st.session_state["df_trades"]

                    st.success("Login realizado com sucesso!")
                    st.rerun()

                else:
                    st.error("E-mail ou senha incorretos.")

    # -----------------------------------------------------
    # CRIAÇÃO DE CONTA
    # -----------------------------------------------------
    with tab_register:
        email_reg = st.text_input("Seu e-mail", key="reg_email")
        senha_reg = st.text_input(
            "Crie uma senha",
            type="password",
            key="reg_senha"
        )
        conf_senha = st.text_input(
            "Confirme sua senha",
            type="password",
            key="reg_conf"
        )

        if st.button(
            "Criar Conta Grátis",
            type="primary",
            use_container_width=True
        ):
            email_reg = email_reg.strip().lower()

            if not email_reg or not senha_reg or not conf_senha:
                st.error("Preencha todos os campos.")

            elif senha_reg != conf_senha:
                st.error("As senhas não coincidem.")

            elif len(senha_reg) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")

            elif not db:
                st.error(f"Banco desconectado: {db_error}")

            else:
                existentes = (
                    db.collection("users")
                    .where("email", "==", email_reg)
                    .stream()
                )

                if any(existentes):
                    st.error("Este e-mail já está cadastrado.")

                else:
                    db.collection("users").add({
                        "email": email_reg,
                        "senha": senha_reg,
                        "plano": "free",
                        "ativo": True,
                        "criado_em": datetime.now()
                    })

                    st.success(
                        "✅ Conta criada! Agora vá até a aba Entrar e faça login."
                    )

    st.markdown("""
    <div class='disclaimer'>
        <b>⚠️ AVISO DE RISCO:</b><br>
        Esta plataforma é apenas uma ferramenta de registro e análise estatística.
        Ela não oferece sinais, recomendações de investimento ou consultoria financeira.
        Trading, forex, criptomoedas e outros ativos envolvem risco de perda financeira.
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# =========================================================
# 5. CONTROLE DE SESSÃO
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()

if "df_trades" not in st.session_state:
    st.session_state.df_trades = load_data()

if "last_asset" not in st.session_state:
    st.session_state.last_asset = "USDJPY"

if "capital_inicial" not in st.session_state:
    st.session_state.capital_inicial = 20.0

# =========================================================
# 6. BARRA LATERAL
# =========================================================

with st.sidebar:
    st.markdown("## 👤 Minha Conta")
    st.markdown(f"**{st.session_state.user_email}**")

    plano = st.session_state.get("user_plano", "free")

    # Plano Free
    if plano == "free":
        st.markdown(
            f"🆓 Plano: **FREE** "
            f"({LIMITE_TRADES_FREE} trades gratuitos)"
        )

        st.markdown("""
        <div class='upgrade-banner'>
            <h4 style='color:white; margin:0;'>🚀 Desbloqueie o PRO</h4>
            <p style='color:#e0e0e0; font-size:14px;'>
                Trades ilimitados, métricas avançadas e Insights Premium.
            </p>
            <b style='color:#ffd700; font-size:22px;'>R$ 29,90/mês</b>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "💳 Assinar Plano PRO",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    # Plano Pro
    elif plano == "pro":
        st.markdown("⭐ Plano: **PRO**")
        st.success("✅ Recursos Premium desbloqueados!")

    # Plano Lifetime (somente você)
    elif plano == "lifetime":
        st.markdown("👑 Plano: **LIFETIME**")
        st.success("✅ Acesso vitalício desbloqueado!")

    st.divider()

    # Capital
    st.markdown("### 💰 Configurações")
    st.session_state.capital_inicial = st.number_input(
        "Capital Inicial (USD)",
        min_value=0.0,
        value=float(st.session_state.capital_inicial),
        step=10.0
    )

    st.divider()

    # Backup
    st.markdown("### 💾 Backup")

    csv_data = (
        st.session_state.df_trades
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        "📥 Baixar meus dados CSV",
        csv_data,
        "meus_trades.csv",
        "text/csv",
        use_container_width=True
    )

    uploaded_file = st.file_uploader(
        "📂 Carregar backup CSV",
        type="csv"
    )

    if uploaded_file:
        try:
            st.session_state.df_trades = pd.read_csv(uploaded_file)
            st.success("Backup carregado localmente!")
        except Exception:
            st.error("Erro ao ler este arquivo CSV.")

    if st.button("🔄 Sincronizar com a Nuvem", use_container_width=True):
        st.session_state.df_trades = load_data()
        st.success("Dados sincronizados!")
        st.rerun()

    st.divider()

    # Logout
    if st.button("🚪 Sair da conta", use_container_width=True):
        st.session_state.logged_in = False

        for key in [
            "user_email",
            "user_id",
            "user_plano",
            "df_trades",
            "last_asset"
        ]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

# =========================================================
# 7. PROCESSAMENTO DAS MÉTRICAS
# =========================================================

df = st.session_state.df_trades.copy()

for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns:
        df[col] = 0

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

total_trades = len(df)

win_df = df[df["Lucro"] > 0]
loss_df = df[df["Lucro"] < 0]

n_wins = len(win_df)
n_losses = len(loss_df)

total_profit = df["Lucro"].sum()

capital_inicial = st.session_state.capital_inicial
equity = capital_inicial + total_profit

win_rate = (n_wins / total_trades * 100) if total_trades > 0 else 0

gross_profit = win_df["Lucro"].sum()
gross_loss = abs(loss_df["Lucro"].sum())

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else 0
)

avg_win_cash = win_df["Lucro"].mean() if n_wins > 0 else 0
avg_loss_cash = abs(loss_df["Lucro"].mean()) if n_losses > 0 else 0

avg_win_pts = (
    abs(win_df["Saída"] - win_df["Entrada"]).mean()
    if n_wins > 0
    else 0
)

avg_loss_pts = (
    abs(loss_df["Entrada"] - loss_df["SL"]).mean()
    if n_losses > 0
    else 0
)

# =========================================================
# 8. MÉTRICAS AVANÇADAS PRO
# =========================================================

def calc_drawdown(dataframe, capital):
    if dataframe.empty:
        curve = np.array([capital])
        drawdown = np.array([0])
        return 0, 0, curve, drawdown

    curve = np.cumsum([capital] + dataframe["Lucro"].tolist())
    running_max = np.maximum.accumulate(curve)
    drawdown = curve - running_max

    max_dd = abs(drawdown.min()) if len(drawdown) else 0

    max_equity = running_max.max() if len(running_max) else 0

    max_dd_pct = (
        (max_dd / max_equity * 100)
        if max_equity > 0
        else 0
    )

    return max_dd, max_dd_pct, curve, drawdown


def calc_streaks(dataframe):
    if dataframe.empty:
        return 0, 0

    max_win_streak = 0
    max_loss_streak = 0

    current_win = 0
    current_loss = 0

    for lucro in dataframe["Lucro"].tolist():
        if lucro > 0:
            current_win += 1
            current_loss = 0
            max_win_streak = max(max_win_streak, current_win)

        elif lucro < 0:
            current_loss += 1
            current_win = 0
            max_loss_streak = max(max_loss_streak, current_loss)

        else:
            current_win = 0
            current_loss = 0

    return max_win_streak, max_loss_streak


def calc_r_multiple(dataframe):
    if dataframe.empty:
        return 0

    risco = abs(dataframe["Entrada"] - dataframe["SL"])
    retorno = abs(dataframe["Saída"] - dataframe["Entrada"])

    risco_valido = risco.replace(0, np.nan)
    r_values = retorno / risco_valido

    return r_values.mean() if not r_values.dropna().empty else 0


def performance_por_ativo(dataframe):
    if dataframe.empty:
        return pd.DataFrame()

    return dataframe.groupby("Ativo").agg(
        Trades=("Lucro", "count"),
        Lucro_Total=("Lucro", "sum"),
        Lucro_Medio=("Lucro", "mean"),
        Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
    ).sort_values("Lucro_Total", ascending=False)


def performance_por_tipo(dataframe):
    if dataframe.empty:
        return pd.DataFrame()

    return dataframe.groupby("Tipo").agg(
        Trades=("Lucro", "count"),
        Lucro_Total=("Lucro", "sum"),
        Lucro_Medio=("Lucro", "mean"),
        Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
    )


max_dd, max_dd_pct, equity_curve, drawdown_curve = calc_drawdown(
    df,
    capital_inicial
)

max_win_streak, max_loss_streak = calc_streaks(df)

expectancy = (
    (win_rate / 100 * avg_win_cash)
    - ((1 - win_rate / 100) * avg_loss_cash)
)

r_multiple = calc_r_multiple(df)

recovery_factor = (
    total_profit / max_dd
    if max_dd > 0
    else 0
)

best_trade = (
    df.loc[df["Lucro"].idxmax()]
    if not df.empty and n_wins > 0
    else None
)

worst_trade = (
    df.loc[df["Lucro"].idxmin()]
    if not df.empty and n_losses > 0
    else None
)

perf_ativo = performance_por_ativo(df)
perf_tipo = performance_por_tipo(df)

# =========================================================
# 9. DASHBOARD
# =========================================================

st.title("📊 Trader Strategy Analytics Pro")
st.caption("Controle seus trades. Analise sua performance. Evolua sua estratégia.")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", n_wins)
c3.metric("❌ Derrotas", n_losses)
c4.metric("🎯 Win Rate", f"{win_rate:.1f}%")
c5.metric("📈 Profit Factor", f"{profit_factor:.2f}")

st.divider()

# =========================================================
# 10. ABAS PRINCIPAIS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Gráficos",
    "📚 Insights Pro",
    "📝 Histórico",
    "➕ Novo Trade"
])

# =========================================================
# TAB 1 - GRÁFICOS
# =========================================================

with tab1:
    if df.empty:
        st.info("Adicione trades para visualizar gráficos.")

    else:
        col_a, col_b = st.columns(2)

        with col_a:
            fig_equity = go.Figure()

            fig_equity.add_trace(go.Scatter(
                y=equity_curve,
                mode="lines",
                name="Equity",
                line=dict(color="#58a6ff", width=3),
                fill="tozeroy",
                fillcolor="rgba(88,166,255,0.12)"
            ))

            fig_equity.update_layout(
                title="📈 Crescimento da Conta",
                template="plotly_dark",
                height=400,
                xaxis_title="Número de Trades",
                yaxis_title="Equity (USD)"
            )

            st.plotly_chart(fig_equity, use_container_width=True)

        with col_b:
            df_chart = df.copy()
            df_chart["Risco_Pts"] = abs(
                df_chart["Entrada"] - df_chart["SL"]
            )

            fig_risco = px.bar(
                df_chart,
                y="Risco_Pts",
                title="⚠️ Risco em Pontos por Trade",
                template="plotly_dark",
                color_discrete_sequence=["#f85149"]
            )

            fig_risco.update_layout(
                height=400,
                xaxis_title="Trades",
                yaxis_title="Risco em Pontos"
            )

            st.plotly_chart(fig_risco, use_container_width=True)

        # Drawdown disponível visualmente para todos,
        # mas as métricas detalhadas ficam no Pro.
        if total_trades > 1:
            st.divider()

            fig_dd = go.Figure()

            fig_dd.add_trace(go.Scatter(
                y=drawdown_curve,
                mode="lines",
                name="Drawdown",
                line=dict(color="#f85149", width=3),
                fill="tozeroy",
                fillcolor="rgba(248,81,73,0.20)"
            ))

            fig_dd.update_layout(
                title="📉 Drawdown Acumulado",
                template="plotly_dark",
                height=320,
                xaxis_title="Número de Trades",
                yaxis_title="Drawdown (USD)"
            )

            st.plotly_chart(fig_dd, use_container_width=True)

# =========================================================
# TAB 2 - INSIGHTS PRO
# =========================================================

with tab2:
    plano = st.session_state.get("user_plano", "free")

    # FREE BLOQUEADO
    if plano == "free":
        st.markdown("""
        <div class='pro-lock-card'>
            <h1>🔒</h1>
            <h2 style='color:#e6edf3;'>Insights PRO Bloqueados</h2>
            <p style='color:#8b949e; font-size:16px;'>
                Desbloqueie métricas profissionais e descubra exatamente
                onde sua estratégia está ganhando ou perdendo dinheiro.
            </p>

            <p style='color:#ffd700; font-size:22px;'>
                <b>Plano PRO por R$ 29,90/mês</b>
            </p>

            <div style='text-align:left; display:inline-block; color:#c9d1d9; line-height:2;'>
                ✅ Drawdown máximo<br>
                ✅ Expectancy por operação<br>
                ✅ R-Multiple<br>
                ✅ Fator de recuperação<br>
                ✅ Sequências de vitórias e perdas<br>
                ✅ Melhor e pior trade<br>
                ✅ Performance por ativo<br>
                ✅ Comparativo Buy vs Sell<br>
                ✅ Histograma de lucros<br>
                ✅ Trades ilimitados
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.link_button(
            "💳 Desbloquear Plano PRO — R$ 29,90/mês",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    # PRO OU LIFETIME
    else:
        st.header("📊 Análise Estatística Profissional")

        st.markdown("### 🎯 Métricas Avançadas")

        m1, m2, m3, m4, m5 = st.columns(5)

        m1.metric(
            "📉 Max Drawdown",
            f"$ {max_dd:,.2f}",
            f"{max_dd_pct:.1f}%"
        )

        m2.metric(
            "💡 Expectancy",
            f"$ {expectancy:,.2f}",
            "por trade"
        )

        m3.metric(
            "⚖️ R-Multiple",
            f"{r_multiple:.2f}R"
        )

        m4.metric(
            "🔄 Fator Recuperação",
            f"{recovery_factor:.2f}x"
        )

        lucro_medio = (
            total_profit / total_trades
            if total_trades > 0
            else 0
        )

        m5.metric(
            "📊 Lucro Médio",
            f"$ {lucro_medio:,.2f}"
        )

        st.divider()

        col_a, col_b = st.columns(2)

        # Streaks e médias
        with col_a:
            st.markdown("### 🔥 Sequências")

            st.markdown(f"""
            <div class='insight-card' style='border-left-color:#3fb950;'>
                <h4>✅ Maior Sequência de Vitórias</h4>
                <p style='font-size:25px; color:#3fb950; margin:0;'>
                    <b>{max_win_streak} trades</b>
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class='insight-card' style='border-left-color:#f85149;'>
                <h4>❌ Maior Sequência de Derrotas</h4>
                <p style='font-size:25px; color:#f85149; margin:0;'>
                    <b>{max_loss_streak} trades</b>
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 📉 Médias de Resultado")

            st.markdown(f"""
            <div class='insight-card'>
                <p>Lucro médio: <b>$ {avg_win_cash:,.2f}</b></p>
                <p>Perda média: <b>$ {avg_loss_cash:,.2f}</b></p>
                <p>Lucro médio em pontos: <b>{avg_win_pts:.3f}</b></p>
                <p>Perda média em pontos: <b>{avg_loss_pts:.3f}</b></p>
            </div>
            """, unsafe_allow_html=True)

        # Melhor, pior e projeção
        with col_b:
            st.markdown("### 🏆 Melhor e Pior Trade")

            if best_trade is not None:
                st.markdown(f"""
                <div class='insight-card' style='border-left-color:#3fb950;'>
                    <h4>🥇 Melhor Trade</h4>
                    <p><b>{best_trade.get("Ativo", "N/A")}</b> | 
                    {best_trade.get("Tipo", "N/A")}</p>
                    <p style='font-size:22px; color:#3fb950; margin:0;'>
                        <b>+$ {best_trade.get("Lucro", 0):,.2f}</b>
                    </p>
                    <p style='font-size:12px; color:#8b949e;'>
                        {best_trade.get("Data", "N/A")}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            if worst_trade is not None:
                st.markdown(f"""
                <div class='insight-card' style='border-left-color:#f85149;'>
                    <h4>🥉 Pior Trade</h4>
                    <p><b>{worst_trade.get("Ativo", "N/A")}</b> | 
                    {worst_trade.get("Tipo", "N/A")}</p>
                    <p style='font-size:22px; color:#f85149; margin:0;'>
                        <b>-$ {abs(worst_trade.get("Lucro", 0)):,.2f}</b>
                    </p>
                    <p style='font-size:12px; color:#8b949e;'>
                        {worst_trade.get("Data", "N/A")}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            projecao_30 = equity + (expectancy * 30)

            st.markdown(f"""
            <div class='insight-card' style='border-left-color:#ffd700;'>
                <h4>🔮 Projeção de 30 Trades</h4>
                <p>Capital estimado:</p>
                <p style='font-size:25px; color:#ffd700; margin:0;'>
                    <b>$ {projecao_30:,.2f}</b>
                </p>
                <p style='font-size:12px; color:#8b949e;'>
                    Baseado na expectancy atual.
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Performance por ativo
        st.markdown("### 💱 Performance por Ativo")

        if not perf_ativo.empty:
            st.dataframe(
                perf_ativo.style.format({
                    "Lucro_Total": "$ {:.2f}",
                    "Lucro_Medio": "$ {:.2f}",
                    "Win_Rate": "{:.1f}%"
                }),
                use_container_width=True
            )
        else:
            st.info("Ainda não há trades suficientes.")

        st.divider()

        # Buy vs Sell
        st.markdown("### 📈 Performance por Tipo: Buy vs Sell")

        if not perf_tipo.empty:
            st.dataframe(
                perf_tipo.style.format({
                    "Lucro_Total": "$ {:.2f}",
                    "Lucro_Medio": "$ {:.2f}",
                    "Win_Rate": "{:.1f}%"
                }),
                use_container_width=True
            )
        else:
            st.info("Ainda não há dados suficientes.")

        st.divider()

        # Histograma
        st.markdown("### 📊 Distribuição dos Resultados")

        if total_trades > 1:
            fig_hist = px.histogram(
                df,
                x="Lucro",
                nbins=20,
                title="Histograma de Lucros e Prejuízos",
                template="plotly_dark",
                color_discrete_sequence=["#58a6ff"]
            )

            fig_hist.update_layout(
                height=360,
                xaxis_title="Resultado por Trade (USD)",
                yaxis_title="Quantidade de Trades"
            )

            st.plotly_chart(fig_hist, use_container_width=True)

        else:
            st.info("Adicione mais trades para visualizar o histograma.")

# =========================================================
# TAB 3 - HISTÓRICO
# =========================================================

with tab3:
    st.subheader("📝 Histórico de Trades")

    if df.empty:
        st.info("Você ainda não registrou nenhum trade.")

    else:
        st.dataframe(
            df.sort_index(ascending=False).style.format({
                "Volume": "{:.2f}",
                "Entrada": "{:.3f}",
                "Saída": "{:.3f}",
                "SL": "{:.3f}",
                "TP": "{:.3f}",
                "Lucro": "$ {:.2f}"
            }),
            use_container_width=True
        )

# =========================================================
# TAB 4 - NOVO TRADE
# =========================================================

with tab4:
    plano = st.session_state.get("user_plano", "free")

    # Aviso quando Free chega perto do limite
    if plano == "free" and total_trades >= 8:
        st.warning(
            f"⚠️ Você usou {total_trades}/{LIMITE_TRADES_FREE} trades gratuitos."
        )

    # Bloqueio para Free
    if plano == "free" and total_trades >= LIMITE_TRADES_FREE:
        st.error(
            f"🚫 Limite de {LIMITE_TRADES_FREE} trades atingido. "
            "Assine o PRO para registrar trades ilimitados."
        )

        st.link_button(
            "💳 Assinar PRO — R$ 29,90/mês",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    else:
        with st.form("add_trade", clear_on_submit=True):
            st.subheader("➕ Registrar Nova Operação")

            ativo = st.text_input(
                "Ativo",
                value=st.session_state.last_asset,
                placeholder="Exemplo: USDJPY, XAUUSD, BTCUSD"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                tipo = st.selectbox("Tipo", ["buy", "sell"])

            with c2:
                vol = st.number_input(
                    "Volume",
                    min_value=0.0,
                    value=0.01,
                    step=0.01,
                    format="%.2f"
                )

            with c3:
                lucro = st.number_input(
                    "Lucro Final (USD)",
                    value=0.0,
                    step=0.01,
                    format="%.2f"
                )

            st.divider()

            c4, c5, c6, c7 = st.columns(4)

            with c4:
                p_in = st.number_input(
                    "Entrada",
                    value=0.0,
                    format="%.3f"
                )

            with c5:
                p_out = st.number_input(
                    "Saída",
                    value=0.0,
                    format="%.3f"
                )

            with c6:
                sl = st.number_input(
                    "Stop Loss (SL)",
                    value=0.0,
                    format="%.3f"
                )

            with c7:
                tp = st.number_input(
                    "Take Profit (TP)",
                    value=0.0,
                    format="%.3f"
                )

            obs = st.text_area(
                "Observações (opcional)",
                placeholder="Exemplo: Entrada baseada em rompimento de resistência."
            )

            submitted = st.form_submit_button(
                "💾 SALVAR TRADE NA NUVEM",
                use_container_width=True
            )

            if submitted:
                if not ativo.strip():
                    st.error("Informe o ativo antes de salvar.")

                else:
                    st.session_state.last_asset = ativo.strip().upper()

                    trade_data = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Ativo": ativo.strip().upper(),
                        "Tipo": tipo,
                        "Volume": float(vol),
                        "Entrada": float(p_in),
                        "Saída": float(p_out),
                        "SL": float(sl),
                        "TP": float(tp),
                        "Lucro": float(lucro),
                        "Obs": obs
                    }

                    ok, msg = salvar_trade(trade_data)

                    if ok:
                        st.success(msg)

                        # Recarrega diretamente da nuvem
                        st.session_state.df_trades = load_data()

                        st.rerun()

                    else:
                        st.error(msg)

# =========================================================
# 11. ÁREA DE COMPARTILHAMENTO
# =========================================================

st.divider()

st.markdown("""
<div class='share-card'>
    <h3 style='margin-top:0;'>📣 Compartilhe o Trader Analytics Pro</h3>
    <p style='color:#8b949e;'>
        Ajude outros traders a registrarem e analisarem suas operações.
    </p>
</div>
""", unsafe_allow_html=True)

mensagem_compartilhar = (
    "Conheça o Trader Analytics Pro! 📊\n\n"
    "Uma plataforma para registrar trades, acompanhar resultados "
    "e analisar a performance da sua estratégia.\n\n"
    f"{URL_APP}"
)

mensagem_codificada = quote(mensagem_compartilhar)
url_codificada = quote(URL_APP)
texto_codificado = quote(
    "Conheça o Trader Analytics Pro! Plataforma para gestão e análise de trades."
)

s1, s2, s3, s4, s5, s6 = st.columns(6)

with s1:
    st.link_button(
        "🟢 WhatsApp",
        f"https://wa.me/?text={mensagem_codificada}",
        use_container_width=True
    )

with s2:
    st.link_button(
        "✈️ Telegram",
        f"https://t.me/share/url?url={url_codificada}&text={texto_codificado}",
        use_container_width=True
    )

with s3:
    st.link_button(
        "𝕏 Twitter / X",
        f"https://twitter.com/intent/tweet?text={mensagem_codificada}",
        use_container_width=True
    )

with s4:
    st.link_button(
        "🔵 Facebook",
        f"https://www.facebook.com/sharer/sharer.php?u={url_codificada}",
        use_container_width=True
    )

with s5:
    st.link_button(
        "📸 Instagram",
        URL_INSTAGRAM,
        use_container_width=True
    )

with s6:
    with st.popover("📋 Copiar Link", use_container_width=True):
        st.write("Copie o link abaixo e compartilhe no Instagram, Stories, Direct ou onde desejar:")
        st.code(URL_APP, language=None)

# =========================================================
# 12. RODAPÉ E DISCLAIMER
# =========================================================

st.divider()

st.markdown("""
<div class='disclaimer'>
    <b>⚠️ AVISO DE RISCO E RESPONSABILIDADE:</b><br><br>
    Esta plataforma é uma ferramenta de registro, gestão e análise estatística de operações.
    Ela não constitui recomendação de investimento, sinal de compra ou venda, consultoria financeira,
    gestão de patrimônio ou promessa de resultado.<br><br>
    Trading de forex, criptomoedas, ações, índices e outros ativos envolve risco substancial,
    incluindo a possibilidade de perda total do capital investido.
    Resultados passados não garantem resultados futuros.
    Cada usuário é integralmente responsável por suas próprias decisões financeiras.
</div>
""", unsafe_allow_html=True)

st.caption("© 2026 Trader Analytics Pro — Gestão inteligente para traders.")
