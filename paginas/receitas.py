import streamlit as st
import pandas as pd
from datetime import datetime
from funcoesAux import (
    get_dataframe, 
    executar_query,
    adicionar_item_receita, 
    remover_item_receita,
    get_receita_produto,
    calcular_custo_produto,
    verificar_disponibilidade_receita,
    baixar_estoque_por_receita
)
import plotly.express as px

def modulo_receitas():
    """Módulo de gestão de receitas e estoque de produtos prontos"""
    st.header("📋 Receitas & Produção")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Gerenciar Receitas", 
        "💰 Análise de Custos", 
        "📊 Simulador",
        "🍞 Estoque Pronto",
        "📈 Produção"
    ])
    
    # =============================
    # TAB 1 - GERENCIAR RECEITAS
    # =============================
    with tab1:
        st.subheader("Configurar Receitas dos Produtos")
        
        produtos = get_dataframe("SELECT id, nome, preco_venda FROM produtos WHERE ativo=1 ORDER BY nome")
        ingredientes = get_dataframe("SELECT id, nome, preco_kg, unidade, estoque_atual FROM ingredientes ORDER BY nome")
        
        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de criar receitas")
            return
        if ingredientes.empty:
            st.warning("⚠️ Cadastre ingredientes antes de criar receitas")
            return
        
        # Seletor de produto
        col1, col2 = st.columns([2, 1])
        with col1:
            produto_id = st.selectbox(
                "Selecione o Produto",
                options=produtos['id'].tolist(),
                format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0]
            )
        with col2:
            produto_selecionado = produtos[produtos['id']==produto_id].iloc[0]
            st.metric("Preço de Venda", f"R$ {produto_selecionado['preco_venda']:.2f}")
        
        # Mostrar receita atual
        receita_atual = get_receita_produto(produto_id)
        
        if not receita_atual.empty:
            st.subheader(f"📝 Receita Atual - {produto_selecionado['nome']}")
            
            # Calcular custo total
            custo_total = receita_atual['custo_item'].sum()
            margem = produto_selecionado['preco_venda'] - custo_total
            margem_percent = (margem / produto_selecionado['preco_venda'] * 100) if produto_selecionado['preco_venda'] > 0 else 0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💸 Custo Variável", f"R$ {custo_total:.2f}")
            c2.metric("💰 Preço Venda", f"R$ {produto_selecionado['preco_venda']:.2f}")
            c3.metric("📊 Margem", f"R$ {margem:.2f}")
            c4.metric("📈 Margem %", f"{margem_percent:.1f}%")
            
            # Tabela de ingredientes
            st.dataframe(
                receita_atual[['ingrediente', 'quantidade', 'unidade', 'preco_kg', 'custo_item', 'estoque_atual']]
                .rename(columns={
                    'ingrediente': 'Ingrediente',
                    'quantidade': 'Qtd/Unidade',
                    'unidade': 'Unidade',
                    'preco_kg': 'Preço Unit. (R$)',
                    'custo_item': 'Custo (R$)',
                    'estoque_atual': 'Estoque Disponível'
                })
                .style.format({
                    'Qtd/Unidade': '{:.3f}',
                    'Preço Unit. (R$)': 'R$ {:.2f}',
                    'Custo (R$)': 'R$ {:.2f}',
                    'Estoque Disponível': '{:.2f}'
                }),
                use_container_width=True
            )
            
            # Remover ingrediente
            st.markdown("---")
            st.subheader("Remover Ingrediente da Receita")
            opcoes_remover = []
            mapa_remover = {}
            for _, row in receita_atual.iterrows():
                txt = f"{row['ingrediente']} ({row['quantidade']:.3f} {row['unidade']})"
                opcoes_remover.append(txt)
                mapa_remover[txt] = int(row['id'])
            
            if opcoes_remover:
                sel_remover = st.selectbox("Selecione para remover", ["-- selecione --"] + opcoes_remover)
                if sel_remover != "-- selecione --":
                    if st.button("🗑️ Remover", key="btn_remover"):
                        receita_id = mapa_remover[sel_remover]
                        sucesso, msg = remover_item_receita(receita_id)
                        if sucesso:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info(f"📝 Nenhuma receita cadastrada para **{produto_selecionado['nome']}**")
        
        # Adicionar ingrediente à receita
        st.markdown("---")
        st.subheader("➕ Adicionar Ingrediente à Receita")
        
        with st.form("form_add_ingrediente"):
            col1, col2 = st.columns(2)
            with col1:
                ingrediente_id = st.selectbox(
                    "Ingrediente",
                    options=ingredientes['id'].tolist(),
                    format_func=lambda x: f"{ingredientes[ingredientes['id']==x]['nome'].iloc[0]} ({ingredientes[ingredientes['id']==x]['unidade'].iloc[0]})"
                )
            with col2:
                ing_sel = ingredientes[ingredientes['id']==ingrediente_id].iloc[0]
                quantidade = st.number_input(
                    f"Quantidade por unidade de produto ({ing_sel['unidade']})",
                    min_value=0.001,
                    step=0.001,
                    format="%.3f"
                )
            
            submit = st.form_submit_button("✅ Adicionar à Receita")
            
            if submit:
                sucesso, msg = adicionar_item_receita(produto_id, ingrediente_id, quantidade)
                if sucesso:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    # =============================
    # TAB 2 - ANÁLISE DE CUSTOS
    # =============================
    with tab2:
        st.subheader("💰 Análise de Custos por Produto")
        
        produtos_com_receita = get_dataframe("""
            SELECT DISTINCT p.id, p.nome, p.preco_venda, p.categoria
            FROM produtos p
            JOIN receitas r ON p.id = r.produto_id
            WHERE p.ativo = 1
            ORDER BY p.nome
        """)
        
        if produtos_com_receita.empty:
            st.info("Nenhum produto com receita cadastrada")
            return
        
        # Calcular custos para cada produto
        analise_custos = []
        for _, prod in produtos_com_receita.iterrows():
            custo = calcular_custo_produto(prod['id'])
            margem = prod['preco_venda'] - custo
            margem_percent = (margem / prod['preco_venda'] * 100) if prod['preco_venda'] > 0 else 0
            
            analise_custos.append({
                'Produto': prod['nome'],
                'Categoria': prod['categoria'],
                'Custo Variável': custo,
                'Preço Venda': prod['preco_venda'],
                'Margem R$': margem,
                'Margem %': margem_percent
            })
        
        df_analise = pd.DataFrame(analise_custos)
        
        # Métricas gerais
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Produtos Analisados", len(df_analise))
        c2.metric("💰 Margem Média", f"{df_analise['Margem %'].mean():.1f}%")
        c3.metric("📊 Menor Margem", f"{df_analise['Margem %'].min():.1f}%")
        
        # Tabela de análise
        st.dataframe(
            df_analise.style.format({
                'Custo Variável': 'R$ {:.2f}',
                'Preço Venda': 'R$ {:.2f}',
                'Margem R$': 'R$ {:.2f}',
                'Margem %': '{:.1f}%'
            }).background_gradient(subset=['Margem %'], cmap='RdYlGn', vmin=0, vmax=100),
            use_container_width=True
        )
        
        # Alertas de margem baixa
        st.subheader("⚠️ Alertas de Margem")
        margem_critica = st.slider("Margem crítica (%)", 0, 50, 20)
        
        produtos_criticos = df_analise[df_analise['Margem %'] < margem_critica]
        if not produtos_criticos.empty:
            st.warning(f"🔴 {len(produtos_criticos)} produto(s) com margem abaixo de {margem_critica}%")
            for _, p in produtos_criticos.iterrows():
                st.error(f"**{p['Produto']}**: Margem de {p['Margem %']:.1f}% (R$ {p['Margem R$']:.2f})")
        else:
            st.success("✅ Todos os produtos com margem saudável")
    
    # =============================
    # TAB 3 - SIMULADOR DE PRODUÇÃO
    # =============================
    with tab3:
        st.subheader("📊 Simulador de Produção")
        st.markdown("Verifique se há estoque suficiente para produzir uma quantidade específica")
        
        produtos_com_receita = get_dataframe("""
            SELECT DISTINCT p.id, p.nome
            FROM produtos p
            JOIN receitas r ON p.id = r.produto_id
            WHERE p.ativo = 1
            ORDER BY p.nome
        """)
        
        if produtos_com_receita.empty:
            st.info("Nenhum produto com receita cadastrada")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            prod_sim_id = st.selectbox(
                "Produto para Simular",
                options=produtos_com_receita['id'].tolist(),
                format_func=lambda x: produtos_com_receita[produtos_com_receita['id']==x]['nome'].iloc[0]
            )
        with col2:
            qtd_simular = st.number_input("Quantidade a Produzir", min_value=1, value=10)
        
        if st.button("🔍 Verificar Disponibilidade"):
            disponivel, mensagem = verificar_disponibilidade_receita(prod_sim_id, qtd_simular)
            
            # Mostrar receita detalhada
            receita_sim = get_receita_produto(prod_sim_id)
            
            st.markdown("### Necessidades de Produção")
            dados_simulacao = []
            for _, item in receita_sim.iterrows():
                necessario = item['quantidade'] * qtd_simular
                disponivel_item = item['estoque_atual']
                status = "✅ OK" if disponivel_item >= necessario else "❌ FALTA"
                falta = max(0, necessario - disponivel_item)
                
                dados_simulacao.append({
                    'Ingrediente': item['ingrediente'],
                    'Necessário': f"{necessario:.3f} {item['unidade']}",
                    'Disponível': f"{disponivel_item:.3f} {item['unidade']}",
                    'Falta': f"{falta:.3f} {item['unidade']}",
                    'Status': status
                })
            
            df_simulacao = pd.DataFrame(dados_simulacao)
            st.dataframe(df_simulacao, use_container_width=True)
            
            # Custo total da produção
            custo_unitario = calcular_custo_produto(prod_sim_id)
            custo_total = custo_unitario * qtd_simular
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💸 Custo Unitário", f"R$ {custo_unitario:.2f}")
            c2.metric("💰 Custo Total", f"R$ {custo_total:.2f}")
            c3.metric("📦 Quantidade", qtd_simular)
            
            if disponivel:
                st.success(f"✅ {mensagem}")
            else:
                st.error(f"❌ {mensagem}")

    # =============================
    # TAB 4 - ESTOQUE DE PRODUTOS PRONTOS
    # =============================
    with tab4:
        st.subheader("🍞 Estoque de Produtos Prontos")
        st.markdown("Gerencie o estoque de pães e produtos já fabricados")
        
        # Criar tabela se não existir
        executar_query("""
            CREATE TABLE IF NOT EXISTS estoque_pronto (
                id INTEGER PRIMARY KEY,
                produto_id INTEGER NOT NULL,
                quantidade_atual REAL DEFAULT 0,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        """)
        
        # Buscar estoque atual
        estoque_pronto = get_dataframe("""
            SELECT 
                ep.id,
                p.nome as produto,
                p.categoria,
                ep.quantidade_atual,
                ep.ultima_atualizacao
            FROM estoque_pronto ep
            JOIN produtos p ON ep.produto_id = p.id
            ORDER BY p.nome
        """)
        
        # Métricas
        if not estoque_pronto.empty:
            total_unidades = estoque_pronto['quantidade_atual'].sum()
            produtos_estoque = len(estoque_pronto)
            zerados = len(estoque_pronto[estoque_pronto['quantidade_atual'] <= 0])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🍞 Total em Estoque", f"{total_unidades:.0f} unidades")
            c2.metric("📦 Produtos", produtos_estoque)
            c3.metric("⚠️ Estoque Zerado", zerados)
            
            # Tabela de estoque
            st.dataframe(
                estoque_pronto.rename(columns={
                    'produto': 'Produto',
                    'categoria': 'Categoria',
                    'quantidade_atual': 'Quantidade',
                    'ultima_atualizacao': 'Última Atualização'
                }).style.format({
                    'Quantidade': '{:.0f}'
                }),
                use_container_width=True
            )
            
            # Gráfico de estoque
            fig = px.bar(
                estoque_pronto,
                x='produto',
                y='quantidade_atual',
                text='quantidade_atual',
                color='categoria',
                title="Estoque Atual por Produto",
                labels={'quantidade_atual': 'Quantidade', 'produto': 'Produto'}
            )
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum produto em estoque no momento")
        
        # Ajuste manual de estoque
        st.markdown("---")
        st.subheader("🔧 Ajustar Estoque Manualmente")
        
        produtos_ativos = get_dataframe("SELECT id, nome FROM produtos WHERE ativo=1 ORDER BY nome")
        
        if not produtos_ativos.empty:
            with st.form("form_ajuste_estoque"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    prod_ajuste_id = st.selectbox(
                        "Produto",
                        options=produtos_ativos['id'].tolist(),
                        format_func=lambda x: produtos_ativos[produtos_ativos['id']==x]['nome'].iloc[0]
                    )
                with col2:
                    tipo_ajuste = st.selectbox("Tipo", ["Adicionar", "Remover", "Definir"])
                with col3:
                    qtd_ajuste = st.number_input("Quantidade", min_value=0.0, step=1.0, format="%.0f")
                
                submit_ajuste = st.form_submit_button("✅ Ajustar Estoque")
                
                if submit_ajuste:
                    # Verificar se produto já existe no estoque
                    existe = get_dataframe(
                        "SELECT quantidade_atual FROM estoque_pronto WHERE produto_id = ?",
                        (prod_ajuste_id,)
                    )
                    
                    if existe.empty:
                        # Criar registro
                        if tipo_ajuste == "Definir" or tipo_ajuste == "Adicionar":
                            executar_query(
                                "INSERT INTO estoque_pronto (produto_id, quantidade_atual) VALUES (?, ?)",
                                (prod_ajuste_id, qtd_ajuste)
                            )
                            st.success(f"✅ Estoque criado com {qtd_ajuste:.0f} unidades")
                        else:
                            st.error("❌ Produto não existe no estoque para remover")
                    else:
                        qtd_atual = float(existe.iloc[0]['quantidade_atual'])
                        
                        if tipo_ajuste == "Adicionar":
                            nova_qtd = qtd_atual + qtd_ajuste
                        elif tipo_ajuste == "Remover":
                            nova_qtd = max(0, qtd_atual - qtd_ajuste)
                        else:  # Definir
                            nova_qtd = qtd_ajuste
                        
                        executar_query(
                            "UPDATE estoque_pronto SET quantidade_atual = ?, ultima_atualizacao = ? WHERE produto_id = ?",
                            (nova_qtd, datetime.now(), prod_ajuste_id)
                        )
                        st.success(f"✅ Estoque ajustado: {qtd_atual:.0f} → {nova_qtd:.0f}")
                    
                    st.rerun()

    # =============================
    # TAB 5 - REGISTRAR PRODUÇÃO
    # =============================
    with tab5:
        st.subheader("📈 Registrar Produção")
        st.markdown("Registre a produção de produtos e baixe automaticamente o estoque de ingredientes")
        
        produtos_com_receita = get_dataframe("""
            SELECT DISTINCT p.id, p.nome
            FROM produtos p
            JOIN receitas r ON p.id = r.produto_id
            WHERE p.ativo = 1
            ORDER BY p.nome
        """)
        
        if produtos_com_receita.empty:
            st.warning("⚠️ Cadastre receitas antes de registrar produção")
            return
        
        with st.form("form_producao"):
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                prod_producao_id = st.selectbox(
                    "Produto Produzido",
                    options=produtos_com_receita['id'].tolist(),
                    format_func=lambda x: produtos_com_receita[produtos_com_receita['id']==x]['nome'].iloc[0]
                )
            
            with col2:
                qtd_producao = st.number_input("Quantidade", min_value=1, value=10, step=1)
            
            with col3:
                data_producao = st.date_input("Data", value=datetime.now().date())
            
            submit_producao = st.form_submit_button("✅ Registrar Produção")
            
            if submit_producao:
                # Verificar disponibilidade
                disponivel, msg = verificar_disponibilidade_receita(prod_producao_id, qtd_producao)
                
                if not disponivel:
                    st.error(f"❌ {msg}")
                else:
                    # Baixar estoque de ingredientes
                    sucesso_baixa, msg_baixa = baixar_estoque_por_receita(prod_producao_id, qtd_producao)
                    
                    if sucesso_baixa:
                        # Atualizar estoque de produtos prontos
                        existe = get_dataframe(
                            "SELECT quantidade_atual FROM estoque_pronto WHERE produto_id = ?",
                            (prod_producao_id,)
                        )
                        
                        if existe.empty:
                            executar_query(
                                "INSERT INTO estoque_pronto (produto_id, quantidade_atual) VALUES (?, ?)",
                                (prod_producao_id, qtd_producao)
                            )
                        else:
                            executar_query(
                                "UPDATE estoque_pronto SET quantidade_atual = quantidade_atual + ?, ultima_atualizacao = ? WHERE produto_id = ?",
                                (qtd_producao, datetime.now(), prod_producao_id)
                            )
                        
                        st.success(f"✅ Produção registrada: {qtd_producao} unidades de {produtos_com_receita[produtos_com_receita['id']==prod_producao_id]['nome'].iloc[0]}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao baixar estoque: {msg_baixa}")
        
        # Histórico de produção (últimos 7 dias)
        st.markdown("---")
        st.subheader("📊 Histórico Recente de Produção")
        
        hist_producao = get_dataframe("""
            SELECT 
                DATE(m.data_movimentacao) as data,
                i.nome as ingrediente,
                SUM(m.quantidade) as qtd_utilizada,
                i.unidade,
                m.motivo
            FROM movimentacoes_estoque m
            JOIN ingredientes i ON m.ingrediente_id = i.id
            WHERE m.tipo = 'saida' 
            AND m.motivo LIKE 'Produção%'
            AND DATE(m.data_movimentacao) >= DATE('now', '-7 days')
            GROUP BY DATE(m.data_movimentacao), i.nome, i.unidade, m.motivo
            ORDER BY m.data_movimentacao DESC
        """)
        
        if not hist_producao.empty:
            st.dataframe(
                hist_producao.rename(columns={
                    'data': 'Data',
                    'ingrediente': 'Ingrediente',
                    'qtd_utilizada': 'Qtd Utilizada',
                    'unidade': 'Unidade',
                    'motivo': 'Motivo'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma produção registrada nos últimos 7 dias")