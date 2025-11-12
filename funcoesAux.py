import hashlib
from banco import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime   

# ==============================
# CONSTANTES / CONFIGURAÇÕES
# ==============================
SALT = "natureba_padaria_2025"


# ==============================
# FUNÇÕES DE BANCO DE DADOS
# (conexão e wrappers)
# ==============================
@st.cache_resource
def iniciar_database():
    conn = sqlite3.connect('natureba.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Funções auxiliares de acesso ao DB
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
# FUNÇÕES AUXILIARES GERAIS
# (utilitários, formatação, hash)
# ==============================
def hash_password(password):
    """Cria hash seguro da senha com salt"""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def format_brl_currency(valor):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "R$ 0,00"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def format_brl_percent(valor):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "0,0%"
    s = f"{v:.1f}".replace(".", ",")
    return f"{s}%"


# ==============================
# FUNÇÕES DE USUÁRIOS
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
    """Atualiza os dados de um usuário"""
    try:
        user = executar_query(
            "SELECT * FROM usuarios WHERE username = ?",
            (username,)
        )
        if not user:
            return False, "Usuário não encontrado"
        
        user_id = user[0]['id']
        
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
        if senha:
            change_user_password(user_id, senha)
        
        return True, "Usuário atualizado com sucesso"
    except Exception as e:
        return False, f"Erro ao atualizar usuário: {e}"


# ==============================
# FUNÇÕES DE RECEITAS
# ==============================
def adicionar_item_receita(produto_id, ingrediente_id, quantidade):
    """Adiciona um ingrediente à receita de um produto"""
    try:
        executar_query(
            "INSERT INTO receitas (produto_id, ingrediente_id, quantidade) VALUES (?, ?, ?)",
            (produto_id, ingrediente_id, quantidade)
        )
        return True, "Ingrediente adicionado à receita"
    except sqlite3.IntegrityError:
        return False, "Este ingrediente já está na receita"
    except Exception as e:
        return False, f"Erro: {e}"

def remover_item_receita(receita_id):
    """Remove um ingrediente da receita"""
    try:
        executar_query("DELETE FROM receitas WHERE id = ?", (receita_id,))
        return True, "Ingrediente removido da receita"
    except Exception as e:
        return False, f"Erro ao remover da receita: {e}"

def get_receita_produto(produto_id):
    """Retorna a receita completa de um produto"""
    return get_dataframe("""
        SELECT r.id, r.quantidade, i.nome as ingrediente, 
               i.preco_kg, i.unidade, i.estoque_atual,
               (r.quantidade * i.preco_kg) as custo_item
        FROM receitas r
        JOIN ingredientes i ON r.ingrediente_id = i.id
        WHERE r.produto_id = ?
    """, (produto_id,))

def calcular_custo_produto(produto_id):
    """Calcula o custo variável total de um produto baseado na receita"""
    receita = get_receita_produto(produto_id)
    if receita.empty:
        return 0.0
    return float(receita['custo_item'].sum())

def verificar_disponibilidade_receita(produto_id, quantidade_producao):
    """Verifica se há estoque suficiente para produzir X unidades"""
    receita = get_receita_produto(produto_id)
    if receita.empty:
        return True, "Produto sem receita cadastrada"
    
    faltantes = []
    for _, item in receita.iterrows():
        necessario = item['quantidade'] * quantidade_producao
        if item['estoque_atual'] < necessario:
            faltantes.append(f"{item['ingrediente']}: falta {necessario - item['estoque_atual']:.2f} {item['unidade']}")
    
    if faltantes:
        return False, "Estoque insuficiente: " + ", ".join(faltantes)
    return True, "Estoque OK"

def baixar_estoque_por_receita(produto_id, quantidade_produzida):
    """Baixa o estoque dos ingredientes ao produzir/vender um produto"""
    receita = get_receita_produto(produto_id)
    if receita.empty:
        return True, "Sem receita cadastrada"
    
    try:
        for _, item in receita.iterrows():
            qtd_usar = item['quantidade'] * quantidade_produzida
            # Buscar ID do ingrediente
            ing_id = executar_query(
                "SELECT id FROM ingredientes WHERE nome = ?", (item['ingrediente'],)
            )[0]['id']
            
            # Baixar estoque
            executar_query(
                "UPDATE ingredientes SET estoque_atual = estoque_atual - ? WHERE id = ?",
                (qtd_usar, ing_id)
            )
            
            # Registrar movimentação
            executar_query(
                "INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, motivo) VALUES (?, 'saida', ?, ?)",
                (ing_id, qtd_usar, f"Produção/Venda: {quantidade_produzida}x produto ID {produto_id}")
            )
        
        return True, "Estoque baixado com sucesso"
    except Exception as e:
        return False, f"Erro ao baixar estoque: {e}"


# ==============================
# FUNÇÕES DE VENDAS (AGRUPAMENTO POR COMPRA)
# ==============================
def criar_venda(data_venda, itens, observacao=""):
    """
    Cria uma venda (compra/pedido) com múltiplos itens
    itens = lista de dicts: [{'produto_id': 1, 'quantidade': 2, 'preco_unitario': 5.0}, ...]
    """
    try:
        conn = iniciar_database()
        
        # Calcular total da venda
        total_venda = sum(item['quantidade'] * item['preco_unitario'] for item in itens)
        
        # Criar venda (pedido)
        venda_id = executar_query(
            "INSERT INTO vendas (data_venda, total, observacao) VALUES (?, ?, ?)",
            (data_venda, total_venda, observacao)
        )
        
        # Adicionar itens e processar estoque
        for item in itens:
            # Calcular custo variável
            custo_var = calcular_custo_produto(item['produto_id']) * item['quantidade']
            subtotal = item['quantidade'] * item['preco_unitario']
            
            # Inserir item
            executar_query(
                "INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal, custo_variavel) VALUES (?, ?, ?, ?, ?, ?)",
                (venda_id, item['produto_id'], item['quantidade'], item['preco_unitario'], subtotal, custo_var)
            )
            
            # Baixar estoque por receita
            baixar_estoque_por_receita(item['produto_id'], item['quantidade'])
        
        return True, "Venda registrada com sucesso", venda_id
    except Exception as e:
        return False, f"Erro ao registrar venda: {e}", None

def get_vendas_detalhadas(data_inicio, data_fim):
    """Retorna vendas com detalhamento de itens"""
    return get_dataframe("""
        SELECT 
            v.id as venda_id,
            v.data_venda,
            v.hora_venda,
            v.total,
            v.observacao,
            p.nome as produto,
            iv.quantidade,
            iv.preco_unitario,
            iv.subtotal,
            iv.custo_variavel,
            (iv.subtotal - iv.custo_variavel) as margem_contribuicao
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        JOIN produtos p ON iv.produto_id = p.id
        WHERE v.data_venda BETWEEN ? AND ?
        ORDER BY v.data_venda DESC, v.id DESC
    """, (data_inicio, data_fim))

def get_resumo_vendas(data_inicio, data_fim):
    """Retorna resumo de vendas agrupadas por pedido"""
    return get_dataframe("""
        SELECT 
            v.id,
            v.data_venda,
            v.hora_venda,
            v.total,
            COUNT(iv.id) as qtd_itens,
            SUM(iv.custo_variavel) as custo_total,
            (v.total - SUM(iv.custo_variavel)) as margem_total,
            v.observacao
        FROM vendas v
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        WHERE v.data_venda BETWEEN ? AND ?
        GROUP BY v.id
        ORDER BY v.data_venda DESC, v.id DESC
    """, (data_inicio, data_fim))

def get_resumo_vendas(data_inicio, data_fim):
    """Retorna resumo de vendas agrupadas por pedido"""
    return get_dataframe("""
        SELECT 
            v.id,
            v.data_venda,
            v.hora_venda,
            v.total,
            COUNT(iv.id) as qtd_itens,
            SUM(iv.custo_variavel) as custo_total,
            (v.total - SUM(iv.custo_variavel)) as margem_total,
            v.observacao
        FROM vendas v
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        WHERE v.data_venda BETWEEN ? AND ?
        GROUP BY v.id
        ORDER BY v.data_venda DESC, v.id DESC
    """, (data_inicio, data_fim))
