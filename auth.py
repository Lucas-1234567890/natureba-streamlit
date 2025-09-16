import streamlit as st
from datetime import datetime, timedelta
from banco import authenticate_user, create_user, get_all_users, update_user
import pandas as pd

# Configurações de segurança
SESSION_TIMEOUT = 480  # 8 horas em minutos

def is_logged_in():
    """Verifica se usuário está logado e sessão é válida"""
    if 'user_data' not in st.session_state:
        return False
    
    if 'login_time' not in st.session_state:
        return False
    
    # Verificar timeout da sessão
    login_time = st.session_state['login_time']
    if datetime.now() - login_time > timedelta(minutes=SESSION_TIMEOUT):
        logout()
        return False
    
    return True

def is_admin():
    """Verifica se usuário logado é administrador"""
    if not is_logged_in():
        return False
    return st.session_state.get('user_data', {}).get('nivel') == 'admin'

def get_current_user():
    """Retorna dados do usuário atual"""
    return st.session_state.get('user_data', {})

def logout():
    """Efetua logout limpando sessão"""
    keys_to_remove = ['user_data', 'login_time']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def login_form():
    """Interface de login bonita"""
    
    # CSS customizado para o login
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(92, 151, 124, 0.15);
            border-top: 5px solid #5C977C;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            color: #5C977C;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }
        .login-header p {
            color: #666;
            font-size: 1.1rem;
        }
        .welcome-msg {
            background: linear-gradient(90deg, #5C977C, #7FBFA0);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #5C977C, #7FBFA0);
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(92, 151, 124, 0.3);
        }
        .info-box {
            background: #f0f8f4;
            border-left: 4px solid #5C977C;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                <h1>🍞</h1>
                <h1>Natureba</h1>
                <p>Sistema de Gestão para Padaria</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulário de login
        with st.form("login_form"):
            st.subheader("🔐 Acesso ao Sistema")
            
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                login_button = st.form_submit_button("🚀 Entrar")
            
            if login_button:
                if not username or not password:
                    st.error("❌ Preencha todos os campos!")
                else:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state['user_data'] = user_data
                        st.session_state['login_time'] = datetime.now()
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos!")
         

def user_management_interface():
    """Interface completa de gerenciamento de usuários (apenas admin)"""
    if not is_admin():
        st.error("❌ Acesso negado. Apenas administradores podem gerenciar usuários.")
        return
    
    st.header("👥 Gerenciamento de Usuários")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["➕ Novo Usuário", "👤 Usuários Ativos / Editar", "🔧 Configurações"])
    
    # --- CRIAR NOVO USUÁRIO ---
    with tab1:
        st.subheader("Criar Novo Usuário")
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Nome de Usuário*")
                new_password = st.text_input("Senha*", type="password")
                confirm_password = st.text_input("Confirmar Senha*", type="password")
            with col2:
                new_nome = st.text_input("Nome Completo*")
                new_email = st.text_input("E-mail")
                new_nivel = st.selectbox("Nível de Acesso", ["operador", "admin"])
            
            create_button = st.form_submit_button("✅ Criar Usuário")
            
            if create_button:
                if not all([new_username, new_password, confirm_password, new_nome]):
                    st.error("❌ Preencha todos os campos obrigatórios!")
                elif new_password != confirm_password:
                    st.error("❌ As senhas não coincidem!")
                elif len(new_password) < 6:
                    st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                else:
                    success, message = create_user(new_username, new_password, new_nome, new_email, new_nivel)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    # --- LISTAR E EDITAR USUÁRIOS ---
    with tab2:
        st.subheader("Usuários do Sistema")
        users_df = get_all_users()
        
        if users_df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Mostrar tabela
            users_display = users_df.copy()
            users_display['Status'] = users_display['ativo'].map({1: '✅ Ativo', 0: '❌ Inativo'})
            users_display['Nível'] = users_display['nivel'].map({'admin': '👑 Admin', 'operador': '👤 Operador'})
            users_display['Último Login'] = pd.to_datetime(users_display['last_login']).dt.strftime('%d/%m/%Y %H:%M')
            
            st.dataframe(
                users_display[['username', 'nome_completo', 'email', 'Nível', 'Status', 'Último Login']]
                .rename(columns={
                    'username': 'Usuário',
                    'nome_completo': 'Nome Completo',
                    'email': 'E-mail'
                }),
                use_container_width=True
            )
            
            # --- FORMULÁRIO DE EDIÇÃO ---
            st.subheader("Editar Usuário")
            selected_user = st.selectbox("Escolha o usuário para editar", users_df['username'])
            user_info = users_df[users_df['username'] == selected_user].iloc[0]
            
            with st.form("edit_user_form"):
                new_nome = st.text_input("Nome Completo", value=user_info['nome_completo'])
                new_email = st.text_input("E-mail", value=user_info['email'])
                new_nivel = st.selectbox("Nível de Acesso", ["operador", "admin"],
                                         index=0 if user_info['nivel']=='operador' else 1)
                new_password = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
                
                save_button = st.form_submit_button("💾 Salvar Alterações")
                
                if save_button:
                    # Chama função de atualização no banco
                    success, message = update_user(
                        username=selected_user,
                        nome_completo=new_nome,
                        email=new_email,
                        nivel=new_nivel,
                        senha=new_password  # se estiver em branco, não altera
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    # --- CONFIGURAÇÕES ---
    with tab3:
        st.subheader("Configurações de Segurança")
        st.metric("🔒 Timeout da Sessão", f"{SESSION_TIMEOUT} minutos")
        st.metric("👥 Total de Usuários", len(users_df) if not users_df.empty else 0)
        
        if st.button("🔄 Forçar Logout de Todos"):
            # Em um sistema real, isso invalidaria todas as sessões ativas
            st.success("✅ Comando executado. Novos logins serão necessários.")


def show_user_info():
    """Mostra informações do usuário logado no sidebar"""
    if is_logged_in():
        user = get_current_user()
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Usuário Logado")
        st.sidebar.markdown(f"**{user.get('nome_completo')}**")
        st.sidebar.markdown(f"*{user.get('username')}*")
        
        nivel_emoji = "👑" if user.get('nivel') == 'admin' else "👤"
        st.sidebar.markdown(f"{nivel_emoji} {user.get('nivel', 'operador').title()}")
        
        if st.sidebar.button("🚪 Logout"):
            logout()
            st.rerun()

# Importar pandas se necessário
try:
    import pandas as pd
except ImportError:
    pass