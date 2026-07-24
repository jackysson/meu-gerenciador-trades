Aqui está a versão final completa com todas as correções:

---

## 1. `requirements.txt`

```text
streamlit>=1.42
pandas
plotly
numpy
google-cloud-firestore
google-auth
```

---

## 2. `app_web.py`

```python
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
# LOGIN COMPATÍVEL
# =========================================================

def check_user_login():
    try:
        _ = st.user["sub"]
        return True
    except (AttributeError, KeyError):
        return False

is_user_logged_in = check_user_login()


# =========================================================
# TEMA DIA / NOITE
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
# TELA DE LOGIN
# =========================================================

if not is_user_logged_in:
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

    has_auth = all(
        key in st.secrets
        for key in ["auth", "gcp_service_account"]
    )

    if not has_auth:
        st.error(
            "⚠️ O login ainda não foi configurado. "
            "O administrador precisa configurar a seção "
            "[auth] e [gcp_service_account] nos Secrets "
            "do Streamlit."
        )

        st.markdown(
            """
            ### Como configurar

            1. Crie uma **Credencial OAuth** no Google Cloud;
            2. Adicione o **Client ID** e **Client Secret** nos Secrets;
            3. Configure o **redirect_uri** correto;
            4. Reinicie o aplicativo.
            """
        )

    else:
        try:
            st.login()
        except Exception as erro:
            st.error(
                f"Erro ao iniciar o login: {erro}"
            )

    st.divider()

    st.caption(
        "A plataforma possui finalidade informativa, "
        "estatística e organizacional. Não oferece "
        "recomendação de investimento nem garante "
        "resultados."
    )

    st.stop()


# =========================================================
# DADOS DO USUÁRIO
# =========================================================

try:
    usuario_id = str(st.user["sub"])
    usuario_email = str(
        st.user.get("email", "")
    ).strip().lower()
    usuario_nome = str(
        st.user.get("name", "Usuário")
    ).strip()
except Exception:
    st.error("Não foi possível identificar sua conta.")
    st.stop()

if not usuario_email:
    st.error("E-mail não encontrado na conta.")
    st.stop()


# =========================================================
# FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "Seção [gcp_service_account] não encontrada."
        )

    info = dict(st.secrets["gcp_service_account"])

    if "private_key" not in info:
        raise RuntimeError(
            "Chave private_key não encontrada."
        )

    info["private_key"] = info["private_key"].replace(
        "\\n", "\n"
    )

    project_id = info.get("project_id", "")

    credenciais = (
        service_account
        .Credentials
        .from_service_account_info(
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
# FUNÇÕES DOS PLANOS
# =========================================================

def get_owner_emails():
    emails = st.secrets.get("owner_emails", [])
    return [
        str(e).strip().lower() for e in emails
    ]


def is_owner(email):
    return email.strip().lower() in get_owner_emails()


def ensure_user(user_id, name, email):
    if db is None:
        return {}

    ref = db.collection("users").document(user_id)
    doc = ref.get()

    if not doc.exists:
        ref.set(
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
        return {"trade_count": 0}

    data = doc.to_dict()

    ref.set(
        {
            "name": name,
            "email": email,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    if "trade_count" not in data:
        trades = (
            db.collection("users")
            .document(user_id)
            .collection("trades")
        )
        total = sum(1 for _ in trades.stream())
        ref.set({"trade_count": total}, merge=True)
        data["trade_count"] = total

    return data


def normalize_expiration(exp):
    if exp is None:
        return None
    if isinstance(exp, datetime):
        if exp.tzinfo is None:
            return exp.replace(tzinfo=timezone.utc)
        return exp
    if isinstance(exp, str):
        try:
            n = exp.replace("Z", "+00:00")
            p = datetime.fromisoformat(n)
            if p.tzinfo is None:
                p = p.replace(tzinfo=timezone.utc)
            return p
        except ValueError:
            return None
    return None


def has_pro_access(user_id, email):
    if is_owner(email):
        return True
    if db is None:
        return False

    doc = (
        db.collection("users")
        .document(user_id)
        .get()
    )

    if not doc.exists:
        return False

    data = doc.to_dict()

    if data.get("plan") != "pro":
        return False

    if data.get("subscription_status") not in {
        "active", "trialing",
    }:
        return False

    if data.get("access_type") == "lifetime":
        return True

    exp = normalize_expiration(
        data.get("subscription_expires_at")
    )

    if exp is None:
        return False

    return exp > datetime.now(timezone.utc)


def get_plan_info(user_id, email):
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

    doc = (
        db.collection("users")
        .document(user_id)
        .get()
    )

    data = doc.to_dict() if doc.exists else {}
    pro = has_pro_access(user_id, email)

    return {
        "is_owner": owner,
        "is_pro": pro,
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

    ref = (
        db.collection("users")
        .document(user_id)
        .collection("trades")
        .order_by("created_at")
    )

    records = []

    for doc in ref.stream():
        d = doc.to_dict()
        ca = d.get("created_at")

        if isinstance(ca, datetime):
            fd = ca.strftime("%Y-%m-%d %H:%M:%S")
        else:
            fd = str(ca) if ca else ""

        records.append({
            "id": doc.id,
            "Data": fd,
            "Ativo": d.get("asset", ""),
            "Tipo": d.get("type", ""),
            "Volume": d.get("volume", 0),
            "Entrada": d.get("entry", 0),
            "Saída": d.get("exit", 0),
            "SL": d.get("sl", 0),
            "TP": d.get("tp", 0),
            "Lucro": d.get("profit", 0),
            "Obs": d.get("observation", ""),
        })

    return pd.DataFrame(records, columns=TRADE_COLUMNS)


def save_trade(user_id, email, td):
    if not user_id:
        raise ValueError("Usuário não autenticado.")
    if db is None:
        raise RuntimeError("Banco indisponível.")

    ref = db.collection("users").document(user_id)
    snap = ref.get()

    if not snap.exists:
        raise ValueError("Usuário não encontrado.")

    data = snap.to_dict()
    count = int(data.get("trade_count", 0))

    if not has_pro_access(user_id, email):
        if count >= FREE_TRADE_LIMIT:
            raise PermissionError(
                "Limite de 10 trades atingido."
            )

    trade_ref = ref.collection("trades").document()

    record = {
        "asset": td["asset"],
        "type": td["type"],
        "volume": float(td["volume"]),
        "entry": float(td["entry"]),
        "exit": float(td["exit"]),
        "sl": float(td["sl"]),
        "tp": float(td["tp"]),
        "profit": float(td["profit"]),
        "observation": td.get("observation", ""),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    trade_ref.set(record)

    ref.set(
        {
            "trade_count": count + 1,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    return trade_ref.id


def edit_trade(user_id, trade_id, td):
    if not user_id or not trade_id:
        raise ValueError("Usuário ou trade inválido.")
    if db is None:
        raise RuntimeError("Banco indisponível.")

    ref = (
        db.collection("users")
        .document(user_id)
        .collection("trades")
        .document(trade_id)
    )

    record = {
        "asset": td["asset"],
        "type": td["type"],
        "volume": float(td["volume"]),
        "entry": float(td["entry"]),
        "exit": float(td["exit"]),
        "sl": float(td["sl"]),
        "tp": float(td["tp"]),
        "profit": float(td["profit"]),
        "observation": td.get("observation", ""),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    ref.set(record, merge=True)


def delete_trade(user_id, trade_id):
    if not user_id or not trade_id:
        raise ValueError("Usuário ou trade inválido.")
    if db is None:
        raise RuntimeError("Banco indisponível.")

    user_ref = (
        db.collection("users").document(user_id)
    )
    trade_ref = (
        user_ref.collection("trades")
        .document(trade_id)
    )

    snap = user_ref.get()
    if not snap.exists:
        return

    data = snap.to_dict()
    count = int(data.get("trade_count", 0))

    trade_ref.delete()

    user_ref.set(
        {
            "trade_count": max(0, count - 1),
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

    doc = (
        db.collection("users")
        .document(user_id)
        .collection("settings")
        .document("profile")
        .get()
    )

    if not doc.exists:
        return 20.0

    return float(doc.to_dict().get("initial_capital", 20.0))


def save_initial_capital(user_id, capital):
    if db is None:
        raise RuntimeError("Banco indisponível.")

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
# INSÍGNIAS
# =========================================================

def calculate_badges(df):
    badges = []
    if df.empty:
        return badges

    total = len(df)
    wins = len(df[df["Lucro"] > 0])
    profit = df["Lucro"].sum()
    wr = wins / total * 100 if total > 0 else 0

    if total >= 10:
        badges.append({
            "icon": "📝",
            "name": "Diário Iniciado",
            "description": "10+ operações registradas.",
        })

    if total >= 50:
        badges.append({
            "icon": "🏅",
            "name": "Trader Consistente",
            "description": "50+ operações registradas.",
        })

    if total >= 100:
        badges.append({
            "icon": "🔥",
            "name": "Centúria",
            "description": "100+ operações registradas.",
        })

    if total >= 20 and wr >= 60:
        badges.append({
            "icon": "🎯",
            "name": "Alta Precisão",
            "description": "Win rate 60%+ em 20 operações.",
        })

    if total >= 20 and wr >= 70:
        badges.append({
            "icon": "👑",
            "name": "Mestre da Precisão",
            "description": "Win rate 70%+ em 20 operações.",
        })

    if total >= 20 and profit > 0:
        badges.append({
            "icon": "📈",
            "name": "Histórico Positivo",
            "description": "Lucro acumulado positivo.",
        })

    if total >= 50 and profit > 0:
        badges.append({
            "icon": "💎",
            "name": "Resultados Sólidos",
            "description": "Lucro positivo com 50+ trades.",
        })

    return badges


# =========================================================
# INICIALIZAR SESSÃO
# =========================================================

if cloud_connected and db is not None:
    try:
        ensure_user(usuario_id, usuario_nome, usuario_email)
    except Exception:
        st.warning("Não foi possível criar seu perfil.")
else:
    st.warning("Modo offline: dados não serão salvos na nuvem.")

if st.session_state.get("active_user_id") != usuario_id:
    st.session_state["active_user_id"] = usuario_id
    for key in [
        "df_trades", "initial_capital",
        "last_asset", "editing_trade_id",
        "confirm_delete_id",
    ]:
        st.session_state.pop(key, None)

if "df_trades" not in st.session_state:
    try:
        st.session_state["df_trades"] = load_trades(usuario_id)
    except Exception:
        st.session_state["df_trades"] = pd.DataFrame(columns=TRADE_COLUMNS)
        st.error("Erro ao carregar trades.")

if "initial_capital" not in st.session_state:
    try:
        st.session_state["initial_capital"] = load_initial_capital(usuario_id)
    except Exception:
        st.session_state["initial_capital"] = 20.0

if "last_asset" not in st.session_state:
    st.session_state["last_asset"] = "USDJPY"

try:
    plan_info = get_plan_info(usuario_id, usuario_email)
except Exception:
    st.error("Erro ao verificar plano.")
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
    theme = st.radio(
        "🎨 Aparência",
        ["🌙 Noite", "☀️ Dia"],
        horizontal=True,
        key="theme_sel",
    )

    if theme != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = theme
        st.rerun()

    st.divider()

    # CONEXÃO
    st.subheader("☁️ Conexão")

    if cloud_connected:
        st.markdown(
            '<div class="connection-ok">✅ Nuvem Conectada</div>',
            unsafe_allow_html=True,
        )
        st.caption("Firestore ativo.")
    else:
        st.markdown(
            '<div class="connection-off">⚠️ Modo Offline</div>',
            unsafe_allow_html=True,
        )
        st.caption("Dados não salvos na nuvem.")

    st.divider()

    # CONTA
    st.subheader("👤 Minha conta")
    st.write(usuario_nome)
    st.caption(usuario_email)

    if owner:
        st.success("🛡️ Desenvolvedor — Pro permanente")
    elif is_pro:
        st.success("⭐ Plano Pro — R$ 29,90/mês")
        exp = plan_info.get("subscription_expires_at")
        if exp:
            st.caption(f"Acesso até {exp.strftime('%d/%m/%Y')}.")
    else:
        st.info("🆓 Plano Gratuito")
        st.caption("Limite de 10 trades.")

    st.divider()

    # CONTADOR
    cur = len(st.session_state["df_trades"])

    if not is_pro:
        rem = max(0, FREE_TRADE_LIMIT - cur)
        st.progress(
            min(cur / FREE_TRADE_LIMIT, 1.0),
            text=f"{cur}/{FREE_TRADE_LIMIT} trades",
        )
        st.caption(f"Restam {rem} trade(s).")
        if cur >= FREE_TRADE_LIMIT:
            st.warning("Limite atingido.")
    else:
        st.caption(f"{cur} trade(s) registrados.")

    st.divider()

    # CAPITAL
    st.subheader("💰 Configuração")

    with st.form("capital_form"):
        cap_val = st.number_input(
            "Capital Inicial (USD)",
            min_value=0.0,
            value=float(st.session_state["initial_capital"]),
            step=1.0,
            format="%.2f",
        )

        if st.form_submit_button("💾 Salvar capital", use_container_width=True):
            try:
                save_initial_capital(usuario_id, cap_val)
                st.session_state["initial_capital"] = cap_val
                st.success("Capital atualizado!")
            except Exception:
                st.error("Erro ao salvar.")

    st.divider()

    # EXPORTAÇÃO
    st.subheader("💾 Exportação")

    exp_df = st.session_state.get("df_trades", pd.DataFrame(columns=TRADE_COLUMNS))
    exp_cols = [c for c in TRADE_COLUMNS if c != "id"]
    csv = exp_df[exp_cols].to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar dados",
        data=csv,
        file_name="meus_trades.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.button("🔄 Sincronizar", use_container_width=True):
        try:
            st.session_state["df_trades"] = load_trades(usuario_id)
            st.rerun()
        except Exception:
            st.error("Erro ao sincronizar.")

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

    # COMPARTILHAR
    st.subheader("🔗 Compartilhar")

    app_url = "https://SEU-APP.streamlit.app"
    share = "Estou usando o Trader Analytics Pro!"

    st.markdown(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <a href="https://wa.me/?text={share}%0A%0A{app_url}"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background-color:#25D366;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 WhatsApp
            </a>
            <a href="https://www.instagram.com/direct/new/?text={share}%20{app_url}"
               target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 Instagram
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
        st.logout()


# =========================================================
# DADOS E MÉTRICAS
# =========================================================

df = st.session_state["df_trades"].copy()

for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

loss_df = df[df["Lucro"] < 0]
win_df = df[df["Lucro"] > 0]
loss_count = len(loss_df)
win_count = len(win_df)

avg_loss_cash = abs(loss_df["Lucro"].mean()) if loss_count > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if loss_count > 0 else 0

total_profit = df["Lucro"].sum()
ic = st.session_state["initial_capital"]
equity = ic + total_profit
win_rate = win_count / len(df) * 100 if len(df) > 0 else 0
gp = win_df["Lucro"].sum()
gl = abs(loss_df["Lucro"].sum())
pf = gp / gl if gl > 0 else 0


# =========================================================
# DASHBOARD
# =========================================================

st.title("📊 Trader Strategy Analytics Pro")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("✅ Vitórias", win_count)
c3.metric("❌ Derrotas", loss_count)
c4.metric("🎯 Win Rate", f"{win_rate:.1f}%")
c5.metric("📈 Profit Factor", f"{pf:.2f}")

st.divider()


# =========================================================
# ABAS
# =========================================================

tab_g, tab_i, tab_h, tab_n, tab_p = st.tabs([
    "🚀 Gráficos",
    "📚 Insights & Insígnias",
    "📝 Histórico",
    "➕ Novo Trade",
    "⭐ Planos",
])


# =========================================================
# GRÁFICOS
# =========================================================

with tab_g:
    if df.empty:
        st.info("Adicione trades para ver os gráficos.")
    else:
        a, b = st.columns(2)

        with a:
            eq = ic + df["Lucro"].cumsum()
            fig1 = px.area(
                x=list(range(1, len(eq) + 1)),
                y=eq,
                title="Crescimento da Conta",
                labels={"x": "Trade", "y": "Equity"},
                template="plotly_dark",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with b:
            rdf = df.copy()
            rdf["Risco"] = abs(rdf["Entrada"] - rdf["SL"])
            fig2 = px.bar(
                rdf,
                x="Ativo",
                y="Risco",
                title="Risco por Trade",
                color_discrete_sequence=["#f85149"],
                template="plotly_dark",
            )
            st.plotly_chart(fig2, use_container_width=True)

        if is_pro:
            c, d = st.columns(2)

            with c:
                fig3 = px.pie(
                    names=["Vitórias", "Derrotas"],
                    values=[win_count, loss_count],
                    title="Distribuição",
                    template="plotly_dark",
                    color_discrete_sequence=["#3fb950", "#f85149"],
                )
                st.plotly_chart(fig3, use_container_width=True)

            with d:
                ap = df.groupby("Ativo")["Lucro"].sum().reset_index()
                fig4 = px.bar(
                    ap,
                    x="Ativo",
                    y="Lucro",
                    title="Lucro por Ativo",
                    color_discrete_sequence=["#58a6ff"],
                    template="plotly_dark",
                )
                st.plotly_chart(fig4, use_container_width=True)


# =========================================================
# INSIGHTS
# =========================================================

with tab_i:
    if not is_pro:
        st.subheader("🔒 Recurso exclusivo do Pro")
        st.info(
            "Assine o Plano Pro por R$ 29,90/mês "
            "para acessar resumos, insights e insígnias."
        )
        st.markdown("""
        ### Recursos exclusivos do Pro

        - Trades ilimitados
        - Resumos estatísticos
        - Insights de desempenho
        - Análise de perdas
        - Simulações
        - Insígnias
        - Gráficos extras
        """)
    else:
        st.header("📚 Resumo Estatístico")

        if df.empty:
            st.info("Adicione trades para gerar análises.")
        else:
            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>📉 Análise de Perdas</h4>
                    <p>Perda média: <b>$ {avg_loss_cash:.2f}</b></p>
                    <p>Perda em pontos: <b>{avg_loss_pts:.3f} pts</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            at = total_profit / len(df) if len(df) > 0 else 0
            s30 = equity + at * 30

            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>🧮 Simulação Estatística</h4>
                    <p>Projeção 30 trades: <b>$ {s30:,.2f}</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "Simulação baseada em dados históricos. "
                "Não garante rentabilidade futura."
            )

            st.divider()
            st.subheader("🏆 Insígnias")

            badges = calculate_badges(df)

            if not badges:
                st.info("Continue registrando para desbloquear insígnias.")
            else:
                cols = st.columns(min(len(badges), 3))
                for idx, badge in enumerate(badges):
                    with cols[idx % len(cols)]:
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
# HISTÓRICO
# =========================================================

with tab_h:
    if df.empty:
        st.info("Nenhum trade registrado.")
    else:
        if "confirm_delete_id" in st.session_state:
            did = st.session_state["confirm_delete_id"]
            st.warning(f"⚠️ Excluir trade {did[:8]}?")

            cc, cx = st.columns(2)
            with cc:
                if st.button("✅ Sim, excluir", type="primary", use_container_width=True):
                    try:
                        delete_trade(usuario_id, did)
                        st.session_state.pop("confirm_delete_id", None)
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.success("Excluído!")
                        st.rerun()
                    except Exception:
                        st.error("Erro ao excluir.")
            with cx:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.pop("confirm_delete_id", None)
                    st.rerun()
            st.divider()

        eid = st.session_state.get("editing_trade_id")

        if eid:
            tr = df[df["id"] == eid]
            if not tr.empty:
                r = tr.iloc[0]
                st.subheader("✏️ Editar Trade")

                with st.form("edit_form"):
                    e1, e2, e3, e4 = st.columns(4)
                    ed_a = e1.text_input("Ativo", value=r["Ativo"])
                    ed_t = e2.selectbox("Tipo", ["buy", "sell"], index=0 if r["Tipo"] == "buy" else 1)
                    ed_v = e3.number_input("Volume", min_value=0.01, value=float(r["Volume"]), step=0.01, format="%.2f")
                    ed_p = e4.number_input("Lucro", value=float(r["Lucro"]), format="%.2f")
                    st.divider()
                    e5, e6, e7, e8 = st.columns(4)
                    ed_en = e5.number_input("Entrada", value=float(r["Entrada"]), format="%.3f")
                    ed_ex = e6.number_input("Saída", value=float(r["Saída"]), format="%.3f")
                    ed_sl = e7.number_input("SL", value=float(r["SL"]), format="%.3f")
                    ed_tp = e8.number_input("TP", value=float(r["TP"]), format="%.3f")
                    ed_ob = st.text_area("Obs", value=r["Obs"], max_chars=500)

                    s1, s2 = st.columns(2)
                    with s1:
                        if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                            try:
                                td = {
                                    "asset": ed_a.strip().upper(), "type": ed_t,
                                    "volume": ed_v, "entry": ed_en, "exit": ed_ex,
                                    "sl": ed_sl, "tp": ed_tp, "profit": ed_p,
                                    "observation": ed_ob.strip(),
                                }
                                edit_trade(usuario_id, eid, td)
                                st.session_state.pop("editing_trade_id", None)
                                st.session_state["df_trades"] = load_trades(usuario_id)
                                st.success("Atualizado!")
                                st.rerun()
                            except Exception:
                                st.error("Erro ao salvar.")
                    with s2:
                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                            st.session_state.pop("editing_trade_id", None)
                            st.rerun()
            st.divider()

        dcols = [c for c in TRADE_COLUMNS if c != "id"]
        st.dataframe(df[dcols].sort_index(ascending=False), use_container_width=True, hide_index=True)
        st.divider()

        st.subheader("Ações por trade")
        tids = df["id"].tolist()
        sel = st.selectbox("Selecione o ID", options=tids, format_func=lambda x: f"{x[:8]}..." if len(x) > 8 else x)

        if sel:
            ce, cd = st.columns(2)
            with ce:
                if st.button("✏️ Editar", use_container_width=True):
                    st.session_state["editing_trade_id"] = sel
                    st.rerun()
            with cd:
                if st.button("🗑️ Excluir", use_container_width=True):
                    st.session_state["confirm_delete_id"] = sel
                    st.rerun()


# =========================================================
# NOVO TRADE
# =========================================================

with tab_n:
    cc = len(df)
    fl = not is_pro and cc >= FREE_TRADE_LIMIT

    if fl:
        st.warning("Limite de 10 trades atingido.")
        st.info("Pro: trades ilimitados por R$ 29,90/mês.")
    else:
        with st.form("add_trade", clear_on_submit=True):
            st.subheader("Registrar Operação")
            r1, r2, r3, r4 = st.columns(4)
            at = r1.text_input("Ativo", value=st.session_state.get("last_asset", "USDJPY"))
            tt = r2.selectbox("Tipo", ["buy", "sell"])
            vl = r3.number_input("Volume", min_value=0.01, value=0.01, step=0.01, format="%.2f")
            pr = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
            st.divider()
            r5, r6, r7, r8 = st.columns(4)
            en = r5.number_input("Entrada", value=0.0, format="%.3f")
            ex = r6.number_input("Saída", value=0.0, format="%.3f")
            sl = r7.number_input("SL", value=0.0, format="%.3f")
            tp = r8.number_input("TP", value=0.0, format="%.3f")
            ob = st.text_area("Observação", max_chars=500)

            if st.form_submit_button("💾 SALVAR TRADE", type="primary", use_container_width=True):
                errs = []
                if not at.strip():
                    errs.append("Informe o ativo.")
                if vl <= 0:
                    errs.append("Volume deve ser maior que zero.")

                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    td = {
                        "asset": at.strip().upper(), "type": tt,
                        "volume": vl, "entry": en, "exit": ex,
                        "sl": sl, "tp": tp, "profit": pr,
                        "observation": ob.strip(),
                    }
                    try:
                        save_trade(usuario_id, usuario_email, td)
                        st.session_state["last_asset"] = at.strip().upper()
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.session_state["flash_message"] = "✅ Trade salvo!"
                        st.rerun()
                    except PermissionError as e:
                        st.warning(str(e))
                    except Exception:
                        st.error("Erro ao salvar.")


# =========================================================
# PLANOS
# =========================================================

with tab_p:
    st.title("⭐ Planos")

    fc, pc = st.columns(2)

    with fc:
        st.markdown(
            """
            <div class="plan-card">
                <h2>🆓 Gratuito</h2>
                <h3>R$ 0</h3><br>
                <p>✅ Até 10 trades</p>
                <p>✅ Métricas básicas</p>
                <p>✅ Gráficos básicos</p>
                <p>✅ Histórico</p>
                <p>✅ Exportação CSV</p><br>
                <p>❌ Insights</p>
                <p>❌ Insígnias</p>
                <p>❌ Gráficos extras</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not is_pro:
            st.info("Seu plano: Gratuito")
        else:
            st.caption("Você já é Pro.")

    with pc:
        st.markdown(
            """
            <div class="plan-card">
                <h2>⭐ Pro</h2>
                <h3>R$ 29,90/mês</h3><br>
                <p>✅ Trades ilimitados</p>
                <p>✅ Resumos estatísticos</p>
                <p>✅ Insights</p>
                <p>✅ Análise de perdas</p>
                <p>✅ Simulações</p>
                <p>✅ Insígnias</p>
                <p>✅ Gráficos extras</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if owner:
            st.success("🛡️ Pro permanente (dev).")
        elif is_pro:
            st.success("⭐ Pro ativo.")
        else:
            st.button(
                "⭐ Assinar — R$ 29,90/mês",
                type="primary",
                use_container_width=True,
                disabled=True,
                help="Pagamento em configuração.",
            )
            st.caption("Em breve.")

    st.divider()

    comp = pd.DataFrame({
        "Recurso": [
            "Trades", "Métricas", "Gráficos",
            "Histórico", "CSV", "Insights",
            "Insígnias", "Extras", "Simulações",
        ],
        "Gratuito": [
            "10", "✅", "✅", "✅", "✅",
            "❌", "❌", "❌", "❌",
        ],
        "Pro (R$29,90)": [
            "Ilimitado", "✅", "✅", "✅", "✅",
            "✅", "✅", "✅", "✅",
        ],
    })

    st.dataframe(comp, use_container_width=True, hide_index=True)
    st.divider()
    st.caption("Finalidade informativa e organizacional. Não garante resultados. Risco de perda.")
```

