import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Gerenciador de Trades Pro", page_icon="📈", layout="wide")

# Inicializar dados na memória do navegador
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Data Abertura", "Ativo", "Tipo", "Volume", "Preço Entrada", "Preço Fechamento", "Lucro"
    ])

st.title("📈 Meu Gerenciador de Trades Web")

# --- FORMULÁRIO DE ENTRADA ---
with st.expander("➕ Registrar Novo Trade", expanded=True):
    with st.form("novo_trade"):
        c1, c2, c3 = st.columns(3)
        ativo = c1.text_input("Ativo")
        tipo = c2.selectbox("Tipo", ["buy", "sell"])
        volume = c3.number_input("Volume", value=0.01)
        
        c4, c5, c6 = st.columns(3)
        p_in = c4.number_input("Preço Entrada")
        p_out = c5.number_input("Preço Fechamento")
        lucro = c6.number_input("Lucro (USD)")
        
        if st.form_submit_button("Salvar Trade"):
            novo = pd.DataFrame([{
                "Data Abertura": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Ativo": ativo, "Tipo": tipo, "Volume": volume,
                "Preço Entrada": p_in, "Preço Fechamento": p_out, "Lucro": lucro
            }])
            st.session_state.trades = pd.concat([st.session_state.trades, novo], ignore_index=True)
            st.rerun()

# --- DASHBOARD ---
if not st.session_state.trades.empty:
    df = st.session_state.trades
    total_lucro = df["Lucro"].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Lucro Total", f"$ {total_lucro:.2f}")
    col2.metric("Total de Trades", len(df))
    
    # Gráfico de Lucro
    fig = px.line(df, y=df["Lucro"].cumsum(), title="Curva de Patrimônio", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    st.dataframe(df, use_container_width=True)
    
    # Botão para baixar CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Relatório CSV", csv, "trades.csv", "text/csv")
else:
    st.info("Nenhum trade registrado ainda. Use o formulário acima!")
