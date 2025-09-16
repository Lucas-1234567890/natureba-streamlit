import sqlite3
import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

# Configuração de segurança para senhas
SALT = "natureba_padaria_2025"

def hash_password(password):
    """Cria hash seguro da senha com salt"""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

@st.cache_resource
def iniciar_database():
    conn = sqlite3.connect('natureba.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Tabela de produtos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            preco_venda REAL NOT NULL,
            categoria TEXT NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de ingredientes
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            preco_kg REAL NOT NULL,
            estoque_atual REAL DEFAULT 0,
            unidade TEXT DEFAULT 'kg',
            fornecedor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de vendas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            total REAL NOT NULL,
            data_venda DATE NOT NULL,
            hora_venda TIME DEFAULT CURRENT_TIME,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')

    # Tabela de custos operacionais
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custos_operacionais (
            id INTEGER PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data_custo DATE NOT NULL,
            recorrente BOOLEAN DEFAULT 0
        )
    ''')

    # Tabela de movimentações de estoque
    conn.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
            id INTEGER PRIMARY KEY,
            ingrediente_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,      -- valores esperados: 'entrada' ou 'saida'
            quantidade REAL NOT NULL,
            motivo TEXT,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id)
        )
    ''')

    # Tabela de usuários - NOVA
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome_completo TEXT NOT NULL,
            email TEXT,
            nivel TEXT DEFAULT 'operador',  -- 'admin' ou 'operador'
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    conn.commit()
    return conn
    
# Funções auxiliares
def executar_query(query, params=None):
    """Executa uma query no banco de dados"""
    conn = iniciar_database()
    if params:
        result = conn.execute(query, params)
    else:
        result = conn.execute(query)
    
    if query.strip().upper().startswith('SELECT'):
        return result.fetchall()
    else:
        conn.commit()
        return result.lastrowid

def get_dataframe(query, params=None):
    """Retorna um DataFrame a partir de uma query"""
    conn = iniciar_database()
    if params:
        return pd.read_sql_query(query, conn, params=params)
    else:
        return pd.read_sql_query(query, conn)

# ==============================
# FUNÇÕES ESPECÍFICAS DE USUÁRIOS
# ==============================

def authenticate_user(username, password):
    """Autentica usuário e retorna dados se válido"""
    conn = iniciar_database()
    
    password_hash = hash_password(password)
    user = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password_hash = ? AND ativo = 1",
        (username, password_hash)
    ).fetchone()
    
    if user:
        # Atualizar último login
        conn.execute(
            "UPDATE usuarios SET last_login = ? WHERE id = ?",
            (datetime.now(), user['id'])
        )
        conn.commit()
        return dict(user)
    
    return None

def create_user(username, password, nome_completo, email="", nivel="operador"):
    """Cria novo usuário"""
    try:
        password_hash = hash_password(password)
        executar_query(
            "INSERT INTO usuarios (username, password_hash, nome_completo, email, nivel) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, nome_completo, email, nivel)
        )
        return True, "Usuário criado com sucesso"
    except sqlite3.IntegrityError:
        return False, "Nome de usuário já existe"
    except Exception as e:
        return False, f"Erro ao criar usuário: {e}"

def get_all_users():
    """Retorna todos os usuários cadastrados"""
    return get_dataframe("""
        SELECT id, username, nome_completo, email, nivel, ativo, 
               created_at, last_login
        FROM usuarios 
        ORDER BY created_at DESC
    """)

def update_user_status(user_id, ativo):
    """Ativa/desativa usuário"""
    try:
        executar_query(
            "UPDATE usuarios SET ativo = ? WHERE id = ?",
            (ativo, user_id)
        )
        return True, "Status do usuário atualizado"
    except Exception as e:
        return False, f"Erro ao atualizar usuário: {e}"

def change_user_password(user_id, new_password):
    """Altera senha do usuário"""
    try:
        password_hash = hash_password(new_password)
        executar_query(
            "UPDATE usuarios SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        return True, "Senha alterada com sucesso"
    except Exception as e:
        return False, f"Erro ao alterar senha: {e}"

def delete_user(user_id):
    """Exclui usuário (use com cuidado!)"""
    try:
        # Verificar se não é o último admin
        admin_count = executar_query(
            "SELECT COUNT(*) FROM usuarios WHERE nivel = 'admin' AND ativo = 1"
        )[0][0]
        
        user_nivel = executar_query(
            "SELECT nivel FROM usuarios WHERE id = ?", (user_id,)
        )[0][0]
        
        if user_nivel == 'admin' and admin_count <= 1:
            return False, "Não é possível excluir o último administrador"
        
        executar_query("DELETE FROM usuarios WHERE id = ?", (user_id,))
        return True, "Usuário excluído com sucesso"
    except Exception as e:
        return False, f"Erro ao excluir usuário: {e}"
    
def update_user(username, nome_completo=None, email=None, nivel=None, senha=None):
    """
    Atualiza os dados de um usuário.
    Se senha for None ou '', não altera.
    """
    try:
        # Buscar usuário pelo username
        user = executar_query(
            "SELECT * FROM usuarios WHERE username = ?",
            (username,)
        )
        if not user:
            return False, "Usuário não encontrado"
        
        user_id = user[0]['id']
        
        # Atualizar campos básicos
        if nome_completo:
            executar_query(
                "UPDATE usuarios SET nome_completo = ? WHERE id = ?",
                (nome_completo, user_id)
            )
        if email is not None:
            executar_query(
                "UPDATE usuarios SET email = ? WHERE id = ?",
                (email, user_id)
            )
        if nivel:
            executar_query(
                "UPDATE usuarios SET nivel = ? WHERE id = ?",
                (nivel, user_id)
            )
        # Atualizar senha se fornecida
        if senha:
            change_user_password(user_id, senha)
        
        return True, "Usuário atualizado com sucesso"
    except Exception as e:
        return False, f"Erro ao atualizar usuário: {e}"
