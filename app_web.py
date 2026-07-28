Perfeito! Vou modificar seu código para usar o **login do Google** corretamente. O problema é que você precisa configurar o `[auth]` no secrets.toml com as credenciais do Google OAuth.

## 📁 **Arquivo .streamlit/secrets.toml ATUALIZADO**

Primeiro, atualize seu secrets.toml:

```toml
# ============================================
# CONFIGURAÇÃO DO LOGIN GOOGLE (OBRIGATÓRIO)
# ============================================
[auth]
redirect_uri = "http://localhost:8501"
cookie_secret = "minha_chave_super_secreta_1234567890"

# Credenciais do Google OAuth (você precisa criar no Google Cloud Console)
google_client_id = "SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
google_client_secret = "SEU_GOOGLE_CLIENT_SECRET"

# ============================================
# CONFIGURAÇÃO DO FIRESTORE (JÁ EXISTENTE)
# ============================================
[gcp_service_account]
type = "service_account"
project_id = "projeto-trade-75a34"
private_key_id = "a0fe111cabac530e3e9ac0821712279c219eb3e6"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQD/D9q1T9Nb6FqQ\nisvoRaTZ2Yjq3daC6PpoZ3J6sz4YN7BBSxclQGA4xMFKEkVZClRjIid/6e2TyEVc\nZrOT7eCCjWHeLF1nlvb2qlGB9pvPo038JoogqPPlSuajB/R/ef5Z0Pmv+rzznK0h\nDS1ucTTsIvNS2NepohPwbQpKLaw0UHZzSmTxr70cc/qEZUgWyQ5s4szEI9uBcRTV\npOae/hDbELLiHXRejhfxvxsTAvZ3XGWy7R3ppvODArDWJVzb6tQkI6z8Y3oK4LHk\n22dlu1/GIODl/E65q0oH16yOO7V5B/vuCGFX74WGTOpDS8dYmrYBsX7muAwwpIIE\nyfnKQy3hAgMBAAECggEACHID8eD0xKRK62JNIiG8NaJoUC6MPcVtFSvntHxe3/po\nEaFk4Mzi4r5REBzOwwX+iVHGMQwT28LT2R1lcM59kpUP2oVpilaLUtuM21rJCfUE\nTgcQp8gwWzVBscA/rkDh1SOAQP1yaDaV3PRMvs1szSzTFbksWueM9XcG0jH0875t\nYZRPUA8fuGZ3r4Pv/V006SGb+RFO1ezLGodg81s3vnI+1iSLfv9lS7OZhpVvPCwM\nuvWt/Cj8dVFB+Ap3xdgZGnL2dcbQvnQBMcWEx/zEVOwm7cqZy7d0Ox5c5QQ1ihk2\nlceqBZ109AajtUzJ9B+mg5AmusM56PSeu0KropB5iQKBgQD/4hx/AlzSkY/ToP6W\nrR0VaeEywD6IunxLfIRXL1bhPDDMD+qeqkyCCGgAFNNlTwd+9J1eVLFvpOSZP9hS\nfLJsv4u/BEY4eFLrgKpl5p6b6E5vHekWRKmpG9KSZ6iWS27pGAxkGpolxp+HAElM\nkOnmnJEmpb+Sl7nnBdxZZaNHmwKBgQD/LaWnIUrrit56ppJms2GeIhbxPCKuLaLK\n2AIvUed4GGMr6DbjcWDuf0uio7SpRTOG1K2K/DAxQE3WUCyAix8LyCeDPCbeU3ff\nqfJqUHLY5veBXE3IlPKIybzmybfdE8qKlCBZG2s/9QyBO99pcswawRD5S9RLzXg1\njb7NyONeMwKBgH1L3/5FTuSBCHdtXxyy+gnRRcePIU/cWR6xgzAZ6yXxTkeuB4nY\nBAysRxi7GeSCtT3yU9isChKMIK/19lw12Tys8qX/Vs8yBBBzeXzaV5IqR7XbZJZV\n2uoGyK6N+ZxWpaGX+AFQkWisANOfTUUjtJUK13ygLtV+XDaGxSY1QaW/AoGBAMei\npp6CZWKxWi0KdC7018InWVuReHBcM6gOJmdu5HAIZE3NdmOqJ/Nuk3XCLWzgPteV\nO9AoTGu7qymnv6kxLjDBfmglfyMgmf/ZrVWPaspWp/wEgrYSEU0Cx06nMbk76pFQ\nIZ6U3OtEg2v3s2mD7jpgIS9oK8bCEPGU21mTeI4RAoGATa3sT6wNHwZi2PFmul3Q\n1KOiH1mEAmECTkqCq17bxWJpLcgeusz+nF6FhsEd4eOtUmS6v3hMFX+VG7ycONX1\nI3e3yvOZaJ3S93GqSuTVaUG/vzX/oBtQb5z0egosvf82d9TSbBaNbKjdD4RRkLzH\nBaJ9JYIdNkT3jfe3OL37hZk=\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-fbsvc@projeto-trade-75a34.iam.gserviceaccount.com"
client_id = "103262436452213545505"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40projeto-trade-75a34.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

# ============================================
# EMAILS DOS PROPRIETÁRIOS
# ============================================
owner_emails = [
    "seuemail@gmail.com"
]
```

