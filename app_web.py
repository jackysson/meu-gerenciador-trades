import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account


# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================

st.set_page_config(
    page_title="Trader Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FREE_TRADE_LIMIT = 10

TRADE_COLUMNS = [
    "id",
    "Data",
    "Ativo",
    "Tipo",
    "Volume",
    "Entrada",
    "Saída",
    "SL",
    "TP",
    "Lucro",
    "Obs",
]


# =========================================================
# TEMA (DIA / NOITE)
# =========================================================

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "🌙 Noite"


def apply_theme(mode):
    if mode == "☀️ Dia":
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #ffffff !important;
                color: #1a1a2e !important;
            }

            section[data-testid="stSidebar"] {
                background-color: #f0f2f6 !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 26px !important;
                color: #0066cc !important;
            }

            [data-testid="stMetricLabel"] {
                color: #333333 !important;
            }

            .stMetric {
                background-color: #f8f9fa !important;
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #dee2e6;
            }

            .insight-card {
                background-color: #f0f7ff !important;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0066cc;
                margin-bottom: 15px;
                color: #1a1a2e !important;
            }

            .badge-card {
                background-color: #f8f9fa !important;
                padding: 18px;
                border-radius: 12px;
                border: 1px solid #dee2e6;
                min-height: 160px;
                margin-bottom: 12px;
                color: #1a1a2e !important;
            }

            .plan-card {
                background-color: #f8f9fa !important;
                padding: 25px;
                border-radius: 14px;
                border: 1px solid #dee2e6;
                margin-bottom: 15px;
                color: #1a1a2e !important;
            }

            .connection-ok {
                background-color: #d4edda;
                color: #155724;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #c3e6cb;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }

            .connection-off {
                background-color: #fff3cd;
                color: #856404;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #ffeeba;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }

            h1, h2, h3, h4, h5, h6, p, span, label, div {
                color: #1a1a2e !important;
            }

            .stAlert > div {
                color: #1a1a2e !important;
            }

            .stTabs [data-baseweb="tab"] {
                color: #333333 !important;
            }

            .stDataFrame {
                color: #1a1a2e !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0d1117 !important;
                color: #e6edf3 !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 26px !important;
                color: #58a6ff !important;
            }

            .stMetric {
                background-color: #161b22 !important;
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #30363d;
            }

            .insight-card {
                background-color: #1c2128 !important;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #58a6ff;
                margin-bottom: 15px;
                color: #e6edf3 !important;
            }

            .badge-card {
                background-color: #161b22 !important;
                padding: 18px;
                border-radius: 12px;
                border: 1px solid #30363d;
                min-height: 160px;
                margin-bottom: 12px;
                color: #e6edf3 !important;
            }

            .plan-card {
                background-color: #161b22 !important;
                padding: 25px;
                border-radius: 14px;
                border: 1px solid #30363d;
                margin-bottom: 15px;
                color: #e6edf3 !important;
            }

            .connection-ok {
                background-color: #0d2818;
                color: #3fb950;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #238636;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }

            .connection-off {
                background-color: #2d1b00;
                color: #f0883e;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #9e6a03;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


apply_theme(st.session_state["theme_mode"])


# =========================================================
# LOGIN
# =========================================================

if not st.user.is_logged_in:
    st.title("📊 Trader Analytics Pro")

    st.markdown(
        """
        Organize suas operações, acompanhe seu desempenho
        e analise seus resultados com segurança.
        """
    )

    st.info(
        "Entre com sua conta Google para acessar seus dados."
    )

    if st.button(
        "🔐 Entrar com Google",
        type="primary",
        use_container_width=True,
    ):
        st.login()

    st.divider()

    st.caption(
        "A plataforma possui finalidade informativa, "
        "estatística e organizacional. Não oferece "
        "recomendação de investimento nem garante resultados."
    )

    st.stop()


# =========================================================
# DADOS DO USUÁRIO AUTENTICADO
# =========================================================

usuario_id = str(st.user["sub"])
usuario_email = str(
    st.user.get("email", "")
).strip().lower()
usuario_nome = str(
    st.user.get("name", "Usuário")
).strip()

if not usuario_email:
    st.error(
        "Não foi possível identificar o e-mail da sua conta."
    )
    st.stop()


# =========================================================
# CONEXÃO COM FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "A seção [gcp_service_account] não foi "
            "encontrada nos Secrets."
        )

    info = dict(st.secrets["gcp_service_account"])

    if "private_key" not in info:
        raise RuntimeError(
            "A chave private_key não foi encontrada."
        )

    info["private_key"] = info["private_key"].replace(
        "\\n", "\n"
    )

    project_id = info.get("project_id", "")

    credenciais = (
        service_account.Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform"
            ],
        )
    )

    return firestore.Client(
        credentials=credenciais,
        project=project_id,
    )


cloud_connected = False
db = None

try:
    db = get_firestore()
    cloud_connected = True
except Exception:
    cloud_connected = False


# =========================================================
# FUNÇÕES DO PROPRIETÁRIO E PLANOS
# =========================================================

def get_owner_emails():
    emails = st.secrets.get("owner_emails", [])
    return [
        str(email).strip().lower()
        for email in emails
    ]


def is_owner(email):
    return email.strip().lower() in get_owner_emails()


def ensure_user(user_id, name, email):
    user_ref = db.collection("users").document(user_id)
    document = user_ref.get()

    if not document.exists:
        user_ref.set(
            {
                "name": name,
                "email": email,
                "plan": "free",
                "access_type": "free",
                "subscription_status": "inactive",
                "subscription_expires_at": None,
                "trade_count": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )

        return {
            "plan": "free",
            "access_type": "free",
            "subscription_status": "inactive",
            "subscription_expires_at": None,
            "trade_count": 0,
        }

    current_data = document.to_dict()

    user_ref.set(
        {
            "name": name,
            "email": email,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    if "trade_count" not in current_data:
        trades_ref = (
            db.collection("users")
            .document(user_id)
            .collection("trades")
        )
        total = sum(1 for _ in trades_ref.stream())
        user_ref.set(
            {"trade_count": total},
            merge=True,
        )
        current_data["trade_count"] = total

    return current_data


def normalize_expiration(expiration):
    if expiration is None:
        return None

    if isinstance(expiration, datetime):
        if expiration.tzinfo is None:
            return expiration.replace(tzinfo=timezone.utc)
        return expiration

    if isinstance(expiration, str):
        try:
            normalized = expiration.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    return None


def has_pro_access(user_id, email):
    if is_owner(email):
        return True

    if db is None:
        return False

    document = (
        db.collection("users")
        .document(user_id)
        .get()
    )

    if not document.exists:
        return False

    data = document.to_dict()

    if data.get("plan") != "pro":
        return False

    if data.get("subscription_status") not in {
        "active",
        "trialing",
    }:
        return False

    if data.get("access_type") == "lifetime":
        return True

    expiration = normalize_expiration(
        data.get("subscription_expires_at")
    )

    if expiration is None:
        return False

    return expiration > datetime.now(timezone.utc)


def get_plan_information(user_id, email):
    owner = is_owner(email)

    if db is None:
        return {
            "is_owner": owner,
            "is_pro": owner,
            "plan": "pro" if owner else "free",
            "access_type": "owner" if owner else "free",
            "subscription_status": (
                "owner" if owner else "inactive"
            ),
            "subscription_expires_at": None,
            "trade_count": 0,
        }

    document = (
        db.collection("users")
        .document(user_id)
        .get()
    )

    data = (
        document.to_dict() if document.exists else {}
    )
    pro_access = has_pro_access(user_id, email)

    return {
        "is_owner": owner,
        "is_pro": pro_access,
        "plan": data.get("plan", "free"),
        "access_type": data.get("access_type", "free"),
        "subscription_status": data.get(
            "subscription_status", "inactive"
        ),
        "subscription_expires_at": normalize_expiration(
            data.get("subscription_expires_at")
        ),
        "trade_count": int(data.get("trade_count", 0)),
    }


# =========================================================
# FUNÇÕES DOS TRADES
# =========================================================

def load_trades(user_id):
    if db is None:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    trades_ref = (
        db.collection("users")
        .document(user_id)
        .collection("trades")
        .order_by("created_at", direction="ASCENDING")
    )

    records = []

    for document in trades_ref.stream():
        data = document.to_dict()
        created_at = data.get("created_at")

        if isinstance(created_at, datetime):
            formatted_date = created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            formatted_date = (
                str(created_at) if created_at else ""
            )

        records.append(
            {
                "id": document.id,
                "Data": formatted_date,
                "Ativo": data.get("asset", ""),
                "Tipo": data.get("type", ""),
                "Volume": data.get("volume", 0),
                "Entrada": data.get("entry", 0),
                "Saída": data.get("exit", 0),
                "SL": data.get("sl", 0),
                "TP": data.get("tp", 0),
                "Lucro": data.get("profit", 0),
                "Obs": data.get("observation", ""),
            }
        )

    return pd.DataFrame(records, columns=TRADE_COLUMNS)


def save_trade(user_id, email, trade_data):
    if not user_id:
        raise ValueError("Usuário não autenticado.")

    if db is None:
        raise RuntimeError("Banco de dados indisponível.")

    user_ref = db.collection("users").document(user_id)
    user_snapshot = user_ref.get()

    if not user_snapshot.exists:
        raise ValueError(
            "Cadastro do usuário não encontrado."
        )

    user_data = user_snapshot.to_dict()
    current_count = int(user_data.get("trade_count", 0))

    pro_access = has_pro_access(user_id, email)

    if (
        not pro_access
        and current_count >= FREE_TRADE_LIMIT
    ):
        raise PermissionError(
            "Você atingiu o limite de 10 trades "
            "do plano gratuito."
        )

    trade_ref = (
        user_ref.collection("trades").document()
    )

    record = {
        "asset": trade_data["asset"],
        "type": trade_data["type"],
        "volume": float(trade_data["volume"]),
        "entry": float(trade_data["entry"]),
        "exit": float(trade_data["exit"]),
        "sl": float(trade_data["sl"]),
        "tp": float(trade_data["tp"]),
        "profit": float(trade_data["profit"]),
        "observation": trade_data.get(
            "observation", ""
        ),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    trade_ref.set(record)

    user_ref.set(
        {
            "trade_count": current_count + 1,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    return trade_ref.id


def edit_trade(user_id, trade_id, trade_data):
    if not user_id or not trade_id:
        raise ValueError("Usuário ou trade inválido.")

    if db is None:
        raise RuntimeError("Banco de dados indisponível.")

    reference = (
        db.collection("users")
        .document(user_id)
        .collection("trades")
        .document(trade_id)
    )

    record = {
        "asset": trade_data["asset"],
        "type": trade_data["type"],
        "volume": float(trade_data["volume"]),
        "entry": float(trade_data["entry"]),
        "exit": float(trade_data["exit"]),
        "sl": float(trade_data["sl"]),
        "tp": float(trade_data["tp"]),
        "profit": float(trade_data["profit"]),
        "observation": trade_data.get(
            "observation", ""
        ),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    reference.set(record, merge=True)


def delete_trade(user_id, trade_id):
    if not user_id or not trade_id:
        raise ValueError("Usuário ou trade inválido.")

    if db is None:
        raise RuntimeError("Banco de dados indisponível.")

    user_ref = db.collection("users").document(user_id)
    trade_ref = (
        user_ref.collection("trades")
        .document(trade_id)
    )

    user_snapshot = user_ref.get()

    if not user_snapshot.exists:
        return

    user_data = user_snapshot.to_dict()
    current_count = int(
        user_data.get("trade_count", 0)
    )

    trade_ref.delete()

    new_count = max(0, current_count - 1)

    user_ref.set(
        {
            "trade_count": new_count,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


# =========================================================
# CAPITAL INICIAL
# =========================================================

def load_initial_capital(user_id):
    if db is None:
        return 20.0

    document = (
        db.collection("users")
        .document(user_id)
        .collection("settings")
        .document("profile")
        .get()
    )

    if not document.exists:
        return 20.0

    data = document.to_dict()
    return float(data.get("initial_capital", 20.0))


def save_initial_capital(user_id, capital):
    if db is None:
        raise RuntimeError("Banco de dados indisponível.")

    (
        db.collection("users")
        .document(user_id)
        .collection("settings")
        .document("profile")
        .set(
            {
                "initial_capital": float(capital),
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
    )


# =========================================================
# INSÍGNIAS PRO
# =========================================================

def calculate_badges(dataframe):
    badges = []

    if dataframe.empty:
        return badges

    total = len(dataframe)
    wins = len(
        dataframe[dataframe["Lucro"] > 0]
    )
    total_profit = dataframe["Lucro"].sum()
    win_rate = (
        wins / total * 100 if total > 0 else 0
    )

    if total >= 10:
        badges.append(
            {
                "icon": "📝",
                "name": "Diário Iniciado",
                "description": (
                    "Registrou pelo menos 10 operações."
                ),
            }
        )

    if total >= 50:
        badges.append(
            {
                "icon": "🏅",
                "name": "Trader Consistente",
                "description": (
                    "Registrou pelo menos 50 operações."
                ),
            }
        )

    if total >= 100:
        badges.append(
            {
                "icon": "🔥",
                "name": "Centúria",
                "description": (
                    "Registrou pelo menos 100 operações."
                ),
            }
        )

    if total >= 20 and win_rate >= 60:
        badges.append(
            {
                "icon": "🎯",
                "name": "Alta Precisão",
                "description": (
                    "Win rate de pelo menos 60% "
                    "em 20 operações."
                ),
            }
        )

    if total >= 20 and win_rate >= 70:
        badges.append(
            {
                "icon": "👑",
                "name": "Mestre da Precisão",
                "description": (
                    "Win rate de pelo menos 70% "
                    "em 20 operações."
                ),
            }
        )

    if total >= 20 and total_profit > 0:
        badges.append(
            {
                "icon": "📈",
                "name": "Histórico Positivo",
                "description": (
                    "Resultado acumulado positivo "
                    "após 20 operações."
                ),
            }
        )

    if total >= 50 and total_profit > 0:
        badges.append(
            {
                "icon": "💎",
                "name": "Resultados Sólidos",
                "description": (
                    "Resultado positivo após "
                    "50 operações."
                ),
            }
        )

    return badges


# =========================================================
# INICIALIZAR USUÁRIO E SESSÃO
# =========================================================

if cloud_connected and db is not None:
    try:
        ensure_user(
            usuario_id,
            usuario_nome,
            usuario_email,
        )
    except Exception:
        st.error(
            "Não foi possível inicializar sua conta."
        )
        st.stop()
else:
    st.warning(
        "Modo offline: os dados não serão "
        "salvos permanentemente."
    )


if st.session_state.get("active_user_id") != usuario_id:
    st.session_state["active_user_id"] = usuario_id
    st.session_state.pop("df_trades", None)
    st.session_state.pop("initial_capital", None)
    st.session_state.pop("last_asset", None)
    st.session_state.pop("editing_trade_id", None)
    st.session_state.pop("confirm_delete_id", None)


if "df_trades" not in st.session_state:
    try:
        st.session_state["df_trades"] = load_trades(
            usuario_id
        )
    except Exception:
        st.session_state["df_trades"] = pd.DataFrame(
            columns=TRADE_COLUMNS
        )
        st.error(
            "Não foi possível carregar seus trades."
        )


if "initial_capital" not in st.session_state:
    try:
        st.session_state["initial_capital"] = (
            load_initial_capital(usuario_id)
        )
    except Exception:
        st.session_state["initial_capital"] = 20.0


if "last_asset" not in st.session_state:
    st.session_state["last_asset"] = "USDJPY"


try:
    plan_info = get_plan_information(
        usuario_id,
        usuario_email,
    )
except Exception:
    st.error(
        "Não foi possível verificar seu plano."
    )
    st.stop()

is_pro = plan_info["is_pro"]
owner = plan_info["is_owner"]


if "flash_message" in st.session_state:
    st.success(st.session_state.pop("flash_message"))


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:
    # TEMA
    theme_choice = st.radio(
        "🎨 Aparência",
        ["🌙 Noite", "☀️ Dia"],
        horizontal=True,
        key="theme_selector",
    )

    if theme_choice != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = theme_choice
        st.rerun()

    st.divider()

    # CONEXÃO COM A NUVEM
    st.subheader("☁️ Status da Conexão")

    if cloud_connected:
        st.markdown(
            """
            <div class="connection-ok">
                ✅ Nuvem Conectada
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Dados sincronizados com o Firestore."
        )
    else:
        st.markdown(
            """
            <div class="connection-off">
                ⚠️ Modo Offline
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "Os dados não estão sendo salvos na nuvem."
        )

    st.divider()

    # CONTA
    st.subheader("👤 Minha conta")

    st.write(usuario_nome)
    st.caption(usuario_email)

    if owner:
        st.success(
            "🛡️ Desenvolvedor — Pro permanente"
        )

    elif is_pro:
        st.success(
            "⭐ Plano Pro — R$ 29,90/mês"
        )

        expiration = plan_info.get(
            "subscription_expires_at"
        )

        if expiration:
            st.caption(
                f"Acesso até "
                f"{expiration.strftime('%d/%m/%Y')}."
            )

    else:
        st.info("🆓 Plano Gratuito")
        st.caption("Limite de 10 trades.")

    st.divider()

    # CONTROLE DE TRADES
    current_count = len(
        st.session_state["df_trades"]
    )

    if not is_pro:
        remaining = max(
            0,
            FREE_TRADE_LIMIT - current_count,
        )

        st.progress(
            min(
                current_count / FREE_TRADE_LIMIT,
                1.0,
            ),
            text=(
                f"{current_count}/"
                f"{FREE_TRADE_LIMIT} trades"
            ),
        )

        st.caption(
            f"Restam {remaining} trade(s)."
        )

        if current_count >= FREE_TRADE_LIMIT:
            st.warning(
                "Limite gratuito atingido."
            )

    else:
        st.caption(
            f"{current_count} trade(s) registrados."
        )

    st.divider()

    # CAPITAL INICIAL
    st.subheader("💰 Configuração")

    with st.form("capital_form"):
        capital_value = st.number_input(
            "Capital Inicial (USD)",
            min_value=0.0,
            value=float(
                st.session_state["initial_capital"]
            ),
            step=1.0,
            format="%.2f",
        )

        save_capital = st.form_submit_button(
            "💾 Salvar capital",
            use_container_width=True,
        )

        if save_capital:
            try:
                save_initial_capital(
                    usuario_id,
                    capital_value,
                )
                st.session_state[
                    "initial_capital"
                ] = capital_value
                st.success(
                    "Capital atualizado!"
                )
            except Exception:
                st.error(
                    "Não foi possível salvar o capital."
                )

    st.divider()

    # EXPORTAÇÃO
    st.subheader("💾 Exportação")

    export_df = st.session_state.get(
        "df_trades",
        pd.DataFrame(columns=TRADE_COLUMNS),
    )

    export_cols = [
        c for c in TRADE_COLUMNS if c != "id"
    ]

    csv_data = export_df[
        export_cols
    ].to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar meus dados",
        data=csv_data,
        file_name="meus_trades.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.button(
        "🔄 Sincronizar agora",
        use_container_width=True,
    ):
        try:
            st.session_state["df_trades"] = (
                load_trades(usuario_id)
            )
            st.rerun()
        except Exception:
            st.error(
                "Não foi possível sincronizar."
            )

    st.divider()

    # REDES SOCIAIS
    st.subheader("📱 Conecte-se")

    st.markdown(
        """
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <a href="https://wa.me/SEUNUMERO?text=Olá!%20Estou%20usando%20o%20Trader%20Analytics%20Pro!"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background-color:#25D366;color:white;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:13px;">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                WhatsApp
            </a>
            <a href="https://instagram.com/SEUPERFIL"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:13px;">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
                Instagram
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("🔗 Compartilhar")

    app_url = (
        "https://SEU-APP.streamlit.app"
    )

    share_text = (
        "Estou usando o Trader Analytics Pro "
        "para organizar minhas operações!"
    )

    st.markdown(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <a href="https://wa.me/?text={share_text}%0A%0A{app_url}"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background-color:#25D366;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 WhatsApp
            </a>
            <a href="https://www.instagram.com/direct/new/?text={share_text}%20{app_url}"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 Instagram
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "🚪 Sair",
        use_container_width=True,
    ):
        st.logout()


# =========================================================
# PREPARAR DADOS E MÉTRICAS
# =========================================================

df = st.session_state["df_trades"].copy()

for column in [
    "Lucro",
    "Entrada",
    "Saída",
    "SL",
    "TP",
    "Volume",
]:
    if column not in df.columns:
        df[column] = 0

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(0)

loss_df = df[df["Lucro"] < 0]
win_df = df[df["Lucro"] > 0]

loss_count = len(loss_df)
win_count = len(win_df)

avg_loss_cash = (
    abs(loss_df["Lucro"].mean())
    if loss_count > 0
    else 0
)

avg_loss_pts = (
    abs(
        loss_df["Entrada"] - loss_df["SL"]
    ).mean()
    if loss_count > 0
    else 0
)

total_profit = df["Lucro"].sum()
initial_capital = st.session_state[
    "initial_capital"
]
equity = initial_capital + total_profit

win_rate = (
    win_count / len(df) * 100
    if len(df) > 0
    else 0
)

gross_profit = win_df["Lucro"].sum()
gross_loss = abs(loss_df["Lucro"].sum())

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else 0
)


# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================

st.title("📊 Trader Strategy Analytics Pro")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "💰 Equity",
    f"$ {equity:,.2f}",
)
c2.metric("✅ Vitórias", win_count)
c3.metric("❌ Derrotas", loss_count)
c4.metric(
    "🎯 Win Rate",
    f"{win_rate:.1f}%",
)
c5.metric(
    "📈 Profit Factor",
    f"{profit_factor:.2f}",
)

st.divider()


# =========================================================
# ABAS
# =========================================================

(
    tab_graphs,
    tab_insights,
    tab_history,
    tab_new,
    tab_plan,
) = st.tabs(
    [
        "🚀 Gráficos",
        "📚 Insights & Insígnias",
        "📝 Histórico",
        "➕ Novo Trade",
        "⭐ Planos",
    ]
)


# =========================================================
# GRÁFICOS BÁSICOS
# =========================================================

with tab_graphs:
    if df.empty:
        st.info(
            "Adicione trades para ver os gráficos."
        )

    else:
        col_a, col_b = st.columns(2)

        with col_a:
            equity_curve = (
                initial_capital
                + df["Lucro"].cumsum()
            )

            fig_equity = px.area(
                x=list(
                    range(1, len(equity_curve) + 1)
                ),
                y=equity_curve,
                title="Crescimento da Conta",
                labels={
                    "x": "Trade",
                    "y": "Equity",
                },
                template="plotly_dark",
            )

            st.plotly_chart(
                fig_equity,
                use_container_width=True,
            )

        with col_b:
            risk_df = df.copy()
            risk_df["Risco_Pts"] = abs(
                risk_df["Entrada"] - risk_df["SL"]
            )

            fig_risk = px.bar(
                risk_df,
                x="Ativo",
                y="Risco_Pts",
                title="Risco por Trade",
                color_discrete_sequence=["#f85149"],
                template="plotly_dark",
            )

            st.plotly_chart(
                fig_risk,
                use_container_width=True,
            )

        if is_pro:
            col_c, col_d = st.columns(2)

            with col_c:
                fig_wins = px.pie(
                    names=[
                        "Vitórias",
                        "Derrotas",
                    ],
                    values=[
                        win_count,
                        loss_count,
                    ],
                    title="Distribuição",
                    template="plotly_dark",
                    color_discrete_sequence=[
                        "#3fb950",
                        "#f85149",
                    ],
                )

                st.plotly_chart(
                    fig_wins,
                    use_container_width=True,
                )

            with col_d:
                if "Ativo" in df.columns:
                    asset_profit = (
                        df.groupby("Ativo")["Lucro"]
                        .sum()
                        .reset_index()
                    )

                    fig_assets = px.bar(
                        asset_profit,
                        x="Ativo",
                        y="Lucro",
                        title="Lucro por Ativo",
                        color_discrete_sequence=[
                            "#58a6ff"
                        ],
                        template="plotly_dark",
                    )

                    st.plotly_chart(
                        fig_assets,
                        use_container_width=True,
                    )


# =========================================================
# INSIGHTS E INSÍGNIAS
# =========================================================

with tab_insights:
    if not is_pro:
        st.subheader(
            "🔒 Recurso exclusivo do Plano Pro"
        )

        st.info(
            "Assine o Plano Pro por R$ 29,90/mês "
            "para acessar resumos, insights e insígnias."
        )

        st.markdown(
            """
            ### Recursos exclusivos do Pro

            - Trades ilimitados
            - Resumos estatísticos avançados
            - Insights de desempenho
            - Análise de perdas detalhada
            - Simulações baseadas no histórico
            - Insígnias de evolução
            - Gráficos adicionais
            """
        )

    else:
        st.header("📚 Resumo Estatístico")

        if df.empty:
            st.info(
                "Adicione trades para gerar suas análises."
            )

        else:
            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>📉 Análise de Perdas</h4>
                    <p>Perda média em dinheiro: <b>$ {avg_loss_cash:.2f}</b></p>
                    <p>Perda média em pontos: <b>{avg_loss_pts:.3f} pts</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            avg_trade = (
                total_profit / len(df)
                if len(df) > 0
                else 0
            )

            sim_30 = equity + avg_trade * 30

            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>🧮 Simulação Estatística</h4>
                    <p>Projeção baseada na média de 30 trades: <b>$ {sim_30:,.2f}</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "Simulação baseada em dados históricos. "
                "Não representa previsão ou garantia de "
                "rentabilidade futura."
            )

            st.divider()

            st.subheader(
                "🏆 Minhas Insígnias"
            )

            badges = calculate_badges(df)

            if not badges:
                st.info(
                    "Continue registrando operações "
                    "para desbloquear insígnias."
                )

            else:
                badge_cols = st.columns(
                    min(len(badges), 3)
                )

                for idx, badge in enumerate(badges):
                    col = badge_cols[
                        idx % len(badge_cols)
                    ]

                    with col:
                        st.markdown(
                            f"""
                            <div class="badge-card">
                                <h2>{badge["icon"]}</h2>
                                <h4>{badge["name"]}</h4>
                                <p>{badge["description"]}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )


# =========================================================
# HISTÓRICO COM EDIÇÃO E EXCLUSÃO
# =========================================================

with tab_history:
    if df.empty:
        st.info("Nenhum trade registrado.")

    else:
        if "confirm_delete_id" in st.session_state:
            del_id = st.session_state[
                "confirm_delete_id"
            ]

            st.warning(
                f"⚠️ Tem certeza que deseja excluir "
                f"o trade {del_id[:8]}?"
            )

            col_confirm, col_cancel = (
                st.columns(2)
            )

            with col_confirm:
                if st.button(
                    "✅ Sim, excluir",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        delete_trade(
                            usuario_id, del_id
                        )
                        st.session_state.pop(
                            "confirm_delete_id",
                            None,
                        )
                        st.session_state[
                            "df_trades"
                        ] = load_trades(
                            usuario_id
                        )
                        st.success(
                            "Trade excluído!"
                        )
                        st.rerun()

                    except Exception:
                        st.error(
                            "Não foi possível "
                            "excluir."
                        )

            with col_cancel:
                if st.button(
                    "❌ Cancelar",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        "confirm_delete_id",
                        None,
                    )
                    st.rerun()

            st.divider()

        editing_id = st.session_state.get(
            "editing_trade_id"
        )

        if editing_id:
            trade_row = df[df["id"] == editing_id]

            if not trade_row.empty:
                row = trade_row.iloc[0]

                st.subheader("✏️ Editar Trade")

                with st.form("edit_trade_form"):
                    e1, e2, e3, e4 = (
                        st.columns(4)
                    )

                    edit_asset = e1.text_input(
                        "Ativo",
                        value=row["Ativo"],
                    )

                    edit_type = e2.selectbox(
                        "Tipo",
                        ["buy", "sell"],
                        index=(
                            0
                            if row["Tipo"] == "buy"
                            else 1
                        ),
                    )

                    edit_volume = e3.number_input(
                        "Volume",
                        min_value=0.01,
                        value=float(
                            row["Volume"]
                        ),
                        step=0.01,
                        format="%.2f",
                    )

                    edit_profit = e4.number_input(
                        "Lucro",
                        value=float(
                            row["Lucro"]
                        ),
                        format="%.2f",
                    )

                    st.divider()

                    e5, e6, e7, e8 = (
                        st.columns(4)
                    )

                    edit_entry = e5.number_input(
                        "Entrada",
                        value=float(
                            row["Entrada"]
                        ),
                        format="%.3f",
                    )

                    edit_exit = e6.number_input(
                        "Saída",
                        value=float(
                            row["Saída"]
                        ),
                        format="%.3f",
                    )

                    edit_sl = e7.number_input(
                        "SL",
                        value=float(row["SL"]),
                        format="%.3f",
                    )

                    edit_tp = e8.number_input(
                        "TP",
                        value=float(row["TP"]),
                        format="%.3f",
                    )

                    edit_obs = st.text_area(
                        "Observação",
                        value=row["Obs"],
                        max_chars=500,
                    )

                    save_edit, cancel_edit = (
                        st.columns(2)
                    )

                    with save_edit:
                        if st.form_submit_button(
                            "💾 Salvar Alterações",
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                trade_data = {
                                    "asset": (
                                        edit_asset.strip()
                                        .upper()
                                    ),
                                    "type": edit_type,
                                    "volume": (
                                        edit_volume
                                    ),
                                    "entry": (
                                        edit_entry
                                    ),
                                    "exit": (
                                        edit_exit
                                    ),
                                    "sl": edit_sl,
                                    "tp": edit_tp,
                                    "profit": (
                                        edit_profit
                                    ),
                                    "observation": (
                                        edit_obs.strip()
                                    ),
                                }

                                edit_trade(
                                    usuario_id,
                                    editing_id,
                                    trade_data,
                                )

                                st.session_state.pop(
                                    "editing_trade_id",
                                    None,
                                )
                                st.session_state[
                                    "df_trades"
                                ] = load_trades(
                                    usuario_id
                                )
                                st.success(
                                    "Trade atualizado!"
                                )
                                st.rerun()

                            except Exception:
                                st.error(
                                    "Não foi possível "
                                    "salvar."
                                )

                    with cancel_edit:
                        if st.form_submit_button(
                            "❌ Cancelar",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                "editing_trade_id",
                                None,
                            )
                            st.rerun()

            st.divider()

        display_df = df.copy()

        display_cols = [
            c
            for c in TRADE_COLUMNS
            if c != "id"
        ]

        st.dataframe(
            display_df[display_cols].sort_index(
                ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.subheader("Ações por trade")

        trade_ids = df["id"].tolist()

        selected_trade = st.selectbox(
            "Selecione o ID do trade",
            options=trade_ids,
            format_func=lambda x: (
                f"{x[:8]}..."
                if len(x) > 8
                else x
            ),
        )

        if selected_trade:
            col_edit, col_delete = (
                st.columns(2)
            )

            with col_edit:
                if st.button(
                    "✏️ Editar",
                    use_container_width=True,
                ):
                    st.session_state[
                        "editing_trade_id"
                    ] = selected_trade
                    st.rerun()

            with col_delete:
                if st.button(
                    "🗑️ Excluir",
                    use_container_width=True,
                ):
                    st.session_state[
                        "confirm_delete_id"
                    ] = selected_trade
                    st.rerun()


# =========================================================
# NOVO TRADE
# =========================================================

with tab_new:
    current_count = len(df)

    free_limit = (
        not is_pro
        and current_count >= FREE_TRADE_LIMIT
    )

    if free_limit:
        st.warning(
            "Você atingiu o limite de 10 trades "
            "do plano gratuito."
        )

        st.info(
            "No Plano Pro você terá trades "
            "ilimitados, resumos, insights e "
            "insígnias por R$ 29,90/mês."
        )

    else:
        with st.form(
            "add_trade_form",
            clear_on_submit=True,
        ):
            st.subheader("Registrar Operação")

            r1, r2, r3, r4 = st.columns(4)

            asset = r1.text_input(
                "Ativo",
                value=st.session_state.get(
                    "last_asset", "USDJPY"
                ),
            )

            trade_type = r2.selectbox(
                "Tipo",
                ["buy", "sell"],
            )

            volume = r3.number_input(
                "Volume",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
            )

            profit_val = r4.number_input(
                "Lucro Final (USD)",
                value=0.0,
                format="%.2f",
            )

            st.divider()

            r5, r6, r7, r8 = st.columns(4)

            entry = r5.number_input(
                "Entrada",
                value=0.0,
                format="%.3f",
            )

            exit_price = r6.number_input(
                "Saída",
                value=0.0,
                format="%.3f",
            )

            sl = r7.number_input(
                "SL",
                value=0.0,
                format="%.3f",
            )

            tp = r8.number_input(
                "TP",
                value=0.0,
                format="%.3f",
            )

            observation = st.text_area(
                "Observação",
                max_chars=500,
            )

            save_btn = st.form_submit_button(
                "💾 SALVAR TRADE",
                type="primary",
                use_container_width=True,
            )

            if save_btn:
                errors = []

                if not asset.strip():
                    errors.append(
                        "Informe o ativo."
                    )

                if volume <= 0:
                    errors.append(
                        "O volume deve ser maior "
                        "que zero."
                    )

                if trade_type not in [
                    "buy",
                    "sell",
                ]:
                    errors.append(
                        "Tipo inválido."
                    )

                if errors:
                    for error in errors:
                        st.error(error)

                else:
                    trade_data = {
                        "asset": (
                            asset.strip().upper()
                        ),
                        "type": trade_type,
                        "volume": volume,
                        "entry": entry,
                        "exit": exit_price,
                        "sl": sl,
                        "tp": tp,
                        "profit": profit_val,
                        "observation": (
                            observation.strip()
                        ),
                    }

                    try:
                        save_trade(
                            usuario_id,
                            usuario_email,
                            trade_data,
                        )

                        st.session_state[
                            "last_asset"
                        ] = (
                            asset.strip().upper()
                        )

                        st.session_state[
                            "df_trades"
                        ] = load_trades(
                            usuario_id
                        )

                        st.session_state[
                            "flash_message"
                        ] = (
                            "✅ Trade salvo "
                            "permanentemente!"
                        )

                        st.rerun()

                    except PermissionError as error:
                        st.warning(str(error))

                    except Exception:
                        st.error(
                            "Não foi possível salvar. "
                            "Tente novamente."
                        )


# =========================================================
# PLANOS
# =========================================================

with tab_plan:
    st.title("⭐ Planos")

    free_col, pro_col = st.columns(2)

    with free_col:
        st.markdown(
            """
            <div class="plan-card">
                <h2>🆓 Gratuito</h2>
                <h3>R$ 0</h3>
                <br>
                <p>✅ Até 10 trades</p>
                <p>✅ Métricas básicas</p>
                <p>✅ Gráficos básicos</p>
                <p>✅ Histórico</p>
                <p>✅ Exportação CSV</p>
                <p>✅ Capital inicial</p>
                <br>
                <p>❌ Insights avançados</p>
                <p>❌ Insígnias</p>
                <p>❌ Gráficos extras</p>
                <p>❌ Trades ilimitados</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not is_pro:
            st.info(
                "Seu plano atual: Gratuito"
            )
        else:
            st.caption(
                "Você já possui acesso Pro."
            )

    with pro_col:
        st.markdown(
            """
            <div class="plan-card">
                <h2>⭐ Pro</h2>
                <h3>R$ 29,90/mês</h3>
                <br>
                <p>✅ Trades ilimitados</p>
                <p>✅ Métricas e gráficos</p>
                <p>✅ Resumos estatísticos</p>
                <p>✅ Insights de desempenho</p>
                <p>✅ Análise de perdas</p>
                <p>✅ Simulações</p>
                <p>✅ Insígnias</p>
                <p>✅ Gráficos extras</p>
                <p>✅ Exportação CSV</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if owner:
            st.success(
                "🛡️ Sua conta de desenvolvedor "
                "já possui Pro permanente."
            )

        elif is_pro:
            st.success(
                "⭐ Seu Plano Pro está ativo."
            )

        else:
            st.button(
                "⭐ Assinar por R$ 29,90/mês",
                type="primary",
                use_container_width=True,
                disabled=True,
                help=(
                    "Pagamento ainda será "
                    "configurado."
                ),
            )

            st.caption(
                "Pagamento em fase de configuração."
            )

    st.divider()

    st.subheader("📊 Comparação dos Planos")

    comparison = pd.DataFrame(
        {
            "Recurso": [
                "Trades",
                "Métricas",
                "Gráficos básicos",
                "Histórico",
                "Exportação CSV",
                "Capital inicial",
                "Insights avançados",
                "Insígnias",
                "Gráficos extras",
                "Análise por ativo",
                "Simulações",
                "Análise de perdas",
            ],
            "Gratuito": [
                "Até 10",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "❌",
                "❌",
                "❌",
                "❌",
                "❌",
                "❌",
            ],
            "Pro (R$ 29,90/mês)": [
                "Ilimitado",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
                "✅",
            ],
        }
    )

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.caption(
        "A plataforma possui finalidade informativa, "
        "estatística e organizacional. Não oferece "
        "recomendação de investimento nem garante "
        "resultados. Operações financeiras envolvem "
        "risco de perda."
    )
