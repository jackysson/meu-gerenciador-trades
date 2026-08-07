import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
import re

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

PERIOD_OPTIONS = ["🗓️ Tudo", "📅 Este mês", "🕒 Últimos 30 dias",
                  "📆 Últimos 90 dias", "🎯 Este ano"]


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
        #MainMenu, header, footer, [data-testid="stFooter"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stBottom"] {visibility: hidden !important; display: none !important;} a[href*="github.com"], a[href*="streamlit.io"] {display: none !important;}
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
        #MainMenu, header, footer, [data-testid="stFooter"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stBottom"] {visibility: hidden !important; display: none !important;} a[href*="github.com"], a[href*="streamlit.io"] {display: none !important;}
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
# IMPORTADOR INTELIGENTE (CSV + HTML MT4/MT5 + ANTI-DUP)
# =========================================================

COLUMN_ALIASES = {
    "Ativo": ["ativo", "asset", "symbol", "símbolo", "simbolo", "par", "pair",
              "instrument", "instrumento", "ticker", "mercado", "market", "currency", "item"],
    "Tipo": ["tipo", "type", "side", "lado", "direção", "direcao", "direction",
             "operation", "operacao", "ação", "acao", "action", "order type", "sentido"],
    "Volume": ["volume", "lot", "lote", "lots", "quantity", "quantidade", "qty",
               "size", "tamanho", "amount", "contratos"],
    "Entrada": ["entrada", "entry", "open", "abertura", "open price",
                "preço de entrada", "preco de entrada", "entry price", "price open", "price", "preço", "preco"],
    "Saída": ["saída", "saida", "exit", "close", "fechamento", "close price",
              "preço de saída", "preco de saida", "exit price", "price close", "preço_2", "preco_2", "price_2"],
    "SL": ["sl", "stop loss", "stop", "stoploss", "stop price", "stop loss price", "s/l"],
    "TP": ["tp", "take profit", "takeprofit", "take profit price", "target", "alvo", "t/p"],
    "Lucro": ["lucro", "profit", "pnl", "p&l", "resultado", "result", "gain",
              "ganho", "net profit", "lucro líquido", "lucro liquido", "profit/loss",
              "realized p&l", "u$s", "usd", "valor", "profit loss"],
    "Data": ["data", "date", "time", "data/hora", "data e hora", "datetime",
             "open time", "close time", "timestamp", "open date", "close date",
             "data de abertura", "data de fechamento", "hora de abertura",
             "hora de fechamento", "horário", "horario"],
    "Obs": ["obs", "observation", "observação", "observacao", "comment",
            "comentário", "comentario", "note", "notes", "nota", "description",
            "descrição", "descricao"],
}

SELL_WORDS = ["sell", "venda", "vender", "short", "put", "down", "s", "0", "-1", "vermelho", "red"]

SKIP_ASSETS = {"TOTAL", "BALANCE", "BALANÇO", "BALANCO", "SALDO", "DEPOSIT",
               "DEPÓSITO", "DEPOSITO", "WITHDRAWAL", "SAQUE", "CREDIT",
               "CRÉDITO", "CREDITO", "COMMISSION", "COMISSÃO", "COMISSAO",
               "SWAP", "EQUITY", "MARGEM", "MARGIN", "FREE MARGIN",
               "ATIVO", "SYMBOL", "TICKET", "LUCRO", "BRUTO", "REBAIXAMENTO"}


def dedupe_columns(df):
    seen = {}
    new_cols = []
    for c in df.columns:
        s = str(c)
        if s in seen:
            seen[s] += 1
            new_cols.append(f"{s}_{seen[s]}")
        else:
            seen[s] = 1
            new_cols.append(s)
    df.columns = new_cols
    return df


def auto_map_columns(columns):
    mapping = {}
    cols_lower = {str(c).strip().lower(): str(c).strip() for c in columns}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in [target.lower()] + aliases:
            if alias in cols_lower and target not in mapping:
                mapping[target] = cols_lower[alias]
                break
    return mapping


def detect_separator(text):
    sample = "\n".join(text.splitlines()[:15])
    counts = {sep: sample.count(sep) for sep in [",", ";", "\t", "|"]}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def br_to_float(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s or s.lower() == "nan":
        return 0.0
    for ch in ["R$", "$", "USD", "usd", "%"]:
        s = s.replace(ch, "")
    s = s.strip()
    has_dot, has_comma = "." in s, "," in s
    if has_dot and has_comma:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_comma:
        parts = s.split(",")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3 and len(parts[0]) <= 3):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date_flexible(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return ""
    fmts = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
        "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y",
        "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y.%m.%d",
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    try:
        return pd.to_datetime(s, dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def decode_smart(raw):
    text = None
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            text = raw.decode("utf-16")
        except Exception:
            text = None
    if text is None:
        for enc in ["utf-8-sig", "cp1252", "latin-1"]:
            try:
                text = raw.decode(enc)
                if text.strip():
                    break
            except Exception:
                continue
    if text is None:
        text = raw.decode("utf-8-sig", errors="replace")
    return text.replace("\x00", "")


def parse_html_manual(text):
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I)
    table = []
    for r in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S | re.I)
        if cells:
            clean = [re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip() for c in cells]
            if len(clean) >= 3 and any(clean):
                table.append(clean)
    if not table:
        raise ValueError("Nenhuma linha de dados encontrada no HTML.")
    keys = ["ticket", "open time", "type", "size", "item", "price",
            "profit", "symbol", "close time", "s/l", "t/p", "swap",
            "horário", "horario", "ativo", "tipo", "volume", "preço", "preco", "lucro"]
    hidx = None
    for i, row in enumerate(table):
        joined = " ".join(row).lower()
        if sum(1 for k in keys if k in joined) >= 3:
            hidx = i
            break
    if hidx is None:
        for i, row in enumerate(table):
            if len(row) >= 8:
                hidx = i
                break
    if hidx is None:
        raise ValueError("Estrutura do HTML não reconhecida.")
    header = [h if h else f"col_{i}" for i, h in enumerate(table[hidx])]
    price_idx = [i for i, h in enumerate(header)
                 if h.lower() in ("price", "preço", "preco")]
    if len(price_idx) >= 2:
        header[price_idx[1]] = "Preço_2"
    ncols = len(header)
    data = [row for row in table[hidx + 1:] if len(row) == ncols]
    if not data:
        data = [row[:ncols] + [""] * (ncols - len(row))
                for row in table[hidx + 1:] if len(row) >= 3]
    return pd.DataFrame(data, columns=header)