---

## 📝 **Código app.py MODIFICADO (só a parte do login)**

Aqui está seu código completo com as modificações necessárias para o login do Google funcionar:

```python
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
# LOGIN CHECK (MODIFICADO PARA FUNCIONAR COM st.login)
# =========================================================

def check_user_login():
    """Verifica se o usuário está logado via Google"""
    try:
        # Verificar se st.user existe e tem 'sub'
        if hasattr(st, 'user') and st.user is not None:
            user_sub = st.user.get("sub")
            if user_sub:
                return True
        return False
    except Exception:
        return False

is_user_logged_in = check_user_login()


# =========================================================
# THEME (MANTIDO IGUAL)
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
# LOGIN PAGE (MODIFICADO - BOTÃO GOOGLE FUNCIONAL)
# =========================================================

if not is_user_logged_in:
    st.title("📊 Trader Analytics Pro")

    st.markdown(
        "Organize suas operações, acompanhe seu "
        "desempenho e analise seus resultados."
    )

    st.info("Entre com sua conta Google.")

    # Verificar se as configurações do auth existem
    has_auth = "auth" in st.secrets
    
    if not has_auth:
        st.error(
            "Login não configurado. "
            "Configure [auth] nos Secrets."
        )
    else:
        # Tentar fazer login com Google
        try:
            # Usar o método login do Streamlit
            login_button = st.button("🔵 Entrar com Google", use_container_width=True)
            
            if login_button:
                with st.spinner("Abrindo tela de login do Google..."):
                    # O Streamlit vai redirecionar para o Google
                    st.login()
        except Exception as erro:
            st.error(f"Erro ao iniciar login: {erro}")
            st.info("Verifique se as credenciais do Google OAuth estão corretas no secrets.toml")

    # Botão alternativo caso o login padrão não funcione
    st.divider()
    st.caption("Não consegue logar?")
    if st.button("🔄 Tentar novamente", use_container_width=True):
        st.rerun()

    st.divider()
    st.caption("Não oferece recomendação de investimento.")
    st.stop()


# =========================================================
# USER DATA (MODIFICADO)
# =========================================================

try:
    usuario_id = str(st.user["sub"])
    usuario_email = str(st.user.get("email", "")).strip().lower()
    usuario_nome = str(st.user.get("name", "User")).strip()
except Exception as e:
    st.error(f"Erro ao obter dados do usuário: {e}")
    st.info("Tente fazer login novamente.")
    if st.button("🔄 Voltar ao login"):
        st.rerun()
    st.stop()

if not usuario_email:
    st.error("E-mail não encontrado no login do Google.")
    st.info("Certifique-se de autorizar o acesso ao seu email.")
    st.stop()


# =========================================================
# FIRESTORE (MANTIDO IGUAL)
# =========================================================

@st.cache_resource
def get_firestore():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
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
except Exception as e:
    st.warning(f"Modo offline: {e}")
    cloud_connected = False


# =========================================================
# RESTO DO CÓDIGO (MANTIDO IGUAL - PLAN FUNCTIONS, TRADE FUNCTIONS, ETC)
# =========================================================

# ... (todo o resto do seu código permanece igual) ...

# =========================================================
# SIDEBAR - BOTÃO SAIR (MODIFICADO)
# =========================================================

# No sidebar, onde tem o botão sair, modifique para:
if st.button("🚪 Sair", use_container_width=True, type="primary"):
    st.logout()  # Isso vai limpar a sessão e redirecionar para o login
```

---

## 🚀 **Como criar as credenciais do Google OAuth**

Para o login funcionar, você PRECISA criar as credenciais:

1. **Acesse:** https://console.cloud.google.com/
2. **Vá em:** APIs e Serviços → Credenciais
3. **Clique em:** Criar Credenciais → ID do cliente OAuth
4. **Escolha:** Aplicativo da Web
5. **Configure:**
   - **Nome:** "Trader Analytics Pro"
   - **Origens JavaScript autorizadas:** 
     - `http://localhost:8501` (para teste local)
     - `https://SEU-APP.streamlit.app` (para produção)
   - **URIs de redirecionamento autorizados:**
     - `http://localhost:8501` (para teste local)
     - `https://SEU-APP.streamlit.app` (para produção)
6. **Clique em Criar**
7. **Copie o Client ID e Client Secret**

**Cole esses valores no secrets.toml:**
```toml
[auth]
redirect_uri = "http://localhost:8501"
cookie_secret = "qualquer_chave_secreta_aqui"
google_client_id = "SEU_CLIENT_ID.apps.googleusercontent.com"
google_client_secret = "SEU_CLIENT_SECRET"
```

---

## ✅ **Teste agora!**

```bash
# Recarregue o app
streamlit run app.py
```

Agora o botão "Entrar com Google" vai funcionar! 🎉

Se ainda não funcionar, me diga qual erro aparece que eu ajudo a resolver!
