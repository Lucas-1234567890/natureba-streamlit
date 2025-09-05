import streamlit as st

def sidebar_navegacao():
    st.sidebar.markdown("### 🍀 Natureba")
    st.sidebar.markdown("*Sistema de Gestão para Padaria*")

    menu_de_opccoes = [
        "🏠 Dashboard",
        "🥖 Produtos",
        "💰 Vendas",
        "📊 Relatórios",
        "🔃 Produção",
        "📦 Estoque",
        "⚙️ Configurações"
    ]

    escolha = st.sidebar.selectbox("Navegação", menu_de_opccoes)

    return escolha