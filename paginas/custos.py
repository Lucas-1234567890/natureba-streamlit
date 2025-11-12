import streamlit as st
from datetime import date
import pandas as pd
from funcoesAux import executar_query, get_dataframe

def custos_fixos_page():
    st.title("💸 Custos Fixos Mensais")

    # ----------------------
    # Formulário de cadastro
    # ----------------------
    st.subheader("Adicionar Novo Custo Fixo")
    with st.form("form_cadastro_custo"):
        descricao = st.text_input("Descrição do Custo")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data_custo = st.date_input("Data do Custo", value=date.today())
        submit = st.form_submit_button("✅ Adicionar Custo")

        if submit:
            if descricao and valor > 0:
                executar_query(
                    "INSERT INTO custos_operacionais (descricao, valor, categoria, data_custo, recorrente) VALUES (?, ?, ?, ?, 1)",
                    (descricao.strip(), valor, "Fixo", data_custo)
                )
                st.success(f"Custo fixo '{descricao}' cadastrado com sucesso!")
            else:
                st.error("Preencha corretamente todos os campos.")

    st.markdown("---")

    # ----------------------
    # Listagem de custos fixos com Expander
    # ----------------------
    st.subheader("Custos Fixos Cadastrados")
    filtro_mes = st.date_input("Filtrar por mês", value=date.today())
    mes = filtro_mes.month
    ano = filtro_mes.year

    df = get_dataframe(
        "SELECT id, descricao, valor, data_custo FROM custos_operacionais "
        "WHERE strftime('%Y', data_custo)=? AND strftime('%m', data_custo)=? "
        "ORDER BY data_custo DESC",
        params=(str(ano), f"{mes:02}")
    )

    if not df.empty:
        st.metric("💰 Total de Custos Fixos do Mês", f"R$ {df['valor'].sum():.2f}")

        for _, row in df.iterrows():
            rid = int(row['id'])
            with st.expander(f"{row['descricao']} — R$ {float(row['valor']):.2f}"):
                st.write(f"**Descrição:** {row['descricao']}")
                st.write(f"**Valor (R$):** {float(row['valor']):.2f}")
                st.write(f"**Data:** {pd.to_datetime(row['data_custo']).date()}")
                c1, c2 = st.columns(2)
                if c1.button("✏️ Editar", key=f"edit-{rid}"):
                    st.session_state["editar_custo_id"] = rid
                if c2.button("🗑️ Excluir", key=f"del-{rid}"):
                    st.session_state["excluir_custo_id"] = rid

    else:
        st.info("Nenhum custo fixo cadastrado neste mês.")

    # ----------------------
    # Formulário de edição (final da página)
    # ----------------------
    if st.session_state.get("editar_custo_id"):
        edit_id = st.session_state["editar_custo_id"]
        row = df[df['id'] == edit_id].iloc[0]

        st.markdown("---")
        st.subheader(f"Editar custo fixo — ID {edit_id}")
        with st.form(f"form_edit_custo_{edit_id}"):
            col1, col2 = st.columns(2)
            with col1:
                desc_edit = st.text_input("Descrição", value=row['descricao'])
                valor_edit = st.number_input("Valor (R$)", min_value=0.0, value=float(row['valor']))
            with col2:
                data_edit = st.date_input("Data do Custo", value=pd.to_datetime(row['data_custo']).date())

            salvar = st.form_submit_button("💾 Salvar")
            cancelar = st.form_submit_button("✖️ Cancelar")

            if salvar:
                executar_query(
                    "UPDATE custos_operacionais SET descricao=?, valor=?, data_custo=? WHERE id=?",
                    (desc_edit.strip(), valor_edit, data_edit, edit_id)
                )
                st.success("Custo fixo atualizado.")
                st.session_state.pop("editar_custo_id")
                st.rerun()

            if cancelar:
                st.session_state.pop("editar_custo_id")
                st.info("Edição cancelada.")

    # ----------------------
    # Confirmação de exclusão
    # ----------------------
    if st.session_state.get("excluir_custo_id"):
        del_id = st.session_state["excluir_custo_id"]
        st.markdown("---")
        st.warning("⚠️ Confirma a exclusão deste registro? Esta ação é irreversível.")
        cdel1, cdel2 = st.columns(2)
        if cdel1.button("🗑️ Confirmar exclusão", key=f"confirm-del-{del_id}"):
            executar_query("DELETE FROM custos_operacionais WHERE id=?", (del_id,))
            st.success("Registro excluído.")
            st.session_state.pop("excluir_custo_id")
            st.rerun()
        if cdel2.button("❌ Cancelar", key=f"cancel-del-{del_id}"):
            st.session_state.pop("excluir_custo_id")
            st.info("Exclusão cancelada.")
