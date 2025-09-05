import streamlit as st

def sidebar_navegacao():
    st.sidebar.markdown("### 🍀 Natureba")
    st.sidebar.markdown("*Sistema de Gestão para Padaria*")

    menu_de_opcoes = [
        "🏠 Dashboard",
        "🥖 Produtos",
        "💰 Vendas",
        "📊 Relatórios",
        "🔃 Produção",
        "📦 Estoque",
        "⚙️ Configurações"
    ]

    escolha = st.sidebar.selectbox("Navegação", menu_de_opcoes)

    # Expander para mostrar os links só quando clicar
    with st.sidebar.expander("👨‍💻 Feito por Lucas Amorim"):
        st.markdown("Siga-me nas redes sociais:")
        st.markdown("[LinkedIn](https://www.linkedin.com/in/lucas-amorim-powerbi/)")
        st.markdown("[Portfólio Xperiun](https://app.xperiun.com/in/lucas-amorim-portf%C3%B3lio)")
        st.markdown("[GitHub](https://github.com/Lucas-1234567890)")
        st.markdown("[Instagram](https://www.instagram.com/engdados.lucas_amorim/)")

    return escolha
