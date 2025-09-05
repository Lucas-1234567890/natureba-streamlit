import streamlit as st
from banco import executar_query, get_dataframe
import pandas as pd

def modulo_produtos():
    st.header("📦 Gestão de Produtos")

    tab1, tab2 = st.tabs(["➕ Cadastrar Produto", "📋 Lista de Produtos"])

    # ----------------------
    # Aba 1: Cadastrar Produto
    # ----------------------
    with tab1:
        st.subheader('Cadastro de Produtos')
        with st.form("form_cadastro_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
            with col2:
                categorias = ["Tradicional", "Integral", "Doce", "Salgado", "Especial"]
                categoria = st.selectbox("Categoria*", categorias)
                custo_producao = st.number_input("Custo de Produção (R$)", min_value=0.0, format="%.2f")
            
            submitted = st.form_submit_button("✅ Cadastrar Produto")
            if submitted:
                if nome and preco_venda > 0 and custo_producao > 0:
                    try:
                        executar_query(
                            "INSERT INTO produtos (nome, preco_venda, custo_producao, categoria, ativo) VALUES (?, ?, ?, ?, 1)",
                            (nome.strip(), preco_venda, custo_producao, categoria)
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
    # Aba 2: Lista de Produtos + CRUD
    # ----------------------
    with tab2:
        st.subheader("Produtos Cadastrados")
        produtos = get_dataframe("""
            SELECT id, nome, categoria, preco_venda, custo_producao,
                   (preco_venda - custo_producao) as lucro_unitario,
                   CASE WHEN preco_venda > 0 THEN ((preco_venda - custo_producao) / preco_venda * 100) ELSE 0 END as margem,
                   ativo
            FROM produtos
            ORDER BY nome
        """)
        if produtos.empty:
            st.info("Nenhum produto cadastrado ainda.")
            return

        # Filtros
        col1, col2 = st.columns([3,1])
        with col1:
            filtro_categoria = st.selectbox("Filtrar por Categoria", ["Todas"] + sorted(produtos['categoria'].unique().tolist()))
        with col2:
            mostrar_inativos = st.checkbox("Mostrar produtos inativos")
        
        produtos_filtrados = produtos.copy()
        if filtro_categoria != "Todas":
            produtos_filtrados = produtos_filtrados[produtos_filtrados['categoria'] == filtro_categoria]
        if not mostrar_inativos:
            produtos_filtrados = produtos_filtrados[produtos_filtrados['ativo'] == 1]

        if produtos_filtrados.empty:
            st.info("Nenhum produto encontrado com os filtros aplicados.")
            return

        # Exibe tabela
        st.dataframe(
            produtos_filtrados.rename(columns={
                'id': 'ID',
                'nome': 'Nome',
                'categoria': 'Categoria',
                'preco_venda': 'Preço (R$)',
                'custo_producao': 'Custo (R$)',
                'lucro_unitario': 'Lucro Unit. (R$)',
                'margem': 'Margem (%)',
                'ativo': 'Status'
            }).assign(Status=lambda df: df['Status'].map({1:'Ativo',0:'Inativo'}))
             .style.format({'Preço (R$)': 'R$ {:.2f}','Custo (R$)': 'R$ {:.2f}','Lucro Unit. (R$)': 'R$ {:.2f}','Margem (%)':'{:.1f}%'})
             , use_container_width=True
        )

        st.markdown("---")
        st.subheader("Ações rápidas")

        # Lista de opções simples
        opções = []
        mapping = {}
        for _, r in produtos_filtrados.iterrows():
            texto = f"{r['id']} — {r['nome']} ({'Ativo' if r['ativo']==1 else 'Inativo'})"
            opções.append(texto)
            mapping[texto] = r['id']

        sel = st.selectbox("Selecione um produto", ["-- nada --"] + opções)
        if sel != "-- nada --":
            pid = mapping[sel]
            row = produtos[produtos['id']==pid].iloc[0]

            st.markdown(f"**ID:** {row['id']} • **Nome:** {row['nome']} • **Categoria:** {row['categoria']} • **Status:** {'Ativo' if row['ativo']==1 else 'Inativo'}")
            st.caption(f"Preço: R$ {row['preco_venda']:.2f} • Custo: R$ {row['custo_producao']:.2f} • Lucro: R$ {row['lucro_unitario']:.2f} • Margem: {row['margem']:.1f}%")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("✏️ Editar", key=f"editar_{pid}"):
                    st.session_state["editar_id"] = pid
            with col_b:
                if row['ativo']==1:
                    if st.button("🗑️ Inativar", key=f"inativar_{pid}"):
                        executar_query("UPDATE produtos SET ativo=0 WHERE id=?", (pid,))
                        st.success("Produto inativado.")
                        st.rerun()
                else:
                    if st.button("♻️ Reativar", key=f"reativar_{pid}"):
                        executar_query("UPDATE produtos SET ativo=1 WHERE id=?", (pid,))
                        st.success("Produto reativado.")
                        st.rerun()
            with col_c:
                if st.button("❌ Excluir", key=f"excluir_{pid}"):
                    st.session_state[f"confirm_delete_{pid}"] = True

            # Confirmação exclusão
            if st.session_state.get(f"confirm_delete_{pid}", False):
                with st.expander("⚠️ Confirmar exclusão permanente"):
                    c1,c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar", key=f"confirm_yes_{pid}"):
                            executar_query("DELETE FROM produtos WHERE id=?", (pid,))
                            st.success("Produto excluído.")
                            st.session_state.pop(f"confirm_delete_{pid}")
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"confirm_no_{pid}"):
                            st.session_state.pop(f"confirm_delete_{pid}")
                            st.info("Exclusão cancelada.")

        # Formulário de edição
        if st.session_state.get("editar_id"):
            edit_id = st.session_state["editar_id"]
            row = produtos[produtos['id']==edit_id].iloc[0]

            st.markdown("---")
            st.subheader(f"Editar produto — ID {edit_id}")
            with st.form(f"form_edit_{edit_id}"):
                col1,col2 = st.columns(2)
                with col1:
                    nome_edit = st.text_input("Nome", value=row['nome'])
                    preco_edit = st.number_input("Preço (R$)", min_value=0.0, value=float(row['preco_venda']))
                with col2:
                    categorias = ["Tradicional", "Integral", "Doce", "Salgado", "Especial"]
                    idx = categorias.index(row['categoria']) if row['categoria'] in categorias else 0
                    categoria_edit = st.selectbox("Categoria", categorias, index=idx)
                    custo_edit = st.number_input("Custo (R$)", min_value=0.0, value=float(row['custo_producao']))

                salvar = st.form_submit_button("💾 Salvar")
                cancelar = st.form_submit_button("✖️ Cancelar")

                if salvar:
                    executar_query(
                        "UPDATE produtos SET nome=?, preco_venda=?, custo_producao=?, categoria=? WHERE id=?",
                        (nome_edit.strip(), preco_edit, custo_edit, categoria_edit, edit_id)
                    )
                    st.success("Produto atualizado.")
                    st.session_state.pop("editar_id")
                    st.rerun()
                if cancelar:
                    st.session_state.pop("editar_id")
                    st.info("Edição cancelada.")
