import streamlit as st
from banco import executar_query, get_dataframe

def modulo_produtos():
    st.header("📦 Gestão de Produtos")

    tab1, tab2 = st.tabs(["➕ Cadastrar Produto", "📋 Lista de Produtos"])

    # ----------------------
    # Aba 1: Cadastrar Produto
    # ----------------------
    with tab1:
        st.subheader('Cadastro de Produtos')
        with st.form("form_cadastro_produto"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome do Produto*")
            with col2:
                categorias = ["Tradicional", "Integral", "Doce", "Salgado", "Especial"]
                categoria = st.selectbox("Categoria*", categorias)
            with col3:
                preco_venda = st.number_input("Preço de Venda (R$)*", min_value=0.0, step=0.1, format="%.2f")
            
            submitted = st.form_submit_button("✅ Cadastrar Produto")
            if submitted:
                if nome and preco_venda >= 0:
                    try:
                        executar_query(
                            "INSERT INTO produtos (nome, preco_venda, categoria, ativo) VALUES (?, ?, ?, 1)",
                            (nome.strip(), preco_venda, categoria)
                        )
                        st.success(f"Produto '{nome}' cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("Já existe um produto com este nome!")
                        else:
                            st.error(f"Erro ao cadastrar produto: {e}")
                else:
                    st.error("Preencha todos os campos corretamente!")


    # ----------------------
    # Aba 2: Lista de Produtos
    # ----------------------
    with tab2:
        st.subheader("Produtos Cadastrados")
        produtos = get_dataframe("SELECT id, nome,preco_venda, categoria, ativo FROM produtos ORDER BY nome")
        
        if produtos.empty:
            st.info("Nenhum produto cadastrado ainda.")
            return

        # Filtros
        filtro_categoria = st.selectbox("Filtrar por Categoria", ["Todas"] + sorted(produtos['categoria'].unique().tolist()))
        mostrar_inativos = st.checkbox("Mostrar produtos inativos")

        produtos_filtrados = produtos.copy()
        if filtro_categoria != "Todas":
            produtos_filtrados = produtos_filtrados[produtos_filtrados['categoria'] == filtro_categoria]
        if not mostrar_inativos:
            produtos_filtrados = produtos_filtrados[produtos_filtrados['ativo'] == 1]

        if produtos_filtrados.empty:
            st.info("Nenhum produto encontrado com os filtros aplicados.")
            return

            # Mostrar tabela simples
        st.dataframe(
        produtos_filtrados.rename(columns={
            'id': 'ID',
            'nome': 'Nome',
            'categoria': 'Categoria',
            'ativo': 'Status',
            'preco_venda': 'Preço (R$)'
        }).assign(Status=lambda df: df['Status'].map({1:'✅ Ativo',0:'❌ Inativo'})),
        use_container_width=True
)


        st.markdown("---")
        st.subheader("Ações rápidas")

        # Ações CRUD
        for _, row in produtos_filtrados.iterrows():
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"✏️ Editar {row['nome']}", key=f"editar_{row['id']}"):
                    st.session_state["editar_id"] = row['id']
            with col2:
                if row['ativo'] == 1:
                    if st.button(f"🗑️ Inativar {row['nome']}", key=f"inativar_{row['id']}"):
                        executar_query("UPDATE produtos SET ativo=0 WHERE id=?", (row['id'],))
                        st.success("Produto inativado.")
                        st.rerun()
                else:
                    if st.button(f"♻️ Reativar {row['nome']}", key=f"reativar_{row['id']}"):
                        executar_query("UPDATE produtos SET ativo=1 WHERE id=?", (row['id'],))
                        st.success("Produto reativado.")
                        st.rerun()
            with col3:
                if st.button(f"❌ Excluir {row['nome']}", key=f"excluir_{row['id']}"):
                    st.session_state[f"confirm_delete_{row['id']}"] = True

            # Confirmação exclusão
            if st.session_state.get(f"confirm_delete_{row['id']}", False):
                with st.expander("⚠️ Confirmar exclusão permanente"):
                    st.warning("Esta ação irá excluir o produto permanentemente!")
                    c1,c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar", key=f"confirm_yes_{row['id']}"):
                            executar_query("DELETE FROM produtos WHERE id=?", (row['id'],))
                            st.success("Produto excluído.")
                            st.session_state.pop(f"confirm_delete_{row['id']}")
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"confirm_no_{row['id']}"):
                            st.session_state.pop(f"confirm_delete_{row['id']}")
                            st.info("Exclusão cancelada.")

        # Formulário de edição
        if st.session_state.get("editar_id"):
            edit_id = st.session_state["editar_id"]
            row = produtos[produtos['id']==edit_id].iloc[0]

            st.markdown("---")
            st.subheader(f"Editar produto — ID {edit_id}")
            with st.form(f"form_edit_{edit_id}"):
                nome_edit = st.text_input("Nome", value=row['nome'])
                categorias = ["Tradicional", "Integral", "Doce", "Salgado", "Especial"]
                idx = categorias.index(row['categoria']) if row['categoria'] in categorias else 0
                categoria_edit = st.selectbox("Categoria", categorias, index=idx)

                salvar = st.form_submit_button("💾 Salvar")
                cancelar = st.form_submit_button("✖️ Cancelar")

                if salvar:
                    executar_query(
                        "UPDATE produtos SET nome=?, categoria=? WHERE id=?",
                        (nome_edit.strip(), categoria_edit, edit_id)
                    )
                    st.success("Produto atualizado.")
                    st.session_state.pop("editar_id")
                    st.rerun()
                if cancelar:
                    st.session_state.pop("editar_id")
                    st.info("Edição cancelada.")