---

## 3. Template dos Secrets

```toml
owner_emails = ["seu-email@gmail.com"]

[auth]
client_id = "CLIENT_ID_DO_GOOGLE_OAUTH.apps.googleusercontent.com"
client_secret = "GOCSPX-CLIENT_SECRET_AQUI"
redirect_uri = "https://SEU-APP.streamlit.app/oauth2callback"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[gcp_service_account]
type = "service_account"
project_id = "projeto-trade-75a34"
private_key_id = "ID_DA_NOVA_CHAVE"
private_key = """-----BEGIN PRIVATE KEY-----
CONTEUDO_DA_NOVA_CHAVE
-----END PRIVATE KEY-----
"""
client_email = "CONTA@projeto-trade-75a34.iam.gserviceaccount.com"
client_id = "ID_DA_CONTA_SERVICO"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "URL_DO_CERTIFICADO"
universe_domain = "googleapis.com"
```

---

## O que precisa ser substituído

```text
SEU-APP       → nome do seu app no Streamlit
SEUNUMERO     → número com DDD e código do país
SEUPERFIL     → usuário Instagram sem @
```

## Correções aplicadas nesta versão

```text
✅ st.user.is_logged_in → check_user_login()
✅ firebase_admin → google-cloud-firestore
✅ Login com verificação de Secrets [auth]
✅ Mensagem amiga se auth não configurada
✅ Tema dia / noite
✅ Indicador de conexão com a nuvem
✅ Planos gratuitos, Pro e owner
✅ Controle de 10 trades no gratuito
✅ Edição e exclusão de trades
✅ Insígnias apenas no Pro
✅ Gráficos extras apenas no Pro
✅ Exportação CSV
✅ Capital inicial permanente
✅ Redes sociais e compartilhamento
✅ Proteção contra troca de sessão
✅ Tratamento de erros em cada operação
```

Faça commit, reinicie o app pelo **Manage app → Reboot app** e teste.
