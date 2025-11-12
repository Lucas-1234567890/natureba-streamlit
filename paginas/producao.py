import streamlit as st
import pandas as pd
import sqlite3

def modulo_producao():
    conn = sqlite3.connect('natureba.db', check_same_thread=False)

    st.header("🥖 Gestão de Produção - Natureba")

    tab1, tab2 = st.tabs(["➕ Registrar Produção", "📋 Estoque Atual"])

    # ----------------------
    # Aba 1: Registrar Produção
    # ----------------------
    with tab1:
        st.subheader("Registrar nova produção")
        
        # Puxar produtos ativos
        produtos = pd.read_sql_query("SELECT id, nome FROM produtos WHERE ativo=1 ORDER BY nome", conn)
        produto_dict = {row['nome']: row['id'] for _, row in produtos.iterrows()}
        
        if produtos.empty:
            st.info("Nenhum produto ativo encontrado.")
        else:
            with st.form("form_producao"):
                col1, col2 = st.columns([3,1])
                with col1:
                    produto_nome = st.selectbox("Produto", options=list(produto_dict.keys()))
                with col2:
                    quantidade = st.number_input("Quantidade produzida", min_value=1, step=1)
                
                submitted = st.form_submit_button("✅ Registrar Produção")
                if submitted:
                    produto_id = produto_dict[produto_nome]
                    
                    estoque = conn.execute(
                        "SELECT quantidade_atual FROM estoque_pronto WHERE produto_id=?",
                        (produto_id,)
                    ).fetchone()
                    
                    if estoque:
                        conn.execute(
                            "UPDATE estoque_pronto SET quantidade_atual = quantidade_atual + ?, ultima_atualizacao = CURRENT_TIMESTAMP WHERE produto_id=?",
                            (quantidade, produto_id)
                        )
                    else:
                        conn.execute(
                            "INSERT INTO estoque_pronto (produto_id, quantidade_atual) VALUES (?, ?)",
                            (produto_id, quantidade)
                        )
                    conn.commit()
                    st.success(f"{quantidade} unidades de {produto_nome} adicionadas ao estoque.")

    # ----------------------
    # Aba 2: Estoque Atual
    # ----------------------
    with tab2:
        st.subheader("Estoque Atual de Produtos Prontos")
        df_estoque = pd.read_sql_query('''
            SELECT p.nome AS produto, e.quantidade_atual, e.ultima_atualizacao
            FROM estoque_pronto e
            JOIN produtos p ON e.produto_id = p.id
            ORDER BY p.nome
        ''', conn)
        
        if df_estoque.empty:
            st.info("Estoque vazio.")
        else:
            st.dataframe(df_estoque, use_container_width=True)
