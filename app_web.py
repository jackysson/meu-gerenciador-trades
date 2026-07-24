import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from datetime import datetime
from urllib.parse import quote

# IMPORTS CORRETOS PARA FIRESTORE
# NÃO USE firebase_admin
from google.cloud import firestore
from google.oauth2 import service_account


# =========================================================
# CONFIGURAÇÕES IMPORTANTES
# =========================================================

URL_APP = "https://SEU-APP.streamlit.app"
URL_INSTAGRAM = "https://www.instagram.com/SEU_USUARIO/"
LINK_PAGAMENTO_PRO = "https://buy.stripe.com/SEU_LINK_PRO"

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
# PÁGINA E ESTILO
# =========================================================

st.set_page_config(
    page_title="Trader Analytics Pro",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background-color: #0d1117;
        color: #e6edf3;
    }

    [data-testid="stMetricValue"] {
        font-size: 25px !important;
        color: #58a6ff !important;
    }

    .stMetric {
        background-color: #161b22;
        padding: 14px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }

    .insight-card {
        background-color: #1c2128;
        padding: 18px;
        border-radius: 10px;
        border-left: 5px solid #58a6ff;
        margin-bottom: 14px;
    }

    .upgrade-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 18px;
        border-radius: 12px;
        text-align: center;
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

    .pro-lock {
        text-align: center;
        padding: 45px;
        border-radius: 12px;
        border: 1px solid #30363d;
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CONEXÃO COM FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore_client():
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

        cliente = firestore.Client(
            credentials=credenciais,
            project=firebase["project_id"]
        )

        return cliente, None

    except Exception as erro:
        return None, str(erro)


db, db_error = get_firestore_client()


# =========================================================
# FUNÇÕES FIRESTORE
# =========================================================

def carregar_trades():
    """Carrega somente os trades do usuário logado."""

    if not db or "user_id" not in st.session_state:
        return pd.DataFrame(columns=COLUNAS_TRADES)

    try:
        documentos = (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .order_by("Data")
            .stream()
        )

        dados = [doc.to_dict() for doc in documentos]

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
    """Conta a quantidade de trades do usuário."""

    if not db or "user_id" not in st.session_state:
        return 0

    try:
        documentos = (
            db.collection("users")
            .document(st.session_state.user_id)
            .collection("trades")
            .stream()
        )

        return sum(1 for _ in documentos)

    except Exception:
        return 0


def salvar_trade(trade):
    """Salva trade e aplica limite do plano Free."""

    if not db:
        return False, "Banco de dados não conectado."

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

        return True, "✅ Trade salvo na nuvem!"

    except Exception as erro:
        return False, f"Erro ao salvar trade: {erro}"


# =========================================================
# LOGIN E REGISTRO
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

    aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "🆕 Criar conta"])

    with aba_login:
        email = st.text_input("E-mail", key="email_login")
        senha = st.text_input("Senha", type="password", key="senha_login")

        if st.button("Entrar", type="primary", use_container_width=True):
            email = email.strip().lower()

            if not email or not senha:
                st.error("Preencha e-mail e senha.")

            elif not db:
                st.error(f"Erro de conexão: {db_error}")

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

                    st.rerun()

                else:
                    st.error("E-mail ou senha incorretos.")

    with aba_cadastro:
        email_novo = st.text_input("Seu e-mail", key="email_novo")
        senha_nova = st.text_input("Crie uma senha", type="password", key="senha_nova")
        confirma_senha = st.text_input(
            "Confirme sua senha",
            type="password",
            key="confirma_senha"
        )

        if st.button("Criar conta gratuita", type="primary", use_container_width=True):
            email_novo = email_novo.strip().lower()

            if not email_novo or not senha_nova or not confirma_senha:
                st.error("Preencha todos os campos.")

            elif senha_nova != confirma_senha:
                st.error("As senhas não são iguais.")

            elif len(senha_nova) < 6:
                st.error("A senha deve ter ao menos 6 caracteres.")

            elif not db:
                st.error(f"Erro de conexão: {db_error}")

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

                    st.success("✅ Conta criada! Agora faça login.")

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
# CONTROLE DE SESSÃO
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
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("👤 Minha Conta")
    st.write(st.session_state.user_email)

    plano = st.session_state.get("user_plano", "free")

    if plano == "free":
        st.info(f"🆓 Plano FREE: até {LIMITE_TRADES_FREE} trades")

        st.markdown("""
        <div class='upgrade-banner'>
            <h3 style='color:white; margin:0;'>🚀 Plano PRO</h3>
            <p style='color:#eeeeee;'>
                Trades ilimitados + insights profissionais
            </p>
            <h2 style='color:#ffd700;'>R$ 29,90/mês</h2>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "💳 Assinar PRO",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    elif plano == "pro":
        st.success("⭐ Plano PRO ativo")

    elif plano == "lifetime":
        st.success("👑 Plano LIFETIME ativo")

    st.divider()

    st.session_state.capital_inicial = st.number_input(
        "Capital inicial (USD)",
        min_value=0.0,
        value=float(st.session_state.capital_inicial),
        step=10.0
    )

    st.divider()

    csv = st.session_state.df_trades.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar backup CSV",
        csv,
        "meus_trades.csv",
        "text/csv",
        use_container_width=True
    )

    if st.button("🔄 Sincronizar dados", use_container_width=True):
        st.session_state.df_trades = carregar_trades()
        st.rerun()

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
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
# MÉTRICAS
# =========================================================

df = st.session_state.df_trades.copy()

for coluna in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

total_trades = len(df)
wins = df[df["Lucro"] > 0]
losses = df[df["Lucro"] < 0]

total_profit = df["Lucro"].sum()
capital = st.session_state.capital_inicial
equity = capital + total_profit

win_rate = (len(wins) / total_trades * 100) if total_trades else 0

gross_profit = wins["Lucro"].sum()
gross_loss = abs(losses["Lucro"].sum())

profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

avg_win = wins["Lucro"].mean() if not wins.empty else 0
avg_loss = abs(losses["Lucro"].mean()) if not losses.empty else 0

equity_curve = np.cumsum([capital] + df["Lucro"].tolist())
running_max = np.maximum.accumulate(equity_curve)
drawdown = equity_curve - running_max
max_drawdown = abs(drawdown.min()) if len(drawdown) else 0

expectancy = (
    (win_rate / 100 * avg_win)
    - ((1 - win_rate / 100) * avg_loss)
)


# =========================================================
# DASHBOARD
# =========================================================

st.title("📊 Trader Strategy Analytics Pro")

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("💰 Equity", f"$ {equity:,.2f}")
m2.metric("✅ Vitórias", len(wins))
m3.metric("❌ Derrotas", len(losses))
m4.metric("🎯 Win Rate", f"{win_rate:.1f}%")
m5.metric("📈 Profit Factor", f"{profit_factor:.2f}")

st.divider()

aba1, aba2, aba3, aba4 = st.tabs([
    "🚀 Gráficos",
    "📚 Insights Pro",
    "📝 Histórico",
    "➕ Novo Trade"
])


# =========================================================
# ABA GRÁFICOS
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
                line=dict(color="#58a6ff", width=3),
                fill="tozeroy",
                name="Equity"
            ))

            fig_equity.update_layout(
                title="📈 Crescimento da Conta",
                template="plotly_dark",
                height=380
            )

            st.plotly_chart(fig_equity, use_container_width=True)

        with col2:
            risco = abs(df["Entrada"] - df["SL"])

            fig_risco = px.bar(
                y=risco,
                title="⚠️ Risco por Trade",
                template="plotly_dark",
                color_discrete_sequence=["#f85149"]
            )

            st.plotly_chart(fig_risco, use_container_width=True)


# =========================================================
# ABA INSIGHTS PRO
# =========================================================

with aba2:
    plano = st.session_state.get("user_plano", "free")

    if plano == "free":
        st.markdown("""
        <div class='pro-lock'>
            <h1>🔒</h1>
            <h2>Insights PRO bloqueados</h2>
            <p>
                Desbloqueie métricas profissionais, trades ilimitados,
                drawdown, expectancy, performance por ativo e muito mais.
            </p>
            <h2 style='color:#ffd700;'>R$ 29,90/mês</h2>
        </div>
        """, unsafe_allow_html=True)

        st.link_button(
            "💳 Assinar plano PRO",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    else:
        st.header("📚 Insights Profissionais")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("📉 Max Drawdown", f"$ {max_drawdown:,.2f}")
        c2.metric("💡 Expectancy", f"$ {expectancy:,.2f}")
        c3.metric("📊 Lucro Médio", f"$ {total_profit / total_trades:,.2f}" if total_trades else "$ 0.00")
        c4.metric("🏆 Melhor Trade", f"$ {df['Lucro'].max():,.2f}" if not df.empty else "$ 0.00")

        st.divider()

        st.subheader("💱 Performance por Ativo")

        if not df.empty:
            por_ativo = df.groupby("Ativo").agg(
                Trades=("Lucro", "count"),
                Lucro_Total=("Lucro", "sum"),
                Win_Rate=("Lucro", lambda x: (x > 0).sum() / len(x) * 100)
            ).sort_values("Lucro_Total", ascending=False)

            st.dataframe(
                por_ativo.style.format({
                    "Lucro_Total": "$ {:.2f}",
                    "Win_Rate": "{:.1f}%"
                }),
                use_container_width=True
            )

        st.subheader("📊 Distribuição de Lucros")

        if total_trades > 1:
            fig_hist = px.histogram(
                df,
                x="Lucro",
                nbins=20,
                template="plotly_dark",
                color_discrete_sequence=["#58a6ff"]
            )

            st.plotly_chart(fig_hist, use_container_width=True)


# =========================================================
# ABA HISTÓRICO
# =========================================================

with aba3:
    if df.empty:
        st.info("Nenhum trade registrado ainda.")

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
# ABA NOVO TRADE
# =========================================================

with aba4:
    plano = st.session_state.get("user_plano", "free")

    if plano == "free" and total_trades >= 8:
        st.warning(
            f"⚠️ Você utilizou {total_trades}/{LIMITE_TRADES_FREE} trades gratuitos."
        )

    if plano == "free" and total_trades >= LIMITE_TRADES_FREE:
        st.error("🚫 Seu limite gratuito foi atingido.")

        st.link_button(
            "💳 Assinar PRO — R$ 29,90/mês",
            LINK_PAGAMENTO_PRO,
            use_container_width=True
        )

    else:
        with st.form("novo_trade", clear_on_submit=True):
            ativo = st.text_input(
                "Ativo",
                value=st.session_state.last_asset
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                tipo = st.selectbox("Tipo", ["buy", "sell"])

            with col2:
                volume = st.number_input(
                    "Volume",
                    min_value=0.0,
                    value=0.01,
                    step=0.01
                )

            with col3:
                lucro = st.number_input(
                    "Lucro final (USD)",
                    value=0.0,
                    step=0.01
                )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                entrada = st.number_input("Entrada", value=0.0, format="%.3f")

            with c2:
                saida = st.number_input("Saída", value=0.0, format="%.3f")

            with c3:
                sl = st.number_input("Stop Loss", value=0.0, format="%.3f")

            with c4:
                tp = st.number_input("Take Profit", value=0.0, format="%.3f")

            observacao = st.text_area("Observação")

            enviar = st.form_submit_button(
                "💾 Salvar Trade",
                use_container_width=True
            )

            if enviar:
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
st.subheader("📣 Compartilhe a plataforma")

mensagem = quote(
    f"Conheça o Trader Analytics Pro! 📊\n\n"
    f"Registre seus trades e analise sua performance.\n\n"
    f"{URL_APP}"
)

url = quote(URL_APP)

s1, s2, s3, s4, s5, s6 = st.columns(6)

with s1:
    st.link_button(
        "🟢 WhatsApp",
        f"https://wa.me/?text={mensagem}",
        use_container_width=True
    )

with s2:
    st.link_button(
        "✈️ Telegram",
        f"https://t.me/share/url?url={url}&text=Trader%20Analytics%20Pro",
        use_container_width=True
    )

with s3:
    st.link_button(
        "𝕏 X / Twitter",
        f"https://twitter.com/intent/tweet?text={mensagem}",
        use_container_width=True
    )

with s4:
    st.link_button(
        "🔵 Facebook",
        f"https://www.facebook.com/sharer/sharer.php?u={url}",
        use_container_width=True
    )

with s5:
    st.link_button(
        "📸 Instagram",
        URL_INSTAGRAM,
        use_container_width=True
    )

with s6:
    with st.popover("📋 Copiar link", use_container_width=True):
        st.code(URL_APP, language=None)


# =========================================================
# RODAPÉ
# =========================================================

st.divider()

st.markdown("""
<div class='disclaimer'>
    <b>⚠️ AVISO DE RISCO E RESPONSABILIDADE:</b><br><br>
    Esta plataforma é uma ferramenta de análise estatística e gestão de operações.
    Não constitui recomendação de investimento, aconselhamento financeiro,
    sinal de compra ou venda, promessa de lucro ou gestão de recursos.
    Trading envolve riscos substanciais, inclusive a perda total do capital.
</div>
""", unsafe_allow_html=True)
