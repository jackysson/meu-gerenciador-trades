import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Trader Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

FREE_TRADE_LIMIT = 10

TRADE_COLUMNS = [
    "id", "Data", "Ativo", "Tipo", "Volume",
    "Entrada", "Saída", "SL", "TP", "Lucro", "Obs",
]

CSV_HEADER_ALIAS = {
    "ativo": "Ativo", "asset": "Ativo",
    "tipo": "Tipo", "type": "Tipo",
    "volume": "Volume",
    "entrada": "Entrada", "entry": "Entrada",
    "saída": "Saída", "saida": "Saída", "exit": "Saída",
    "sl": "SL",
    "tp": "TP",
    "lucro": "Lucro", "profit": "Lucro",
    "obs": "Obs", "observation": "Obs",
    "observacao": "Obs", "observação": "Obs",
    "data": "Data",
}


# =========================================================
# LOGIN CHECK & PAGE
# =========================================================

try:
    is_user_logged_in = bool(st.user.is_logged_in)
except Exception:
    is_user_logged_in = False

if not is_user_logged_in:
    st.title("📊 Trader Analytics Pro")
    st.markdown(
        "Organize suas operações, acompanhe seu "
        "desempenho e analise seus resultados."
    )
    st.info("🔐 Clique abaixo para entrar com sua conta Google.")

    try:
        st.login()
    except Exception as erro:
        st.error(f"⚠️ Erro ao iniciar login: {erro}")
        st.info("💡 Verifique a seção [auth] nos Secrets do Streamlit Cloud.")

    st.divider()
    st.caption("Não oferece recomendação de investimento.")
    st.stop()


# =========================================================
# USER DATA (apos login)
# =========================================================

try:
    usuario_email = str(st.user.email or "").strip().lower()
    usuario_nome = str(st.user.name or usuario_email.split("@")[0] or "Trader").strip()
    usuario_id = usuario_email.replace("@", "").replace(".", "")
except Exception as e:
    st.error(f"❌ Conta não identificada: {e}")
    st.stop()

if not usuario_email:
    st.error("❌ E-mail não encontrado na autenticação.")
    st.stop()


# =========================================================
# THEME (unico seletor: aba Config)
# =========================================================

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "🌙 Noite"

PLOTLY_TEMPLATE = "plotly_dark" if st.session_state["theme_mode"] == "🌙 Noite" else "plotly_white"

if st.session_state["theme_mode"] == "☀️ Dia":
    st.markdown("""
        <style>
        #MainMenu, [data-testid="stToolbar"], [data-testid="stFooter"], footer {visibility: hidden !important; display: none !important;}
        .stApp { background-color: #ffffff !important; }
        section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, li, td, th { color: #1a1a2e !important; }
        .stMetric { background-color: #f8f9fa !important; padding: 15px; border-radius: 12px; border: 1px solid #dee2e6; }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background-color: #ffffff !important; color: #1a1a2e !important; border-color: #ced4da !important; }
        .stSelectbox [data-baseweb="select"] { background-color: #ffffff !important; }
        [data-baseweb="popover"], [data-baseweb="menu"] { background-color: #ffffff !important; }
        .stForm { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 12px !important; padding: 15px !important; }
        .insight-card { background-color: #f0f7ff !important; padding: 20px; border-radius: 10px; border-left: 5px solid #0066cc; margin-bottom: 15px; }
        .badge-card { background-color: #f8f9fa !important; padding: 18px; border-radius: 12px; border: 1px solid #dee2e6; min-height: 160px; margin-bottom: 12px; }
        .plan-card { background-color: #f8f9fa !important; padding: 25px; border-radius: 14px; border: 1px solid #dee2e6; margin-bottom: 15px; }
        .connection-ok { background-color: #d4edda; color: #155724; padding: 10px 16px; border-radius: 10px; border: 1px solid #c3e6cb; font-weight: bold; font-size: 14px; margin-bottom: 10px; }
        .connection-off { background-color: #fff3cd; color: #856404; padding: 10px 16px; border-radius: 10px; border: 1px solid #ffeeba; font-weight: bold; font-size: 14px; margin-bottom: 10px; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        #MainMenu, [data-testid="stToolbar"], [data-testid="stFooter"], footer {visibility: hidden !important; display: none !important;}
        .stApp { background-color: #0d1117 !important; color: #e6edf3 !important; }
        section[data-testid="stSidebar"] { background-color: #161b22 !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, li, td, th, div { color: #c9d1d9 !important; }
        .stMetric { background-color: #161b22 !important; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            background-color: #0d1117 !important; color: #e6edf3 !important; border-color: #30363d !important; }
        .stSelectbox [data-baseweb="select"] { background-color: #0d1117 !important; color: #e6edf3 !important; }
        [data-baseweb="popover"], [data-baseweb="menu"] { background-color: #161b22 !important; }
        .stForm { background-color: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px !important; padding: 15px !important; }
        .insight-card { background-color: #1c2128 !important; padding: 20px; border-radius: 10px; border-left: 5px solid #58a6ff; margin-bottom: 15px; }
        .badge-card { background-color: #161b22 !important; padding: 18px; border-radius: 12px; border: 1px solid #30363d; min-height: 160px; margin-bottom: 12px; }
        .plan-card { background-color: #161b22 !important; padding: 25px; border-radius: 14px; border: 1px solid #30363d; margin-bottom: 15px; }
        .connection-ok { background-color: #0d2818 !important; color: #3fb950 !important; padding: 10px 16px; border-radius: 10px; border: 1px solid #238636; font-weight: bold; font-size: 14px; margin-bottom: 10px; }
        .connection-off { background-color: #2d1b00 !important; color: #f0883e !important; padding: 10px 16px; border-radius: 10px; border: 1px solid #9e6a03; font-weight: bold; font-size: 14px; margin-bottom: 10px; }
        </style>
        """, unsafe_allow_html=True)


