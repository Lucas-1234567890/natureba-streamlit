import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from funcoesAux import (
    get_dataframe,
    executar_query,
    criar_venda,
    get_resumo_vendas,
    calcular_custo_produto,
    verificar_disponibilidade_receita
)
import plotly.express as px

def modulo_vendas():
    st.header("💰 Vendas")

    tab1, tab2, tab3 = st.tabs(["🛒 Nova Venda", "📋 Histórico de Vendas", "📊 Análises"])

    # =============================
    # TAB 1 - NOVA VENDA (CARRINHO)
    # =============================
    with tab1:
        st.subheader("🛒 Registrar Nova Venda")
        
        # Inicializar carrinho na sessão
        if 'carrinho' not in st.session_state:
            st.session_state.carrinho = []
        
        st.markdown("### 🛍️ Adicionar Produtos ao Pedido")
        
        produtos = get_dataframe("SELECT id, nome, preco_venda FROM produtos WHERE ativo=1 ORDER BY nome")
        
        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar vendas!")
            return
        
        # Formulário para adicionar produtos
        with st.form("form_add_produto", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            
            with col1:
                produto_id = st.selectbox(
                    "Produto",
                    options=produtos['id'].tolist(),
                    format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0]
                )
            
            with col2:
                qtd = st.number_input("Qtd", min_value=1, value=1, key="qtd_produto")
            
            with col3:
                produto_sel = produtos[produtos['id'] == produto_id].iloc[0]
                
                # Atualiza o valor inicial do número com base no produto selecionado
                # key fixa, mas value dinâmico
                preco = st.number_input(
                    "Preço Unit.", 
                    min_value=0.01, 
                    value=float(produto_sel['preco_venda']), 
                    format="%.2f", 
                    key=f"preco_produto_{produto_id}"  # chave única por produto
                )

            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                adicionar = st.form_submit_button("➕ Adicionar", use_container_width=True)
            
            if adicionar:
                # Verificar estoque antes de adicionar
                disponivel, msg_estoque = verificar_disponibilidade_receita(produto_id, qtd)
                
                if not disponivel:
                    st.error(f"⚠️ {msg_estoque}")
                else:
                    item = {
                        'produto_id': int(produto_id),
                        'nome': produto_sel['nome'],
                        'quantidade': int(qtd),
                        'preco_unitario': float(preco),
                        'subtotal': float(qtd * preco)
                    }
                    st.session_state.carrinho.append(item)
                    st.success(f"✅ {item['nome']} adicionado ao pedido")
                    st.rerun()
        
        # Mostrar carrinho
        if st.session_state.carrinho:
            st.markdown("---")
            st.markdown("### 🛒 Itens do Pedido")
            
            df_carrinho = pd.DataFrame(st.session_state.carrinho)
            total_venda = df_carrinho['subtotal'].sum()
            
            # Tabela do carrinho
            for idx, item in enumerate(st.session_state.carrinho):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
                with col1:
                    st.write(f"**{item['nome']}**")
                with col2:
                    st.write(f"{item['quantidade']}x")
                with col3:
                    st.write(f"R$ {item['preco_unitario']:.2f}")
                with col4:
                    st.write(f"**R$ {item['subtotal']:.2f}**")
                with col5:
                    if st.button("🗑️", key=f"remove_{idx}"):
                        st.session_state.carrinho.pop(idx)
                        st.rerun()
            
            st.markdown("---")
            
            # Total e ações
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"### 💰 Total: R$ {total_venda:.2f}")
            with col2:
                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    st.session_state.carrinho = []
                    st.rerun()
            with col3:
                pass  # Espaçamento
            
            # Dados finais da venda
            st.markdown("---")
            col1, col2 = st.columns([2, 3])
            with col1:
                data_venda = st.date_input("📅 Data da Venda", value=datetime.now().date())
            with col2:
                observacao = st.text_input("📝 Observação (opcional)", placeholder="Ex: Cliente pediu sem glúten")
            
            if st.button("✅ Finalizar Venda", type="primary", use_container_width=True):
                if not st.session_state.carrinho:
                    st.error("❌ Carrinho vazio!")
                else:
                    # Preparar itens para a venda
                    itens_venda = [
                        {
                            'produto_id': item['produto_id'],
                            'quantidade': item['quantidade'],
                            'preco_unitario': item['preco_unitario']
                        }
                        for item in st.session_state.carrinho
                    ]
                    
                    # Criar venda
                    sucesso, msg, venda_id = criar_venda(data_venda, itens_venda, observacao)
                    
                    if sucesso:
                        st.success(f"✅ Venda #{venda_id} registrada com sucesso!")
                        st.balloons()
                        st.session_state.carrinho = []
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        else:
            st.info("🛒 Carrinho vazio. Adicione produtos ao pedido.")
    
    # =============================
    # TAB 2 - HISTÓRICO DE VENDAS
    # =============================
    with tab2:
        st.subheader("📋 Histórico de Vendas")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7), key="hist_inicio")
        with col2:
            fim = st.date_input("Data Fim", value=datetime.now().date(), key="hist_fim")
        
        # Buscar resumo de vendas
        vendas = get_resumo_vendas(inicio, fim)
        
        if vendas.empty:
            st.info("Nenhuma venda encontrada no período")
            return
        
        # Métricas do período
        total_periodo = vendas['total'].sum()
        qtd_vendas = len(vendas)
        ticket_medio = total_periodo / qtd_vendas if qtd_vendas > 0 else 0
        margem_total = vendas['margem_total'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Faturamento", f"R$ {total_periodo:.2f}")
        c2.metric("🛒 Nº de Vendas", qtd_vendas)
        c3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:.2f}")
        c4.metric("📊 Margem Total", f"R$ {margem_total:.2f}")
        
        st.markdown("---")
        
        # Lista de vendas com expander
        for _, venda in vendas.iterrows():
            venda_id = int(venda['id'])
            data_formatada = pd.to_datetime(venda['data_venda']).strftime('%d/%m/%Y')
            hora = venda['hora_venda'] if pd.notna(venda['hora_venda']) else ''
            
            # Título do expander
            titulo = f"Venda #{venda_id} - {data_formatada} {hora} - R$ {venda['total']:.2f}"
            if pd.notna(venda['observacao']) and venda['observacao']:
                titulo += f" | 📝 {venda['observacao']}"
            
            with st.expander(titulo):
                # Buscar itens da venda
                itens = get_dataframe("""
                    SELECT p.nome as produto, iv.quantidade, iv.preco_unitario, 
                           iv.subtotal, iv.custo_variavel,
                           (iv.subtotal - iv.custo_variavel) as margem
                    FROM itens_venda iv
                    JOIN produtos p ON iv.produto_id = p.id
                    WHERE iv.venda_id = ?
                """, (venda_id,))
                
                if not itens.empty:
                    # Tabela de itens
                    st.dataframe(
                        itens.rename(columns={
                            'produto': 'Produto',
                            'quantidade': 'Qtd',
                            'preco_unitario': 'Preço Unit.',
                            'subtotal': 'Subtotal',
                            'custo_variavel': 'Custo Var.',
                            'margem': 'Margem'
                        }).style.format({
                            'Preço Unit.': 'R$ {:.2f}',
                            'Subtotal': 'R$ {:.2f}',
                            'Custo Var.': 'R$ {:.2f}',
                            'Margem': 'R$ {:.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    # Totais
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("💰 Total", f"R$ {venda['total']:.2f}")
                    c2.metric("📦 Itens", int(venda['qtd_itens']))
                    c3.metric("💸 Custo", f"R$ {venda['custo_total']:.2f}")
                    c4.metric("📊 Margem", f"R$ {venda['margem_total']:.2f}")
                
                # Botão de excluir
                st.markdown("---")
                if st.button("🗑️ Excluir Venda", key=f"del_venda_{venda_id}"):
                    st.session_state[f"confirm_del_venda_{venda_id}"] = True
                
                # Confirmação de exclusão
                if st.session_state.get(f"confirm_del_venda_{venda_id}", False):
                    st.warning("⚠️ Atenção: Esta ação NÃO reverterá o estoque automaticamente. Confirma?")
                    col_y, col_n = st.columns(2)
                    with col_y:
                        if st.button("✅ Confirmar Exclusão", key=f"yes_del_venda_{venda_id}"):
                            try:
                                executar_query("DELETE FROM vendas WHERE id=?", (venda_id,))
                                st.success("✅ Venda excluída")
                                st.session_state.pop(f"confirm_del_venda_{venda_id}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                    with col_n:
                        if st.button("❌ Cancelar", key=f"no_del_venda_{venda_id}"):
                            st.session_state.pop(f"confirm_del_venda_{venda_id}")
                            st.rerun()
    
    # =============================
    # TAB 3 - ANÁLISES
    # =============================
    with tab3:
        st.subheader("📊 Análises de Vendas")
        
        col1, col2 = st.columns(2)
        with col1:
            data_ini_analise = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=30), key="analise_ini")
        with col2:
            data_fim_analise = st.date_input("Data Fim", value=datetime.now().date(), key="analise_fim")
        
        # Produtos mais vendidos
        produtos_vendidos = get_dataframe("""
            SELECT p.nome, 
                   SUM(iv.quantidade) as qtd_vendida, 
                   SUM(iv.subtotal) as receita,
                   SUM(iv.custo_variavel) as custo,
                   SUM(iv.subtotal - iv.custo_variavel) as margem,
                   COUNT(DISTINCT iv.venda_id) as num_vendas
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            JOIN vendas v ON iv.venda_id = v.id
            WHERE v.data_venda BETWEEN ? AND ?
            GROUP BY p.id, p.nome
            ORDER BY receita DESC
        """, (data_ini_analise, data_fim_analise))
        
        if not produtos_vendidos.empty:
            st.markdown("### 🏆 Produtos Mais Vendidos")
            
            # Gráfico de barras
            fig = px.bar(
                produtos_vendidos.head(10),
                x='nome',
                y='receita',
                text='receita',
                color='margem',
                color_continuous_scale=['#FF6B6B', '#FFA07A', '#5C977C'],
                labels={'nome': 'Produto', 'receita': 'Receita (R$)', 'margem': 'Margem (R$)'}
            )
            fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.markdown("### 📋 Detalhamento")
            st.dataframe(
                produtos_vendidos.rename(columns={
                    'nome': 'Produto',
                    'qtd_vendida': 'Qtd Vendida',
                    'receita': 'Receita',
                    'custo': 'Custo',
                    'margem': 'Margem',
                    'num_vendas': 'Nº Vendas'
                }).style.format({
                    'Receita': 'R$ {:.2f}',
                    'Custo': 'R$ {:.2f}',
                    'Margem': 'R$ {:.2f}',
                    'Qtd Vendida': '{:.0f}',
                    'Nº Vendas': '{:.0f}'
                }).background_gradient(subset=['Margem'], cmap='Greens'),
                use_container_width=True
            )
            
            # Análise de performance
            st.markdown("---")
            st.markdown("### 🎯 Performance de Vendas")
            
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
                    COUNT(*) as num_vendas,
                    SUM(total) as faturamento,
                    AVG(total) as ticket_medio
                FROM vendas
                WHERE data_venda BETWEEN ? AND ?
                GROUP BY strftime('%w', data_venda)
                ORDER BY strftime('%w', data_venda)
            """, (data_ini_analise, data_fim_analise))
            
            if not vendas_semana.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_semana = px.bar(
                        vendas_semana,
                        x='dia_semana',
                        y='faturamento',
                        text='faturamento',
                        title="Faturamento por Dia da Semana",
                        color_discrete_sequence=['#5C977C']
                    )
                    fig_semana.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                    st.plotly_chart(fig_semana, use_container_width=True)
                
                with col2:
                    fig_ticket = px.bar(
                        vendas_semana,
                        x='dia_semana',
                        y='ticket_medio',
                        text='ticket_medio',
                        title="Ticket Médio por Dia da Semana",
                        color_discrete_sequence=['#7FBFA0']
                    )
                    fig_ticket.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                    st.plotly_chart(fig_ticket, use_container_width=True)
        else:
            st.info("Nenhuma venda no período selecionado")