import streamlit as st
from auth import show_user_info, is_admin

def sidebar_navegacao():
    st.sidebar.markdown("### 🍀 Natureba")
    st.sidebar.markdown("*Sistema de Gestão para Padaria*")
    st.sidebar.markdown("---")

    # Inicializa menu_escolha na sessão
    if 'menu_escolha' not in st.session_state:
        st.session_state['menu_escolha'] = "🏠 Dashboard"

    # -------------------
    # ATALHOS RÁPIDOS (como radio buttons)
    # -------------------
    st.sidebar.markdown("### ⚡ Acesso Rápido")
    atalhos = ["🏠 Dashboard", "💰 Vendas", "📋 Receitas & Produção"]
    
    # Radio para atalhos
    escolha_atalho = st.sidebar.radio(
        "Escolha Rápida",
        options=atalhos,
        index=atalhos.index(st.session_state['menu_escolha']) if st.session_state['menu_escolha'] in atalhos else 0
    )
    st.session_state['menu_escolha'] = escolha_atalho

    st.sidebar.markdown("---")
    
    # -------------------
    # MENU COMPLETO
    # -------------------
    st.sidebar.markdown("### 📂 Menu Completo")
    menu_completo = ["🥖 Produtos", "📦 Estoque", "💸 Custos Fixos", "⚙️ Configurações"]
    if is_admin():
        menu_completo.append("👥 Usuários")
    
    escolha_menu = st.sidebar.selectbox(
        "Outras Opções",
        ["-- selecione --"] + menu_completo,
        index=0
    )
    
    # Se usuário escolheu algo, atualiza sessão
    if escolha_menu != "-- selecione --":
        st.session_state['menu_escolha'] = escolha_menu

    # -------------------
    # INFORMAÇÕES DO USUÁRIO
    # -------------------
    st.sidebar.markdown("---")
    show_user_info()
    
    # -------------------
    # LINKS DO DESENVOLVEDOR
    # -------------------
    st.sidebar.markdown("---")
    with st.sidebar.expander("👨‍💻 Desenvolvedor"):
        st.markdown("**Lucas Amorim**")
        st.markdown("[LinkedIn](https://www.linkedin.com/in/lucas-amorim-powerbi/) | [GitHub](https://github.com/Lucas-1234567890)")
        st.markdown("[Portfolio](https://app.xperiun.com/in/lucas-amorim-portf%C3%B3lio) | [Instagram](https://www.instagram.com/engdados.lucas_amorim/)")
    
    return st.session_state['menu_escolha']