# =========================================================
# FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
    elif "firebase" in st.secrets:
        info = dict(st.secrets["firebase"])
    else:
        raise KeyError("Faltando [gcp_service_account] (ou [firebase]) nos Secrets.")

    pk = info.get("private_key", "")
    if "\\n" in pk:
        pk = pk.replace("\\n", "\n")
    info["private_key"] = pk.strip() + "\n"

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return firestore.Client(
        credentials=creds,
        project=info.get("project_id", ""),
    )


cloud_connected = False
db = None
db_error = ""
try:
    db = get_firestore()
    list(db.collection("users").limit(1).stream())
    cloud_connected = True
except Exception as e:
    cloud_connected = False
    db_error = f"{type(e).__name__}: {e}"

if not cloud_connected and db_error:
    st.error(f"🔧 Debug Firestore: {db_error}")


# =========================================================
# PLAN FUNCTIONS
# =========================================================

def get_owner_emails():
    return [str(e).strip().lower() for e in st.secrets.get("owner_emails", [])]

def is_owner(email):
    return email.strip().lower() in get_owner_emails()

def ensure_user(uid, name, email):
    if db is None:
        return {}
    ref = db.collection("users").document(uid)
    doc = ref.get()
    if not doc.exists:
        ref.set({
            "name": name, "email": email,
            "plan": "free", "access_type": "free",
            "subscription_status": "inactive",
            "subscription_expires_at": None,
            "trade_count": 0,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        return {"trade_count": 0}
    data = doc.to_dict()
    ref.set({"name": name, "email": email,
             "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
    if "trade_count" not in data:
        t = db.collection("users").document(uid).collection("trades")
        total = sum(1 for _ in t.stream())
        ref.set({"trade_count": total}, merge=True)
        data["trade_count"] = total
    return data

def normalize_exp(exp):
    if exp is None:
        return None
    if isinstance(exp, datetime):
        return exp.replace(tzinfo=timezone.utc) if exp.tzinfo is None else exp
    if isinstance(exp, str):
        try:
            p = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            return p.replace(tzinfo=timezone.utc) if p.tzinfo is None else p
        except ValueError:
            return None
    return None

def has_pro_access(uid, email):
    if is_owner(email):
        return True
    if db is None:
        return False
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        return False
    d = doc.to_dict()
    if str(d.get("plan", "")).strip().lower() != "pro":
        return False
    if str(d.get("subscription_status", "")).strip().lower() not in ("active", "trialing"):
        return False
    if str(d.get("access_type", "")).strip().lower() == "lifetime":
        return True
    exp = normalize_exp(d.get("subscription_expires_at"))
    if exp is None:
        return False
    return exp > datetime.now(timezone.utc)

def get_plan_info(uid, email):
    owner = is_owner(email)
    if db is None:
        return {"is_owner": owner, "is_pro": owner,
                "plan": "pro" if owner else "free",
                "subscription_expires_at": None,
                "trade_count": 0}
    doc = db.collection("users").document(uid).get()
    d = doc.to_dict() if doc.exists else {}
    return {
        "is_owner": owner,
        "is_pro": has_pro_access(uid, email),
        "plan": d.get("plan", "free"),
        "access_type": d.get("access_type", "free"),
        "subscription_status": d.get("subscription_status", "inactive"),
        "subscription_expires_at": normalize_exp(d.get("subscription_expires_at")),
        "trade_count": int(d.get("trade_count", 0)),
    }


# =========================================================
# TRADE FUNCTIONS
# =========================================================

def load_trades(uid):
    if db is None:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    ref = db.collection("users").document(uid).collection("trades").order_by("created_at")
    recs = []
    for doc in ref.stream():
        d = doc.to_dict()
        ca = d.get("created_at")
        fd = ca.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ca, datetime) else str(ca) if ca else ""
        recs.append({
            "id": doc.id, "Data": fd,
            "Ativo": d.get("asset", ""), "Tipo": d.get("type", ""),
            "Volume": d.get("volume", 0), "Entrada": d.get("entry", 0),
            "Saída": d.get("exit", 0), "SL": d.get("sl", 0),
            "TP": d.get("tp", 0), "Lucro": d.get("profit", 0),
            "Obs": d.get("observation", ""),
        })
    return pd.DataFrame(recs, columns=TRADE_COLUMNS)

def save_trade(uid, email, td):
    if not uid:
        raise ValueError("Usuário não autenticado.")
    if db is None:
        raise RuntimeError("Banco indisponível.")
    ref = db.collection("users").document(uid)
    
