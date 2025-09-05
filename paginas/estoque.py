import streamlit as st
import pandas as pd
import plotly.express as px
from banco import get_dataframe, executar_query
from datetime import datetime, timedelta


# Módulo de Estoque
def modulo_estoque():
    st.header("📊 Controle de Estoque")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Ingredientes", "➕ Movimentação", "📋 Histórico", "⚠️ Alertas"])
    
    with tab1:
        st.subheader("Gestão de Ingredientes")
        
        # Formulário para cadastrar/editar ingredientes
        with st.expander("➕ Cadastrar Novo Ingrediente"):
            with st.form("form_ingrediente"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nome_ingrediente = st.text_input("Nome do Ingrediente*")
                    preco_kg = st.number_input("Preço por KG/Unidade (R$)*", min_value=0.01, format="%.2f")
                
                with col2:
                    estoque_inicial = st.number_input("Estoque Inicial", min_value=0.0, format="%.2f")
                    unidade = st.selectbox("Unidade", ["kg", "litros", "unidades", "dúzia", "pacotes"])
                
                with col3:
                    fornecedor = st.text_input("Fornecedor")
                
                submitted = st.form_submit_button("✅ Cadastrar Ingrediente")
                
                if submitted:
                    if nome_ingrediente and preco_kg > 0:
                        try:
                            executar_query(
                                "INSERT INTO ingredientes (nome, preco_kg, estoque_atual, unidade, fornecedor) VALUES (?, ?, ?, ?, ?)",
                                (nome_ingrediente, preco_kg, estoque_inicial, unidade, fornecedor or "Não informado")
                            )
                            
                            # Se tem estoque inicial, registrar movimentação
                            if estoque_inicial > 0:
                                ingrediente_id = executar_query(
                                    "SELECT id FROM ingredientes WHERE nome = ?", (nome_ingrediente,)
                                )[0][0]
                                
                                executar_query("""
                                    INSERT INTO movimentacoes_estoque 
                                    (ingrediente_id, tipo, quantidade, motivo) 
                                    VALUES (?, 'entrada', ?, 'Estoque inicial')
                                """, (ingrediente_id, estoque_inicial))
                            
                            st.success(f"✅ Ingrediente '{nome_ingrediente}' cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.error("❌ Já existe um ingrediente com este nome!")
                            else:
                                st.error(f"❌ Erro ao cadastrar ingrediente: {str(e)}")
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios!")
        
        # Lista de ingredientes
        st.subheader("📋 Ingredientes Cadastrados")
        
        ingredientes = get_dataframe("""
            SELECT id, nome, preco_kg, estoque_atual, unidade, fornecedor,
                   (preco_kg * estoque_atual) as valor_estoque
            FROM ingredientes
            ORDER BY nome
        """)
        
        if not ingredientes.empty:
            # Estatísticas gerais
            valor_total_estoque = ingredientes['valor_estoque'].sum()
            total_ingredientes = len(ingredientes)
            ingredientes_zerados = len(ingredientes[ingredientes['estoque_atual'] <= 0])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Valor Total Estoque", f"R$ {valor_total_estoque:.2f}")
            with col2:
                st.metric("📦 Total Ingredientes", total_ingredientes)
            with col3:
                st.metric("⚠️ Estoque Zerado", ingredientes_zerados)
            
            # Tabela com status visual
            def status_estoque(valor):
                if valor <= 0:
                    return "🔴 Zerado"
                elif valor <= 5:
                    return "🟡 Baixo"
                else:
                    return "🟢 OK"
            
            ingredientes['status'] = ingredientes['estoque_atual'].apply(status_estoque)
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_status = st.selectbox("Filtrar por Status", 
                                           ["Todos", "🔴 Zerado", "🟡 Baixo", "🟢 OK"])
            with col2:
                busca_nome = st.text_input("🔍 Buscar por nome")
            
            # Aplicar filtros
            ingredientes_filtrados = ingredientes.copy()
            
            if filtro_status != "Todos":
                ingredientes_filtrados = ingredientes_filtrados[ingredientes_filtrados['status'] == filtro_status]
            
            if busca_nome:
                ingredientes_filtrados = ingredientes_filtrados[
                    ingredientes_filtrados['nome'].str.contains(busca_nome, case=False, na=False)
                ]
            
            # Exibir tabela
            if not ingredientes_filtrados.empty:
                st.dataframe(
                    ingredientes_filtrados[['nome', 'estoque_atual', 'unidade', 'preco_kg', 'valor_estoque', 'fornecedor', 'status']].style.format({
                        'preco_kg': 'R$ {:.2f}',
                        'valor_estoque': 'R$ {:.2f}',
                        'estoque_atual': '{:.2f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum ingrediente encontrado com os filtros aplicados.")
        else:
            st.info("Nenhum ingrediente cadastrado ainda.")
    
    with tab2:
        st.subheader("Movimentação de Estoque")
        
        # Buscar ingredientes
        ingredientes = get_dataframe("SELECT id, nome, estoque_atual, unidade FROM ingredientes ORDER BY nome")
        
        if ingredientes.empty:
            st.warning("⚠️ Cadastre ingredientes antes de fazer movimentações!")
            return
        
        with st.form("form_movimentacao"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ingrediente_id = st.selectbox("Ingrediente*", 
                                            options=ingredientes['id'].tolist(),
                                            format_func=lambda x: f"{ingredientes[ingredientes['id']==x]['nome'].iloc[0]} (Atual: {ingredientes[ingredientes['id']==x]['estoque_atual'].iloc[0]:.2f})")
            
            with col2:
                tipo_movimentacao = st.selectbox("Tipo*", ["entrada", "saida"])
                quantidade = st.number_input("Quantidade*", min_value=0.01, format="%.2f")
            
            with col3:
                motivo = st.text_input("Motivo*", placeholder="Ex: Compra, Perda, Ajuste...")
            
            # Mostrar informações do ingrediente
            if ingrediente_id:
                ingrediente_info = ingredientes[ingredientes['id']==ingrediente_id].iloc[0]
                estoque_atual = ingrediente_info['estoque_atual']
                
                if tipo_movimentacao == "entrada":
                    novo_estoque = estoque_atual + quantidade
                    cor = "green"
                else:
                    novo_estoque = estoque_atual - quantidade
                    cor = "red" if novo_estoque < 0 else "blue"
                
                st.markdown(f"""
                **Ingrediente:** {ingrediente_info['nome']}
                **Estoque Atual:** {estoque_atual:.2f} {ingrediente_info['unidade']}
                **Novo Estoque:** <span style="color: {cor}">{novo_estoque:.2f} {ingrediente_info['unidade']}</span>
                """, unsafe_allow_html=True)
                
                if novo_estoque < 0:
                    st.error("⚠️ ATENÇÃO: Esta movimentação resultará em estoque negativo!")
            
            submitted = st.form_submit_button("✅ Registrar Movimentação")
            
            if submitted:
                if ingrediente_id and quantidade > 0 and motivo:
                    try:
                        # Registrar movimentação
                        executar_query("""
                            INSERT INTO movimentacoes_estoque 
                            (ingrediente_id, tipo, quantidade, motivo) 
                            VALUES (?, ?, ?, ?)
                        """, (ingrediente_id, tipo_movimentacao, quantidade, motivo))
                        
                        # Atualizar estoque
                        if tipo_movimentacao == "entrada":
                            executar_query("""
                                UPDATE ingredientes 
                                SET estoque_atual = estoque_atual + ? 
                                WHERE id = ?
                            """, (quantidade, ingrediente_id))
                        else:
                            executar_query("""
                                UPDATE ingredientes 
                                SET estoque_atual = estoque_atual - ? 
                                WHERE id = ?
                            """, (quantidade, ingrediente_id))
                        
                        st.success(f"✅ Movimentação registrada: {tipo_movimentacao.title()} de {quantidade:.2f} - {motivo}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar movimentação: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    with tab3:
        st.subheader("Histórico de Movimentações")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
        with col3:
            filtro_tipo = st.selectbox("Tipo", ["Todos", "entrada", "saida"])
        
        # Montar query
        where_clause = "WHERE DATE(m.data_movimentacao) BETWEEN ? AND ?"
        params = [data_inicio, data_fim]
        
        if filtro_tipo != "Todos":
            where_clause += " AND m.tipo = ?"
            params.append(filtro_tipo)
        
        movimentacoes = get_dataframe(f"""
            SELECT m.data_movimentacao, i.nome as ingrediente, m.tipo,
                   m.quantidade, i.unidade, m.motivo
            FROM movimentacoes_estoque m
            JOIN ingredientes i ON m.ingrediente_id = i.id
            {where_clause}
            ORDER BY m.data_movimentacao DESC
        """, params)
        
        if not movimentacoes.empty:
            # Resumo do período
            total_entradas = movimentacoes[movimentacoes['tipo'] == 'entrada']['quantidade'].sum()
            total_saidas = movimentacoes[movimentacoes['tipo'] == 'saida']['quantidade'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 Total Entradas", f"{total_entradas:.2f}")
            with col2:
                st.metric("📉 Total Saídas", f"{total_saidas:.2f}")
            with col3:
                st.metric("📊 Movimentações", len(movimentacoes))
            
            # Gráfico de movimentações por dia
            movimentacoes['data'] = pd.to_datetime(movimentacoes['data_movimentacao']).dt.date
            movimentacoes_diarias = movimentacoes.groupby(['data', 'tipo'])['quantidade'].sum().reset_index()
            
            if not movimentacoes_diarias.empty:
                fig = px.bar(movimentacoes_diarias, x='data', y='quantidade', color='tipo',
                           title="Movimentações Diárias",
                           barmode='group',
                           color_discrete_map={'entrada': '#4ECDC4', 'saida': '#FF6B6B'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de movimentações
            st.dataframe(
                movimentacoes[['data_movimentacao', 'ingrediente', 'tipo', 'quantidade', 'unidade', 'motivo']],
                use_container_width=True
            )
        else:
            st.info("Nenhuma movimentação encontrada no período selecionado.")
    
    with tab4:
        st.subheader("⚠️ Alertas de Estoque")
        
        # Configuração de alertas
        col1, col2 = st.columns(2)
        with col1:
            limite_baixo = st.number_input("Limite para Estoque Baixo", value=5.0, min_value=0.1)
        with col2:
            limite_critico = st.number_input("Limite para Estoque Crítico", value=2.0, min_value=0.1)
        
        # Buscar ingredientes com problemas
        ingredientes_problema = get_dataframe(f"""
            SELECT nome, estoque_atual, unidade, fornecedor,
                   CASE 
                       WHEN estoque_atual <= 0 THEN 'Zerado'
                       WHEN estoque_atual <= {limite_critico} THEN 'Crítico'
                       WHEN estoque_atual <= {limite_baixo} THEN 'Baixo'
                       ELSE 'OK'
                   END as status_alerta
            FROM ingredientes
            WHERE estoque_atual <= {limite_baixo}
            ORDER BY estoque_atual ASC
        """)
        
        if not ingredientes_problema.empty:
            # Contar por tipo de problema
            zerados = len(ingredientes_problema[ingredientes_problema['status_alerta'] == 'Zerado'])
            criticos = len(ingredientes_problema[ingredientes_problema['status_alerta'] == 'Crítico'])
            baixos = len(ingredientes_problema[ingredientes_problema['status_alerta'] == 'Baixo'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.error(f"🔴 **{zerados} ingredientes ZERADOS**")
            with col2:
                st.warning(f"🟠 **{criticos} ingredientes CRÍTICOS**")
            with col3:
                st.info(f"🟡 **{baixos} ingredientes BAIXOS**")
            
            # Lista detalhada
            for _, ingrediente in ingredientes_problema.iterrows():
                status = ingrediente['status_alerta']
                
                if status == 'Zerado':
                    st.error(f"🔴 **{ingrediente['nome']}** - ESTOQUE ZERADO!")
                elif status == 'Crítico':
                    st.warning(f"🟠 **{ingrediente['nome']}** - {ingrediente['estoque_atual']:.2f} {ingrediente['unidade']} (CRÍTICO)")
                else:
                    st.info(f"🟡 **{ingrediente['nome']}** - {ingrediente['estoque_atual']:.2f} {ingrediente['unidade']} (BAIXO)")
                
                # Mostrar fornecedor se disponível
                if ingrediente['fornecedor'] and ingrediente['fornecedor'] != 'Não informado':
                    st.write(f"   📞 Fornecedor: {ingrediente['fornecedor']}")
            
            # Sugestão de compras
            st.subheader("🛒 Lista de Compras Sugerida")
            lista_compras = ingredientes_problema.copy()
            lista_compras['quantidade_sugerida'] = lista_compras.apply(
                lambda x: max(limite_baixo * 2 - x['estoque_atual'], limite_baixo), axis=1
            )
            
            st.dataframe(
                lista_compras[['nome', 'estoque_atual', 'quantidade_sugerida', 'unidade', 'fornecedor']].style.format({
                    'estoque_atual': '{:.2f}',
                    'quantidade_sugerida': '{:.2f}'
                }),
                use_container_width=True
            )
            
            # Botão para gerar lista de compras
            lista_texto = "LISTA DE COMPRAS - PADARIA\n" + "="*30 + "\n\n"
            for _, item in lista_compras.iterrows():
                lista_texto += f"• {item['nome']}: {item['quantidade_sugerida']:.2f} {item['unidade']}\n"
                if item['fornecedor'] and item['fornecedor'] != 'Não informado':
                    lista_texto += f"  Fornecedor: {item['fornecedor']}\n"
                lista_texto += "\n"
            
            st.download_button(
                label="📋 Baixar Lista de Compras",
                data=lista_texto,
                file_name=f"lista_compras_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        else:
            st.success("✅ Todos os ingredientes estão com estoque adequado!")
            
            # Mostrar próximos a ficar baixos
            proximos_baixos = get_dataframe(f"""
                SELECT nome, estoque_atual, unidade
                FROM ingredientes
                WHERE estoque_atual > {limite_baixo} AND estoque_atual <= {limite_baixo * 1.5}
                ORDER BY estoque_atual ASC
                LIMIT 5
            """)
            
            if not proximos_baixos.empty:
                st.subheader("👀 Ingredientes para Ficar de Olho")
                st.write("*Estes ingredientes ainda estão OK, mas podem precisar de reposição em breve:*")
                
                for _, item in proximos_baixos.iterrows():
                    st.write(f"• **{item['nome']}**: {item['estoque_atual']:.2f} {item['unidade']}")