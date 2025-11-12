import streamlit as st
import pandas as pd
from funcoesAux import get_dataframe, format_brl_currency, format_brl_percent
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta



# --- Função principal
def modulo_relatorios():
    st.header("📊 Relatórios e Análises")
    tab1, tab2, tab3 = st.tabs(["📈 Financeiro", "📦 Produtos", "📅 Período"])

    # --- Aba Financeiro atualizada
    with tab1:
        st.subheader("💹 Métricas Financeiras")
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date().replace(day=1))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

        # Receita total
        receita_total = float(get_dataframe(
            "SELECT COALESCE(SUM(total),0) as total FROM vendas WHERE data_venda BETWEEN ? AND ?", 
            (data_inicio, data_fim)
        )['total'].iloc[0])

        # Custos variáveis (entradas de estoque)
        custos_variaveis = float(get_dataframe("""
            SELECT COALESCE(SUM(m.quantidade * i.preco_kg), 0) AS total_custo
            FROM movimentacoes_estoque m
            JOIN ingredientes i ON m.ingrediente_id = i.id
            WHERE m.tipo = 'entrada' 
            AND DATE(m.data_movimentacao) BETWEEN ? AND ?
        """, (data_inicio, data_fim))['total_custo'].iloc[0])

        # Custos fixos
        custos_fixos = float(get_dataframe("""
            SELECT COALESCE(SUM(valor),0) as total_custo_fixo
            FROM custos_operacionais
            WHERE recorrente = 1 AND data_custo BETWEEN ? AND ?
        """, (data_inicio, data_fim))['total_custo_fixo'].iloc[0])

        # Margens e indicadores
        margem_contrib_total = receita_total - custos_variaveis
        margem_contrib_percent = (margem_contrib_total / receita_total * 100) if receita_total > 0 else 0
        lucro_liquido = receita_total - (custos_variaveis + custos_fixos)
        margem_liquida = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0
        ponto_equilibrio = (custos_fixos / (margem_contrib_percent / 100)) if margem_contrib_percent > 0 else 0
        margem_seguranca = ((receita_total - ponto_equilibrio) / receita_total * 100) if receita_total > 0 else 0

        # Exibir KPIs
        cols = st.columns(6)
        cols[0].metric("💰 Receita Total", f"R$ {receita_total:,.2f}")
        cols[1].metric("💸 Custos Variáveis", f"R$ {custos_variaveis:,.2f}", f"{margem_contrib_percent:.1f}%")
        cols[2].metric("🏠 Custos Fixos", f"R$ {custos_fixos:,.2f}")
        cols[3].metric("📊 Margem Contribuição", f"R$ {margem_contrib_total:,.2f}", f"{margem_contrib_percent:.1f}%")
        cols[4].metric("📈 Lucro Líquido", f"R$ {lucro_liquido:,.2f}")
        cols[5].metric("🎯 Margem Líquida", f"{margem_liquida:.1f}%")

        # Gráfico de composição Receita vs Custos vs Lucro
        fig = go.Figure(data=[
            go.Bar(name='Custos Variáveis', x=['Análise'], y=[custos_variaveis], marker_color='#FF6B6B'),
            go.Bar(name='Custos Fixos', x=['Análise'], y=[custos_fixos], marker_color='#FFA07A'),
            go.Bar(name='Lucro Líquido', x=['Análise'], y=[lucro_liquido], marker_color='#4ECDC4')
        ])
        fig.update_layout(
            title='Composição Receita vs Custos vs Lucro',
            barmode='stack',
            yaxis_title='Valor (R$)'
        )
        st.plotly_chart(fig, use_container_width=True)


    # --- Aba Produtos
    with tab2:
        st.subheader("Análise de Produtos")

        ranking_produtos = get_dataframe("""
       SELECT 
    p.id,
    p.nome AS produto,
    p.categoria,
    SUM(iv.quantidade) AS quantidade_vendida,
    SUM(iv.subtotal) AS receita
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
JOIN vendas v ON iv.venda_id = v.id
WHERE v.data_venda BETWEEN ? AND ?
GROUP BY p.id, p.nome, p.categoria
ORDER BY receita DESC

    """, (data_inicio, data_fim))


        if not ranking_produtos.empty:
            st.subheader("🏆 Top Produtos por Receita")
            fig = px.bar(
                ranking_produtos.head(20),
                x='produto',
                y='receita',
                text='receita',
                color='receita',
                title="Receita por Produto",
                color_continuous_scale=['#CFF5E0', '#5C977C'],
                labels={'receita': 'Receita (R$)'}
            )
            fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Ranking Completo")
            st.dataframe(
                ranking_produtos.style.format({
                    'receita': 'R$ {:.2f}',
                    'quantidade_vendida': '{:.0f}'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma venda registrada no período selecionado.")

    # --- Aba Período
    with tab3:
        st.subheader("Análise por Período")
        vendas_semana = get_dataframe("""
            SELECT 
                CASE CAST(strftime('%w', data_venda) AS INTEGER)
                    WHEN 0 THEN 'Domingo'
                    WHEN 1 THEN 'Segunda'
                    WHEN 2 THEN 'Terça'
                    WHEN 3 THEN 'Quarta'
                    WHEN 4 THEN 'Quinta'
                    WHEN 5 THEN 'Sexta'
                    WHEN 6 THEN 'Sábado'
                END as dia_semana,
                        SUM(total) as faturamento,
        COUNT(id) as produtos_vendidos

            FROM vendas
            WHERE data_venda >= ?
            GROUP BY strftime('%w', data_venda)
            ORDER BY strftime('%w', data_venda)
        """, (datetime.now().date() - timedelta(days=30),))

        if not vendas_semana.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    vendas_semana,
                    x='dia_semana',
                    y='faturamento',
                    text='faturamento',
                    title="Faturamento por Dia da Semana",
                    color_discrete_sequence=['#5C977C']
                )
                fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    vendas_semana,
                    x='dia_semana',
                    y='produtos_vendidos',
                    text='produtos_vendidos',
                    title="Produtos Vendidos por Dia da Semana",
                    color_discrete_sequence=['#5C977C']
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma venda registrada nos últimos 30 dias.")
