# paginas/ml_insights.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from banco import get_dataframe
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

def modulo_ml_insights():
    """
    Módulo de Machine Learning para insights preditivos
    Modelos simples e práticos para gestão da padaria
    """
    st.header("🤖 ML Insights - Previsões Inteligentes")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Previsão Vendas", 
        "🏆 Produtos Recomendados", 
        "📦 Controle Estoque", 
        "💡 Insights Automáticos"
    ])
    
    # ===========================================
    # TAB 1: PREVISÃO DE VENDAS POR PRODUTO
    # ===========================================
    with tab1:
        st.subheader("📊 Previsão de Vendas")
        
        # Buscar dados históricos
        vendas_historico = get_dataframe("""
            SELECT 
                v.data_venda,
                p.nome as produto,
                p.categoria,
                v.quantidade,
                v.total,
                CASE strftime('%w', v.data_venda)
                    WHEN '0' THEN 'Domingo'
                    WHEN '1' THEN 'Segunda'
                    WHEN '2' THEN 'Terça'
                    WHEN '3' THEN 'Quarta'
                    WHEN '4' THEN 'Quinta'
                    WHEN '5' THEN 'Sexta'
                    WHEN '6' THEN 'Sábado'
                END as dia_semana,
                strftime('%m', v.data_venda) as mes,
                strftime('%d', v.data_venda) as dia
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda >= date('now', '-90 days')
            ORDER BY v.data_venda
        """)
        
        if vendas_historico.empty:
            st.warning("⚠️ Dados insuficientes. Cadastre pelo menos 30 dias de vendas.")
            return
        
        # Seleção de produto
        produtos_disponiveis = vendas_historico['produto'].unique()
        produto_selecionado = st.selectbox("Escolha o produto:", produtos_disponiveis)
        
        if st.button("🔮 Gerar Previsão"):
            previsao_result = gerar_previsao_vendas(vendas_historico, produto_selecionado)
            
            if previsao_result:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("📈 Previsão Próximos 7 dias", f"{previsao_result['previsao_7dias']:.0f} unidades")
                    st.metric("📊 Precisão do Modelo", f"{previsao_result['precisao']:.1f}%")
                
                with col2:
                    st.metric("💰 Receita Estimada", f"R$ {previsao_result['receita_estimada']:.2f}")
                    st.metric("📋 Recomendação Estoque", f"{previsao_result['estoque_recomendado']:.0f} unidades")
                
                # Gráfico de tendência
                fig = px.line(
                    previsao_result['historico_df'], 
                    x='data_venda', 
                    y='quantidade_acumulada',
                    title=f"Tendência de Vendas - {produto_selecionado}",
                    color_discrete_sequence=['#5C977C']
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Insights automáticos
                st.subheader("💡 Insights Automáticos")
                for insight in previsao_result['insights']:
                    st.info(f"💡 {insight}")
    
    # ===========================================
    # TAB 2: PRODUTOS RECOMENDADOS (CLUSTERING SIMPLES)
    # ===========================================
    with tab2:
        st.subheader("🎯 Produtos Recomendados")
        
        analise_produtos = get_dataframe("""
            SELECT 
                p.nome,
                p.categoria,
                p.preco_venda,
                COUNT(v.id) as freq_vendas,
                SUM(v.quantidade) as qtd_total,
                SUM(v.total) as receita_total,
                AVG(v.quantidade) as media_por_venda,
                MIN(v.data_venda) as primeira_venda,
                MAX(v.data_venda) as ultima_venda
            FROM produtos p
            LEFT JOIN vendas v ON p.id = v.produto_id
            WHERE p.ativo = 1
            GROUP BY p.id, p.nome, p.categoria, p.preco_venda
        """)
        
        if not analise_produtos.empty:
            # Calcular scores de performance
            analise_produtos['score_freq'] = analise_produtos['freq_vendas'] / analise_produtos['freq_vendas'].max()
            analise_produtos['score_receita'] = analise_produtos['receita_total'] / analise_produtos['receita_total'].max()
            analise_produtos['score_geral'] = (analise_produtos['score_freq'] + analise_produtos['score_receita']) / 2
            
            # Categorizar produtos
            analise_produtos['categoria_performance'] = pd.cut(
                analise_produtos['score_geral'], 
                bins=[0, 0.3, 0.7, 1.0], 
                labels=['🔴 Baixa', '🟡 Média', '🟢 Alta']
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top Performers")
                top_produtos = analise_produtos.nlargest(5, 'score_geral')
                for _, produto in top_produtos.iterrows():
                    st.metric(
                        produto['nome'],
                        f"Score: {produto['score_geral']:.2f}",
                        f"Receita: R$ {produto['receita_total']:.2f}"
                    )
            
            with col2:
                st.subheader("⚡ Oportunidades")
                baixa_performance = analise_produtos[analise_produtos['categoria_performance'] == '🔴 Baixa']
                if not baixa_performance.empty:
                    for _, produto in baixa_performance.head(3).iterrows():
                        st.warning(f"📉 {produto['nome']}: Considere promoção ou reformulação")
                else:
                    st.success("✅ Todos os produtos têm boa performance!")
            
            # Gráfico de dispersão
            fig = px.scatter(
                analise_produtos,
                x='freq_vendas',
                y='receita_total',
                color='categoria',
                size='qtd_total',
                hover_data=['nome'],
                title="Análise de Performance dos Produtos",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ===========================================
    # TAB 3: CONTROLE INTELIGENTE DE ESTOQUE
    # ===========================================
    with tab3:
        st.subheader("📦 Gestão Inteligente de Estoque")
        
        # Análise de movimentação de estoque
        estoque_data = get_dataframe("""
            SELECT 
                i.nome,
                i.estoque_atual,
                i.preco_kg,
                COUNT(m.id) as movimentacoes,
                COALESCE(SUM(CASE WHEN m.tipo='saida' THEN m.quantidade ELSE 0 END), 0) as total_saidas,
                COALESCE(AVG(CASE WHEN m.tipo='saida' THEN m.quantidade ELSE NULL END), 0) as media_saida,
                MAX(m.data_movimentacao) as ultima_movimentacao
            FROM ingredientes i
            LEFT JOIN movimentacoes_estoque m ON i.id = m.ingrediente_id
            WHERE m.data_movimentacao >= date('now', '-30 days') OR m.data_movimentacao IS NULL
            GROUP BY i.id, i.nome, i.estoque_atual, i.preco_kg
        """)
        
        if not estoque_data.empty:
            # Calcular dias de estoque restante
            estoque_data['dias_restantes'] = np.where(
                estoque_data['media_saida'] > 0,
                estoque_data['estoque_atual'] / estoque_data['media_saida'],
                999  # Produto sem saída recente
            )
            
            # Classificar criticidade
            def classificar_criticidade(dias):
                if dias <= 3:
                    return "🔴 Crítico"
                elif dias <= 7:
                    return "🟡 Atenção"
                elif dias <= 15:
                    return "🟢 Normal"
                else:
                    return "🔵 Sobra"
            
            estoque_data['status'] = estoque_data['dias_restantes'].apply(classificar_criticidade)
            
            # Métricas gerais
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔴 Críticos", len(estoque_data[estoque_data['status'] == '🔴 Crítico']))
            col2.metric("🟡 Atenção", len(estoque_data[estoque_data['status'] == '🟡 Atenção']))
            col3.metric("🟢 Normal", len(estoque_data[estoque_data['status'] == '🟢 Normal']))
            col4.metric("🔵 Sobra", len(estoque_data[estoque_data['status'] == '🔵 Sobra']))
            
            # Lista de prioridades
            st.subheader("⚠️ Prioridades de Compra")
            criticos = estoque_data[estoque_data['status'] == '🔴 Crítico'].sort_values('dias_restantes')
            
            if not criticos.empty:
                for _, item in criticos.iterrows():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.error(f"🔴 {item['nome']}")
                    with col2:
                        st.write(f"📅 {item['dias_restantes']:.1f} dias")
                    with col3:
                        st.write(f"💰 R$ {item['preco_kg']:.2f}/kg")
            else:
                st.success("✅ Nenhum item crítico no momento!")
    
    # ===========================================
    # TAB 4: INSIGHTS AUTOMÁTICOS
    # ===========================================
    with tab4:
        st.subheader("🧠 Insights Automáticos do Negócio")
        
        # Análise de sazonalidade
        sazonalidade = get_dataframe("""
            SELECT 
                CASE strftime('%w', data_venda)
                    WHEN '0' THEN 'Domingo'
                    WHEN '1' THEN 'Segunda'
                    WHEN '2' THEN 'Terça'
                    WHEN '3' THEN 'Quarta'
                    WHEN '4' THEN 'Quinta'
                    WHEN '5' THEN 'Sexta'
                    WHEN '6' THEN 'Sábado'
                END as dia_semana,
                COUNT(*) as num_vendas,
                SUM(total) as receita_total,
                AVG(total) as ticket_medio
            FROM vendas
            WHERE data_venda >= date('now', '-30 days')
            GROUP BY strftime('%w', data_venda)
            ORDER BY strftime('%w', data_venda)
        """)
        
        if not sazonalidade.empty:
            # Identificar melhor e pior dia
            melhor_dia = sazonalidade.loc[sazonalidade['receita_total'].idxmax()]
            pior_dia = sazonalidade.loc[sazonalidade['receita_total'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"🏆 Melhor dia: {melhor_dia['dia_semana']} - R$ {melhor_dia['receita_total']:.2f}")
            with col2:
                st.info(f"📉 Menor movimento: {pior_dia['dia_semana']} - R$ {pior_dia['receita_total']:.2f}")
            
            # Gráfico de sazonalidade
            fig = px.bar(
                sazonalidade,
                x='dia_semana',
                y='receita_total',
                title="Receita por Dia da Semana (Últimos 30 dias)",
                color='receita_total',
                color_continuous_scale=['#EAF3EF', '#5C977C']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análise de crescimento
        crescimento = get_dataframe("""
            SELECT 
                strftime('%Y-%m', data_venda) as mes,
                SUM(total) as receita,
                COUNT(DISTINCT data_venda) as dias_ativos,
                SUM(total) / COUNT(DISTINCT data_venda) as receita_por_dia
            FROM vendas
            WHERE data_venda >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', data_venda)
            ORDER BY mes
        """)
        
        if len(crescimento) >= 2:
            # Calcular taxa de crescimento
            crescimento['crescimento_mes'] = crescimento['receita'].pct_change() * 100
            ultimo_crescimento = crescimento['crescimento_mes'].iloc[-1]
            
            if ultimo_crescimento > 0:
                st.success(f"📈 Crescimento mensal: +{ultimo_crescimento:.1f}%")
            else:
                st.warning(f"📉 Variação mensal: {ultimo_crescimento:.1f}%")
        
        # Recomendações automáticas
        st.subheader("💡 Recomendações Personalizadas")
        
        recomendacoes = gerar_recomendacoes_automaticas()
        for rec in recomendacoes:
            st.info(f"💡 {rec}")


def gerar_previsao_vendas(dados, produto):
    """
    Modelo simples de previsão usando Linear Regression
    """
    try:
        # Filtrar dados do produto
        produto_data = dados[dados['produto'] == produto].copy()
        
        if len(produto_data) < 7:
            return None
        
        # Preparar features temporais
        produto_data['data_venda'] = pd.to_datetime(produto_data['data_venda'])
        produto_data = produto_data.groupby('data_venda')['quantidade'].sum().reset_index()
        produto_data['dias_desde_inicio'] = (produto_data['data_venda'] - produto_data['data_venda'].min()).dt.days
        
        # Preparar dados para ML
        X = produto_data[['dias_desde_inicio']].values
        y = produto_data['quantidade'].values
        
        # Treinar modelo
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        # Fazer previsões
        ultimo_dia = produto_data['dias_desde_inicio'].max()
        proximos_dias = np.array([[ultimo_dia + i] for i in range(1, 8)])
        previsoes = modelo.predict(proximos_dias)
        previsoes = np.maximum(previsoes, 0)  # Não pode ser negativo
        
        # Calcular métricas
        y_pred = modelo.predict(X)
        precisao = max(0, r2_score(y, y_pred) * 100)
        
        # Buscar preço médio do produto
        preco_medio = dados[dados['produto'] == produto]['total'].sum() / dados[dados['produto'] == produto]['quantidade'].sum()
        
        # Adicionar coluna de quantidade acumulada para o gráfico
        produto_data['quantidade_acumulada'] = produto_data['quantidade'].cumsum()
        
        # Gerar insights
        insights = []
        media_vendas = produto_data['quantidade'].mean()
        previsao_media = previsoes.mean()
        
        if previsao_media > media_vendas * 1.2:
            insights.append(f"Vendas de {produto} devem aumentar 20% na próxima semana")
        elif previsao_media < media_vendas * 0.8:
            insights.append(f"Vendas de {produto} podem diminuir 20% - considere promoção")
        else:
            insights.append(f"Vendas de {produto} devem manter padrão atual")
        
        return {
            'previsao_7dias': previsoes.sum(),
            'precisao': precisao,
            'receita_estimada': previsoes.sum() * preco_medio,
            'estoque_recomendado': previsoes.sum() * 1.3,  # 30% de margem
            'historico_df': produto_data,
            'insights': insights
        }
    
    except Exception as e:
        st.error(f"Erro na previsão: {e}")
        return None


def gerar_recomendacoes_automaticas():
    """
    Gera recomendações automáticas baseadas nos dados
    """
    recomendacoes = []
    
    try:
        # Análise de produtos sem venda recente
        produtos_sem_venda = get_dataframe("""
            SELECT p.nome 
            FROM produtos p
            LEFT JOIN vendas v ON p.id = v.produto_id AND v.data_venda >= date('now', '-7 days')
            WHERE p.ativo = 1 AND v.id IS NULL
        """)
        
        if not produtos_sem_venda.empty:
            recomendacoes.append(f"Produtos sem venda há 7+ dias: {len(produtos_sem_venda)}. Considere promoções.")
        
        # Análise de estoque baixo
        estoque_baixo = get_dataframe("""
            SELECT COUNT(*) as count FROM ingredientes WHERE estoque_atual <= 5
        """)
        
        if estoque_baixo.iloc[0]['count'] > 0:
            recomendacoes.append(f"Existem {estoque_baixo.iloc[0]['count']} ingredientes com estoque baixo.")
        
        # Análise de performance semanal
        vendas_semana = get_dataframe("""
            SELECT SUM(total) as total_semana
            FROM vendas 
            WHERE data_venda >= date('now', '-7 days')
        """)
        
        vendas_semana_anterior = get_dataframe("""
            SELECT SUM(total) as total_semana_anterior
            FROM vendas 
            WHERE data_venda BETWEEN date('now', '-14 days') AND date('now', '-7 days')
        """)
        
        if not vendas_semana.empty and not vendas_semana_anterior.empty:
            atual = vendas_semana.iloc[0]['total_semana'] or 0
            anterior = vendas_semana_anterior.iloc[0]['total_semana_anterior'] or 0
            
            if anterior > 0:
                variacao = ((atual - anterior) / anterior) * 100
                if variacao > 10:
                    recomendacoes.append(f"Vendas cresceram {variacao:.1f}% esta semana! Ótimo trabalho!")
                elif variacao < -10:
                    recomendacoes.append(f"Vendas caíram {abs(variacao):.1f}% esta semana. Analise as causas.")
        
        if not recomendacoes:
            recomendacoes.append("Tudo funcionando bem! Continue o ótimo trabalho.")
        
    except Exception as e:
        recomendacoes.append("Erro ao gerar recomendações automáticas.")
    
    return recomendacoes