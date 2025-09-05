import streamlit as st
import pandas as pd
from banco import get_dataframe, iniciar_database
from datetime import datetime, timedelta
import plotly.express as px

def dashboard():
    st.markdown('<div class="main-header"><h1>🍞 Dashboard - Natureba</h1></div>', unsafe_allow_html=True)

    # ---------- MÉTRICAS PRINCIPAIS ----------
    with st.container():
        col1, col2, col3, col4 = st.columns([1.2,1.2,1.2,1.2])  # largura proporcional

        hoje = datetime.now().date()
        faturamento_hoje = get_dataframe(
            "SELECT SUM(total) as total FROM vendas WHERE data_venda = ?", (hoje,)
        )['total'].iloc[0] or 0

        primeiro_dia_mes = hoje.replace(day=1)
        faturamento_mes = get_dataframe(
            "SELECT SUM(total) as total FROM vendas WHERE data_venda >= ?", (primeiro_dia_mes,)
        )['total'].iloc[0] or 0

        produtos_vendidos_hoje = get_dataframe(
            "SELECT SUM(quantidade) as total FROM vendas WHERE data_venda = ?", (hoje,)
        )['total'].iloc[0] or 0

        vendas_com_custo = get_dataframe("""
            SELECT SUM(v.total) as receita, SUM(v.quantidade * p.custo_producao) as custo
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda >= ?
        """, (primeiro_dia_mes,))

        receita_total = vendas_com_custo['receita'].iloc[0] or 0
        custo_total = vendas_com_custo['custo'].iloc[0] or 0
        margem_media = ((receita_total - custo_total) / receita_total * 100) if receita_total > 0 else 0

        col1.metric("💰 Faturamento Hoje", f"R$ {faturamento_hoje:.2f}")
        col2.metric("📅 Faturamento Mês", f"R$ {faturamento_mes:.2f}")
        col3.metric("🥖 Pães Vendidos Hoje", f"{int(produtos_vendidos_hoje)}")
        col4.metric("📈 Margem Média", f"{margem_media:.1f}%")

    st.markdown("---")  # separador

    # ---------- GRÁFICOS ----------
    with st.container():
        col1, col2 = st.columns([1.5,1.5])  # mais espaço para os gráficos

        with col1:
            st.subheader("📊 Vendas por Produto (Últimos 7 dias)")
            vendas_produto = get_dataframe("""
                SELECT p.nome, SUM(v.quantidade) as total_vendido, SUM(v.total) as faturamento
                FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                WHERE v.data_venda >= ?
                GROUP BY p.nome
                ORDER BY total_vendido DESC
            """, (hoje - timedelta(days=7),))

            if not vendas_produto.empty:
                fig = px.bar(
                    vendas_produto,
                    x='nome',
                    y='total_vendido',
                    text='total_vendido',
                    labels={'nome': 'Produto', 'total_vendido': 'Quantidade Vendida'},
                    title="Produtos mais vendidos nos últimos 7 dias",
                    color='total_vendido',
                    color_continuous_scale=['#5C977C', '#7FBFA0']
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_tickangle=-45, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma venda registrada nos últimos 7 dias.")

        with col2:
            st.subheader("📈 Evolução de Vendas (Últimos 7 dias)")
            vendas_diarias = get_dataframe("""
                SELECT data_venda, SUM(total) as faturamento_diario, SUM(quantidade) as produtos_vendidos
                FROM vendas
                WHERE data_venda >= ?
                GROUP BY data_venda
                ORDER BY data_venda
            """, (hoje - timedelta(days=7),))

            if not vendas_diarias.empty:
                fig = px.line(
                    vendas_diarias,
                    x='data_venda',
                    y='faturamento_diario',
                    markers=True,
                    labels={'data_venda': 'Data', 'faturamento_diario': 'Faturamento (R$)'},
                    title="Evolução do Faturamento Diário",
                )
                fig.update_traces(line_color='#5C977C', marker_color='#7FBFA0')
                fig.update_layout(margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma venda registrada nos últimos 7 dias.")

    st.markdown("---")

    # ---------- TOP 5 PRODUTOS LUCRATIVOS ----------
    st.subheader("💎 Top 5 Produtos Mais Lucrativos")
    produtos_lucrativos = get_dataframe("""
        SELECT p.nome, p.preco_venda, p.custo_producao,
               (p.preco_venda - p.custo_producao) as lucro_unitario,
               ((p.preco_venda - p.custo_producao) / p.preco_venda * 100) as margem,
               COALESCE(SUM(v.quantidade), 0) as total_vendido
        FROM produtos p
        LEFT JOIN vendas v ON p.id = v.produto_id AND v.data_venda >= ?
        WHERE p.ativo = 1
        GROUP BY p.id, p.nome, p.preco_venda, p.custo_producao
        ORDER BY margem DESC
        LIMIT 5
    """, (hoje - timedelta(days=30),))

    if not produtos_lucrativos.empty:
        st.dataframe(
            produtos_lucrativos[['nome', 'preco_venda', 'custo_producao', 'lucro_unitario', 'margem', 'total_vendido']].style.format({
                'preco_venda': 'R$ {:.2f}',
                'custo_producao': 'R$ {:.2f}',
                'lucro_unitario': 'R$ {:.2f}',
                'margem': '{:.1f}%',
                'total_vendido': '{:.0f}'
            }),
            use_container_width=True
        )


        


        
