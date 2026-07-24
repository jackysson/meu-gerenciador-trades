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


# =========================================================
# LOGIN CHECK
# =========================================================

def check_user_login():
    try:
        _ = st.user["sub"]
        return True
    except (AttributeError, KeyError):
        return False

is_user_logged_in = check_user_login()


# =========================================================
# THEME
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
            [data-testid="stMetricLabel"],
            [data-testid="stMetricDelta"] {
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
            h1, h2, h3, h4, h5, h6,
            p, span, label, li, td, th {
                color: #1a1a2e !important;
            }
            .stAlert > div { color: #1a1a2e !important; }
            .stTabs [data-baseweb="tab"] { color: #333333 !important; }
            .stTabs [aria-selected="true"] { color: #0066cc !important; }
            .stTextInput label, .stNumberInput label,
            .stSelectbox label, .stTextArea label,
            .stRadio label, .stForm label,
            .stDownloadButton label { color: #333333 !important; }
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
            section[data-testid="stSidebar"] {
                background-color: #161b22 !important;
                color: #e6edf3 !important;
            }
            section[data-testid="stSidebar"] * {
                color: #e6edf3 !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 26px !important;
                color: #58a6ff !important;
            }
            [data-testid="stMetricLabel"],
            [data-testid="stMetricDelta"] {
                color: #8b949e !important;
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
                background-color: #0d2818 !important;
                color: #3fb950 !important;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #238636;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            .connection-off {
                background-color: #2d1b00 !important;
                color: #f0883e !important;
                padding: 10px 16px;
                border-radius: 10px;
                border: 1px solid #9e6a03;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            h1, h2, h3, h4, h5, h6 { color: #e6edf3 !important; }
            p, span, li, td, th, div { color: #c9d1d9 !important; }
            label, .stMarkdown p { color: #c9d1d9 !important; }
            .stAlert > div { color: #c9d1d9 !important; }
            .stWarning > div { color: #e3b341 !important; }
            .stInfo > div { color: #58a6ff !important; }
            .stSuccess > div { color: #3fb950 !important; }
            .stError > div { color: #f85149 !important; }
            .stTextInput label, .stNumberInput label,
            .stSelectbox label, .stTextArea label,
            .stRadio label, .stForm label,
            .stDownloadButton label { color: #e6edf3 !important; }
            .stTextInput input, .stNumberInput input,
            .stTextArea textarea {
                color: #e6edf3 !important;
                background-color: #0d1117 !important;
                border-color: #30363d !important;
            }
            .stSelectbox [data-baseweb="select"] {
                color: #e6edf3 !important;
                background-color: #0d1117 !important;
            }
            .stTabs [data-baseweb="tab"] { color: #8b949e !important; }
            .stTabs [aria-selected="true"] { color: #e6edf3 !important; }
            .stCaption { color: #8b949e !important; }
            .stDataFrame { color: #e6edf3 !important; }
            .stProgress > div > div { background-color: #58a6ff !important; }
            .stProgress label { color: #c9d1d9 !important; }
            .stForm {
                background-color: #161b22 !important;
                border: 1px solid #30363d !important;
                border-radius: 12px !important;
                padding: 15px !important;
            }
            .streamlit-expanderHeader { color: #e6edf3 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )


apply_theme(st.session_state["theme_mode"])


# =========================================================
# LOGIN PAGE
# =========================================================

if not is_user_logged_in:
    st.title("📊 Trader Analytics Pro")

    st.markdown(
        "Organize suas operações, acompanhe seu "
        "desempenho e analise seus resultados."
    )

    st.info("Entre com sua conta Google.")

    has_auth = all(
        key in st.secrets
        for key in ["auth", "gcp_service_account"]
    )

    if not has_auth:
        st.error(
            "Login não configurado. "
            "Configure [auth] nos Secrets."
        )
    else:
        try:
            st.login()
        except Exception as erro:
            st.error(f"Erro login: {erro}")

    st.divider()
    st.caption("Não oferece recomendação de investimento.")
    st.stop()


# =========================================================
# USER DATA
# =========================================================

try:
    usuario_id = str(st.user["sub"])
    usuario_email = str(
        st.user.get("email", "")
    ).strip().lower()
    usuario_nome = str(
        st.user.get("name", "User")
    ).strip()
except Exception:
    st.error("Conta não identificada.")
    st.stop()

if not usuario_email:
    st.error("E-mail não encontrado.")
    st.stop()


# =========================================================
# FIRESTORE
# =========================================================

@st.cache_resource
def get_firestore():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace(
        "\\n", "\n"
    )
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
try:
    db = get_firestore()
    cloud_connected = True
except Exception:
    cloud_connected = False


# =========================================================
# PLAN FUNCTIONS
# =========================================================

def get_owner_emails():
    return [
        str(e).strip().lower()
        for e in st.secrets.get("owner_emails", [])
    ]

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
    if d.get("plan") != "pro":
        return False
    if d.get("subscription_status") not in ("active", "trialing"):
        return False
    if d.get("access_type") == "lifetime":
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
    snap = ref.get()
    if not snap.exists:
        raise ValueError("Usuário não encontrado.")
    count = int(snap.to_dict().get("trade_count", 0))
    if not has_pro_access(uid, email) and count >= FREE_TRADE_LIMIT:
        raise PermissionError("Limite de 10 trades atingido.")
    tref = ref.collection("trades").document()
    tref.set({
        "asset": td["asset"], "type": td["type"],
        "volume": float(td["volume"]), "entry": float(td["entry"]),
        "exit": float(td["exit"]), "sl": float(td["sl"]),
        "tp": float(td["tp"]), "profit": float(td["profit"]),
        "observation": td.get("observation", ""),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    ref.set({"trade_count": count + 1,
             "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
    return tref.id

def edit_trade(uid, tid, td):
    if not uid or not tid:
        raise ValueError("Inválido.")
    if db is None:
        raise RuntimeError("Banco indisponível.")
    db.collection("users").document(uid).collection("trades").document(tid).set({
        "asset": td["asset"], "type": td["type"],
        "volume": float(td["volume"]), "entry": float(td["entry"]),
        "exit": float(td["exit"]), "sl": float(td["sl"]),
        "tp": float(td["tp"]), "profit": float(td["profit"]),
        "observation": td.get("observation", ""),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)

def delete_trade(uid, tid):
    if not uid or not tid:
        raise ValueError("Inválido.")
    if db is None:
        raise RuntimeError("Banco indisponível.")
    uref = db.collection("users").document(uid)
    snap = uref.get()
    if not snap.exists:
        return
    count = int(snap.to_dict().get("trade_count", 0))
    uref.collection("trades").document(tid).delete()
    uref.set({"trade_count": max(0, count - 1),
              "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)


# =========================================================
# CAPITAL
# =========================================================

def load_capital(uid):
    if db is None:
        return 20.0
    doc = db.collection("users").document(uid).collection("settings").document("profile").get()
    return float(doc.to_dict().get("initial_capital", 20.0)) if doc.exists else 20.0

def save_capital(uid, cap):
    if db is None:
        raise RuntimeError("Banco indisponível.")
    db.collection("users").document(uid).collection("settings").document("profile").set({
        "initial_capital": float(cap),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)


# =========================================================
# BADGES
# =========================================================

def calc_badges(df):
    b = []
    if df.empty:
        return b
    t = len(df)
    w = len(df[df["Lucro"] > 0])
    p = df["Lucro"].sum()
    wr = w / t * 100 if t > 0 else 0
    if t >= 10:
        b.append({"icon": "📝", "name": "Diário Iniciado", "desc": "10+ operações."})
    if t >= 50:
        b.append({"icon": "🏅", "name": "Consistente", "desc": "50+ operações."})
    if t >= 100:
        b.append({"icon": "🔥", "name": "Centúria", "desc": "100+ operações."})
    if t >= 20 and wr >= 60:
        b.append({"icon": "🎯", "name": "Alta Precisão", "desc": "WR 60%+ em 20 ops."})
    if t >= 20 and wr >= 70:
        b.append({"icon": "👑", "name": "Mestre", "desc": "WR 70%+ em 20 ops."})
    if t >= 20 and p > 0:
        b.append({"icon": "📈", "name": "Positivo", "desc": "Lucro acumulado."})
    if t >= 50 and p > 0:
        b.append({"icon": "💎", "name": "Sólido", "desc": "Lucro com 50+ trades."})
    return b


# =========================================================
# SESSION INIT
# =========================================================

if cloud_connected and db is not None:
    try:
        ensure_user(usuario_id, usuario_nome, usuario_email)
    except Exception:
        st.warning("Perfil não criado.")
else:
    st.warning("Offline: dados não salvos na nuvem.")

if st.session_state.get("active_user_id") != usuario_id:
    st.session_state["active_user_id"] = usuario_id
    for k in ["df_trades", "initial_capital", "last_asset",
              "editing_trade_id", "confirm_delete_id"]:
        st.session_state.pop(k, None)

if "df_trades" not in st.session_state:
    try:
        st.session_state["df_trades"] = load_trades(usuario_id)
    except Exception:
        st.session_state["df_trades"] = pd.DataFrame(columns=TRADE_COLUMNS)
        st.error("Erro ao carregar trades.")

if "initial_capital" not in st.session_state:
    try:
        st.session_state["initial_capital"] = load_capital(usuario_id)
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
# SIDEBAR
# =========================================================

with st.sidebar:
    theme = st.radio("Aparencia", ["🌙 Noite", "☀️ Dia"],
                     horizontal=True, key="theme_sel")
    if theme != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = theme
        st.rerun()

    st.divider()
    st.subheader("☁️ Conexao")

    if cloud_connected:
        st.markdown('<div class="connection-ok">✅ Nuvem Conectada</div>',
                     unsafe_allow_html=True)
    else:
        st.markdown('<div class="connection-off">⚠️ Modo Offline</div>',
                     unsafe_allow_html=True)

    st.divider()
    st.subheader("👤 Conta")
    st.write(usuario_nome)
    st.caption(usuario_email)

    if owner:
        st.success("🛡️ Dev — Pro permanente")
    elif is_pro:
        st.success("⭐ Pro — R$ 29,90/mes")
        exp = plan_info.get("subscription_expires_at")
        if exp:
            st.caption(f"Ate {exp.strftime('%d/%m/%Y')}.")
    else:
        st.info("🆓 Gratuito")
        st.caption("Limite de 10 trades.")

    st.divider()
    cur = len(st.session_state["df_trades"])

    if not is_pro:
        rem = max(0, FREE_TRADE_LIMIT - cur)
        st.progress(min(cur / FREE_TRADE_LIMIT, 1.0),
                     text=f"{cur}/{FREE_TRADE_LIMIT} trades")
        st.caption(f"Restam {rem} trade(s).")
        if cur >= FREE_TRADE_LIMIT:
            st.warning("Limite atingido.")
    else:
        st.caption(f"{cur} trade(s) registrados.")

    st.divider()
    st.subheader("💰 Capital")

    with st.form("capital_form"):
        cap = st.number_input("Capital Inicial (USD)", min_value=0.0,
                              value=float(st.session_state["initial_capital"]),
                              step=1.0, format="%.2f")
        if st.form_submit_button("💾 Salvar", use_container_width=True):
            try:
                save_capital(usuario_id, cap)
                st.session_state["initial_capital"] = cap
                st.success("Salvo!")
            except Exception:
                st.error("Erro ao salvar.")

    st.divider()
    st.subheader("💾 Exportar")

    edf = st.session_state.get("df_trades", pd.DataFrame(columns=TRADE_COLUMNS))
    ecols = [c for c in TRADE_COLUMNS if c != "id"]
    csv = edf[ecols].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar CSV", data=csv,
                       file_name="meus_trades.csv",
                       mime="text/csv", use_container_width=True)

    if st.button("🔄 Sincronizar", use_container_width=True):
        try:
            st.session_state["df_trades"] = load_trades(usuario_id)
            st.rerun()
        except Exception:
            st.error("Erro ao sincronizar.")

    st.divider()
    st.subheader("📱 Redes")

    st.markdown(
        """
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <a href="https://wa.me/SEUNUMERO" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background-color:#25D366;color:white;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:13px;">
                WhatsApp</a>
            <a href="https://instagram.com/SEUPERFIL" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:13px;">
                Instagram</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("🔗 Compartilhar")

    app_url = "https://SEU-APP.streamlit.app"
    share = "Estou usando o Trader Analytics Pro!"

    st.markdown(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <a href="https://wa.me/?text={share}%0A%0A{app_url}" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background-color:#25D366;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 WhatsApp</a>
            <a href="https://www.instagram.com/direct/new/?text={share}%20{app_url}" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;padding:10px 14px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:12px;">
                📤 Instagram</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
        st.logout()


# =========================================================
# METRICS
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
# TABS
# =========================================================

tab_g, tab_i, tab_h, tab_n, tab_p = st.tabs([
    "🚀 Graficos", "📚 Insights", "📝 Historico",
    "➕ Novo Trade", "⭐ Planos",
])


# =========================================================
# GRAPHS
# =========================================================

with tab_g:
    if df.empty:
        st.info("Adicione trades para ver graficos.")
    else:
        a, b = st.columns(2)
        with a:
            eq = ic + df["Lucro"].cumsum()
            fig1 = px.area(x=list(range(1, len(eq)+1)), y=eq,
                           title="Crescimento da Conta",
                           labels={"x": "Trade", "y": "Equity"},
                           template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)
        with b:
            rdf = df.copy()
            rdf["Risco"] = abs(rdf["Entrada"] - rdf["SL"])
            fig2 = px.bar(rdf, x="Ativo", y="Risco",
                          title="Risco por Trade",
                          color_discrete_sequence=["#f85149"],
                          template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

        if is_pro:
            c, d = st.columns(2)
            with c:
                fig3 = px.pie(names=["Vitorias", "Derrotas"],
                              values=[win_count, loss_count],
                              title="Distribuicao",
                              template="plotly_dark",
                              color_discrete_sequence=["#3fb950", "#f85149"])
                st.plotly_chart(fig3, use_container_width=True)
            with d:
                ap = df.groupby("Ativo")["Lucro"].sum().reset_index()
                fig4 = px.bar(ap, x="Ativo", y="Lucro",
                              title="Lucro por Ativo",
                              color_discrete_sequence=["#58a6ff"],
                              template="plotly_dark")
                st.plotly_chart(fig4, use_container_width=True)


# =========================================================
# INSIGHTS
# =========================================================

with tab_i:
    if not is_pro:
        st.subheader("🔒 Exclusivo Pro")
        st.info("Assine Pro por R$ 29,90/mes.")
        st.markdown("""
        ### Pro inclui
        - Trades ilimitados
        - Resumos estatisticos
        - Insights
        - Analise de perdas
        - Simulacoes
        - Insignias
        - Graficos extras
        """)
    else:
        st.header("📚 Resumo")
        if df.empty:
            st.info("Adicione trades.")
        else:
            st.markdown(f"""
            <div class="insight-card">
                <h4>📉 Perdas</h4>
                <p>Media: <b>$ {avg_loss_cash:.2f}</b></p>
                <p>Pontos: <b>{avg_loss_pts:.3f}</b></p>
            </div>""", unsafe_allow_html=True)

            at = total_profit / len(df) if len(df) > 0 else 0
            s30 = equity + at * 30
            st.markdown(f"""
            <div class="insight-card">
                <h4>🧮 Simulacao 30 trades</h4>
                <p><b>$ {s30:,.2f}</b></p>
            </div>""", unsafe_allow_html=True)
            st.caption("Simulacao historica. Nao garante resultados.")

            st.divider()
            st.subheader("🏆 Insignias")
            badges = calc_badges(df)
            if not badges:
                st.info("Registre operacoes para desbloquear.")
            else:
                cols = st.columns(min(len(badges), 3))
                for idx, badge in enumerate(badges):
                    with cols[idx % len(cols)]:
                        st.markdown(f"""
                        <div class="badge-card">
                            <h2>{badge["icon"]}</h2>
                            <h4>{badge["name"]}</h4>
                            <p>{badge["desc"]}</p>
                        </div>""", unsafe_allow_html=True)


# =========================================================
# HISTORY
# =========================================================

with tab_h:
    if df.empty:
        st.info("Nenhum trade.")
    else:
        if "confirm_delete_id" in st.session_state:
            did = st.session_state["confirm_delete_id"]
            st.warning(f"Excluir trade {did[:8]}?")
            cc, cx = st.columns(2)
            with cc:
                if st.button("✅ Excluir", type="primary", use_container_width=True):
                    try:
                        delete_trade(usuario_id, did)
                        st.session_state.pop("confirm_delete_id", None)
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.success("Excluido!")
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
                    ea = e1.text_input("Ativo", value=r["Ativo"])
                    et = e2.selectbox("Tipo", ["buy", "sell"],
                                      index=0 if r["Tipo"] == "buy" else 1)
                    ev = e3.number_input("Volume", min_value=0.01,
                                         value=float(r["Volume"]),
                                         step=0.01, format="%.2f")
                    ep = e4.number_input("Lucro",
                                         value=float(r["Lucro"]),
                                         format="%.2f")
                    st.divider()
                    e5, e6, e7, e8 = st.columns(4)
                    een = e5.number_input("Entrada",
                                          value=float(r["Entrada"]),
                                          format="%.3f")
                    eex = e6.number_input("Saida",
                                          value=float(r["Saída"]),
                                          format="%.3f")
                    esl = e7.number_input("SL",
                                          value=float(r["SL"]),
                                          format="%.3f")
                    etp = e8.number_input("TP",
                                          value=float(r["TP"]),
                                          format="%.3f")
                    eob = st.text_area("Obs", value=r["Obs"],
                                       max_chars=500)
                    s1, s2 = st.columns(2)
                    with s1:
                        if st.form_submit_button("💾 Salvar",
                                                  type="primary",
                                                  use_container_width=True):
                            try:
                                td = {"asset": ea.strip().upper(),
                                      "type": et, "volume": ev,
                                      "entry": een, "exit": eex,
                                      "sl": esl, "tp": etp,
                                      "profit": ep,
                                      "observation": eob.strip()}
                                edit_trade(usuario_id, eid, td)
                                st.session_state.pop("editing_trade_id", None)
                                st.session_state["df_trades"] = load_trades(usuario_id)
                                st.success("Atualizado!")
                                st.rerun()
                            except Exception:
                                st.error("Erro ao salvar.")
                    with s2:
                        if st.form_submit_button("❌ Cancelar",
                                                  use_container_width=True):
                            st.session_state.pop("editing_trade_id", None)
                            st.rerun()
            st.divider()

        dcols = [c for c in TRADE_COLUMNS if c != "id"]
        st.dataframe(df[dcols].sort_index(ascending=False),
                     use_container_width=True, hide_index=True)
        st.divider()

        st.subheader("Acoes por trade")
        tids = df["id"].tolist()
        sel = st.selectbox("Selecione o ID", options=tids,
                           format_func=lambda x: f"{x[:8]}..." if len(x) > 8 else x)
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
# NEW TRADE
# =========================================================

with tab_n:
    cc = len(df)
    fl = not is_pro and cc >= FREE_TRADE_LIMIT

    if fl:
        st.warning("Limite de 10 trades atingido.")
        st.info("Pro: ilimitado por R$ 29,90/mes.")
    else:
        with st.form("add_trade", clear_on_submit=True):
            st.subheader("Registrar Operacao")
            r1, r2, r3, r4 = st.columns(4)
            at = r1.text_input("Ativo",
                               value=st.session_state.get("last_asset", "USDJPY"))
            tt = r2.selectbox("Tipo", ["buy", "sell"])
            vl = r3.number_input("Volume", min_value=0.01,
                                 value=0.01, step=0.01, format="%.2f")
            pr = r4.number_input("Lucro (USD)", value=0.0, format="%.2f")
            st.divider()
            r5, r6, r7, r8 = st.columns(4)
            en = r5.number_input("Entrada", value=0.0, format="%.3f")
            ex = r6.number_input("Saida", value=0.0, format="%.3f")
            sl = r7.number_input("SL", value=0.0, format="%.3f")
            tp = r8.number_input("TP", value=0.0, format="%.3f")
            ob = st.text_area("Observacao", max_chars=500)

            if st.form_submit_button("💾 SALVAR TRADE",
                                     type="primary",
                                     use_container_width=True):
                errs = []
                if not at.strip():
                    errs.append("Informe o ativo.")
                if vl <= 0:
                    errs.append("Volume > zero.")
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    td = {"asset": at.strip().upper(), "type": tt,
                          "volume": vl, "entry": en, "exit": ex,
                          "sl": sl, "tp": tp, "profit": pr,
                          "observation": ob.strip()}
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
# PLANS
# =========================================================

with tab_p:
    st.title("⭐ Planos")

    fc, pc = st.columns(2)
    with fc:
        st.markdown("""
        <div class="plan-card">
            <h2>🆓 Gratuito</h2>
            <h3>R$ 0</h3><br>
            <p>✅ Ate 10 trades</p>
            <p>✅ Metricas basicas</p>
            <p>✅ Graficos basicos</p>
            <p>✅ Historico</p>
            <p>✅ CSV</p><br>
            <p>❌ Insights</p>
            <p>❌ Insignias</p>
            <p>❌ Graficos extras</p>
        </div>""", unsafe_allow_html=True)
        if not is_pro:
            st.info("Seu plano: Gratuito")
        else:
            st.caption("Voce ja e Pro.")

    with pc:
        st.markdown("""
        <div class="plan-card">
            <h2>⭐ Pro</h2>
            <h3>R$ 29,90/mes</h3><br>
            <p>✅ Trades ilimitados</p>
            <p>✅ Resumos estatisticos</p>
            <p>✅ Insights</p>
            <p>✅ Analise de perdas</p>
            <p>✅ Simulacoes</p>
            <p>✅ Insignias</p>
            <p>✅ Graficos extras</p>
        </div>""", unsafe_allow_html=True)
        if owner:
            st.success("🛡️ Pro permanente (dev).")
        elif is_pro:
            st.success("⭐ Pro ativo.")
        else:
            st.button("⭐ Assinar R$ 29,90/mes",
                      type="primary", use_container_width=True,
                      disabled=True, help="Pagamento em configuracao.")
            st.caption("Em breve.")

    st.divider()

    comp = pd.DataFrame({
        "Recurso": ["Trades", "Metricas", "Graficos",
                    "Historico", "CSV", "Insights",
                    "Insignias", "Extras", "Simulacoes"],
        "Gratuito": ["10", "✅", "✅", "✅", "✅",
                     "❌", "❌", "❌", "❌"],
        "Pro": ["Ilimitado", "✅", "✅", "✅", "✅",
                "✅", "✅", "✅", "✅"],
    })
    st.dataframe(comp, use_container_width=True, hide_index=True)
    st.divider()
    st.caption("Finalidade informativa. Nao garante resultados.")
