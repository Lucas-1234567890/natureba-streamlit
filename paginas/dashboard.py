import streamlit as st
import pandas as pd
from funcoesAux import get_dataframe
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

# -----------------------------
# Dashboard com Atalhos
# -----------------------------
def dashboard():
    st.markdown('<div class="main-header"><h1>🍞 Dashboard - Natureba</h1></div>', unsafe_allow_html=True)

    # =============================
    # SEÇÃO DE ATALHOS RÁPIDOS
    # =============================
    st.subheader("⚡ Ações Rápidas do Dia")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛒 Nova Venda", use_container_width=True, type="primary"):
            st.session_state['menu_escolha'] = "💰 Vendas"
            st.rerun()
    
    with col2:
        if st.button("🍞 Registrar Produção", use_container_width=True, type="primary"):
            st.session_state['menu_escolha'] = "📋 Receitas & Produção"
            st.rerun()
    
    with col3:
        if st.button("📦 Consultar Estoque", use_container_width=True, type="primary"):
            st.session_state['menu_escolha'] = "📦 Estoque"
            st.rerun()
    
    st.markdown("---")
    
    # =============================
    # ALERTAS E NOTIFICAÇÕES
    # =============================
    st.subheader("🔔 Alertas e Notificações")
    
    # Verificar estoque baixo de ingredientes
    ingredientes_baixos = get_dataframe("""
        SELECT nome, estoque_atual, unidade
        FROM ingredientes
        WHERE estoque_atual <= 5 AND estoque_atual > 0
        ORDER BY estoque_atual ASC
        LIMIT 5
    """)
    
    # Verificar estoque zerado
    ingredientes_zerados = get_dataframe("""
        SELECT COUNT(*) as total
        FROM ingredientes
        WHERE estoque_atual <= 0
    """)
    
    # Estoque de produtos prontos baixo
    produtos_baixos = get_dataframe("""
        SELECT p.nome, ep.quantidade_atual
        FROM estoque_pronto ep
        JOIN produtos p ON ep.produto_id = p.id
        WHERE ep.quantidade_atual <= 10 AND ep.quantidade_atual > 0
        ORDER BY ep.quantidade_atual ASC
        LIMIT 5
    """)
    
    alerta_col1, alerta_col2 = st.columns(2)
    
    with alerta_col1:
        if not ingredientes_zerados.empty and ingredientes_zerados.iloc[0]['total'] > 0:
            st.error(f"🔴 **{ingredientes_zerados.iloc[0]['total']} ingrediente(s) zerado(s)!**")
        
        if not ingredientes_baixos.empty:
            st.warning("🟡 **Ingredientes com estoque baixo:**")
            for _, item in ingredientes_baixos.iterrows():
                st.write(f"• {item['nome']}: {item['estoque_atual']:.2f} {item['unidade']}")
    
    with alerta_col2:
        if not produtos_baixos.empty:
            st.warning("🟡 **Produtos prontos com estoque baixo:**")
            for _, item in produtos_baixos.iterrows():
                st.write(f"• {item['nome']}: {item['quantidade_atual']:.0f} unidades")
    
    st.markdown("---")
    
    # =============================
    # FILTRO GLOBAL DE PERÍODO
    # =============================
    st.subheader("📊 Análise Financeira")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", value=datetime(2025,1,1))
    with col2:
        data_fim = st.date_input("Data Fim", value=datetime.now().date())

    # =============================
    # MÉTRICAS FINANCEIRAS
    # =============================
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
    st.subheader("💹 Indicadores do Período")

    cols = st.columns(6)

    cols[0].markdown(f"<div style='font-size:12px'>💰 Receita<br><b>{format_brl(receita_total)}</b></div>", unsafe_allow_html=True)
    cols[1].markdown(f"<div style='font-size:12px'>💸 Custos Fixos<br><b>{format_brl(custos_fixos)}</b></div>", unsafe_allow_html=True)
    cols[2].markdown(f"<div style='font-size:12px'>🛠 Custos Variáveis<br><b>{format_brl(custos_variaveis)}</b></div>", unsafe_allow_html=True)
    cols[3].markdown(f"<div style='font-size:12px'>📊 Margem Contrib.<br><b>{format_percent(margem_contrib_percent)}</b></div>", unsafe_allow_html=True)
    cols[4].markdown(f"<div style='font-size:12px'>📈 Lucro Líquido<br><b>{format_brl(lucro_liquido)}</b></div>", unsafe_allow_html=True)
    cols[5].markdown(f"<div style='font-size:12px'>🎯 Margem Líquida<br><b>{format_percent(margem_liquida)}</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # =============================
    # RESUMO DIÁRIO DE HOJE
    # =============================
    st.subheader("📅 Resumo de Hoje")
    
    hoje = datetime.now().date()
    vendas_hoje = get_dataframe("""
        SELECT COUNT(*) as total_vendas, 
               COALESCE(SUM(total), 0) as faturamento_hoje
        FROM vendas
        WHERE data_venda = ?
    """, (hoje,))
    
    if not vendas_hoje.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("🛒 Vendas Hoje", int(vendas_hoje.iloc[0]['total_vendas']))
        c2.metric("💰 Faturamento Hoje", format_brl(vendas_hoje.iloc[0]['faturamento_hoje']))
        
        # Meta diária (exemplo: R$ 500)
        meta_diaria = 500.0
        percentual_meta = (vendas_hoje.iloc[0]['faturamento_hoje'] / meta_diaria * 100) if meta_diaria > 0 else 0
        c3.metric("🎯 Meta Diária", f"{percentual_meta:.1f}%", delta=f"Meta: {format_brl(meta_diaria)}")
    
    st.markdown("---")

    # =============================
    # GRÁFICOS
    # =============================
    # Vendas por produto
    st.subheader("📊 Produtos Mais Vendidos")
    vendas_produto = get_dataframe(f"""
        SELECT 
            p.nome, 
            SUM(iv.quantidade) AS total_vendido, 
            SUM(iv.subtotal) AS faturamento
        FROM itens_venda iv
        JOIN produtos p ON iv.produto_id = p.id
        JOIN vendas v ON iv.venda_id = v.id
        WHERE v.data_venda BETWEEN ? AND ?
        GROUP BY p.nome
        ORDER BY total_vendido DESC
        LIMIT 10
    """, (data_inicio, data_fim))

    if not vendas_produto.empty:
        fig_produtos = px.bar(
            vendas_produto, y='nome', x='total_vendido', text='total_vendido', orientation='h',
            labels={'nome':'Produto', 'total_vendido':'Qtd Vendida'},
            title="Top 10 Produtos",
            color='total_vendido', color_continuous_scale=['#5C977C', '#7FBFA0']
        )
        fig_produtos.update_traces(textposition='inside', insidetextanchor='middle', textfont=dict(color='white'))
        fig_produtos.update_layout(margin=dict(l=150,r=20,t=40,b=20))
        st.plotly_chart(fig_produtos, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período selecionado.")

    # Evolução de receita
    st.subheader("📈 Evolução de Receita")
    agrupar_por_mes = st.checkbox("📅 Agrupar por Mês", value=False)
    
    if agrupar_por_mes:
        vendas_agrupadas = get_dataframe(f"""
            SELECT strftime('%Y-%m', data_venda) as mes, SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ?
            GROUP BY mes
            ORDER BY mes
        """, (data_inicio, data_fim))
        eixo_x = 'mes'
        titulo = "Evolução de Receita por Mês"
    else:
        vendas_agrupadas = get_dataframe(f"""
            SELECT data_venda, SUM(total) as faturamento
            FROM vendas
            WHERE data_venda BETWEEN ? AND ?
            GROUP BY data_venda
            ORDER BY data_venda
        """, (data_inicio, data_fim))
        eixo_x = 'data_venda'
        titulo = "Evolução de Receita por Dia"

    if not vendas_agrupadas.empty:
        fig = px.line(vendas_agrupadas, x=eixo_x, y='faturamento', markers=True,
                      labels={eixo_x:'Data','faturamento':'Faturamento (R$)'}, title=titulo)
        fig.update_traces(line_color='#5C977C', marker_color='#7FBFA0')
        fig.update_layout(margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada no período selecionado.")
    
    # =============================
    # PRODUTOS PRONTOS EM ESTOQUE
    # =============================
    st.markdown("---")
    st.subheader("🍞 Estoque de Produtos Prontos")
    
    estoque_pronto = get_dataframe("""
        SELECT p.nome, ep.quantidade_atual, p.categoria
        FROM estoque_pronto ep
        JOIN produtos p ON ep.produto_id = p.id
        WHERE ep.quantidade_atual > 0
        ORDER BY ep.quantidade_atual DESC
    """)
    
    if not estoque_pronto.empty:
        fig_estoque = px.bar(
            estoque_pronto,
            x='nome',
            y='quantidade_atual',
            text='quantidade_atual',
            color='categoria',
            title="Estoque Atual de Produtos Prontos",
            labels={'quantidade_atual': 'Quantidade', 'nome': 'Produto'}
        )
        fig_estoque.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig_estoque, use_container_width=True)
    else:
        st.info("Nenhum produto pronto em estoque no momento")