def read_html_smart(text):
    text = text.replace("\x00", "")
    try:
        tables = pd.read_html(io.StringIO(text), flavor="lxml")
    except Exception:
        tables = []
    best, best_score = None, -1
    for t in tables:
        if len(t) == 0:
            continue
        cand = t
        generic = all(str(c).startswith("Unnamed") or str(c).isdigit() for c in cand.columns)
        if generic and len(cand) > 1:
            cand = cand.copy()
            cand.columns = [str(v).strip() for v in cand.iloc[0]]
            cand = cand.iloc[1:].reset_index(drop=True)
        cand = dedupe_columns(cand.copy())
        m = auto_map_columns(cand.columns)
        if "Ativo" not in m:
            continue
        score = len(m) * 1000 + len(cand)
        if score > best_score:
            best_score = score
            best = cand
    if best is not None:
        return best
    return dedupe_columns(parse_html_manual(text))


def read_file_smart(file):
    fname = (getattr(file, "name", "") or "").lower()
    raw = file.getvalue()
    text = decode_smart(raw)
    if fname.endswith(".html") or fname.endswith(".htm") or "<table" in text[:8000].lower():
        return read_html_smart(text)
    sep = detect_separator(text)
    return pd.read_csv(io.StringIO(text), sep=sep, engine="python")


def convert_rows(tmp, mapping):
    rows = []
    col_ativo = mapping.get("Ativo")
    if not col_ativo or col_ativo not in tmp.columns:
        return rows

    def gv(target, r):
        col = mapping.get(target)
        if col and col in tmp.columns:
            return br_to_float(r.get(col))
        return 0.0

    for _, r in tmp.iterrows():
        ativo = str(r.get(col_ativo, "")).strip().upper().rstrip(":")
        if "(" in ativo or "%" in ativo or " " in ativo:
            continue
        try:
            float(ativo.replace(",", "."))
            continue
        except ValueError:
            pass
        if not ativo or ativo == "NAN" or ativo in SKIP_ASSETS:
            continue
        tipo = "buy"
        tcol = mapping.get("Tipo")
        if tcol and tcol in tmp.columns:
            tr = str(r.get(tcol, "")).strip().lower()
            if tr in SELL_WORDS or tr.startswith("s") or tr.startswith("v"):
                tipo = "sell"
        obs = ""
        ocol = mapping.get("Obs")
        if ocol and ocol in tmp.columns and pd.notna(r.get(ocol)):
            obs = str(r.get(ocol)).strip()
        data = ""
        dcol = mapping.get("Data")
        if dcol and dcol in tmp.columns:
            data = parse_date_flexible(r.get(dcol))
        rows.append({
            "asset": ativo, "type": tipo,
            "volume": gv("Volume", r) or 0.01,
            "entry": gv("Entrada", r), "exit": gv("Saída", r),
            "sl": gv("SL", r), "tp": gv("TP", r),
            "profit": gv("Lucro", r),
            "observation": obs, "data": data,
        })
    return rows


def trade_fingerprint(data, asset, profit, volume):
    return f"{data}|{asset}|{round(float(profit), 4)}|{round(float(volume), 4)}"


