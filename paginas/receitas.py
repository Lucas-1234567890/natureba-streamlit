import streamlit as st
import pandas as pd
from funcoesAux import (
    get_dataframe, 
    adicionar_item_receita, 
    remover_item_receita,
    get_receita_produto,
    calcular_custo_produto,
    verificar_disponibilidade_receita
)

def modulo_receitas():
    """Módulo de gestão de receitas (ingredientes por produto)"""
    st.header("📋 Receitas e Custo de Produção")
    
    tab1, tab2, tab3 = st.tabs(["🔧 Gerenciar Receitas", "💰 Análise de Custos", "📊 Simulador de Produção"])
    
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