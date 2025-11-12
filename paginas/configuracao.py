import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from funcoesAux import get_dataframe, executar_query
import os
from io import BytesIO  # <- necessário para Excel em memória

def modulo_configuracao():

    st.header("⚙️ Configurações do Sistema")

    tab1, tab2, tab3 = st.tabs(["🗃️ Backup", "🔄 Dados", "ℹ️ Sistema"])

    # ------------------ TAB 1: Backup ------------------
    with tab1:
        st.subheader("Backup dos Dados")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💾 Exportar Dados")
            # Ler o arquivo do banco
            with open("natureba.db", "rb") as f:
                dados_db = f.read()
            st.download_button(
                label="📥 Baixar Backup do Banco de Dados",
                data=dados_db,
                file_name="natureba_backup.db",
                mime="application/x-sqlite3"
            )

        with col2:
            st.markdown("### 📈 Exportar Relatórios")
            data_inicio = st.date_input("Data Início", value=datetime.now().date().replace(day=1))
            data_fim = st.date_input("Data Fim", value=datetime.now().date())

            if st.button("📊 Gerar Relatório Excel"):
                # Itens vendidos detalhados
                itens_vendidos = get_dataframe("""
                    SELECT 
                        v.data_venda,
                        v.hora_venda,
                        p.nome AS produto,
                        p.categoria,
                        iv.quantidade,
                        iv.preco_unitario,
                        iv.subtotal AS total,
                        iv.custo_variavel,
                        (iv.subtotal - iv.custo_variavel) AS margem
                    FROM itens_venda iv
                    JOIN vendas v ON iv.venda_id = v.id
                    JOIN produtos p ON iv.produto_id = p.id
                    WHERE v.data_venda BETWEEN ? AND ?
                    ORDER BY v.data_venda DESC
                """, (data_inicio, data_fim))

                # Resumo diário das vendas
                resumo_vendas = itens_vendidos.groupby(['data_venda']).agg(
                    total_venda=('total', 'sum'),
                    custo_total=('custo_variavel', 'sum'),
                    margem_total=('margem', 'sum'),
                    qtd_itens=('quantidade', 'sum')
                ).reset_index()

                # Produtos cadastrados
                produtos = get_dataframe("SELECT * FROM produtos")

                # Custos operacionais no período
                custos = get_dataframe("""
                    SELECT * FROM custos_operacionais
                    WHERE data_custo BETWEEN ? AND ?
                """, (data_inicio, data_fim))

                # Movimentações de estoque
                movimentos = get_dataframe("""
                    SELECT * FROM movimentacoes_estoque
                    WHERE data_movimentacao BETWEEN ? AND ?
                """, (data_inicio, data_fim))

                # Criar Excel em memória
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    itens_vendidos.to_excel(writer, sheet_name='Itens Vendidos', index=False)
                    resumo_vendas.to_excel(writer, sheet_name='Resumo Vendas', index=False)
                    produtos.to_excel(writer, sheet_name='Produtos', index=False)
                    custos.to_excel(writer, sheet_name='Custos Operacionais', index=False)
                    movimentos.to_excel(writer, sheet_name='Movimentacoes Estoque', index=False)

                output.seek(0)
                st.download_button(
                    label="📥 Baixar Relatório Completo",
                    data=output,
                    file_name=f"relatorio_natureba_{data_inicio}_{data_fim}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


    # ------------------ TAB 2: Gerenciar Dados ------------------
    with tab2:
        st.subheader("Gerenciar Dados")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧹 Limpeza de Dados")
            if st.button("🗑️ Limpar Vendas Antigas (>1 ano)"):
                data_limite = datetime.now().date() - timedelta(days=365)
                vendas_antigas = executar_query(
                    "SELECT COUNT(*) FROM vendas WHERE data_venda < ?", (data_limite,)
                )
                if vendas_antigas and vendas_antigas[0][0] > 0:
                    executar_query("DELETE FROM vendas WHERE data_venda < ?", (data_limite,))
                    st.success(f"✅ {vendas_antigas[0][0]} vendas antigas removidas!")
                else:
                    st.info("Nenhuma venda antiga encontrada.")
            
            if st.button("🔄 Recalcular Totais"):
                executar_query("""
                    UPDATE vendas 
                    SET total = quantidade * preco_unitario 
                    WHERE total != quantidade * preco_unitario
                """)
                st.success("✅ Totais recalculados!")

        with col2:
            st.markdown("### 📊 Estatísticas do Banco")
            stats_produtos = executar_query("SELECT COUNT(*) FROM produtos")[0][0]
            stats_vendas = executar_query("SELECT COUNT(*) FROM vendas")[0][0]
            stats_ingredientes = executar_query("SELECT COUNT(*) FROM ingredientes")[0][0]

            st.metric("📦 Produtos Cadastrados", stats_produtos)
            st.metric("💰 Vendas Registradas", stats_vendas)
            st.metric("🥖 Ingredientes", stats_ingredientes)

            try:
                db_size = os.path.getsize('natureba.db') / (1024 * 1024)
                st.metric("💾 Tamanho do Banco", f"{db_size:.2f} MB")
            except:
                st.metric("💾 Tamanho do Banco", "N/A")

    # ------------------ TAB 3: Informações do Sistema ------------------
    with tab3:
        st.subheader("Informações do Sistema")
        st.markdown("""
        ### 🍞 Natureba v1.0

        **Sistema de Gestão para Padaria Artesanal**

        #### ✨ Funcionalidades Principais:
        - 📊 Dashboard em tempo real
        - 📦 Gestão completa de produtos
        - 💰 Controle de vendas
        - 📈 Relatórios detalhados
        - 💾 Backup automático de dados

        #### 🛠️ Tecnologias:
        - **Frontend:** Streamlit (Python)
        - **Banco de Dados:** SQLite
        - **Visualizações:** Plotly
        - **Análises:** Pandas

        #### 📞 Suporte:
        Entre em contato via:
        - WhatsApp: [Clique aqui](https://wa.me/5571996420649)
        - E-mail: [lucas.amorim.porciuncula@gmail.com](mailto:lucas.amorim.porciuncula@gmail.com)

        ---
        
        ### 📋 Próximas Atualizações:
        - 🏪 Controle de estoque avançado
        - 📱 App móvel
        - 🤖 Análises preditivas
        - 📧 Relatórios por email
        - 🔐 Sistema de usuários
        """)

        with st.expander("🔧 Informações Técnicas"):
            st.code(f"""
Sistema Operacional: {os.name}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Banco de Dados: SQLite (natureba.db)
Versão Python: 3.8+
Dependências: streamlit, pandas, plotly, sqlite3
            """)

        st.markdown("© 2025 Natureba - Todos os direitos reservados.")
