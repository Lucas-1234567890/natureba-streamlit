import streamlit as st
import pandas as pd
from banco import get_dataframe
from datetime import datetime
import plotly.express as px
from dateutil.relativedelta import relativedelta

# -----------------------------
# Funções de formatação
# -----------------------------
def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percent(valor):
    return f"{valor:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def calcula_delta_atual_anterior(valor_atual, valor_anterior, tipo='valor'):
    if tipo == 'percent':
        delta = ((valor_atual - valor_anterior)/valor_anterior*100) if valor_anterior else 0
        return format_percent(delta)
    else:
        delta = valor_atual - valor_anterior
        return format_brl(delta)

# -----------------------------
# Dashboard
# -----------------------------
def dashboard():
    st.markdown('<div class="main-header"><h1>🍞 Dashboard - Natureba</h1></div>', unsafe_allow_html=True)

    # -----------------------------
    # FILTRO GLOBAL DE PERÍODO
    # -----------------------------
    st.subheader("⏳ Filtro de Período")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", value=datetime(2025,1,1))
    with col2:
        data_fim = st.date_input("Data Fim", value=datetime.now().date())

    # -----------------------------
    # FILTRO DE PRODUTO
    # -----------------------------
    produtos_disponiveis = get_dataframe("SELECT id, nome FROM produtos WHERE ativo=1 ORDER BY nome")
    produtos_dict = {row['nome']: row['id'] for _, row in produtos_disponiveis.iterrows()}
    produtos_dict["Todos"] = 0
    selecionado = st.selectbox("Filtrar por Produto", sorted(produtos_dict.keys()))
    produto_param = produtos_dict[selecionado] if selecionado != "Todos" else None

    # -----------------------------
    # FUNÇÃO AUXILIAR PARA PARAMETROS DE PRODUTO
    # -----------------------------
    def build_where(query_base):
        # Ajuste mínimo: usa produto_id sem alias para evitar referências a 'v' quando o FROM não declara alias
        if produto_param:
            return query_base + " AND produto_id = ?"
        return query_base

    # -----------------------------
    # MÉTRICAS FINANCEIRAS
    # -----------------------------
    # Receita
    query_receita = "SELECT COALESCE(SUM(total),0) as total FROM vendas v WHERE data_venda BETWEEN ? AND ?"
    if produto_param:
        receita_total = float(get_dataframe(query_receita + " AND v.produto_id = ?", (data_inicio, data_fim, produto_param))['total'].iloc[0])
    else:
        receita_total = float(get_dataframe(query_receita, (data_inicio, data_fim))['total'].iloc[0])

    # Custos Variáveis
    query_custos_var = """
        SELECT COALESCE(SUM(m.quantidade * i.preco_kg),0) AS total_custo
        FROM movimentacoes_estoque m
        JOIN ingredientes i ON m.ingrediente_id = i.id
        JOIN vendas v ON v.data_venda BETWEEN ? AND ?  -- vínculo de período
    """
    custos_variaveis = float(get_dataframe(query_custos_var, (data_inicio, data_fim))['total_custo'].iloc[0])

    # Custos Fixos
    query_custos_fixos = "SELECT COALESCE(SUM(valor),0) as total_custo_fixo FROM custos_operacionais WHERE recorrente=1 AND data_custo BETWEEN ? AND ?"
    custos_fixos = float(get_dataframe(query_custos_fixos, (data_inicio, data_fim))['total_custo_fixo'].iloc[0])

    # Margens
    margem_contrib_total = receita_total - custos_variaveis
    margem_contrib_percent = (margem_contrib_total / receita_total * 100) if receita_total else 0
    ponto_equilibrio = (custos_fixos / (margem_contrib_percent / 100)) if margem_contrib_percent else 0
    margem_seguranca = ((receita_total - ponto_equilibrio) / receita_total * 100) if receita_total else 0

    st.subheader("💹 Métricas Financeiras")
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Receita", format_brl(receita_total))
    col2.metric("💸 Custos Fixos", format_brl(custos_fixos))
    col3.metric("🛠 Custos Variáveis", format_brl(custos_variaveis))

    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Margem de Contribuição", format_percent(margem_contrib_percent))
    col2.metric("⚖️ Ponto de Equilíbrio", format_brl(ponto_equilibrio))
    col3.metric("🛡 Margem de Segurança", format_percent(margem_seguranca))

    st.markdown("---")

    # -----------------------------
    # GRÁFICOS
    # -----------------------------
    # Ajuste mínimo: onde for usado sem alias, usa 'produto_id' sem o prefixo 'v.'
    where_produto = "" if produto_param is None else "AND produto_id = ?"
    params = (data_inicio, data_fim) if produto_param is None else (data_inicio, data_fim, produto_param)

    # Vendas por produto
    st.subheader("📊 Vendas por Produto")
    vendas_produto = get_dataframe(f"""
        SELECT p.nome, SUM(v.quantidade) as total_vendido, SUM(v.total) as faturamento
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda BETWEEN ? AND ? {where_produto}
        GROUP BY p.nome
        ORDER BY total_vendido DESC
    """, params)
    if not vendas_produto.empty:
        fig_produtos = px.bar(
            vendas_produto, y='nome', x='total_vendido', text='total_vendido', orientation='h',
            labels={'nome':'Produto', 'total_vendido':'Qtd Vendida'},
            title="Produtos mais vendidos",
            color='total_vendido', color_continuous_scale=['#5C977C', '#7FBFA0']
        )
        fig_produtos.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color='white'))
        fig_produtos.update_layout(margin=dict(l=150,r=20,t=40,b=20))
        st.plotly_chart(fig_produtos, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período/produto selecionado.")

    # Evolução de receita
    st.subheader("📈 Evolução de Receita")
    agrupar_por_mes = st.checkbox("📅 Agrupar por Mês", value=True)
    if agrupar_por_mes:
        vendas_agrupadas = get_dataframe(f"""
            SELECT strftime('%Y-%m', data_venda) as mes, SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ? {where_produto}
            GROUP BY mes
            ORDER BY mes
        """, params)
        eixo_x = 'mes'
        titulo = "Evolução de Receita por Mês"
    else:
        vendas_agrupadas = get_dataframe(f"""
            SELECT data_venda, SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ? {where_produto}
            GROUP BY data_venda
            ORDER BY data_venda
        """, params)
        eixo_x = 'data_venda'
        titulo = "Evolução de Receita por Dia"

    if not vendas_agrupadas.empty:
        fig = px.line(vendas_agrupadas, x=eixo_x, y='faturamento', markers=True,
                      labels={eixo_x:'Data','faturamento':'Faturamento (R$)'}, title=titulo)
        fig.update_traces(line_color='#5C977C', marker_color='#7FBFA0')
        fig.update_layout(margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período/produto selecionado.")
