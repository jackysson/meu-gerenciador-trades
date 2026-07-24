import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Trader Analytics Pro", page_icon="📊", layout="wide")

# 2. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Tenta ler da nuvem
        return conn.read(ttl="0s")
    except:
        # Se falhar, cria o banco do zero com TODAS as colunas que você pediu
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"])

if 'df_trades' not in st.session_state:
    st.session_state.df_trades = load_data()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🛡️ Gestão de Dados")
    # Botão para limpar a memória se o backup antigo estiver travando tudo
    if st.button("🚨 Resetar Memória Local"):
        st.session_state.df_trades = load_data()
        st.rerun()
    
    st.divider()
    st.subheader("💾 Backup Manual")
    csv_data = st.session_state.df_trades.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Meus Dados (CSV)", csv_data, "meus_trades.csv", "text/csv")

# 4. PROCESSAMENTO (O CORAÇÃO DO SISTEMA)
df = st.session_state.df_trades

# FORÇAR AS COLUNAS (Isso evita o erro do backup antigo)
for c in ["Data", "Ativo", "Tipo", "Volume", "Entrada", "Saída", "SL", "TP", "Lucro", "Obs"]:
    if c not in df.columns:
        df[c] = 0

df["Lucro"] = pd.to_numeric(df["Lucro"], errors='coerce').fillna(0)
total_profit = df["Lucro"].sum()
equity = 20.0 + total_profit # Capital inicial fixo em 20

# 5. DASHBOARD
st.title("📊 Trader Strategy Analytics Pro")
c1, c2, c3 = st.columns(3)
c1.metric("💰 Equity", f"$ {equity:,.2f}")
c2.metric("📈 Lucro Total", f"$ {total_profit:,.2f}")
c3.metric("🎯 Total Trades", len(df))

# 6. ABAS
tab1, tab2, tab3 = st.tabs(["📝 Histórico Real", "➕ Novo Trade", "🚀 Gráficos"])

with tab1:
    st.subheader("Seus Trades Salvos")
    # Mostra o histórico do mais novo para o mais antigo
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

with tab2:
    with st.form("form_v3", clear_on_submit=True):
        st.subheader("Registrar Operação")
        col1, col2, col3 = st.columns(3)
        ativo = col1.text_input("Ativo", value="USDJPY")
        tipo = col2.selectbox("Tipo", ["buy", "sell"])
        lucro = col3.number_input("Lucro (USD)", format="%.2f")
        
        st.write("---")
        col4, col5, col6, col7 = st.columns(4)
        p_in = col4.number_input("Entrada", format="%.3f")
        p_out = col5.number_input("Saída", format="%.3f")
        sl = col6.number_input("SL", format="%.3f")
        tp = col7.number_input("TP", format="%.3f")
        
        if st.form_submit_button("💾 SALVAR AGORA"):
            novo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ativo": ativo, "Tipo": tipo, "Volume": 0.01,
                "Entrada": p_in, "Saída": p_out, "SL": sl, "TP": tp,
                "Lucro": lucro, "Obs": ""
            }])
            
            # ATUALIZA A MEMÓRIA NA HORA
            st.session_state.df_trades = pd.concat([st.session_state.df_trades, novo], ignore_index=True)
            
            # TENTA SALVAR NA NUVEM
            try:
                conn.update(data=st.session_state.df_trades)
                st.success("✅ SALVO NA NUVEM E NO HISTÓRICO!")
            except:
                st.warning("⚠️ Salvo no Histórico, mas a Nuvem falhou (Secrets).")
            
            st.rerun() # ISSO FORÇA O HISTÓRICO A ATUALIZAR

with tab3:
    if not df.empty:
        equity_curve = np.cumsum([20.0] + df["Lucro"].tolist())
        st.plotly_chart(px.area(y=equity_curve, title="Crescimento"), use_container_width=True)
