import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from datetime import datetime
from urllib.parse import quote
from google.cloud import firestore
from google.oauth2 import service_account


# =========================================================
# CONFIGURAÇÕES IMPORTANTES
# =========================================================

# Troque pela URL real do seu aplicativo
URL_APP = "https://SEU-APP.streamlit.app"

# Troque pelo seu Instagram
URL_INSTAGRAM = "https://www.instagram.com/SEU_USUARIO/"

# Troque pelo link real de pagamento do Stripe, Mercado Pago, Kiwify etc.
LINK_PAGAMENTO_PRO = "https://buy.stripe.com/SEU_LINK_PRO"

# Limite de trades para usuários gratuitos
LIMITE_TRADES_FREE = 10

COLUNAS_TRADES = [
    "Data",
    "Ativo",
    "Tipo",
    "Volume",
    "Entrada",
    "Saída",
    "SL",
    "TP",
    "Lucro",
    "Obs"
]


# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Trader Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CONTROLE DO TEMA
# =========================================================

if "modo_claro" not in st.session_state:
    st.session_state.modo_claro = False

modo_claro = st.session_state.modo_claro

if modo_claro:
    COR_FUNDO = "#f6f8fa"
    COR_CARD = "#ffffff"
    COR_CARD_SECUNDARIO = "#f0f2f6"
    COR_TEXTO = "#1f2328"
    COR_TEXTO_SECUNDARIO = "#57606a"
    COR_BORDA = "#d0d7de"
    COR_DESTAQUE = "#0969da"
    COR_AVISO_FUNDO = "#fff8c5"
    COR_AVISO_TEXTO = "#7a4d00"
else:
    COR_FUNDO = "#0d1117"
    COR_CARD = "#161b22"
    COR_CARD_SECUNDARIO = "#1c2128"
    COR_TEXTO = "#e6edf3"
    COR_TEXTO_SECUNDARIO = "#8b949e"
    COR_BORDA = "#30363d"
    COR_DESTAQUE = "#58a6ff"
    COR_AVISO_FUNDO = "#3d1f00"
    COR_AVISO_TEXTO = "#ffcc80"


# =========================================================
# ESTILO VISUAL
# =========================================================

