import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

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

    # NOVA: Tabela de receitas (relaciona produtos com ingredientes)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER NOT NULL,
            ingrediente_id INTEGER NOT NULL,
            quantidade REAL NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id) ON DELETE CASCADE,
            UNIQUE(produto_id, ingrediente_id)
        )
    ''')

    # Tabela de vendas - Agrupamento por compra (pedido)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY,
            data_venda DATE NOT NULL,
            hora_venda TIME DEFAULT CURRENT_TIME,
            total REAL NOT NULL,
            observacao TEXT
        )
    ''')

    # NOVA: Tabela de itens de venda (detalhamento dos produtos vendidos)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            custo_variavel REAL DEFAULT 0,
            FOREIGN KEY (venda_id) REFERENCES vendas (id) ON DELETE CASCADE,
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
            tipo TEXT NOT NULL,
            quantidade REAL NOT NULL,
            motivo TEXT,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id)
        )
    ''')

    # Tabela de usuários
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome_completo TEXT NOT NULL,
            email TEXT,
            nivel TEXT DEFAULT 'operador',
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    conn.commit()
    return conn
    