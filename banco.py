import sqlite3
import streamlit as st
import pandas as pd

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
            custo_producao REAL NOT NULL,
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

     # Tabela de receitas (relaciona produtos com ingredientes)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            ingrediente_id INTEGER,
            quantidade REAL NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id)
        )
    ''')

    # Tabela de produção diária
    conn.execute('''
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            custo_total REAL NOT NULL,
            data_producao DATE NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
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

    