import streamlit as st
import pandas as pd
from banco import get_dataframe
from datetime import datetime
import plotly.express as px
from dateutil.relativedelta import relativedelta

    # Função rápida para formatar no padrão BR
def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(valor):
    return f"{valor:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def calcula_delta_atual_anterior(valor_atual, valor_anterior, tipo='valor'):
    """
    Calcula o delta entre valor atual e anterior.
    
    Parâmetros:
    - valor_atual: número atual
    - valor_anterior: número do período anterior
    - tipo: 'valor' para delta em R$, 'percent' para percentual
    
    Retorna:
    - delta formatado para st.metric
    """
    if tipo == 'percent':
        delta = ((valor_atual - valor_anterior)/valor_anterior*100) if valor_anterior else 0
        return format_percent(delta)
    else:  # valor monetário
        delta = valor_atual - valor_anterior
        return format_brl(delta)


def dashboard():
    st.markdown('<div class="main-header"><h1>🍞 Dashboard - Natureba</h1></div>', unsafe_allow_html=True)

    # -----------------------------
    # FILTRO GLOBAL DE PERÍODO
    # -----------------------------
    st.subheader("⏳ Filtro de Período")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime(2025,1,1))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

    # -----------------------------
    # MÉTRICAS FINANCEIRAS
    # -----------------------------
    receita_total = float(get_dataframe(
        "SELECT SUM(total) as total FROM vendas WHERE data_venda BETWEEN ? AND ?", 
        (data_inicio, data_fim)
    )['total'].iloc[0] or 0)

    custos_variaveis = float(get_dataframe("""
        SELECT SUM(p.custo_producao * v.quantidade) as total_custo
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda BETWEEN ? AND ?
    """, (data_inicio, data_fim))['total_custo'].iloc[0] or 0)

    custos_fixos = float(get_dataframe("""
        SELECT SUM(valor) as total_custo_fixo
        FROM custos_operacionais
        WHERE recorrente = 1 AND data_custo BETWEEN ? AND ?
    """, (data_inicio, data_fim))['total_custo_fixo'].iloc[0] or 0)

    margem_contrib_total = receita_total - custos_variaveis
    margem_contrib_percent = (margem_contrib_total / receita_total * 100) if receita_total > 0 else 0
    ponto_equilibrio = (custos_fixos / (margem_contrib_percent / 100)) if margem_contrib_percent > 0 else 0
    margem_seguranca = ((receita_total - ponto_equilibrio) / receita_total * 100) if receita_total > 0 else 0


    st.subheader("💹 Métricas Financeiras")

    # -----------------------------
    # CALCULO DO MÊS ANTERIOR
    # -----------------------------
    
    mes_anterior_inicio = (data_inicio - relativedelta(months=1)).replace(day=1)
    mes_anterior_fim = (data_inicio - relativedelta(months=1)).replace(day=28)  # garante pegar todo mês

    # Receita do mês anterior
    receita_mes_anterior = float(get_dataframe(
        "SELECT SUM(total) as total FROM vendas WHERE data_venda BETWEEN ? AND ?", 
        (mes_anterior_inicio, mes_anterior_fim)
    )['total'].iloc[0] or 0)

    # Custos variáveis do mês anterior
    custos_variaveis_mes_anterior = float(get_dataframe("""
        SELECT SUM(p.custo_producao * v.quantidade) as total_custo
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda BETWEEN ? AND ?
    """, (mes_anterior_inicio, mes_anterior_fim))['total_custo'].iloc[0] or 0)

    # Custos fixos do mês anterior
    custos_fixos_mes_anterior = float(get_dataframe("""
        SELECT SUM(valor) as total_custo_fixo
        FROM custos_operacionais
        WHERE recorrente = 1 AND data_custo BETWEEN ? AND ?
    """, (mes_anterior_inicio, mes_anterior_fim))['total_custo_fixo'].iloc[0] or 0)

    # -----------------------------
    # EXIBIÇÃO DAS MÉTRICAS COM DELTA (MoM)
    # -----------------------------
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "💰 Receita", 
                format_brl(receita_total),
                delta=calcula_delta_atual_anterior(receita_total, receita_mes_anterior, tipo='percent')
            )
        with col2:
            st.metric(
                "💸 Custos Fixos", 
                format_brl(custos_fixos),
                delta=calcula_delta_atual_anterior(custos_fixos, custos_fixos_mes_anterior, tipo='percent')
            )
        with col3:
            st.metric(
                "🛠 Custos Variáveis", 
                format_brl(custos_variaveis),
                delta=calcula_delta_atual_anterior(custos_variaveis, custos_variaveis_mes_anterior, tipo='percent')
            )

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            margem_contrib_total_mes_anterior = receita_mes_anterior - custos_variaveis_mes_anterior
            margem_contrib_percent_mes_anterior = (margem_contrib_total_mes_anterior / receita_mes_anterior * 100) if receita_mes_anterior > 0 else 0

            st.metric(
                "📊 Margem de Contribuição",
                format_percent(margem_contrib_percent),
                delta=calcula_delta_atual_anterior(margem_contrib_percent, margem_contrib_percent_mes_anterior, tipo='percent')
            )
        with col2:
            ponto_equilibrio_mes_anterior = (custos_fixos_mes_anterior / (margem_contrib_percent_mes_anterior / 100)) if margem_contrib_percent_mes_anterior > 0 else 0
            st.metric(
                "⚖️ Ponto de Equilíbrio",
                format_brl(ponto_equilibrio),
                delta=calcula_delta_atual_anterior(ponto_equilibrio, ponto_equilibrio_mes_anterior, tipo='percent')
            )
        with col3:
            margem_seguranca_mes_anterior = ((receita_mes_anterior - ponto_equilibrio_mes_anterior) / receita_mes_anterior * 100) if receita_mes_anterior > 0 else 0
            st.metric(
                "🛡 Margem de Segurança",
                format_percent(margem_seguranca),
                delta=calcula_delta_atual_anterior(margem_seguranca, margem_seguranca_mes_anterior, tipo='percent')
            )
            
    st.markdown("---")

    # -----------------------------
    # VENDAS POR PRODUTO
    # -----------------------------
    st.subheader("📊 Vendas por Produto")
    vendas_produto = get_dataframe("""
        SELECT p.nome, SUM(v.quantidade) as total_vendido, SUM(v.total) as faturamento
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda BETWEEN ? AND ?
        GROUP BY p.nome
        ORDER BY total_vendido DESC
    """, (data_inicio, data_fim))

    if not vendas_produto.empty:
        fig_produtos = px.bar(
            vendas_produto,
            y='nome',            # Categoria no eixo Y
            x='total_vendido',   # Valores no eixo X
            text='total_vendido',
            orientation='h',
            labels={'nome':'Produto', 'total_vendido':'Quantidade Vendida'},
            title="Produtos mais vendidos",
            color='total_vendido',
            color_continuous_scale=['#5C977C', '#7FBFA0']
        )
        # Melhor posicionamento do texto para barras horizontais
        fig_produtos.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color='white'))

        # Ajuste do layout
        fig_produtos.update_layout(
            margin=dict(l=150,r=20,t=40,b=20)  # Deixe margem maior à esquerda para nomes longos
        )
        
        st.plotly_chart(fig_produtos, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período selecionado.")


    # -----------------------------
    # EVOLUÇÃO DE RECEITA
    # -----------------------------
    st.subheader("📈 Evolução de Receita")
    agrupar_por_mes = st.checkbox("📅 Agrupar por Mês", value=True)

    if agrupar_por_mes:
        vendas_agrupadas = get_dataframe("""
            SELECT strftime('%Y-%m', data_venda) as mes, 
                   SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ?
            GROUP BY mes
            ORDER BY mes
        """, (data_inicio, data_fim))
        eixo_x = 'mes'
        titulo = "Evolução de Receita por Mês"
    else:
        vendas_agrupadas = get_dataframe("""
            SELECT data_venda, SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ?
            GROUP BY data_venda
            ORDER BY data_venda
        """, (data_inicio, data_fim))
        eixo_x = 'data_venda'
        titulo = "Evolução de Receita por Dia"

    if not vendas_agrupadas.empty:
        fig = px.line(
            vendas_agrupadas,
            x=eixo_x,
            y='faturamento',
            markers=True,
            labels={eixo_x: 'Data', 'faturamento':'Faturamento (R$)'},
            title=titulo
        )
        fig.update_traces(line_color='#5C977C', marker_color='#7FBFA0')
        fig.update_layout(margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período selecionado.")

    # -----------------------------
    # TOP 5 PRODUTOS LUCRATIVOS
    # -----------------------------
    st.subheader("💎 Top 5 Produtos Mais Lucrativos")
    produtos_lucrativos = get_dataframe("""
        SELECT p.nome, p.preco_venda, p.custo_producao,
               (p.preco_venda - p.custo_producao) as lucro_unitario,
               ((p.preco_venda - p.custo_producao) / p.preco_venda * 100) as margem,
               COALESCE(SUM(v.quantidade), 0) as total_vendido
        FROM produtos p
        LEFT JOIN vendas v ON p.id = v.produto_id AND v.data_venda BETWEEN ? AND ?
        WHERE p.ativo = 1
        GROUP BY p.id, p.nome, p.preco_venda, p.custo_producao
        ORDER BY margem DESC
        LIMIT 5
    """, (data_inicio, data_fim))

    if not produtos_lucrativos.empty:
        st.dataframe(
            produtos_lucrativos[['nome','preco_venda','custo_producao','lucro_unitario','margem','total_vendido']].style.format({
                'preco_venda':'R$ {:.2f}',
                'custo_producao':'R$ {:.2f}',
                'lucro_unitario':'R$ {:.2f}',
                'margem':'{:.1f}%',
                'total_vendido':'{:.0f}'
            }),
            use_container_width=True
        )
