import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from banco import get_dataframe, executar_query
import plotly.express as px

def modulo_producao():
    """
    Módulo simplificado de Produção.
    Comentários estilo sênior: direto, seguro e pragmático.
    - Registro faz o débito dos ingredientes se existir receita.
    - Edição/Exclusão não alteram histórico de movimentação automaticamente (evitar alterações complexas de estoque ao editar).
      Se for necessário ajustar estoque depois de editar, faça via módulo de ingredientes/movimentações.
    """

    st.header("🥖 Controle de Produção")
    tab1, tab2, tab3 = st.tabs(["➕ Registrar Produção", "📋 Produção Hoje", "📊 Histórico"])

    # -----------------------------
    # Aba 1 — Registrar Produção
    # -----------------------------
    with tab1:
        st.subheader("Registrar Nova Produção (simples e rápido)")

        produtos = get_dataframe("SELECT id, nome, custo_producao FROM produtos WHERE ativo = 1 ORDER BY nome")
        if produtos is None or produtos.empty:
            st.warning("⚠️ Cadastre produtos ativos antes de registrar produção.")
        else:
            # Formulário de registro — tudo dentro do form para evitar re-runs a cada input
            with st.form("form_producao"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    produto_id = st.selectbox(
                        "Produto*",
                        options=produtos['id'].tolist(),
                        format_func=lambda x: produtos.loc[produtos['id']==x, 'nome'].values[0]
                    )
                with col2:
                    quantidade = st.number_input("Quantidade*", min_value=1, step=1, value=1)
                with col3:
                    data_producao = st.date_input("Data da Produção*", value=datetime.now().date())

                # Informações do produto e cálculo rápido
                produto_row = produtos[produtos['id'] == produto_id].iloc[0]
                custo_unitario = float(produto_row['custo_producao'] or 0.0)
                custo_total = round(custo_unitario * int(quantidade), 2)
                st.info(f"Produto: {produto_row['nome']} • Custo unit.: R$ {custo_unitario:.2f} • Custo total: R$ {custo_total:.2f}")

                observacoes = st.text_area("Observações (opcional)")
                submitted = st.form_submit_button("✅ Registrar Produção")

                if submitted:
                    # validação simples
                    if quantidade <= 0:
                        st.error("Quantidade deve ser maior que zero.")
                    else:
                        try:
                            # 1) Inserir produção
                            executar_query(
                                "INSERT INTO producao (produto_id, quantidade, custo_total, data_producao, observacoes) VALUES (?, ?, ?, ?, ?)",
                                (int(produto_id), int(quantidade), float(custo_total), data_producao, observacoes)
                            )

                            # 2) Se houver receita, decrementar ingredientes e registrar movimentação
                            receita = get_dataframe("""
                                SELECT r.ingrediente_id, i.nome, r.quantidade, i.unidade
                                FROM receitas r
                                JOIN ingredientes i ON r.ingrediente_id = i.id
                                WHERE r.produto_id = ?
                            """, (int(produto_id),))

                            if receita is not None and not receita.empty:
                                # LOOP: para cada ingrediente, subtrai do estoque e registra movimentação
                                for _, ingr in receita.iterrows():
                                    qtd_necessaria = ingr['quantidade'] * int(quantidade)
                                    # reduz estoque — assumimos que estoque suficiente já foi verificado por você
                                    executar_query(
                                        "UPDATE ingredientes SET estoque_atual = estoque_atual - ? WHERE id = ?",
                                        (float(qtd_necessaria), int(ingr['ingrediente_id']))
                                    )
                                    motivo = f"Produção: {int(quantidade)}x {produto_row['nome']}"
                                    executar_query(
                                        "INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, motivo, data_movimentacao) VALUES (?, 'saida', ?, ?, ?)",
                                        (int(ingr['ingrediente_id']), float(qtd_necessaria), motivo, datetime.now())
                                    )

                                st.success("Produção registrada e estoque de ingredientes atualizado.")
                            else:
                                st.success("Produção registrada.")

                            st.rerun()

                        except Exception as e:
                            # Sênior diz: capture erros e mostre mensagem clara
                            st.error(f"Erro ao registrar produção: {e}")

    # -----------------------------
    # Aba 2 — Produção de Hoje
    # -----------------------------
    with tab2:
        st.subheader("Produção de Hoje")
        hoje = datetime.now().date()
        producao_hoje = get_dataframe("""
            SELECT pr.id, pr.data_producao, p.nome as produto, pr.quantidade, pr.custo_total,
                   (pr.custo_total / pr.quantidade) as custo_unitario
            FROM producao pr
            JOIN produtos p ON pr.produto_id = p.id
            WHERE pr.data_producao = ?
            ORDER BY pr.id DESC
        """, (hoje,))

        if producao_hoje is None or producao_hoje.empty:
            st.info("Nenhuma produção registrada hoje.")
        else:
            total_itens = int(producao_hoje['quantidade'].sum())
            total_custo = float(producao_hoje['custo_total'].sum())

            c1, c2 = st.columns(2)
            with c1:
                st.metric("🍞 Itens Produzidos (hoje)", f"{total_itens}")
            with c2:
                st.metric("💸 Custo Total (hoje)", f"R$ {total_custo:.2f}")

            # tabela simples
            st.dataframe(
                producao_hoje.rename(columns={
                    'id': 'ID', 'data_producao': 'Data', 'produto': 'Produto',
                    'quantidade': 'Qtd', 'custo_unitario': 'Custo Unit. (R$)', 'custo_total': 'Custo Total (R$)'
                }).style.format({'Custo Unit. (R$)': 'R$ {:.2f}', 'Custo Total (R$)': 'R$ {:.2f}'}),
                use_container_width=True
            )

            # gráfico (distribuição por produto)
            fig = px.pie(producao_hoje, values='quantidade', names='produto', title="Distribuição da Produção (Hoje)")
            st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # Aba 3 — Histórico + CRUD (simples)
    # -----------------------------
    with tab3:
        st.subheader("Histórico de Produção (editar / excluir)")

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

        producao_historico = get_dataframe("""
            SELECT pr.id, pr.data_producao, p.nome as produto, p.categoria,
                   pr.quantidade, pr.custo_total,
                   (pr.custo_total / pr.quantidade) as custo_unitario
            FROM producao pr
            JOIN produtos p ON pr.produto_id = p.id
            WHERE pr.data_producao BETWEEN ? AND ?
            ORDER BY pr.data_producao DESC, pr.id DESC
        """, (data_inicio, data_fim))

        if producao_historico is None or producao_historico.empty:
            st.info("Nenhuma produção no período selecionado.")
            return

        # resumo rápido
        total_produzido = int(producao_historico['quantidade'].sum())
        total_custo_periodo = float(producao_historico['custo_total'].sum())
        custo_medio = (total_custo_periodo / total_produzido) if total_produzido > 0 else 0.0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🍞 Total Produzido", f"{total_produzido}")
        with c2:
            st.metric("💸 Custo Total", f"R$ {total_custo_periodo:.2f}")
        with c3:
            st.metric("📊 Custo Médio por Unidade", f"R$ {custo_medio:.2f}")

        # tabela principal
        st.dataframe(
            producao_historico.rename(columns={
                'id': 'ID', 'data_producao': 'Data', 'produto': 'Produto',
                'categoria': 'Categoria', 'quantidade': 'Qtd',
                'custo_unitario': 'Custo Unit. (R$)', 'custo_total': 'Custo Total (R$)'
            }).style.format({'Custo Unit. (R$)': 'R$ {:.2f}', 'Custo Total (R$)': 'R$ {:.2f}'}),
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Editar / Excluir registro de produção")

        # Criar lista de opções e mapping de forma simples (mais legível que lambda/apply)
        opcoes = []
        mapping = {}
        for _, r in producao_historico.iterrows():
            texto = f"{int(r['id'])} — {r['data_producao']} — {r['produto']} — {int(r['quantidade'])}x — R$ {float(r['custo_total']):.2f}"
            opcoes.append(texto)
            mapping[texto] = int(r['id'])

        selecao = st.selectbox("Selecione um registro", ["-- nada --"] + opcoes)
        if selecao and selecao != "-- nada --":
            pid = mapping[selecao]
            row = producao_historico[producao_historico['id'] == pid].iloc[0]

            # Mostrar resumo do registro selecionado
            st.markdown(f"**ID:** {int(row['id'])}  •  **Produto:** {row['produto']}  •  **Data:** {row['data_producao']}")
            st.caption(f"Quantidade: {int(row['quantidade'])} • Custo total: R$ {float(row['custo_total']):.2f} • Custo unit.: R$ {float(row['custo_unitario']):.2f}")

            # Formulário de edição simples — não mexe automaticamente em estoque
            with st.form(f"form_edit_producao_{pid}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    quantidade_edit = st.number_input("Quantidade", min_value=1, value=int(row['quantidade']))
                with col2:
                    custo_unit_edit = st.number_input("Custo unit. (R$)", min_value=0.0, format="%.2f", value=float(row['custo_unitario']))
                with col3:
                    data_edit = st.date_input("Data produção", value=pd.to_datetime(row['data_producao']).date())

                col_a, col_b = st.columns(2)
                with col_a:
                    salvar = st.form_submit_button("💾 Salvar")
                with col_b:
                    excluir = st.form_submit_button("❌ Excluir")

                if salvar:
                    # Atualiza producao: recalcula custo_total a partir do custo unitário fornecido
                    novo_total = round(float(custo_unit_edit) * int(quantidade_edit), 2)
                    try:
                        executar_query(
                            "UPDATE producao SET quantidade=?, custo_total=?, data_producao=? WHERE id=?",
                            (int(quantidade_edit), float(novo_total), data_edit, int(pid))
                        )
                        st.success("Registro de produção atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar produção: {e}")

                if excluir:
                    # ATENÇÃO: exclusão é permanente; sênior recomenda checar movimentações relacionadas antes de apagar em produção em produção real
                    try:
                        executar_query("DELETE FROM producao WHERE id = ?", (int(pid),))
                        st.success("Registro de produção excluído.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