def import_trades(uid, email, rows):
    if not uid:
        raise ValueError("Usuário não autenticado.")
    if db is None:
        raise RuntimeError("Banco indisponível.")
    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap.exists:
        raise ValueError("Usuário não encontrado.")

    existing = load_trades(uid)
    existing_fps = set()
    if not existing.empty:
        for _, r in existing.iterrows():
            existing_fps.add(trade_fingerprint(r["Data"], r["Ativo"], r["Lucro"], r["Volume"]))

    fresh = []
    dup = 0
    for td in rows:
        fp = trade_fingerprint(td.get("data", ""), td["asset"], td["profit"], td["volume"])
        if fp in existing_fps:
            dup += 1
            continue
        existing_fps.add(fp)
        fresh.append(td)
    rows = fresh

    count = int(snap.to_dict().get("trade_count", 0))
    skipped = 0
    if not has_pro_access(uid, email):
        allowed = max(0, FREE_TRADE_LIMIT - count)
        if len(rows) > allowed:
            skipped = len(rows) - allowed
            rows = rows[:allowed]

    if not rows:
        return 0, skipped, dup

    batch = db.batch()
    for td in rows:
        tref = ref.collection("trades").document()
        created = firestore.SERVER_TIMESTAMP
        if td.get("data"):
            try:
                created = datetime.strptime(td["data"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                created = firestore.SERVER_TIMESTAMP
        batch.set(tref, {
            "asset": td["asset"], "type": td["type"],
            "volume": float(td["volume"]), "entry": float(td["entry"]),
            "exit": float(td["exit"]), "sl": float(td["sl"]),
            "tp": float(td["tp"]), "profit": float(td["profit"]),
            "observation": td.get("observation", ""),
            "created_at": created,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
    batch.commit()
    ref.set({"trade_count": count + len(rows),
             "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
    return len(rows), skipped, dup


# =========================================================
# CAPITAL & APORTES
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

def load_deposits(uid):
    if db is None:
        return 0.0, []
    total = 0.0
    events = []
    for doc in db.collection("users").document(uid).collection("deposits").stream():
        d = doc.to_dict()
        amt = float(d.get("amount", 0))
        ca = d.get("created_at")
        total += amt
        if isinstance(ca, datetime):
            events.append((ca, amt))
    return total, events

def save_aporte(uid, value):
    if db is None:
        raise RuntimeError("Banco indisponível.")
    db.collection("users").document(uid).collection("deposits").document().set({
        "amount": float(value),
        "created_at": firestore.SERVER_TIMESTAMP,
    })


# =========================================================
# FORMATTERS + SEMAFORO + CARDS + PERIODO
# =========================================================

def fmt_money(v):
    av, sign = abs(v), "-" if v < 0 else ""
    if av >= 1e12: return f"{sign}$ {av/1e12:,.2f} T"
    if av >= 1e9:  return f"{sign}$ {av/1e9:,.2f} B"
    if av >= 1e6:  return f"{sign}$ {av/1e6:,.2f} M"
    return f"{sign}$ {v:,.2f}"

def fmt_mult(v):
    if v >= 1e6: return f"{v/1e6:,.2f}M x"
    if v >= 1e3: return f"{v/1e3:,.1f}K x"
    return f"{v:,.2f}x"

def sem_wr(v):
    return "good" if v >= 55 else ("ok" if v >= 40 else "bad")

def sem_ratio(v):
    return "good" if v >= 1.5 else ("ok" if v >= 1.0 else "bad")

def metric_card(label, value, help_text, status="none", sub=""):
    color = {"good": "#3fb950", "ok": "#d29922",
             "bad": "#f85149", "none": "#58a6ff"}.get(status, "#58a6ff")
    sub_html = f'<p style="margin:4px 0 0 0; font-size:12px; opacity:.7;">{sub}</p>' if sub else ""
    st.markdown(
        f'<div class="plan-card" style="border-left:5px solid {color}; padding:14px; margin-bottom:0;">'
        f'<p style="margin:0; font-size:13px; opacity:.85;">{label} '
        f'<span title="{help_text}" style="cursor:help;">ⓘ</span></p>'
        f'<h3 style="margin:6px 0 0 0;">{value}</h3>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def period_start(period):
    now = datetime.now()
    if period == "📅 Este mês":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == "🕒 Últimos 30 dias":
        return now - pd.Timedelta(days=30)
    if period == "📆 Últimos 90 dias":
        return now - pd.Timedelta(days=90)
    if period == "🎯 Este ano":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def filter_by_period(dframe, period):
    start = period_start(period)
    if start is None or dframe.empty:
        return dframe
    datas = pd.to_datetime(dframe["Data"], errors="coerce")
    return dframe[datas >= pd.Timestamp(start)].reset_index(drop=True)


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
              "editing_trade_id", "confirm_delete_id",
              "deposit_total", "deposit_events",
              "csv_file_name", "csv_df", "csv_auto_map", "last_imported_name"]:
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

if "deposit_total" not in st.session_state:
    try:
        dt, de = load_deposits(usuario_id)
        st.session_state["deposit_total"] = dt
        st.session_state["deposit_events"] = de
    except Exception:
        st.session_state["deposit_total"] = 0.0
        st.session_state["deposit_events"] = []

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
# SIDEBAR (enxuta)
# =========================================================

with st.sidebar:
    st.subheader("☁️ Conexao")

    if cloud_connected:
        st.markdown('<div class="connection-ok">✅ Nuvem Conectada</div>',
                     unsafe_allow_html=True)
    else:
        st.markdown('<div class="connection-off">⚠️ Modo Offline</div>',
                     unsafe_allow_html=True)

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
    st.subheader("💰 Capital & Aportes")

    with st.form("capital_form"):
        cap = st.number_input("Capital Inicial (USD)", min_value=0.0,
                              value=float(st.session_state["initial_capital"]),
                              step=1.0, format="%.2f")
        aporte = st.number_input("Novo Aporte (USD)", min_value=0.0,
                                 value=0.0, step=10.0, format="%.2f")
        b1, b2 = st.columns(2)
        with b1:
            salvar_cap = st.form_submit_button("💾 Capital", use_container_width=True)
        with b2:
            add_aporte = st.form_submit_button("➕ Aporte", use_container_width=True)

        if salvar_cap:
            try:
                save_capital(usuario_id, cap)
                st.session_state["initial_capital"] = cap
                st.success("Capital salvo!")
            except Exception:
                st.error("Erro ao salvar.")
        if add_aporte and aporte > 0:
            try:
                save_aporte(usuario_id, aporte)
                st.session_state["deposit_total"] = st.session_state.get("deposit_total", 0.0) + aporte
                st.session_state["deposit_events"] = st.session_state.get("deposit_events", []) + [(datetime.now(timezone.utc), aporte)]
                st.success(f"Aporte de $ {aporte:,.2f} registrado!")
            except Exception:
                st.error("Erro ao salvar aporte.")

    st.caption(f"Total em aportes: $ {st.session_state.get('deposit_total', 0.0):,.2f}")

    st.divider()
    st.subheader("💾 Exportar / Importar")

    edf = st.session_state.get("df_trades", pd.DataFrame(columns=TRADE_COLUMNS))
    ecols = [c for c in TRADE_COLUMNS if c != "id"]
    csv = edf[ecols].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar CSV", data=csv,
                       file_name="meus_trades.csv",
                       mime="text/csv", use_container_width=True)

    up = st.file_uploader("📤 Importar (duplicados sao ignorados)",
                          type=["csv", "txt", "html", "htm"], key="import_csv")
    if up is not None:
        fname = up.name
        if st.session_state.get("csv_file_name") != fname:
            try:
                tmp = read_file_smart(up)
                st.session_state["csv_file_name"] = fname
                st.session_state["csv_df"] = tmp
                st.session_state["csv_auto_map"] = auto_map_columns(tmp.columns)
            except Exception as e:
                st.error(f"❌ Não consegui ler o arquivo: {e}")
                st.session_state["csv_file_name"] = None
        tmp = st.session_state.get("csv_df")
        auto_map = st.session_state.get("csv_auto_map", {})
        if tmp is not None and len(tmp) > 0:
            if "Ativo" not in auto_map:
                st.error("❌ Não reconheci a coluna de Ativo automaticamente.")
                st.caption("🔎 Colunas lidas: " + " | ".join(str(c) for c in tmp.columns[:14]))
            else:
                preview_rows = convert_rows(tmp, auto_map)
                st.caption(f"🔎 {len(preview_rows)} trade(s) pronto(s) para importar.")
                if st.button("✅ Confirmar importação", type="primary", use_container_width=True):
                    try:
                        n, skipped, dup = import_trades(usuario_id, usuario_email, preview_rows)
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.session_state["csv_file_name"] = None
                        if n:
                            st.success(f"✅ {n} trade(s) importado(s)!")
                        if dup:
                            st.warning(f"🔁 {dup} trade(s) ignorado(s): já existiam na sua conta.")
                        if skipped:
                            st.warning(f"⚠️ {skipped} ignorado(s) pelo limite do plano gratuito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao importar: {e}")
        elif tmp is not None:
            st.warning("Arquivo sem linhas válidas.")

    if st.button("🔄 Sincronizar", use_container_width=True):
        try:
            st.session_state["df_trades"] = load_trades(usuario_id)
            dt, de = load_deposits(usuario_id)
            st.session_state["deposit_total"] = dt
            st.session_state["deposit_events"] = de
            st.rerun()
        except Exception:
            st.error("Erro ao sincronizar.")


# =========================================================
# DASHBOARD + PERIODO + METRICAS + ONBOARDING
# =========================================================

ic = st.session_state["initial_capital"]
deposit_total = st.session_state.get("deposit_total", 0.0)
deposit_events = st.session_state.get("deposit_events", [])
base_capital = ic + deposit_total

st.title("📊 Trader Strategy Analytics Pro")

# ---- conta inteira (nunca filtra) ----
df_all = st.session_state["df_trades"].copy()
for col in ["Lucro", "Entrada", "Saída", "SL", "TP", "Volume"]:
    if col not in df_all.columns:
        df_all[col] = 0
    df_all[col] = pd.to_numeric(df_all[col], errors="coerce").fillna(0)

total_profit_all = float(df_all["Lucro"].sum())
equity = base_capital + total_profit_all

# ---- periodo ----
if not df_all.empty:
    period = st.radio("Período de análise", PERIOD_OPTIONS,
                      horizontal=True, key="period_filter")
    if period != "🗓️ Tudo":
        st.caption(f"📊 Métricas, gráficos e histórico refletindo: **{period}**")
else:
    period = "🗓️ Tudo"

# ---- ONBOARDING (conta vazia) ----
if df_all.empty:
    st.markdown(f"""
        <div class="plan-card" style="text-align:center; padding:40px 20px; margin-bottom:20px;">
            <h1 style="margin:0 0 10px 0;">👋 Bem-vindo(a), {usuario_nome}!</h1>
            <p style="margin:0; font-size:16px;">Seu painel esta pronto. Em 3 passos ele vira o seu centro de comando do trading.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="insight-card">
            <h4>🚀 Inicio rapido</h4>
            <p>✅ <b>1. Entrar com o Google</b> — conta criada e dados salvos na nuvem com seguranca.</p>
            <p>⬜ <b>2. Trazer suas operacoes</b> — importe seu historico pelo botao 📤 Importar na barra lateral (MT4/MT5, Binance, cTrader ou CSV) ou registre a primeira na aba ➕ Novo Trade.</p>
            <p>⬜ <b>3. Desbloquear a primeira insignia</b> — com 10 trades registrados voce ganha a 📝 Diario Iniciado.</p>
        </div>
        """, unsafe_allow_html=True)

    h1, h2 = st.columns(2)
    with h1:
        st.markdown("""
            <div class="plan-card">
                <h4>📤 Ja opera em alguma plataforma?</h4>
                <p>Exporte o historico (na MT5: botao direito em Historico → Salvar como Relatorio) e envie na barra lateral. Centenas de trades entram em segundos, sem digitar nada.</p>
            </div>
            """, unsafe_allow_html=True)
    with h2:
        st.markdown("""
            <div class="plan-card">
                <h4>✍️ Comecando agora?</h4>
                <p>Va na aba ➕ Novo Trade e registre cada operacao ao fechar. Em poucos dias voce tera estatisticas reais do seu desempenho.</p>
            </div>
            """, unsafe_allow_html=True)

    if st.button("🔄 Ja fiz — atualizar painel", use_container_width=True):
        st.session_state["df_trades"] = load_trades(usuario_id)
        st.rerun()

# ---- periodo selecionado ----
df = filter_by_period(df_all, period)
loss_df = df[df["Lucro"] < 0]
win_df = df[df["Lucro"] > 0]
loss_count = len(loss_df)
win_count = len(win_df)
avg_loss_cash = abs(loss_df["Lucro"].mean()) if loss_count > 0 else 0
avg_loss_pts = abs(loss_df["Entrada"] - loss_df["SL"]).mean() if loss_count > 0 else 0
total_profit = float(df["Lucro"].sum())
win_rate = win_count / len(df) * 100 if len(df) > 0 else 0
gp = win_df["Lucro"].sum()
gl = abs(loss_df["Lucro"].sum())
pf = gp / gl if gl > 0 else 0

avg_win = float(win_df["Lucro"].mean()) if win_count > 0 else 0.0
avg_loss = abs(float(loss_df["Lucro"].mean())) if loss_count > 0 else 0.0
payoff = (avg_win / avg_loss) if avg_loss > 0 else (float("inf") if avg_win > 0 else 0.0)
if len(df) > 0:
    wr_frac = win_count / len(df)
    expectancy = wr_frac * avg_win - (1 - wr_frac) * avg_loss
else:
    expectancy = 0.0
expectancy_pct = (expectancy / base_capital * 100) if base_capital > 0 else 0.0

if len(df) > 0:
    eq_curve = base_capital + df["Lucro"].cumsum()
    peak = eq_curve.cummax()
    dd = peak - eq_curve
    max_dd = float(dd.max())
else:
    max_dd = 0.0

max_loss_streak = 0
_cur = 0
for _v in df["Lucro"]:
    if _v < 0:
        _cur += 1
        if _cur > max_loss_streak:
            max_loss_streak = _cur
    else:
        _cur = 0

best_row = df.loc[df["Lucro"].idxmax()] if len(df) > 0 else None
worst_row = df.loc[df["Lucro"].idxmin()] if len(df) > 0 else None

# ---- metricas (so com dados) ----
if not df_all.empty:
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("💰 Capital Inicial", f"$ {ic:,.2f}",
              help="Valor que voce comecou a operar. Editavel na sidebar. (Conta inteira)")
    r2.metric("➕ Total Aportes", f"$ {deposit_total:,.2f}",
              help="Soma de todos os depositos extras registrados. (Conta inteira)")
    r3.metric("📊 Resultado do Período", f"$ {total_profit:,.2f}",
              help="Lucro ou prejuizo acumulado apenas no periodo selecionado acima.")
    r4.metric("💵 Equity Final", f"$ {equity:,.2f}",
              help="Capital inicial + aportes + resultado acumulado da conta inteira.")

    st.markdown("")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        metric_card("🎯 Win Rate", f"{win_rate:.1f}%",
                    "Percentual de trades vencedores no periodo. Verde acima de 55%, amarelo entre 40 e 55%, vermelho abaixo de 40%.",
                    sem_wr(win_rate), "Meta profissional: acima de 50%")
    with p2:
        metric_card("📈 Profit Factor", f"{pf:.2f}",
                    "Lucro bruto dividido pela perda bruta no periodo. Verde acima de 1.5, amarelo entre 1.0 e 1.5, vermelho abaixo de 1.0.",
                    sem_ratio(pf), "Acima de 1.0 = sistema lucrativo")
    with p3:
        pf_disp = "∞" if payoff == float("inf") else f"{payoff:.2f}"
        metric_card("⚖️ Payoff", pf_disp,
                    "Ganho medio dividido pela perda media no periodo. Mostra se suas vitorias pagam suas derrotas.",
                    sem_ratio(payoff if payoff != float("inf") else 99), "Ideal acima de 1.5")
    with p4:
        metric_card("🎲 Expectativa por Trade", f"$ {expectancy:,.2f}",
                    "Quanto voce ganha em media por trade no periodo. Positivo significa vantagem estatistica a seu favor.",
                    "good" if expectancy > 0 else "bad",
                    f"{expectancy_pct:+.2f}% do capital por trade")

    st.markdown("")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("✅ Vitórias", win_count, help="Trades com lucro no periodo.")
    s2.metric("❌ Derrotas", loss_count, help="Trades com prejuizo no periodo.")
    s3.metric("📉 Drawdown Máx", f"$ {max_dd:,.2f}",
              help="Maior queda da conta a partir de um topo dentro do periodo selecionado.")
    s4.metric("🔻 Sequência de Perdas", max_loss_streak,
              help="Maior numero de perdas consecutivas no periodo.")

    if best_row is not None:
        st.caption(
            f"🏆 Melhor trade do período: **{best_row['Ativo']}** em {best_row['Data']} "
            f"($ {float(best_row['Lucro']):+,.2f})   •   "
            f"💀 Pior trade do período: **{worst_row['Ativo']}** em {worst_row['Data']} "
            f"($ {float(worst_row['Lucro']):+,.2f})"
        )

st.divider()


# =========================================================
# TABS
# =========================================================

tab_g, tab_i, tab_h, tab_n, tab_p, tab_c = st.tabs([
    "🚀 Graficos", "📚 Insights", "📝 Historico",
    "➕ Novo Trade", "⭐ Planos", "⚙️ Config",
])


# =========================================================
# GRAPHS
# =========================================================

with tab_g:
    if df_all.empty:
        st.info("🚀 Seu painel esta vazio. Importe seu historico na barra lateral (📤 Importar) ou registre a primeira operacao na aba ➕ Novo Trade para ver os graficos ganharem vida.")
    elif df.empty:
        st.info("Nenhum trade neste periodo. Mude o periodo no topo para ver os graficos.")
    else:
        st.subheader("📈 Evolução do Capital da Conta")
        eventos = []
        for _, row in df_all.iterrows():
            dtp = pd.to_datetime(row["Data"], errors="coerce")
            if pd.notna(dtp):
                eventos.append((dtp.to_pydatetime(), float(row["Lucro"])))
        for dtp, amt in deposit_events:
            eventos.append((dtp, float(amt)))
        eventos.sort(key=lambda e: e[0])

        if eventos:
            datas = [e[0] for e in eventos]
            deltas = [e[1] for e in eventos]
            curva = [ic] + list(ic + np.cumsum(deltas))
            datas = [datas[0]] + datas
            fig_ev = px.line(x=datas, y=curva, markers=True,
                             title="Crescimento da Conta (tempo real)",
                             labels={"x": "Data", "y": "Saldo (USD)"},
                             template=PLOTLY_TEMPLATE,
                             color_discrete_sequence=["#3fb950"])
            st.plotly_chart(fig_ev, use_container_width=True)
            st.caption("📌 Eixo X: data de cada operação e aporte | Eixo Y: saldo real da conta em dólares. Mostra o histórico COMPLETO, independente do período selecionado.")
        else:
            st.info("Sem datas válidas para montar a evolução.")

        st.divider()

        a, b = st.columns(2)
        with a:
            gm = df["Lucro"].expanding().mean().reset_index(drop=True)
            fig_gm = px.bar(x=list(range(1, len(gm) + 1)), y=gm,
                            title="Ganho Médio por Trade",
                            labels={"x": "Nº do Trade", "y": "Média (USD)"},
                            template=PLOTLY_TEMPLATE,
                            color_discrete_sequence=["#58a6ff"])
            st.plotly_chart(fig_gm, use_container_width=True)
            st.caption("📌 Eixo X: quantidade de trades no período | Eixo Y: ganho médio acumulado por trade em dólares.")
        with b:
            ml = win_df["Lucro"].expanding().mean().reset_index(drop=True)
            if len(ml) > 0:
                fig_ml = px.bar(x=list(range(1, len(ml) + 1)), y=ml,
                                title="Média de Lucro (só vencedores)",
                                labels={"x": "Nº do Trade Vencedor", "y": "Média (USD)"},
                                template=PLOTLY_TEMPLATE,
                                color_discrete_sequence=["#3fb950"])
                st.plotly_chart(fig_ml, use_container_width=True)
                st.caption("📌 Eixo X: sequência de trades vencedores no período | Eixo Y: valor médio de lucro em dólares.")
            else:
                st.info("Nenhum trade vencedor no período.")

        c, d = st.columns(2)
        with c:
            ga = df["Lucro"].cumsum().reset_index(drop=True)
            fig_ga = px.bar(x=list(range(1, len(ga) + 1)), y=ga,
                            title="Ganhos Acumulados",
                            labels={"x": "Nº do Trade", "y": "Lucro Acumulado (USD)"},
                            template=PLOTLY_TEMPLATE,
                            color_discrete_sequence=["#d29922"])
            st.plotly_chart(fig_ga, use_container_width=True)
            st.caption("📌 Eixo X: quantidade de trades no período | Eixo Y: lucro acumulado em dólares até aquele trade.")
        with d:
            rdf = df.copy()
            rdf["Risco"] = abs(rdf["Entrada"] - rdf["SL"])
            fig2 = px.bar(rdf, x="Ativo", y="Risco",
                          title="Risco por Trade",
                          color_discrete_sequence=["#f85149"],
                          template=PLOTLY_TEMPLATE)
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("📌 Eixo X: ativo operado | Eixo Y: distância Entrada→SL (risco assumido).")

        st.divider()

        if is_pro:
            st.subheader("🧮 Projeção de Crescimento")

            if len(df) > 0 and base_capital > 0:
                avg_per_trade = total_profit / len(df)
                hist_rate = avg_per_trade / base_capital

                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    modo = st.radio("Modo de projeção",
                                    ["📏 Linear (média $ por trade)",
                                     "📈 Juros compostos (% por trade)"],
                                    key="proj_mode")
                with cc2:
                    custom_n = st.number_input("Nº de trades projetados",
                                               min_value=1, value=100, step=10,
                                               key="proj_n")
                with cc3:
                    if "composto" in modo.lower():
                        default_rate = round(min(max(hist_rate, 0.001), 0.02) * 100, 1)
                        rate_pct = st.slider("% por trade", 0.1, 10.0,
                                             default_rate, 0.1,
                                             key="proj_rate") / 100.0
                        st.caption(f"Sua média no período: {hist_rate*100:.2f}%/trade")
                    else:
                        rate_pct = None
                        st.caption(f"Sua média no período: $ {avg_per_trade:,.2f}/trade")

                counts = sorted({n for n in [10, 50, 100, 250, 500, int(custom_n)]
                                 if n <= int(custom_n)})
                curva_n, curva_v = [], []
                for n in range(1, int(custom_n) + 1):
                    if rate_pct is not None:
                        proj = base_capital * ((1 + rate_pct) ** n)
                    else:
                        proj = base_capital + avg_per_trade * n
                    curva_n.append(n)
                    curva_v.append(proj)

                rows = []
                for n in counts:
                    idx = n - 1
                    proj = curva_v[idx]
                    rows.append({
                        "Trades": n,
                        "Equity Projetado": fmt_money(proj),
                        "Lucro Projetado": fmt_money(proj - base_capital),
                        "Multiplicador": fmt_mult(proj / base_capital),
                    })

                proj_final = curva_v[-1]
                m1, m2, m3 = st.columns(3)
                m1.metric("💵 Equity projetado", fmt_money(proj_final))
                m2.metric("📈 Lucro projetado", fmt_money(proj_final - base_capital))
                m3.metric("✖️ Multiplicador", fmt_mult(proj_final / base_capital))

                fig_proj = px.area(x=curva_n, y=curva_v,
                                   title=f"Projeção de Equity até {int(custom_n)} trades",
                                   labels={"x": "Nº do Trade", "y": "Equity (USD)"},
                                   template=PLOTLY_TEMPLATE,
                                   color_discrete_sequence=["#3fb950"])
                if max(curva_v) > 1_000_000:
                    fig_proj.update_yaxes(type="log")
                st.plotly_chart(fig_proj, use_container_width=True)
                st.caption("📌 Eixo X: quantidade de trades | Eixo Y: equity projetado em dólares (escala logarítmica quando os valores são muito grandes). Baseada no desempenho do período selecionado.")

                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                if hist_rate > 0.05 and rate_pct is not None:
                    st.warning(
                        f"⚠️ Sua média no período ({hist_rate*100:.1f}%/trade) é alta demais "
                        "para projetar a longo prazo com juros compostos. O slider começa em "
                        "um valor conservador — ajuste com cautela."
                    )
                if avg_per_trade <= 0:
                    st.warning("Seu resultado médio no período é negativo ou zero — a projeção mostra o impacto de manter esse desempenho.")
                st.caption(
                    f"Base de cálculo: capital $ {base_capital:,.2f} | "
                    f"modo {'composto ' + f'{(rate_pct or 0)*100:.1f}%/trade' if rate_pct else 'linear $ ' + f'{avg_per_trade:,.2f}/trade'}. "
                    "Projeção teórica; não garante resultados futuros."
                )
            else:
                st.info("Registre trades no período para calcular a projeção.")

            st.divider()
            e, f = st.columns(2)
            with e:
                fig3 = px.pie(names=["Vitorias", "Derrotas"],
                              values=[win_count, loss_count],
                              title="Distribuicao",
                              template=PLOTLY_TEMPLATE,
                              color_discrete_sequence=["#3fb950", "#f85149"])
                st.plotly_chart(fig3, use_container_width=True)
            with f:
                ap = df.groupby("Ativo")["Lucro"].sum().reset_index()
                fig4 = px.bar(ap, x="Ativo", y="Lucro",
                              title="Lucro por Ativo",
                              color_discrete_sequence=["#58a6ff"],
                              template=PLOTLY_TEMPLATE)
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
        if df_all.empty:
            st.info("🚀 Assim que voce trouxer suas operacoes, esta aba vira o seu raio-X: media de perdas, simulacoes e conquistas.")
        elif df.empty:
            st.info("Nenhum trade no periodo selecionado. Mude o periodo no topo.")
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
            st.caption("Simulacao historica baseada no periodo. Nao garante resultados.")

        st.divider()
        st.subheader("🏆 Insignias")
        st.caption("Conquistas contam sua história COMPLETA, independente do período.")
        badges = calc_badges(df_all)
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
    if df_all.empty:
        st.info("🚀 Nenhuma operacao por aqui ainda. Use 📤 Importar na barra lateral para trazer seu historico da MT4/MT5, Binance ou cTrader em segundos — ou registre a primeira na aba ➕ Novo Trade.")
    else:
        if "confirm_bulk_ids" in st.session_state:
            ids = st.session_state["confirm_bulk_ids"]
            st.warning(f"⚠️ Excluir {len(ids)} trade(s) selecionado(s)? Esta ação não pode ser desfeita.")
            st.info(f"⏳ A exclusão não é imediata: leva cerca de {max(1, round(len(ids) * 0.8))} segundo(s). Não feche a página até ver a confirmação ✅.")
            cc, cx = st.columns(2)
            with cc:
                if st.button("✅ Sim, excluir", type="primary", use_container_width=True):
                    try:
                        for tid in ids:
                            delete_trade(usuario_id, tid)
                        st.session_state.pop("confirm_bulk_ids", None)
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.success("Trades excluidos!")
                        st.rerun()
                    except Exception:
                        st.error("Erro ao excluir.")
            with cx:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.pop("confirm_bulk_ids", None)
                    st.rerun()
            st.divider()

        if st.session_state.get("confirm_delete_all"):
            st.warning(f"⚠️ Excluir TODOS os {len(df_all)} trades da sua conta? Esta ação não pode ser desfeita.")
            st.info(f"⏳ A exclusão não é imediata: leva cerca de {max(1, round(len(df_all) * 0.8))} segundo(s). Não feche a página até ver a confirmação ✅.")
            cc, cx = st.columns(2)
            with cc:
                if st.button("✅ Sim, excluir tudo", type="primary", use_container_width=True):
                    try:
                        for tid in df_all["id"].tolist():
                            delete_trade(usuario_id, tid)
                        st.session_state["confirm_delete_all"] = False
                        st.session_state["df_trades"] = load_trades(usuario_id)
                        st.success("Todos os trades foram excluidos!")
                        st.rerun()
                    except Exception:
                        st.error("Erro ao excluir.")
            with cx:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state["confirm_delete_all"] = False
                    st.rerun()
            st.divider()

        eid = st.session_state.get("editing_trade_id")
        if eid:
            tr = df_all[df_all["id"] == eid]
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
                    s1b, s2b = st.columns(2)
                    with s1b:
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
                    with s2b:
                        if st.form_submit_button("❌ Cancelar",
                                                  use_container_width=True):
                            st.session_state.pop("editing_trade_id", None)
                            st.rerun()
            st.divider()

        if period != "🗓️ Tudo":
            st.caption(f"📅 Período: **{period}** — mostrando {len(df)} de {len(df_all)} trades.")

        st.subheader("🔍 Buscar no histórico")
        f1, f2 = st.columns([3, 1])
        with f1:
            search_txt = st.text_input("Filtrar por ativo ou observação",
                                       key="hist_search", placeholder="Ex.: USDJPY")
        with f2:
            tipo_filter = st.selectbox("Tipo", ["Todos", "buy", "sell"], key="hist_type")

        df_view = df.copy()
        if search_txt.strip():
            q = search_txt.strip().lower()
            mask = (df_view["Ativo"].astype(str).str.lower().str.contains(q, na=False) |
                    df_view["Obs"].astype(str).str.lower().str.contains(q, na=False))
            df_view = df_view[mask]
        if tipo_filter != "Todos":
            df_view = df_view[df_view["Tipo"] == tipo_filter]
        df_view = df_view.reset_index(drop=True)

        if df.empty:
            st.info("Nenhum trade neste período.")
        elif df_view.empty:
            st.info("Nenhum trade corresponde à busca. Limpe o filtro acima.")
        else:
            if search_txt.strip() or tipo_filter != "Todos":
                st.caption(f"🔎 Mostrando **{len(df_view)}** de **{len(df)}** trades do período.")
            dcols = [c for c in TRADE_COLUMNS if c != "id"]
            st.dataframe(df_view[dcols].sort_index(ascending=False),
                         use_container_width=True, hide_index=True)
            st.divider()

            st.subheader("Acoes por trade")
            labels = []
            label_to_id = {}
            for _, r in df_view.sort_index(ascending=False).iterrows():
                lbl = f"{r['Data']}  |  {r['Ativo']}  |  {r['Tipo']}  |  $ {float(r['Lucro']):,.2f}  |  #{str(r['id'])[:4]}"
                labels.append(lbl)
                label_to_id[lbl] = r["id"]
            sel_labels = st.multiselect("Selecione um ou mais trades", options=labels)
            sel_ids = [label_to_id[l] for l in sel_labels]
            if sel_labels:
                st.caption(f"{len(sel_ids)} trade(s) selecionado(s).")

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("✏️ Editar", use_container_width=True,
                             disabled=len(sel_ids) != 1):
                    st.session_state["editing_trade_id"] = sel_ids[0]
                    st.rerun()
            with b2:
                if st.button("🗑️ Excluir selecionados", use_container_width=True,
                             disabled=len(sel_ids) == 0):
                    st.session_state["confirm_bulk_ids"] = sel_ids
                    st.rerun()
            with b3:
                if st.button("☠️ Excluir TODOS", use_container_width=True):
                    st.session_state["confirm_delete_all"] = True
                    st.rerun()


# =========================================================
# NEW TRADE
# =========================================================

with tab_n:
    cc = len(df_all)
    fl = not is_pro and cc >= FREE_TRADE_LIMIT

    if fl:
        st.warning("Limite de 10 trades atingido.")
        st.info("Pro: ilimitado por R$ 29,90/mes.")
    else:
        with st.form("add_trade", clear_on_submit=True):
            st.subheader("Registrar Operacao")
            r1b, r2b, r3b, r4b = st.columns(4)
            at = r1b.text_input("Ativo",
                               value=st.session_state.get("last_asset", "USDJPY"))
            tt = r2b.selectbox("Tipo", ["buy", "sell"])
            vl = r3b.number_input("Volume", min_value=0.01,
                                 value=0.01, step=0.01, format="%.2f")
            pr = r4b.number_input("Lucro (USD)", value=0.0, format="%.2f")
            st.divider()
            r5b, r6b, r7b, r8b = st.columns(4)
            en = r5b.number_input("Entrada", value=0.0, format="%.3f")
            ex = r6b.number_input("Saida", value=0.0, format="%.3f")
            sl = r7b.number_input("SL", value=0.0, format="%.3f")
            tp = r8b.number_input("TP", value=0.0, format="%.3f")
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


# =========================================================
# CONFIG
# =========================================================

with tab_c:
    st.title("⚙️ Configurações")

    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("🎨 Aparência")
        theme = st.radio("Tema do aplicativo", ["🌙 Noite", "☀️ Dia"],
                         horizontal=True, key="theme_sel")
        if theme != st.session_state["theme_mode"]:
            st.session_state["theme_mode"] = theme
            st.rerun()
        st.caption("Aplicado em todo o aplicativo.")

        st.divider()
        st.subheader("👤 Conta")
        st.markdown(f"""
        <div class="plan-card">
            <h4>{usuario_nome}</h4>
            <p>{usuario_email}</p>
        </div>""", unsafe_allow_html=True)
        if owner:
            st.success("🛡️ Dev — Pro permanente")
        elif is_pro:
            st.success("⭐ Pro ativo")
        else:
            st.info("🆓 Plano Gratuito — limite de 10 trades")

    with c_right:
        st.subheader("🔗 Compartilhar")
        app_url = "https://meu-trade-top.streamlit.app"
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
            """, unsafe_allow_html=True)

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
            """, unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 Sair da conta", use_container_width=True):
            st.logout()
