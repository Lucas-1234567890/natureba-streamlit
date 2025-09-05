import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from banco import get_dataframe, executar_query
import plotly.express as px

def modulo_producao():

    st.header("🥖 Controle de Produção")
    
    tab1, tab2, tab3 = st.tabs(["➕ Registrar Produção", "📋 Produção Hoje", "📊 Histórico"])

    with tab1:
        st.subheader("Registrar Nova Produção")

        # Buscar produtos ativos
        produtos = get_dataframe("SELECT id, nome, custo_producao FROM produtos WHERE ativo = 1")

        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar produção!")
            return
        
        with st.form("form_producao"):
            col1, col2, col3 = st.columns(3)

            with col1:
                produto_selecionado = st.selectbox(
                    "Produto*", 
                    options=produtos['id'].tolist(),
                    format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0]
                )
            with col2:
                quantidade = st.number_input("Quantidade*", min_value=1, step=1)
            with col3:    
                data_producao = st.date_input("Data da Produção*", value=datetime.now().date()) 

            # Mostrar informações adicionais se o produto for selecionado
            if produto_selecionado:
                produto_info = produtos[produtos['id'] == produto_selecionado].iloc[0]
                custo_unitario = produto_info['custo_producao']
                custo_total = custo_unitario * quantidade

                st.info(f"🍞 Produto: {produto_info['nome']} | Custo Unit.: R$ {custo_unitario:.2f} | Custo Total: R$ {custo_total:.2f}")

                # Mostrar receita se existir
                receita = get_dataframe("""
                    SELECT i.nome, r.quantidade, i.unidade
                    FROM receitas r
                    JOIN ingredientes i ON r.ingrediente_id = i.id
                    WHERE r.produto_id = ?
                """, [produto_selecionado])

                if not receita.empty:
                    with st.expander("📋 Ver Receita"):
                        st.write("**Ingredientes necessários por unidade:**")
                        for _, row in receita.iterrows():
                            st.write(f"• {row['nome']}: {row['quantidade']} {row['unidade']}")
                        st.write(f"**Para {quantidade} unidades será necessário:**")
                        for _, row in receita.iterrows():
                            total_ingrediente = row['quantidade'] * quantidade
                            st.write(f"• {row['nome']}: {total_ingrediente} {row['unidade']}")

                observacoes = st.text_area("Observações (opcional)")

                submitted = st.form_submit_button("✅ Registrar Produção") 

                if submitted:
                    if produto_selecionado and quantidade > 0:
                        try:
                            # Registrar produção
                            executar_query(
                                "INSERT INTO producao (produto_id, quantidade, custo_total, data_producao) VALUES (?, ?, ?, ?)",
                                (produto_selecionado, quantidade, custo_total, data_producao)
                            )

                            # Baixar ingredientes do estoque se existir receita
                            if not receita.empty:
                                for _, row in receita.iterrows():
                                    quantidade_necessaria = row['quantidade'] * quantidade

                                    # Baixar do estoque
                                    executar_query("""
                                        UPDATE ingredientes 
                                        SET estoque_atual = estoque_atual - ? 
                                        WHERE id = ?
                                    """, (quantidade_necessaria, row['ingrediente_id']))
                                    
                                    # Registrar movimentação
                                    motivo = f"Produção: {quantidade}x {produto_info['nome']}"
                                    executar_query("""
                                        INSERT INTO movimentacoes_estoque 
                                        (ingrediente_id, tipo, quantidade, motivo, data_movimentacao) 
                                        VALUES (?, 'saida', ?, ?, ?)
                                    """, (row['ingrediente_id'], quantidade_necessaria, motivo, datetime.now()))
                            
                            st.success(f"✅ Produção registrada: {quantidade}x {produto_info['nome']} = R$ {custo_total:.2f}")
                            
                            if not receita.empty:
                                st.info("📦 Estoque de ingredientes atualizado automaticamente!")

                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Erro ao registrar produção: {str(e)}")
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios!")
        with tab2:
            st.subheader("Produção de Hoje")
            
            hoje = datetime.now().date()
            producao_hoje = get_dataframe("""
                SELECT p.nome as produto, pr.quantidade, pr.custo_total,
                    (pr.custo_total / pr.quantidade) as custo_unitario
                FROM producao pr
                JOIN produtos p ON pr.produto_id = p.id
                WHERE pr.data_producao = ?
                ORDER BY pr.id DESC
            """, (hoje,))
            
            if not producao_hoje.empty:
                # Resumo do dia
                total_itens = producao_hoje['quantidade'].sum()
                total_custo = producao_hoje['custo_total'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🍞 Itens Produzidos", f"{int(total_itens)}")
                with col2:
                    st.metric("💸 Custo Total", f"R$ {total_custo:.2f}")
                
                # Tabela da produção
                st.dataframe(
                    producao_hoje.style.format({
                        'custo_unitario': 'R$ {:.2f}',
                        'custo_total': 'R$ {:.2f}'
                    }),
                    use_container_width=True
                )
                
                # Gráfico de produção por produto
                fig = px.pie(producao_hoje, values='quantidade', names='produto',
                            title="Distribuição da Produção de Hoje")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("😴 Nenhuma produção registrada hoje ainda.")
                
                # Sugestão baseada nas vendas de ontem
                ontem = hoje - timedelta(days=1)
                vendas_ontem = get_dataframe("""
                    SELECT p.nome, SUM(v.quantidade) as vendido_ontem
                    FROM vendas v
                    JOIN produtos p ON v.produto_id = p.id
                    WHERE v.data_venda = ?
                    GROUP BY p.id, p.nome
                    ORDER BY vendido_ontem DESC
                """, (ontem,))
                
                if not vendas_ontem.empty:
                    st.subheader("💡 Sugestão baseada nas vendas de ontem:")
                    for _, row in vendas_ontem.iterrows():
                        st.write(f"• **{row['nome']}**: {int(row['vendido_ontem'])} unidades")
                
    with tab3:
        st.subheader("Histórico de Produção")
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
        
        producao_historico = get_dataframe("""
            SELECT pr.data_producao, p.nome as produto, p.categoria,
                   pr.quantidade, pr.custo_total,
                   (pr.custo_total / pr.quantidade) as custo_unitario
            FROM producao pr
            JOIN produtos p ON pr.produto_id = p.id
            WHERE pr.data_producao BETWEEN ? AND ?
            ORDER BY pr.data_producao DESC, pr.id DESC
        """, (data_inicio, data_fim))
        
        if not producao_historico.empty:
            # Resumo do período
            total_producao = producao_historico['quantidade'].sum()
            total_custo_periodo = producao_historico['custo_total'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🍞 Total Produzido", f"{int(total_producao)}")
            with col2:
                st.metric("💸 Custo Total", f"R$ {total_custo_periodo:.2f}")
            with col3:
                custo_medio = total_custo_periodo / total_producao if total_producao > 0 else 0
                st.metric("📊 Custo Médio", f"R$ {custo_medio:.2f}")
            
            # Gráfico de produção por dia
            producao_diaria = producao_historico.groupby('data_producao').agg({
                'quantidade': 'sum',
                'custo_total': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(producao_diaria, x='data_producao', y='quantidade',
                             title="Produção Diária (Unidades)",
                             markers=True)
                fig.update_traces(line_color='#FF6B6B')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(producao_diaria, x='data_producao', y='custo_total',
                             title="Custo de Produção Diária",
                             markers=True)
                fig.update_traces(line_color='#4ECDC4')
                st.plotly_chart(fig, use_container_width=True)
            
            # Ranking de produtos mais produzidos
            ranking_producao = producao_historico.groupby('produto').agg({
                'quantidade': 'sum',
                'custo_total': 'sum'
            }).reset_index().sort_values('quantidade', ascending=False)
            
            st.subheader("🏆 Produtos Mais Produzidos no Período")
            fig = px.bar(ranking_producao.head(10), x='produto', y='quantidade',
                        color='custo_total',
                        title="Ranking de Produção por Produto",
                        text='quantidade',
                        color_continuous_scale='Oranges')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("📋 Detalhes da Produção")
            st.dataframe(
                producao_historico.style.format({
                    'custo_unitario': 'R$ {:.2f}',
                    'custo_total': 'R$ {:.2f}'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma produção registrada no período selecionado.")