st.markdown(f"""
<style>
    .stApp {{
        background-color: {COR_FUNDO};
        color: {COR_TEXTO};
    }}

    .main {{
        background-color: {COR_FUNDO};
        color: {COR_TEXTO};
    }}

    h1, h2, h3, h4, h5, p, span, label {{
        color: {COR_TEXTO};
    }}

    [data-testid="stSidebar"] {{
        background-color: {COR_CARD};
    }}

    [data-testid="stMetricValue"] {{
        font-size: 25px !important;
        color: {COR_DESTAQUE} !important;
    }}

    .stMetric {{
        background-color: {COR_CARD};
        padding: 14px;
        border-radius: 12px;
        border: 1px solid {COR_BORDA};
    }}

    .insight-card {{
        background-color: {COR_CARD_SECUNDARIO};
        padding: 18px;
        border-radius: 10px;
        border-left: 5px solid {COR_DESTAQUE};
        margin-bottom: 14px;
    }}

    .upgrade-banner {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 18px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
    }}

    .disclaimer {{
        background-color: {COR_AVISO_FUNDO};
        border: 1px solid #ff8c00;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 12px;
        color: {COR_AVISO_TEXTO};
    }}

    .cloud-connected {{
        background-color: #0f5132;
        color: #d1e7dd !important;
        border: 1px solid #198754;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }}

    .cloud-offline {{
        background-color: #842029;
        color: #f8d7da !important;
        border: 1px solid #dc3545;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }}

    .pro-lock {{
        text-align: center;
        padding: 45px;
        border-radius: 12px;
        border: 1px solid {COR_BORDA};
        background: {COR_CARD};
    }}

    .share-card {{
        background-color: {COR_CARD};
        padding: 20px;
        border-radius: 12px;
        border: 1px solid {COR_BORDA};
        margin-top: 10px;
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# CONEXÃO COM FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore_client():
    """
    Conecta ao Firestore usando os Secrets do Streamlit.
    Não usa firebase_admin.
    """

    try:
        firebase = st.secrets["firebase"]

        credenciais = service_account.Credentials.from_service_account_info({
            "type": firebase["type"],
            "project_id": firebase["project_id"],
            "private_key_id": firebase["private_key_id"],
            "private_key": firebase["private_key"],
            "client_email": firebase["client_email"],
            "client_id": firebase["client_id"],
            "auth_uri": firebase["auth_uri"],
            "token_uri": firebase["token_uri"],
        })

        client = firestore.Client(
            credentials=credenciais,
            project=firebase["project_id"]
        )

        return client, None

    except Exception as erro:
        return None, str(erro)


db, db_error = get_firestore_client()


# =========================================================
# FUNÇÕES DE FIRESTORE
# =========================================================

def carregar_trades():
    """Carrega os trades do usuário atualmente logado."""

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

        dados = [doc.to_dict() for doc in docs]

        if not dados:
            return pd.DataFrame(columns=COLUNAS_TRADES)

        dataframe = pd.DataFrame(dados)

        for coluna in COLUNAS_TRADES:
            if coluna not in dataframe.columns:
                dataframe[coluna] = None

        return dataframe[COLUNAS_TRADES]

    except Exception:
        return pd.DataFrame(columns=COLUNAS_TRADES)


def contar_trades():
    """Conta os trades existentes do usuário no Firestore."""

    if not db or "user_id" not in st.session_state:
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


def salvar_trade(trade):
    """Salva um trade e aplica limite ao plano Free."""

    if not db:
        return False, "❌ Banco de dados não conectado."

    plano = st.session_state.get("user_plano", "free")

    if plano == "free":
        quantidade = contar_trades()

        if quantidade >= LIMITE_TRADES_FREE:
            return False, (
                f"🚫 Limite Free atingido: {LIMITE_TRADES_FREE} trades. "
                "Assine o plano PRO para continuar."
            )

    try:
        (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .add(trade)
        )

        return True, "✅ Trade salvo na nuvem com sucesso!"

    except Exception as erro:
        return False, f"❌ Erro ao salvar: {erro}"


# =========================================================
# TELA DE LOGIN E CADASTRO
# =========================================================

def tela_login():
    st.markdown(
        "<h1 style='text-align:center;'>📊 Trader Analytics Pro</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h4 style='text-align:center; color:#8b949e;'>"
        "Gestão profissional de trades"
        "</h4>",
        unsafe_allow_html=True
    )

    st.divider()

    aba_login, aba_cadastro = st.tabs([
        "🔑 Entrar",
        "🆕 Criar Conta"
    ])

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------
    with aba_login:
        email = st.text_input("E-mail", key="email_login")
        senha = st.text_input(
            "Senha",
            type="password",
            key="senha_login"
        )

        if st.button(
            "Entrar na Plataforma",
            type="primary",
            use_container_width=True
        ):
            email = email.strip().lower()

            if not email or not senha:
                st.error("Preencha o e-mail e a senha.")

            elif not db:
                st.error(f"Erro ao conectar à nuvem: {db_error}")

            else:
                usuarios = (
                    db.collection("users")
                    .where("email", "==", email)
                    .stream()
                )

                usuario = None

                for doc in usuarios:
                    usuario = doc.to_dict()
                    usuario["id"] = doc.id
                    break

                if usuario and usuario.get("senha") == senha:
                    st.session_state.logged_in = True
                    st.session_state.user_id = usuario["id"]
                    st.session_state.user_email = email
                    st.session_state.user_plano = usuario.get("plano", "free")

                    if "df_trades" in st.session_state:
                        del st.session_state["df_trades"]

                    st.success("✅ Login realizado!")
                    st.rerun()

                else:
                    st.error("E-mail ou senha incorretos.")

    # -----------------------------------------------------
    # CADASTRO
    # -----------------------------------------------------
    with aba_cadastro:
        email_novo = st.text_input("Seu e-mail", key="email_novo")
        senha_nova = st.text_input(
            "Crie uma senha",
            type="password",
            key="senha_nova"
        )
        confirmar_senha = st.text_input(
            "Confirme a senha",
            type="password",
            key="confirmar_senha"
        )

        if st.button(
            "Criar Conta Gratuita",
            type="primary",
            use_container_width=True
        ):
            email_novo = email_novo.strip().lower()

            if not email_novo or not senha_nova or not confirmar_senha:
                st.error("Preencha todos os campos.")

            elif senha_nova != confirmar_senha:
                st.error("As senhas não coincidem.")

            elif len(senha_nova) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")

            elif not db:
                st.error(f"Erro ao conectar à nuvem: {db_error}")

            else:
                existentes = (
                    db.collection("users")
                    .where("email", "==", email_novo)
                    .stream()
                )

                if any(existentes):
                    st.error("Este e-mail já possui cadastro.")

                else:
                    db.collection("users").add({
                        "email": email_novo,
                        "senha": senha_nova,
                        "plano": "free",
                        "ativo": True,
                        "criado_em": datetime.now()
                    })

                    st.success(
                        "✅ Conta criada! Agora use a aba Entrar para acessar."
                    )

    st.markdown("""
    <div class='disclaimer'>
        <b>⚠️ AVISO DE RISCO:</b><br>
        Esta plataforma é uma ferramenta de registro e análise estatística.
        Não representa recomendação de investimento, sinal de compra ou venda
        e não garante resultados financeiros.
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# =========================================================
# CONTROLE DE LOGIN
# Não usa st.user, st.login ou st.logout
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tela_login()

if "df_trades" not in st.session_state:
    st.session_state.df_trades = carregar_trades()

if "last_asset" not in st.session_state:
    st.session_state.last_asset = "USDJPY"

if "capital_inicial" not in st.session_state:
    st.session_state.capital_inicial = 20.0


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:
    st.title("⚙️ Painel de Controle")

    # Tema
    novo_modo = st.toggle(
        "☀️ Modo Claro",
        value=st.session_state.modo_claro,
        help="Ative para usar a plataforma no modo claro."
    )

    if novo_modo != st.session_state.modo_claro:
        st.session_state.modo_claro = novo_modo
        st.rerun()

    if st.session_state.modo_claro:
        st.caption("Tema atual: ☀️ Modo Claro")
    else:
        st.caption("Tema atual: 🌙 Modo Escuro")

    st.divider()

    # Status da nuvem
    st.subheader("☁️ Status da Nuvem")

    if db:
        st.markdown("""
        <div class='cloud-connected'>
            ✅ Nuvem Conectada<br>
            <span style='font-size:12px; color:#d1e7dd !important;'>
                Firebase Firestore ativo
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='cloud-offline'>
            ❌ Nuvem Desconectada<br>
            <span style='font-size:12px; color:#f8d7da !important;'>
                Erro ao conectar ao Firestore
            </span>
        </div>
        """, unsafe_allow_html=True)

        if db_error:
            with st.expander("Ver detalhe técnico"):
                st.code(db_error)

    st.divider()

    # Dados do usuário
    st.subheader("👤 Minha Conta")
    st.write(st.session_state.user_email)

    plano = st.session_state.get("user_plano", "free")

    if plano == "free":
        st.info(f"🆓 Plano FREE: até {LIMITE_TRADES_FREE} trades")

        st.markdown("""
        <div class='upgrade-banner'>
            <h3 style='color:white; margin:0;'>🚀 Plano PRO</h3>
            <p style='color:#eeeeee;'>
                Trades ilimitados + Insights profissionais
            </p>
            <h2 style='color:#ffd700;'>R$ 29,90/mês</h2>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "💳 Assinar Plano PRO",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    elif plano == "pro":
        st.success("⭐ Plano PRO ativo")

    elif plano == "lifetime":
        st.success("👑 Plano LIFETIME ativo")

    st.divider()

    # Capital inicial
    st.subheader("💰 Configurações")

    st.session_state.capital_inicial = st.number_input(
        "Capital Inicial (USD)",
        min_value=0.0,
        value=float(st.session_state.capital_inicial),
        step=10.0
    )

    st.divider()

    # Backup CSV
    st.subheader("💾 Backup")

    csv = st.session_state.df_trades.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar Backup CSV",
        csv,
        "meus_trades.csv",
        "text/csv",
        use_container_width=True
    )

    if st.button("🔄 Sincronizar Nuvem", use_container_width=True):
        st.session_state.df_trades = carregar_trades()
        st.success("Dados sincronizados!")
        st.rerun()

    st.divider()

    # Logout
    if st.button("🚪 Sair da Conta", use_container_width=True):
        for chave in [
            "logged_in",
            "user_id",
            "user_email",
            "user_plano",
            "df_trades",
            "last_asset"
        ]:
            if chave in st.session_state:
                del st.session_state[chave]

        st.rerun()


# =========================================================
# PROCESSAMENTO DE MÉTRICAS
# =========================================================

df = st.session_state.df_trades.copy()

for coluna in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if coluna not in df.columns:
        df[coluna] = 0

    df[coluna] = pd.to_numeric(
        df[coluna],
        errors="coerce"
    ).fillna(0)

total_trades = len(df)

wins = df[df["Lucro"] > 0]
losses = df[df["Lucro"] < 0]

n_wins = len(wins)
n_losses = len(losses)

total_profit = df["Lucro"].sum()

capital = st.session_state.capital_inicial
equity = capital + total_profit

win_rate = (n_wins / total_trades * 100) if total_trades > 0 else 0

gross_profit = wins["Lucro"].sum()
gross_loss = abs(losses["Lucro"].sum())

profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

avg_win = wins["Lucro"].mean() if not wins.empty else 0
avg_loss = abs(losses["Lucro"].mean()) if not losses.empty else 0

equity_curve = np.cumsum([capital] + df["Lucro"].tolist())
running_max = np.maximum.accumulate(equity_curve)
drawdown_curve = equity_curve - running_max

max_drawdown = abs(drawdown_curve.min()) if len(drawdown_curve) else 0

max_equity = running_max.max() if len(running_max) else 0
max_drawdown_pct = (
    max_drawdown / max_equity * 100
    if max_equity > 0
    else 0
)

expectancy = (
    (win_rate / 100 * avg_win)
    - ((1 - win_rate / 100) * avg_loss)
)


def calcular_streaks(dataframe):
    """Calcula sequências máximas de vitórias e derrotas."""

    if dataframe.empty:
        return 0, 0

    atual_win = 0
    atual_loss = 0
    max_win = 0
    max_loss = 0

    for lucro in dataframe["Lucro"].tolist():
        if lucro > 0:
            atual_win += 1
            atual_loss = 0
            max_win = max(max_win, atual_win)

        elif lucro < 0:
            atual_loss += 1
            atual_win = 0
            max_loss = max(max_loss, atual_loss)

        else:
            atual_win = 0
            atual_loss = 0

    return max_win, max_loss


def calcular_r_multiple(dataframe):
    """Calcula a média de retorno/risco."""

    if dataframe.empty:
        return 0

    risco = abs(dataframe["Entrada"] - dataframe["SL"])
    retorno = abs(dataframe["Saída"] - dataframe["Entrada"])

    risco = risco.replace(0, np.nan)
    r_multiple = retorno / risco

    if r_multiple.dropna().empty:
        return 0

    return r_multiple.mean()


max_win_streak, max_loss_streak = calcular_streaks(df)
r_multiple = calcular_r_multiple(df)

recovery_factor = (
    total_profit / max_drawdown
    if max_drawdown > 0
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


# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================

st.title("📊 Trader Strategy Analytics Pro")
st.caption("Controle seus trades. Analise sua performance. Evolua sua estratégia.")

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("💰 Equity", f"$ {equity:,.2f}")
m2.metric("✅ Vitórias", n_wins)
m3.metric("❌ Derrotas", n_losses)
m4.metric("🎯 Win Rate", f"{win_rate:.1f}%")
m5.metric("📈 Profit Factor", f"{profit_factor:.2f}")

st.divider()


# =========================================================
# ABAS
# =========================================================

aba1, aba2, aba3, aba4 = st.tabs([
    "🚀 Gráficos",
    "📚 Insights Pro",
    "📝 Histórico",
    "➕ Novo Trade"
])


# =========================================================
# ABA 1 - GRÁFICOS
# =========================================================

with aba1:
    if df.empty:
        st.info("Adicione trades para visualizar os gráficos.")

    else:
        col1, col2 = st.columns(2)

        with col1:
            fig_equity = go.Figure()

            fig_equity.add_trace(go.Scatter(
                y=equity_curve,
                mode="lines",
                name="Equity",
                line=dict(color="#58a6ff", width=3),
                fill="tozeroy",
                fillcolor="rgba(88,166,255,0.15)"
            ))

            fig_equity.update_layout(
                title="📈 Crescimento da Conta",
                template="plotly_dark" if not modo_claro else "plotly_white",
                height=400,
                xaxis_title="Número de Trades",
                yaxis_title="Equity (USD)"
            )

            st.plotly_chart(fig_equity, use_container_width=True)

        with col2:
            risco = abs(df["Entrada"] - df["SL"])

            fig_risco = px.bar(
                y=risco,
                title="⚠️ Risco por Trade",
                template="plotly_dark" if not modo_claro else "plotly_white",
                color_discrete_sequence=["#f85149"]
            )

            fig_risco.update_layout(
                height=400,
                xaxis_title="Trades",
                yaxis_title="Risco"
            )

            st.plotly_chart(fig_risco, use_container_width=True)

        if total_trades > 1:
            st.divider()

            fig_drawdown = go.Figure()

            fig_drawdown.add_trace(go.Scatter(
                y=drawdown_curve,
                mode="lines",
                name="Drawdown",
                line=dict(color="#f85149", width=3),
                fill="tozeroy",
                fillcolor="rgba(248,81,73,0.20)"
            ))

            fig_drawdown.update_layout(
                title="📉 Drawdown Acumulado",
                template="plotly_dark" if not modo_claro else "plotly_white",
                height=300,
                xaxis_title="Número de Trades",
                yaxis_title="Drawdown (USD)"
            )

            st.plotly_chart(fig_drawdown, use_container_width=True)


# =========================================================
# ABA 2 - INSIGHTS PRO
# =========================================================

with aba2:
    plano = st.session_state.get("user_plano", "free")

    if plano == "free":
        st.markdown("""
        <div class='pro-lock'>
            <h1>🔒</h1>
            <h2>Insights PRO Bloqueados</h2>
            <p>
                Desbloqueie análises profissionais para entender sua estratégia,
                identificar erros e melhorar sua performance.
            </p>
            <h2 style='color:#ffd700;'>R$ 29,90/mês</h2>
            <p>
                ✅ Trades ilimitados<br>
                ✅ Max Drawdown<br>
                ✅ Expectancy<br>
                ✅ R-Multiple<br>
                ✅ Melhor e pior trade<br>
                ✅ Streaks de vitórias e derrotas<br>
                ✅ Performance por ativo<br>
                ✅ Buy vs Sell<br>
                ✅ Histograma de resultados
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "💳 Desbloquear Plano PRO",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    else:
        st.header("📚 Insights Profissionais")

        p1, p2, p3, p4, p5 = st.columns(5)

        p1.metric(
            "📉 Max Drawdown",
            f"$ {max_drawdown:,.2f}",
            f"{max_drawdown_pct:.1f}%"
        )

        p2.metric(
            "💡 Expectancy",
            f"$ {expectancy:,.2f}"
        )

        p3.metric(
            "⚖️ R-Multiple",
            f"{r_multiple:.2f}R"
        )

        p4.metric(
            "🔄 Recuperação",
            f"{recovery_factor:.2f}x"
        )

        lucro_medio = total_profit / total_trades if total_trades > 0 else 0

        p5.metric(
            "📊 Lucro Médio",
            f"$ {lucro_medio:,.2f}"
        )

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("### 🔥 Streaks")

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
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### 💱 Performance por Ativo")

        if not df.empty:
            por_ativo = df.groupby("Ativo").agg(
                Trades=("Lucro", "count"),
                Lucro_Total=("Lucro", "sum"),
                Lucro_Medio=("Lucro", "mean"),
                Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
            ).sort_values("Lucro_Total", ascending=False)

            st.dataframe(
                por_ativo.style.format({
                    "Lucro_Total": "$ {:.2f}",
                    "Lucro_Medio": "$ {:.2f}",
                    "Win_Rate": "{:.1f}%"
                }),
                use_container_width=True
            )

        st.divider()

        st.markdown("### 📈 Buy vs Sell")

        if not df.empty:
            por_tipo = df.groupby("Tipo").agg(
                Trades=("Lucro", "count"),
                Lucro_Total=("Lucro", "sum"),
                Lucro_Medio=("Lucro", "mean"),
                Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
            )

            st.dataframe(
                por_tipo.style.format({
                    "Lucro_Total": "$ {:.2f}",
                    "Lucro_Medio": "$ {:.2f}",
                    "Win_Rate": "{:.1f}%"
                }),
                use_container_width=True
            )

        st.divider()

        st.markdown("### 📊 Distribuição de Resultados")

        if total_trades > 1:
            fig_hist = px.histogram(
                df,
                x="Lucro",
                nbins=20,
                title="Histograma de Lucros e Prejuízos",
                template="plotly_dark" if not modo_claro else "plotly_white",
                color_discrete_sequence=["#58a6ff"]
            )

            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Adicione mais trades para gerar o histograma.")


# =========================================================
# ABA 3 - HISTÓRICO
# =========================================================

with aba3:
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
# ABA 4 - NOVO TRADE
# =========================================================

with aba4:
    plano = st.session_state.get("user_plano", "free")

    if plano == "free" and total_trades >= 8:
        st.warning(
            f"⚠️ Você utilizou {total_trades}/{LIMITE_TRADES_FREE} trades gratuitos."
        )

    if plano == "free" and total_trades >= LIMITE_TRADES_FREE:
        st.error(
            f"🚫 Limite de {LIMITE_TRADES_FREE} trades atingido. "
            "Assine o PRO para continuar."
        )

        st.link_button(
            "💳 Assinar PRO — R$ 29,90/mês",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    else:
        with st.form("novo_trade", clear_on_submit=True):
            st.subheader("➕ Registrar Nova Operação")

            ativo = st.text_input(
                "Ativo",
                value=st.session_state.last_asset,
                placeholder="Exemplo: USDJPY, BTCUSD, XAUUSD"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                tipo = st.selectbox("Tipo", ["buy", "sell"])

            with c2:
                volume = st.number_input(
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
                entrada = st.number_input(
                    "Entrada",
                    value=0.0,
                    format="%.3f"
                )

            with c5:
                saida = st.number_input(
                    "Saída",
                    value=0.0,
                    format="%.3f"
                )

            with c6:
                sl = st.number_input(
                    "Stop Loss",
                    value=0.0,
                    format="%.3f"
                )

            with c7:
                tp = st.number_input(
                    "Take Profit",
                    value=0.0,
                    format="%.3f"
                )

            observacao = st.text_area(
                "Observação",
                placeholder="Exemplo: Rompimento de resistência."
            )

            salvar = st.form_submit_button(
                "💾 Salvar Trade na Nuvem",
                use_container_width=True
            )

            if salvar:
                if not ativo.strip():
                    st.error("Informe o ativo.")

                else:
                    st.session_state.last_asset = ativo.strip().upper()

                    trade = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Ativo": ativo.strip().upper(),
                        "Tipo": tipo,
                        "Volume": float(volume),
                        "Entrada": float(entrada),
                        "Saída": float(saida),
                        "SL": float(sl),
                        "TP": float(tp),
                        "Lucro": float(lucro),
                        "Obs": observacao
                    }

                    sucesso, mensagem = salvar_trade(trade)

                    if sucesso:
                        st.success(mensagem)
                        st.session_state.df_trades = carregar_trades()
                        st.rerun()
                    else:
                        st.error(mensagem)


# =========================================================
# COMPARTILHAMENTO
# =========================================================

st.divider()

st.markdown("""
<div class='share-card'>
    <h3 style='margin-top:0;'>📣 Compartilhe o Trader Analytics Pro</h3>
    <p>
        Ajude outros traders a registrarem trades e analisarem sua performance.
    </p>
</div>
""", unsafe_allow_html=True)

mensagem_compartilhar = quote(
    f"Conheça o Trader Analytics Pro! 📊\n\n"
    f"Registre seus trades e acompanhe sua performance.\n\n"
    f"{URL_APP}"
)

url_codificada = quote(URL_APP)

s1, s2, s3, s4, s5, s6 = st.columns(6)

with s1:
    st.link_button(
        "🟢 WhatsApp",
        f"https://wa.me/?text={mensagem_compartilhar}",
        use_container_width=True
    )

with s2:
    st.link_button(
        "✈️ Telegram",
        f"https://t.me/share/url?url={url_codificada}&text=Trader%20Analytics%20Pro",
        use_container_width=True
    )

with s3:
    st.link_button(
        "𝕏 X / Twitter",
        f"https://twitter.com/intent/tweet?text={mensagem_compartilhar}",
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
        st.write("Copie e compartilhe onde desejar:")
        st.code(URL_APP, language=None)


# =========================================================
# RODAPÉ
# =========================================================

st.divider()

st.markdown("""
<div class='disclaimer'>
    <b>⚠️ AVISO DE RISCO E RESPONSABILIDADE:</b><br><br>
    Esta plataforma é uma ferramenta de registro e análise estatística.
    Não constitui recomendação de investimento, consultoria financeira,
    sinal de compra ou venda, promessa de lucro ou gestão de patrimônio.<br><br>
    Trading de forex, criptomoedas, ações, índices e demais ativos envolve risco
    substancial, incluindo a possibilidade de perda total do capital.
    Resultados passados não garantem resultados futuros.
</div>
""", unsafe_allow_html=True)

st.caption("© 2026 Trader Analytics Pro")
