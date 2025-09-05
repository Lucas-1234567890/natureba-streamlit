import streamlit as st
import pandas as pd
from banco import get_dataframe, executar_query
from datetime import datetime, timedelta

def modulo_vendas():
    st.header("💰 Registro de Vendas")
    
    tab1, tab2 = st.tabs(["➕ Nova Venda", "📋 Histórico"])

    with tab1:
        st.subheader("Registrar Nova Venda")

        # Buscar produtos ativos
        produtos = get_dataframe("SELECT id, nome, preco_venda FROM produtos WHERE ativo = 1 ORDER BY nome")

        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar vendas!")
            return
        
        with st.form("form_nova_venda"):
            col1, col2, col3 = st.columns(3)

            with col1:
                produto_selecionado = st.selectbox("Produto*", 
                                                 options=produtos['id'].tolist(),
                                                 format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0])
            
            with col2:
                quantidade = st.number_input("Quantidade*", min_value=1, step=1, value=1)

            with col3:
                data_venda = st.date_input("Data da Venda*", value=datetime.now().date())

            # mostrar informações do produto selecionado
            if produto_selecionado:
                produto_info = produtos[produtos['id']==produto_selecionado].iloc[0]
                preco_unitario = produto_info['preco_venda']
                total = preco_unitario * quantidade

                st.info(f"💰 Produto: {produto_info['nome']} | Preço: R$ {preco_unitario:.2f} | Total: R$ {total:.2f}")

            submitted = st.form_submit_button("✅ Registrar Venda")

            if submitted:
                if submitted:
                    if produto_selecionado and quantidade > 0:
                        try:
                            executar_query(
                                "INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) VALUES (?, ?, ?, ?, ?)",
                                (produto_selecionado, quantidade, preco_unitario, total, data_venda)
                            )
                            st.success(f"✅ Venda registrada: {quantidade}x {produto_info['nome']} = R$ {total:.2f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao registrar venda: {str(e)}")
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios!")

    with tab2:
        st.subheader("Histórico de Vendas")

        col1,col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7))

        with col2:
           with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

        vendas = get_dataframe("""
            SELECT v.data_venda, v.hora_venda, p.nome as produto,
                   v.quantidade, v.preco_unitario, v.total
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC, v.hora_venda DESC
        """, (data_inicio, data_fim))
        
        if not vendas.empty:
            # Resumo do período
            total_vendas = vendas['total'].sum()
            total_itens = vendas['quantidade'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Total do Período", f"R$ {total_vendas:.2f}")
            with col2:
                st.metric("🥖 Itens Vendidos", f"{int(total_itens)}")
            
            # Tabela de vendas
            st.dataframe(
                vendas.style.format({
                    'preco_unitario': 'R$ {:.2f}',
                    'total': 'R$ {:.2f}'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma venda encontrada no período selecionado.")