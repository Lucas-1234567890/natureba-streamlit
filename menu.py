from sidebar import *
from paginas.dashboard import *
import streamlit as st
from paginas import produtos
from paginas import vendas
from paginas import configuracao
from paginas import estoque
from paginas import custos
from paginas import receitas
from auth import user_management_interface, get_current_user

# Configuração da página 
st.set_page_config(
    page_title="Natureba - Gestão de Padaria",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #5C977C, #7FBFA0);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        font-weight: bold;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #5C977C;
        margin-bottom: 1rem;
    }
    .quick-action-card {
        background: linear-gradient(135deg, #5C977C 0%, #7FBFA0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .quick-action-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    .user-welcome {
        background: linear-gradient(90deg, #5C977C, #7FBFA0);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def menu():
    escolha = sidebar_navegacao()
    
    # Saudação personalizada
    user = get_current_user()
    nome = user.get('nome_completo', 'Usuário')
    st.markdown(f'<div class="user-welcome">👋 Bem-vindo(a), <strong>{nome}</strong>!</div>', unsafe_allow_html=True)

    st.markdown('<div class="main-header">🍀 Natureba - Sistema de Gestão</div>', unsafe_allow_html=True)

    # Roteamento otimizado (sem relatórios)
    if escolha == "🏠 Dashboard":
        dashboard()
    elif escolha == "🥖 Produtos":
        produtos.modulo_produtos()
    elif escolha == "📋 Receitas & Produção":
        receitas.modulo_receitas()
    elif escolha == "💰 Vendas":
        vendas.modulo_vendas()
    elif escolha == "📦 Estoque":
        estoque.modulo_estoque()
    elif escolha == "⚙️ Configurações":
        configuracao.modulo_configuracao()
    elif escolha == '💸 Custos Fixos':
        custos.custos_fixos_page()
    elif escolha == "👥 Usuários":
        user_management_interface()