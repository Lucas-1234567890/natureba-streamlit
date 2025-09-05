import streamlit as st
from banco import executar_query , get_dataframe
import pandas as pd

def modulo_produtos():
    st.header("📦 Gestão de Produtos")

    tab1, tab2 = st.tabs(["➕ Cadastrar/Editar", "📋 Lista de Produtos"])

    with tab1:
        st.subheader('Cadastro de Produtos')

        with st.form("form_cadastro_produto"):
            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input("Nome do Produto")
                preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")

            with col2:
                categoria = st.selectbox(
                    "Categoria*",
                    ["Tradicional", "Integral", "Doce", "Salgado", "Especial"]
                )
                custo_producao = st.number_input("Custo de Produção (R$)", min_value=0.0, format="%.2f")

            # Esse nível de indentação é **dentro do with st.form**
            submitted = st.form_submit_button("✅ Cadastrar Produto")

            if submitted:
                if nome and preco_venda > 0 and custo_producao > 0:
                    try:
                        executar_query(
                            "INSERT INTO produtos (nome, preco_venda, custo_producao, categoria) VALUES (?, ?, ?, ?)",
                            (nome, preco_venda, custo_producao, categoria)
                        )
                        st.success(f"✅ Produto '{nome}' cadastrado com sucesso!")
                        st.experimental_rerun()  # use st.experimental_rerun() em vez de st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("❌ Já existe um produto com este nome!")
                        else:
                            st.error(f"❌ Erro ao cadastrar produto: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")

    with tab2:
        st.subheader("Produtos Cadastrados")
        
        produtos = get_dataframe("""
            SELECT id, nome, categoria, preco_venda, custo_producao,
                   (preco_venda - custo_producao) as lucro_unitario,
                   ((preco_venda - custo_producao) / preco_venda * 100) as margem,
                   ativo
            FROM produtos
            ORDER BY nome
        """)

        if not produtos.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_categoria = st.selectbox("Filtrar por Categoria", 
                                              ["Todas"] + list(produtos['categoria'].unique()))
            with col2:
                mostrar_inativos = st.checkbox("Mostrar produtos inativos")
            
            # Aplicar filtros
            produtos_filtrados = produtos.copy()
            
            if filtro_categoria != "Todas":
                produtos_filtrados = produtos_filtrados[produtos_filtrados['categoria'] == filtro_categoria]
            
            if not mostrar_inativos:
                produtos_filtrados = produtos_filtrados[produtos_filtrados['ativo'] == 1]
            
            # Exibir tabela
            if not produtos_filtrados.empty:
                st.dataframe(
                    produtos_filtrados[['nome', 'categoria', 'preco_venda', 'custo_producao', 'lucro_unitario', 'margem']].style.format({
                        'preco_venda': 'R$ {:.2f}',
                        'custo_producao': 'R$ {:.2f}',
                        'lucro_unitario': 'R$ {:.2f}',
                        'margem': '{:.1f}%'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum produto encontrado com os filtros aplicados.")
        else:
            st.info("Nenhum produto cadastrado ainda.")

