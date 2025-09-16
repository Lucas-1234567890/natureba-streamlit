import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from banco import get_dataframe, executar_query

def modulo_vendas():
    st.header("💰 Vendas")

    tab1, tab2 = st.tabs(["➕ Nova Venda", "📋 Histórico"]) 

    # --------------------
    # Aba 1: Nova Venda
    # --------------------
    with tab1:
        produtos = get_dataframe("SELECT id, nome, preco_venda FROM produtos WHERE ativo=1 ORDER BY nome")
        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar vendas!")
            return
        
        with st.form("nova_venda"):
            col1, col2, col3 = st.columns(3)
            with col1:
                produto_id = st.selectbox(
                    "Produto",
                    options=produtos['id'],
                    format_func=lambda x: produtos.loc[produtos['id']==x, 'nome'].values[0]
                )
            with col2:
                qtd = st.number_input("Quantidade", min_value=1, value=1)
            with col3:
                data = st.date_input("Data da venda", value=datetime.now().date())
            
            submitted = st.form_submit_button("Registrar")
            if submitted:
                produto = produtos[produtos['id']==produto_id].iloc[0]
                total = float(produto['preco_venda']) * qtd
                executar_query(
                    "INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) VALUES (?, ?, ?, ?, ?)",
                    (int(produto_id), int(qtd), float(produto['preco_venda']), total, data)
                )
                st.success(f"Venda registrada: {qtd}x {produto['nome']} = R$ {total:.2f}")
                st.rerun()

    # --------------------
    # Aba 2: Histórico / CRUD
    # --------------------
    with tab2:
        # filtros
        col1, col2 = st.columns(2)
        with col1:
            inicio = st.date_input("Data início", value=datetime.now().date() - timedelta(days=7))
        with col2:
            fim = st.date_input("Data fim", value=datetime.now().date())

        vendas = get_dataframe("""
            SELECT v.id, v.data_venda, p.nome as produto, v.quantidade, v.preco_unitario, v.total
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC
        """, (inicio, fim))

        if vendas.empty:
            st.info("Nenhuma venda encontrada.")
            return

        # mostra tabela
        st.subheader("Vendas")
        st.dataframe(
            vendas.rename(columns={
                'id': 'ID', 
                'data_venda': 'Data', 
                'produto': 'Produto', 
                'quantidade': 'Qtd', 
                'preco_unitario': 'Preço Unit.', 
                'total': 'Total'
            }).style.format({
                'Preço Unit.': 'R$ {:.2f}',
                'Total': 'R$ {:.2f}'
            }),
            use_container_width=True
        )

        # --------------------
        # Área de edição/exclusão
        # --------------------
        st.subheader("Editar / Excluir Venda")
        opções = vendas.apply(
            lambda r: f"{r['id']} — {r['data_venda']} — {r['produto']} ({r['quantidade']}x) R$ {r['total']:.2f}", axis=1
        ).tolist()
        mapping = {opções[i]: int(vendas.iloc[i]['id']) for i in range(len(opções))}

        sel = st.selectbox("Selecione a venda", ["-- nada --"] + opções)
        if sel != "-- nada --":
            vid = mapping[sel]
            row = vendas[vendas['id'] == vid].iloc[0]

            # Formulário de edição -- somente o botão de salvar está dentro do form
            with st.form(f"form_edit_{vid}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    qtd_edit = st.number_input("Quantidade", min_value=1, value=int(row['quantidade']))
                with col2:
                    preco_edit = st.number_input("Preço unit.", min_value=0.0, format="%.2f", value=float(row['preco_unitario']))
                with col3:
                    data_edit = st.date_input("Data", value=pd.to_datetime(row['data_venda']).date())

                col1, col2 = st.columns(2)
                with col1:
                    salvar = st.form_submit_button("💾 Salvar")
                # removido o botão de excluir de dentro do form para evitar conflitos

                if salvar:
                    total_edit = qtd_edit * preco_edit
                    executar_query(
                        "UPDATE vendas SET quantidade=?, preco_unitario=?, total=?, data_venda=? WHERE id=?",
                        (int(qtd_edit), float(preco_edit), float(total_edit), data_edit, vid)
                    )
                    st.success("Venda atualizada.")
                    st.rerun()

            # Botão de exclusão fora do form (ação imediata)
            if st.button("🗑️ Excluir", key=f"del_{vid}"):
                executar_query("DELETE FROM vendas WHERE id=?", (vid,))
                st.warning("Venda excluída.")
                st.rerun()
