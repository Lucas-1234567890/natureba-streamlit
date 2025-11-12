import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from funcoesAux import get_dataframe, executar_query
import plotly.express as px

def modulo_estoque():
    """
    Módulo simplificado de Estoque - Ingredients & Movimentações
    Comentários estilo sênior:
    - Interface limpa: tabela + filtros no topo, ações (editar/inativar/excluir/movimentar) abaixo.
    - Evitamos lógica complexa ao editar histórico que afete estoque automaticamente. 
      Se for necessário, trate ajuste de estoque manualmente via Movimentação.
    - Uso de loops simples para mapear opções (legível, previsível).
    """

    st.header("📊 Controle de Estoque")
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Ingredientes", "➕ Movimentação", "📋 Histórico", "⚠️ Alertas"])

    # ------------------------
    # TAB 1 - INGREDIENTES (CRUD simples) 
    # ------------------------
    with tab1:
        st.subheader("Gestão de Ingredientes")

        # --- Formulário rápido para cadastrar ingrediente
        with st.expander("➕ Cadastrar Novo Ingrediente", expanded=False):
            with st.form("form_cad_ingrediente"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    nome = st.text_input("Nome do Ingrediente*")
                    preco_kg = st.number_input("Preço por KG/Unidade (R$)*", min_value=0.01, format="%.2f")
                with c2:
                    estoque_inicial = st.number_input("Estoque Inicial", min_value=0.0, format="%.2f")
                    unidade = st.selectbox("Unidade", ["kg", "litros", "unidades", "dúzia", "pacotes"])
                with c3:
                    fornecedor = st.text_input("Fornecedor (opcional)")

                submit = st.form_submit_button("✅ Cadastrar")
                if submit:
                    if not nome or preco_kg <= 0:
                        st.error("Preencha nome e preço corretamente.")
                    else:
                        try:
                            # Insert e registro de estoque inicial (movimentação) se > 0
                            executar_query(
                                "INSERT INTO ingredientes (nome, preco_kg, estoque_atual, unidade, fornecedor) VALUES (?, ?, ?, ?, ?)",
                                (nome.strip(), float(preco_kg), float(estoque_inicial), unidade, fornecedor or "Não informado")
                            )
                            if estoque_inicial > 0:
                                # pega id recém-criado (assume que executar_query retorna algo ou temos que consultar)
                                # aqui utilizamos SELECT para garantir compatibilidade
                                novo = get_dataframe("SELECT id FROM ingredientes WHERE nome = ? ORDER BY id DESC LIMIT 1", (nome.strip(),))
                                if novo is not None and not novo.empty:
                                    ing_id = int(novo.iloc[0]['id'])
                                    executar_query(
                                        "INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, motivo, data_movimentacao) VALUES (?, 'entrada', ?, 'Estoque inicial', ?)",
                                        (ing_id, float(estoque_inicial), datetime.now())
                                    )
                            st.success("Ingrediente cadastrado.")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.error("Já existe um ingrediente com esse nome.")
                            else:
                                st.error(f"Erro ao cadastrar: {e}")

        # --- Tabela de ingredientes com filtros simples
        ingredientes = get_dataframe("""
            SELECT id, nome, preco_kg, estoque_atual, unidade, fornecedor,
                   (preco_kg * estoque_atual) as valor_estoque
            FROM ingredientes
            ORDER BY nome
        """)
        if ingredientes is None or ingredientes.empty:
            st.info("Nenhum ingrediente cadastrado.")
        else:
            # Estatísticas rápidas
            total_valor = float(ingredientes['valor_estoque'].sum())
            total_itens = len(ingredientes)
            zerados = int((ingredientes['estoque_atual'] <= 0).sum())

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("💰 Valor Total Estoque", f"R$ {total_valor:.2f}")
            with c2:
                st.metric("📦 Total Ingredientes", f"{total_itens}")
            with c3:
                st.metric("⚠️ Estoque Zerado", f"{zerados}")

            # adiciona coluna de status legível
            def status_estoque(v):
                try:
                    v = float(v)
                except:
                    v = 0.0
                if v <= 0:
                    return "🔴 Zerado"
                if v <= 5:
                    return "🟡 Baixo"
                return "🟢 OK"
            ingredientes['status'] = ingredientes['estoque_atual'].apply(status_estoque)

            # Filtros UI
            f1, f2 = st.columns([3,1])
            with f1:
                filtro_status = st.selectbox("Filtrar por Status", ["Todos", "🔴 Zerado", "🟡 Baixo", "🟢 OK"])
            with f2:
                busca = st.text_input("🔍 Buscar por nome")

            df_filtrado = ingredientes.copy()
            if filtro_status != "Todos":
                df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
            if busca:
                df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(busca, case=False, na=False)]

            if df_filtrado.empty:
                st.info("Nenhum ingrediente encontrado com os filtros.")
            else:
                st.dataframe(
                    df_filtrado[['id','nome','estoque_atual','unidade','preco_kg','valor_estoque','fornecedor','status']]
                    .rename(columns={'id':'ID','nome':'Nome','estoque_atual':'Estoque','unidade':'Unidade','preco_kg':'Preço (R$)','valor_estoque':'Valor (R$)','fornecedor':'Fornecedor','status':'Status'})
                    .style.format({'Estoque':'{:.2f}','Preço (R$)':'R$ {:.2f}','Valor (R$)':'R$ {:.2f}'}),
                    use_container_width=True
                )

            st.markdown("---")
            st.subheader("Ações rápidas (selecionar e operar abaixo)")

            # Mapear opções de forma simples (legível)
            opcoes = []
            mapa = {}
            for _, r in df_filtrado.iterrows():
                txt = f"{int(r['id'])} — {r['nome']} — {r['estoque_atual']:.2f} {r['unidade']}"
                opcoes.append(txt)
                mapa[txt] = int(r['id'])

            sel = st.selectbox("Selecione um ingrediente", ["-- nada --"] + opcoes)
            if sel != "-- nada --":
                ing_id = mapa[sel]
                row = ingredientes[ingredientes['id'] == ing_id].iloc[0]

                st.markdown(f"**{row['nome']}** — Estoque atual: {float(row['estoque_atual']):.2f} {row['unidade']}")
                cA, cB, cC = st.columns(3)
                with cA:
                    if st.button("✏️ Editar", key=f"edit_ing_{ing_id}"):
                        st.session_state["edit_ingrediente"] = ing_id
                with cB:
                    if st.button("❌ Excluir", key=f"del_ing_{ing_id}"):
                        st.session_state[f"confirm_del_ing_{ing_id}"] = True
                with cC:
                    if st.button("📥 Histórico Mov.", key=f"hist_ing_{ing_id}"):
                        st.session_state["focus_ing_hist"] = ing_id

                # confirmação exclusão
                if st.session_state.get(f"confirm_del_ing_{ing_id}", False):
                    with st.expander("⚠️ Confirmar exclusão"):
                        st.write("Excluir ingrediente remove também o histórico de movimentações relacionado. Confirma?")
                        y, n = st.columns(2)
                        with y:
                            if st.button("Confirmar", key=f"conf_yes_ing_{ing_id}"):
                                try:
                                    executar_query("DELETE FROM movimentacoes_estoque WHERE ingrediente_id = ?", (ing_id,))
                                    executar_query("DELETE FROM ingredientes WHERE id = ?", (ing_id,))
                                    st.success("Ingrediente e movimentações excluídos.")
                                    st.session_state.pop(f"confirm_del_ing_{ing_id}", None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir: {e}")
                        with n:
                            if st.button("Cancelar", key=f"conf_no_ing_{ing_id}"):
                                st.session_state.pop(f"confirm_del_ing_{ing_id}", None)
                                st.info("Exclusão cancelada.")

            # Editar ingrediente (form abaixo, acionado pela flag)
            if st.session_state.get("edit_ingrediente"):
                edit_id = st.session_state["edit_ingrediente"]
                r = ingredientes[ingredientes['id'] == edit_id].iloc[0]
                st.markdown("---")
                st.subheader(f"Editar ingrediente — ID {edit_id}")
                with st.form(f"form_edit_ing_{edit_id}"):
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        nome_e = st.text_input("Nome", value=r['nome'])
                        preco_e = st.number_input("Preço por KG/Un. (R$)", min_value=0.01, value=float(r['preco_kg']))
                    with e2:
                        estoque_e = st.number_input("Estoque atual", min_value=0.0, value=float(r['estoque_atual']))
                        unidade_e = st.selectbox("Unidade", ["kg","litros","unidades","dúzia","pacotes"], index=["kg","litros","unidades","dúzia","pacotes"].index(r['unidade']) if r['unidade'] in ["kg","litros","unidades","dúzia","pacotes"] else 0)
                    with e3:
                        fornecedor_e = st.text_input("Fornecedor", value=r['fornecedor'])
                    salvar, cancelar = st.columns(2)
                    with salvar:
                        if st.form_submit_button("💾 Salvar"):
                            try:
                                executar_query("UPDATE ingredientes SET nome=?, preco_kg=?, estoque_atual=?, unidade=?, fornecedor=? WHERE id=?",
                                              (nome_e.strip(), float(preco_e), float(estoque_e), unidade_e, fornecedor_e or "Não informado", edit_id))
                                st.success("Ingrediente atualizado.")
                                st.session_state.pop("edit_ingrediente", None)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar: {e}")
                    with cancelar:
                        if st.form_submit_button("✖️ Cancelar"):
                            st.session_state.pop("edit_ingrediente", None)
                            st.info("Edição cancelada.")

    # ------------------------
    # TAB 2 - MOVIMENTAÇÃO (entrada/saída simples)
    # ------------------------
    with tab2:
        st.subheader("Movimentação de Estoque")
        ingredientes = get_dataframe("SELECT id, nome, estoque_atual, unidade FROM ingredientes ORDER BY nome")
        if ingredientes is None or ingredientes.empty:
            st.info("Cadastre ingredientes antes de movimentar.")
        else:
            with st.form("form_mov"):
                m1, m2, m3 = st.columns(3)
                with m1:
                    ingr_id = st.selectbox("Ingrediente*", options=ingredientes['id'].tolist(),
                                           format_func=lambda x: f"{ingredientes[ingredientes['id']==x]['nome'].iloc[0]} (Atual: {ingredientes[ingredientes['id']==x]['estoque_atual'].iloc[0]:.2f})")
                with m2:
                    tipo = st.selectbox("Tipo*", ["entrada","saida"])
                    qtd = st.number_input("Quantidade*", min_value=0.01, format="%.2f")
                with m3:
                    motivo = st.text_input("Motivo*", placeholder="Ex: Compra, Perda, Ajuste...")
                submit = st.form_submit_button("✅ Registrar Movimentação")
                if submit:
                    if not motivo or qtd <= 0:
                        st.error("Preencha motivo e quantidade corretamente.")
                    else:
                        try:
                            # registra movimentação
                            executar_query("INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, motivo, data_movimentacao) VALUES (?, ?, ?, ?, ?)",
                                          (int(ingr_id), tipo, float(qtd), motivo, datetime.now()))
                            # atualiza estoque
                            if tipo == "entrada":
                                executar_query("UPDATE ingredientes SET estoque_atual = estoque_atual + ? WHERE id = ?", (float(qtd), int(ingr_id)))
                            else:
                                executar_query("UPDATE ingredientes SET estoque_atual = estoque_atual - ? WHERE id = ?", (float(qtd), int(ingr_id)))
                            st.success("Movimentação registrada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registrar movimentação: {e}")

    # ------------------------
    # TAB 3 - HISTÓRICO MOVIMENTAÇÕES (com filtro e delete)
    # ------------------------
    with tab3:
        st.subheader("Histórico de Movimentações")
        c1, c2 = st.columns(2)
        with c1:
            inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=30))
        with c2:
            fim = st.date_input("Data Fim", value=datetime.now().date())

        movimentacoes = get_dataframe("""
            SELECT m.id, m.data_movimentacao, i.nome as ingrediente, m.tipo, m.quantidade, i.unidade, m.motivo
            FROM movimentacoes_estoque m
            JOIN ingredientes i ON m.ingrediente_id = i.id
            WHERE DATE(m.data_movimentacao) BETWEEN ? AND ?
            ORDER BY m.data_movimentacao DESC
        """, (inicio, fim))

        if movimentacoes is None or movimentacoes.empty:
            st.info("Nenhuma movimentação no período.")
        else:
            # resumo rápido
            entradas = movimentacoes[movimentacoes['tipo']=='entrada']['quantidade'].sum()
            saidas = movimentacoes[movimentacoes['tipo']=='saida']['quantidade'].sum()
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("📈 Entradas", f"{entradas:.2f}")
            with s2:
                st.metric("📉 Saídas", f"{saidas:.2f}")
            with s3:
                st.metric("📊 Movimentações", len(movimentacoes))

            st.dataframe(
                movimentacoes.rename(columns={'data_movimentacao':'Data','ingrediente':'Ingrediente','tipo':'Tipo','quantidade':'Qtd','unidade':'Unidade','motivo':'Motivo'}),
                use_container_width=True
            )

            st.markdown("---")
            st.subheader("Ações: selecionar e excluir (permanente)")

            # lista simples para deletar
            op = []
            mapa = {}
            for _, r in movimentacoes.iterrows():
                txt = f"{int(r['id'])} — {pd.to_datetime(r['data_movimentacao']).strftime('%Y-%m-%d %H:%M')} — {r['ingrediente']} — {r['tipo']} {float(r['quantidade']):.2f}"
                op.append(txt); mapa[txt] = int(r['id'])

            sel = st.selectbox("Selecione movimentação", ["-- nada --"] + op)
            if sel != "-- nada --":
                mid = mapa[sel]
                if st.button("❌ Excluir movimentação"):
                    try:
                        # Observação: excluindo movimentação não reverte estoque automaticamente (evitar efeitos colaterais)
                        executar_query("DELETE FROM movimentacoes_estoque WHERE id = ?", (mid,))
                        st.success("Movimentação excluída.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

    # ------------------------
    # TAB 4 - ALERTAS e LISTA DE COMPRAS
    # ------------------------
    with tab4:
        st.subheader("⚠️ Alertas de Estoque / Lista de Compras")

        c1, c2 = st.columns(2)
        with c1:
            limite_baixo = st.number_input("Limite Baixo", value=5.0, min_value=0.1)
        with c2:
            limite_critico = st.number_input("Limite Crítico", value=2.0, min_value=0.1)

        problemas = get_dataframe(f"""
            SELECT nome, estoque_atual, unidade, fornecedor,
                   CASE WHEN estoque_atual <= 0 THEN 'Zerado'
                        WHEN estoque_atual <= {limite_critico} THEN 'Crítico'
                        WHEN estoque_atual <= {limite_baixo} THEN 'Baixo'
                        ELSE 'OK' END as status_alerta
            FROM ingredientes
            WHERE estoque_atual <= {limite_baixo}
            ORDER BY estoque_atual ASC
        """)

        if problemas is None or problemas.empty:
            st.success("✅ Estoque dentro dos limites.")
        else:
            zerados = len(problemas[problemas['status_alerta']=='Zerado'])
            criticos = len(problemas[problemas['status_alerta']=='Crítico'])
            baixos = len(problemas[problemas['status_alerta']=='Baixo'])

            st.error(f"🔴 Zerados: {zerados}") if zerados else None
            st.warning(f"🟠 Críticos: {criticos}") if criticos else None
            st.info(f"🟡 Baixos: {baixos}") if baixos else None

            for _, item in problemas.iterrows():
                tag = item['status_alerta']
                if tag == 'Zerado':
                    st.error(f"🔴 {item['nome']} — ESTOQUE ZERADO")
                elif tag == 'Crítico':
                    st.warning(f"🟠 {item['nome']} — {item['estoque_atual']:.2f} {item['unidade']} (CRÍTICO)")
                else:
                    st.info(f"🟡 {item['nome']} — {item['estoque_atual']:.2f} {item['unidade']} (BAIXO)")
                if item.get('fornecedor') and item['fornecedor'] != 'Não informado':
                    st.write(f"   📞 Fornecedor: {item['fornecedor']}")

            # montagem da lista de compras sugerida
            problemas['quantidade_sugerida'] = problemas.apply(lambda x: max(limite_baixo*2 - x['estoque_atual'], limite_baixo), axis=1)
            st.subheader("🛒 Lista de Compras Sugerida")
            st.dataframe(problemas[['nome','estoque_atual','quantidade_sugerida','unidade','fornecedor']].style.format({'estoque_atual':'{:.2f}','quantidade_sugerida':'{:.2f}'}), use_container_width=True)

            # botão para baixar lista
            texto = "LISTA DE COMPRAS\n\n"
            for _, it in problemas.iterrows():
                texto += f"• {it['nome']}: {it['quantidade_sugerida']:.2f} {it['unidade']} - Fornecedor: {it.get('fornecedor','-')}\n"
            st.download_button("📋 Baixar Lista", texto, file_name=f"lista_compras_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain")
