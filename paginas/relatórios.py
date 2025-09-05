import streamlit as st
import pandas as pd
from banco import get_dataframe
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


def modulo_relatorios():
    st.header("📊 Relatórios e Análises")

    tab1, tab2, tab3 = st.tabs(["📈 Financeiro", "📦 Produtos", "📅 Período"])

    with tab1:
       st.subheader("Análise Financeira")
        #perido para analsie
       col1, col2 = st.columns(2)
       with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date().replace(day=1))
       with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

        # analise de rentabilidade
       rentabilidade = get_dataframe("""
            SELECT 
                SUM(v.total) as receita_total,
                SUM(v.quantidade * p.custo_producao) as custo_total,
                (SUM(v.total) - SUM(v.quantidade * p.custo_producao)) as lucro_bruto,
                ((SUM(v.total) - SUM(v.quantidade * p.custo_producao)) / SUM(v.total) * 100) as margem_bruta
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda BETWEEN ? AND ?
        """, (data_inicio, data_fim))
       
       if not rentabilidade.empty and rentabilidade['receita_total'].iloc[0]:
           dados = rentabilidade.iloc[0]

           col1, col2, col3, col4 = st.columns(4)
           with col1:
               st.metric("💰 Receita", f"R$ {dados['receita_total']:.2f}")
           with col2:
               st.metric("💸 Custos", f"R$ {dados['custo_total']:.2f}")
           with col3:
               st.metric("📈 Lucro Bruto", f"R$ {dados['lucro_bruto']:.2f}")
           with col4:
                st.metric("🎯 Margem", f"{dados['margem_bruta']:.1f}%")

            # Gráfico de composição
           fig = go.Figure(data=[
                go.Bar(name='Custos', x=['Análise'], y=[dados['custo_total']], marker_color='#FF6B6B'),
                go.Bar(name='Lucro', x=['Análise'], y=[dados['lucro_bruto']], marker_color='#4ECDC4')
            ])
           fig.update_layout(
                title='Composição Receita vs Custos vs Lucro',
                barmode='stack',
                yaxis_title='Valor (R$)'
            )
           st.plotly_chart(fig, use_container_width=True)
       else:
           st.info("Nenhuma venda no período selecionado.")

    with tab2:
        st.subheader("Análise de Produtos")

        ranking_produtos = get_dataframe("""
            SELECT 
                p.nome,
                p.categoria,
                SUM(v.quantidade) as quantidade_vendida,
                SUM(v.total) as receita,
                SUM(v.quantidade * p.custo_producao) as custo,
                (SUM(v.total) - SUM(v.quantidade * p.custo_producao)) as lucro,
                ((SUM(v.total) - SUM(v.quantidade * p.custo_producao)) / SUM(v.total) * 100) as margem
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda >= ?
            GROUP BY p.id, p.nome, p.categoria
            ORDER BY receita DESC
        """, (datetime.now().date() - timedelta(days=30),))

        if not ranking_produtos.empty:
    # top produtos por receita
            st.subheader("🏆 Top Produtos por Receita (Últimos 30 dias)")
            fig = px.bar(
                ranking_produtos.head(20), 
                x='nome', 
                y='receita',
                text='receita',              # mostra os valores nas barras
                color='margem',              # cor baseada na margem
                title="Receita por Produto",
                color_continuous_scale=['#CFF5E0', '#5C977C'],  # degradê do verde claro ao verde forte
                labels={'margem': 'Margem (%)', 'receita': 'Receita (R$)'}
            )
            fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
            fig.update_layout(xaxis_tickangle=-45,
                            plot_bgcolor='#F6FAF8',
                            paper_bgcolor='#F6FAF8',
                            font=dict(color='#1F2A27', family='sans serif')
                            )
            st.plotly_chart(fig, use_container_width=True)

            # tabela completa
            st.subheader("📋 Ranking Completo")
            st.dataframe(
        ranking_produtos.style.format({
            'receita': 'R$ {:.2f}',
            'custo': 'R$ {:.2f}',
            'lucro': 'R$ {:.2f}',
            'margem': '{:.1f}%'
        }),
        use_container_width=True,
        column_config={
            "margem": st.column_config.ProgressColumn(
                "Margem",
                format="%d%%",
                min_value=0,
                max_value=100,
                width="small"
            )
    }
)
        else:
            st.info("Nenhuma venda registrada nos últimos 30 dias.")

    with tab3:
        st.subheader("Análise por Período")
        # Vendas por dia da semana
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
                SUM(quantidade) as produtos_vendidos
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
                    text='faturamento',  # rótulos nas barras
                    title="Faturamento por Dia da Semana",
                    color_discrete_sequence=['#5C977C']  # cor tema
                )
                fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                fig.update_layout(
                    plot_bgcolor='#F6FAF8',
                    paper_bgcolor='#F6FAF8',
                    font=dict(color='#1F2A27', family='sans serif')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    vendas_semana,
                    x='dia_semana',
                    y='produtos_vendidos',
                    text='produtos_vendidos',  # rótulos nas barras
                    title="Produtos Vendidos por Dia da Semana",
                    color_discrete_sequence=['#5C977C']
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='#F6FAF8',
                    paper_bgcolor='#F6FAF8',
                    font=dict(color='#1F2A27', family='sans serif')
                )
                st.plotly_chart(fig, use_container_width=True)



