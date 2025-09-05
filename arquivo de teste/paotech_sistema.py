import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sqlite3
import os
from decimal import Decimal
import json

# Configuração da página
st.set_page_config(
    page_title="PãoTech - Gestão de Padaria",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #FF8E53);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B6B;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do banco de dados
@st.cache_resource
def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect('padaria.db', check_same_thread=False)
    
    # Tabela de produtos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            preco_venda REAL NOT NULL,
            custo_producao REAL NOT NULL,
            categoria TEXT NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de ingredientes
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            preco_kg REAL NOT NULL,
            estoque_atual REAL DEFAULT 0,
            unidade TEXT DEFAULT 'kg',
            fornecedor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de receitas (relaciona produtos com ingredientes)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            ingrediente_id INTEGER,
            quantidade REAL NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id)
        )
    ''')
    
    # Tabela de produção diária
    conn.execute('''
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            custo_total REAL NOT NULL,
            data_producao DATE NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    # Tabela de vendas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            total REAL NOT NULL,
            data_venda DATE NOT NULL,
            hora_venda TIME DEFAULT CURRENT_TIME,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    # Tabela de custos operacionais
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custos_operacionais (
            id INTEGER PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data_custo DATE NOT NULL,
            recorrente BOOLEAN DEFAULT 0
        )
    ''')
    
    conn.commit()
    return conn

# Funções auxiliares
def executar_query(query, params=None):
    """Executa uma query no banco de dados"""
    conn = init_database()
    if params:
        result = conn.execute(query, params)
    else:
        result = conn.execute(query)
    
    if query.strip().upper().startswith('SELECT'):
        return result.fetchall()
    else:
        conn.commit()
        return result.lastrowid

def get_dataframe(query, params=None):
    """Retorna um DataFrame a partir de uma query"""
    conn = init_database()
    if params:
        return pd.read_sql_query(query, conn, params=params)
    else:
        return pd.read_sql_query(query, conn)

# Função para popular dados de exemplo
def popular_dados_exemplo():
    """Popula o banco com dados de exemplo"""
    conn = init_database()
    
    # Verificar se já existem dados
    produtos_exist = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    
    if produtos_exist == 0:
        # Inserir produtos de exemplo
        produtos_exemplo = [
            ("Pão Integral", 8.50, 3.20, "Integral"),
            ("Pão de Chocolate", 12.00, 5.40, "Doce"),
            ("Pão de Cebola", 10.00, 4.10, "Salgado"),
            ("Pão de Abóbora", 9.50, 4.00, "Especial"),
            ("Pão Francês Artesanal", 7.00, 2.80, "Tradicional"),
            ("Pão de Centeio", 11.00, 4.50, "Integral")
        ]
        
        for produto in produtos_exemplo:
            conn.execute(
                "INSERT INTO produtos (nome, preco_venda, custo_producao, categoria) VALUES (?, ?, ?, ?)",
                produto
            )
        
        # Inserir ingredientes de exemplo
        ingredientes_exemplo = [
            ("Farinha de Trigo", 4.50, 50.0, "kg", "Fornecedor A"),
            ("Farinha Integral", 6.20, 25.0, "kg", "Fornecedor B"),
            ("Chocolate", 25.00, 5.0, "kg", "Fornecedor C"),
            ("Cebola", 3.50, 10.0, "kg", "Mercado Local"),
            ("Ovos", 12.00, 30.0, "dúzia", "Granja XYZ"),
            ("Fermento", 8.00, 2.0, "kg", "Fornecedor A")
        ]
        
        for ingrediente in ingredientes_exemplo:
            conn.execute(
                "INSERT INTO ingredientes (nome, preco_kg, estoque_atual, unidade, fornecedor) VALUES (?, ?, ?, ?, ?)",
                ingrediente
            )
        
        # Inserir algumas vendas de exemplo (últimos 7 dias)
        import random
        data_hoje = datetime.now().date()
        
        for i in range(7):
            data_venda = data_hoje - timedelta(days=i)
            
            # Vendas aleatórias para cada produto
            produtos = conn.execute("SELECT id, nome, preco_venda FROM produtos").fetchall()
            
            for produto_id, nome, preco in produtos:
                # Quantidade aleatória de vendas (0 a 15)
                quantidade = random.randint(0, 15)
                if quantidade > 0:
                    total = quantidade * preco
                    conn.execute(
                        "INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) VALUES (?, ?, ?, ?, ?)",
                        (produto_id, quantidade, preco, total, data_venda)
                    )
        
        conn.commit()
        st.success("✅ Dados de exemplo inseridos com sucesso!")

# Sidebar com navegação
def sidebar_navigation():
    st.sidebar.markdown("### 🍞 PãoTech")
    st.sidebar.markdown("*Sistema de Gestão para Padaria*")
    
    menu_options = [
        "🏠 Dashboard",
        "📦 Produtos",
        "🥖 Produção",
        "💰 Vendas",
        "📊 Relatórios",
        "⚙️ Configurações",
        "📦 Estoque"
    ]
    
    selected = st.sidebar.selectbox("Navegação", menu_options)
    
    # Botão para popular dados de exemplo
    if st.sidebar.button("🔄 Dados de Exemplo"):
        popular_dados_exemplo()
    
    return selected

# Dashboard Principal
def dashboard():
    st.markdown('<div class="main-header"><h1>🍞 Dashboard - PãoTech</h1></div>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    # Faturamento hoje
    hoje = datetime.now().date()
    faturamento_hoje = get_dataframe(
        "SELECT SUM(total) as total FROM vendas WHERE data_venda = ?",
        (hoje,)
    )['total'].iloc[0] or 0
    
    # Faturamento mês
    primeiro_dia_mes = hoje.replace(day=1)
    faturamento_mes = get_dataframe(
        "SELECT SUM(total) as total FROM vendas WHERE data_venda >= ?",
        (primeiro_dia_mes,)
    )['total'].iloc[0] or 0
    
    # Produtos vendidos hoje
    produtos_hoje = get_dataframe(
        "SELECT SUM(quantidade) as total FROM vendas WHERE data_venda = ?",
        (hoje,)
    )['total'].iloc[0] or 0
    
    # Margem média
    vendas_com_custo = get_dataframe("""
        SELECT SUM(v.total) as receita, SUM(v.quantidade * p.custo_producao) as custo
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda >= ?
    """, (primeiro_dia_mes,))
    
    receita = vendas_com_custo['receita'].iloc[0] or 0
    custo = vendas_com_custo['custo'].iloc[0] or 0
    margem = ((receita - custo) / receita * 100) if receita > 0 else 0
    
    with col1:
        st.metric("💰 Faturamento Hoje", f"R$ {faturamento_hoje:.2f}")
    
    with col2:
        st.metric("📅 Faturamento Mês", f"R$ {faturamento_mes:.2f}")
    
    with col3:
        st.metric("🥖 Pães Vendidos Hoje", f"{int(produtos_hoje)}")
    
    with col4:
        st.metric("📈 Margem Média", f"{margem:.1f}%")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Vendas por Produto (Últimos 7 dias)")
        vendas_produto = get_dataframe("""
            SELECT p.nome, SUM(v.quantidade) as total_vendido, SUM(v.total) as faturamento
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda >= ?
            GROUP BY p.nome
            ORDER BY total_vendido DESC
        """, (hoje - timedelta(days=7),))
        
        if not vendas_produto.empty:
            fig = px.bar(vendas_produto, x='nome', y='total_vendido',
                        title="Quantidade Vendida por Produto",
                        color='faturamento',
                        color_continuous_scale='Oranges')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma venda registrada nos últimos 7 dias.")
    
    with col2:
        st.subheader("📈 Evolução de Vendas (Últimos 7 dias)")
        vendas_diarias = get_dataframe("""
            SELECT data_venda, SUM(total) as faturamento_diario, SUM(quantidade) as produtos_vendidos
            FROM vendas
            WHERE data_venda >= ?
            GROUP BY data_venda
            ORDER BY data_venda
        """, (hoje - timedelta(days=7),))
        
        if not vendas_diarias.empty:
            fig = px.line(vendas_diarias, x='data_venda', y='faturamento_diario',
                         title="Faturamento Diário",
                         markers=True)
            fig.update_traces(line_color='#FF6B6B')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma venda registrada nos últimos 7 dias.")
    
    # Produtos mais lucrativos
    st.subheader("💎 Top 5 Produtos Mais Lucrativos")
    produtos_lucrativos = get_dataframe("""
        SELECT p.nome, p.preco_venda, p.custo_producao,
               (p.preco_venda - p.custo_producao) as lucro_unitario,
               ((p.preco_venda - p.custo_producao) / p.preco_venda * 100) as margem,
               COALESCE(SUM(v.quantidade), 0) as total_vendido
        FROM produtos p
        LEFT JOIN vendas v ON p.id = v.produto_id AND v.data_venda >= ?
        WHERE p.ativo = 1
        GROUP BY p.id, p.nome, p.preco_venda, p.custo_producao
        ORDER BY margem DESC
        LIMIT 5
    """, (hoje - timedelta(days=30),))
    
    if not produtos_lucrativos.empty:
        st.dataframe(
            produtos_lucrativos[['nome', 'preco_venda', 'custo_producao', 'lucro_unitario', 'margem', 'total_vendido']].style.format({
                'preco_venda': 'R$ {:.2f}',
                'custo_producao': 'R$ {:.2f}',
                'lucro_unitario': 'R$ {:.2f}',
                'margem': '{:.1f}%',
                'total_vendido': '{:.0f}'
            }),
            use_container_width=True
        )

# Módulo de Produtos
def modulo_produtos():
    st.header("📦 Gestão de Produtos")
    
    tab1, tab2 = st.tabs(["➕ Cadastrar/Editar", "📋 Lista de Produtos"])
    
    with tab1:
        st.subheader("Cadastro de Produto")
        
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome do Produto*")
                preco_venda = st.number_input("Preço de Venda (R$)*", min_value=0.01, format="%.2f")
                
            with col2:
                categoria = st.selectbox("Categoria*", 
                                       ["Tradicional", "Integral", "Doce", "Salgado", "Especial"])
                custo_producao = st.number_input("Custo de Produção (R$)*", min_value=0.01, format="%.2f")
            
            submitted = st.form_submit_button("✅ Cadastrar Produto")
            
            if submitted:
                if nome and preco_venda > 0 and custo_producao > 0:
                    try:
                        executar_query(
                            "INSERT INTO produtos (nome, preco_venda, custo_producao, categoria) VALUES (?, ?, ?, ?)",
                            (nome, preco_venda, custo_producao, categoria)
                        )
                        st.success(f"✅ Produto '{nome}' cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("❌ Já existe um produto com este nome!")
                        else:
                            st.error(f"❌ Erro ao cadastrar produto: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    with tab2:
        st.subheader("Produtos Cadastrados")
        
        produtos = get_dataframe("""
            SELECT id, nome, categoria, preco_venda, custo_producao,
                   (preco_venda - custo_producao) as lucro_unitario,
                   ((preco_venda - custo_producao) / preco_venda * 100) as margem,
                   ativo
            FROM produtos
            ORDER BY nome
        """)
        
        if not produtos.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_categoria = st.selectbox("Filtrar por Categoria", 
                                              ["Todas"] + list(produtos['categoria'].unique()))
            with col2:
                mostrar_inativos = st.checkbox("Mostrar produtos inativos")
            
            # Aplicar filtros
            produtos_filtrados = produtos.copy()
            
            if filtro_categoria != "Todas":
                produtos_filtrados = produtos_filtrados[produtos_filtrados['categoria'] == filtro_categoria]
            
            if not mostrar_inativos:
                produtos_filtrados = produtos_filtrados[produtos_filtrados['ativo'] == 1]
            
            # Exibir tabela
            if not produtos_filtrados.empty:
                st.dataframe(
                    produtos_filtrados[['nome', 'categoria', 'preco_venda', 'custo_producao', 'lucro_unitario', 'margem']].style.format({
                        'preco_venda': 'R$ {:.2f}',
                        'custo_producao': 'R$ {:.2f}',
                        'lucro_unitario': 'R$ {:.2f}',
                        'margem': '{:.1f}%'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum produto encontrado com os filtros aplicados.")
        else:
            st.info("Nenhum produto cadastrado ainda.")

# Módulo de Vendas
def modulo_vendas():
    st.header("💰 Registro de Vendas")
    
    tab1, tab2 = st.tabs(["➕ Nova Venda", "📋 Histórico"])
    
    with tab1:
        st.subheader("Registrar Nova Venda")
        
        # Buscar produtos ativos
        produtos = get_dataframe("SELECT id, nome, preco_venda FROM produtos WHERE ativo = 1 ORDER BY nome")
        
        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar vendas!")
            return
        
        with st.form("form_venda"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                produto_selecionado = st.selectbox("Produto*", 
                                                 options=produtos['id'].tolist(),
                                                 format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0])
            
            with col2:
                quantidade = st.number_input("Quantidade*", min_value=1, value=1)
            
            with col3:
                data_venda = st.date_input("Data da Venda*", value=datetime.now().date())
            
            # Mostrar informações do produto selecionado
            if produto_selecionado:
                produto_info = produtos[produtos['id']==produto_selecionado].iloc[0]
                preco_unitario = produto_info['preco_venda']
                total = preco_unitario * quantidade
                
                st.info(f"💰 Produto: {produto_info['nome']} | Preço: R$ {preco_unitario:.2f} | Total: R$ {total:.2f}")
            
            submitted = st.form_submit_button("✅ Registrar Venda")
            
            if submitted:
                if produto_selecionado and quantidade > 0:
                    try:
                        executar_query(
                            "INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) VALUES (?, ?, ?, ?, ?)",
                            (produto_selecionado, quantidade, preco_unitario, total, data_venda)
                        )
                        st.success(f"✅ Venda registrada: {quantidade}x {produto_info['nome']} = R$ {total:.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar venda: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    with tab2:
        st.subheader("Histórico de Vendas")
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
        
        vendas = get_dataframe("""
            SELECT v.data_venda, v.hora_venda, p.nome as produto,
                   v.quantidade, v.preco_unitario, v.total
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda BETWEEN ? AND ?
            ORDER BY v.data_venda DESC, v.hora_venda DESC
        """, (data_inicio, data_fim))
        
        if not vendas.empty:
            # Resumo do período
            total_vendas = vendas['total'].sum()
            total_itens = vendas['quantidade'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Total do Período", f"R$ {total_vendas:.2f}")
            with col2:
                st.metric("🥖 Itens Vendidos", f"{int(total_itens)}")
            
            # Tabela de vendas
            st.dataframe(
                vendas.style.format({
                    'preco_unitario': 'R$ {:.2f}',
                    'total': 'R$ {:.2f}'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma venda encontrada no período selecionado.")

# Módulo de Relatórios
def modulo_relatorios():
    st.header("📊 Relatórios e Análises")
    
    tab1, tab2, tab3 = st.tabs(["📈 Financeiro", "📦 Produtos", "📅 Período"])
    
    with tab1:
        st.subheader("Análise Financeira")
        
        # Período para análise
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date().replace(day=1))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
        
        # Análise de rentabilidade
        rentabilidade = get_dataframe("""
            SELECT 
                SUM(v.total) as receita_total,
                SUM(v.quantidade * p.custo_producao) as custo_total,
                (SUM(v.total) - SUM(v.quantidade * p.custo_producao)) as lucro_bruto,
                ((SUM(v.total) - SUM(v.quantidade * p.custo_producao)) / SUM(v.total) * 100) as margem_bruta
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda BETWEEN ? AND ?
        """, (data_inicio, data_fim))
        
        if not rentabilidade.empty and rentabilidade['receita_total'].iloc[0]:
            dados = rentabilidade.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Receita", f"R$ {dados['receita_total']:.2f}")
            with col2:
                st.metric("💸 Custos", f"R$ {dados['custo_total']:.2f}")
            with col3:
                st.metric("📈 Lucro Bruto", f"R$ {dados['lucro_bruto']:.2f}")
            with col4:
                st.metric("🎯 Margem", f"{dados['margem_bruta']:.1f}%")
            
            # Gráfico de composição
            fig = go.Figure(data=[
                go.Bar(name='Custos', x=['Análise'], y=[dados['custo_total']], marker_color='#FF6B6B'),
                go.Bar(name='Lucro', x=['Análise'], y=[dados['lucro_bruto']], marker_color='#4ECDC4')
            ])
            fig.update_layout(
                title='Composição Receita vs Custos vs Lucro',
                barmode='stack',
                yaxis_title='Valor (R$)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma venda no período selecionado.")
    
    with tab2:
        st.subheader("Análise por Produtos")
        
        ranking_produtos = get_dataframe("""
            SELECT 
                p.nome,
                p.categoria,
                SUM(v.quantidade) as quantidade_vendida,
                SUM(v.total) as receita,
                SUM(v.quantidade * p.custo_producao) as custo,
                (SUM(v.total) - SUM(v.quantidade * p.custo_producao)) as lucro,
                ((SUM(v.total) - SUM(v.quantidade * p.custo_producao)) / SUM(v.total) * 100) as margem
            FROM vendas v
            JOIN produtos p ON v.produto_id = p.id
            WHERE v.data_venda >= ?
            GROUP BY p.id, p.nome, p.categoria
            ORDER BY receita DESC
        """, (datetime.now().date() - timedelta(days=30),))
        
        if not ranking_produtos.empty:
            # Top produtos por receita
            st.subheader("🏆 Top Produtos por Receita (Últimos 30 dias)")
            fig = px.bar(ranking_produtos.head(10), 
                        x='nome', y='receita',
                        color='margem',
                        title="Receita por Produto",
                        color_continuous_scale='Viridis')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela completa
            st.subheader("📋 Ranking Completo")
            st.dataframe(
                ranking_produtos.style.format({
                    'receita': 'R$ {:.2f}',
                    'custo': 'R$ {:.2f}',
                    'lucro': 'R$ {:.2f}',
                    'margem': '{:.1f}%'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma venda nos últimos 30 dias.")
    
    with tab3:
        st.subheader("Análise por Período")
        
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
                SUM(total) as faturamento,
                SUM(quantidade) as produtos_vendidos
            FROM vendas
            WHERE data_venda >= ?
            GROUP BY strftime('%w', data_venda)
            ORDER BY strftime('%w', data_venda)
        """, (datetime.now().date() - timedelta(days=30),))
        
        if not vendas_semana.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(vendas_semana, x='dia_semana', y='faturamento',
                           title="Faturamento por Dia da Semana")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(vendas_semana, x='dia_semana', y='produtos_vendidos',
                           title="Produtos Vendidos por Dia da Semana")
                st.plotly_chart(fig, use_container_width=True)

# Função principal
def main():
    # Inicializar banco
    init_database()
    
    # Navegação
    selected_page = sidebar_navigation()
    
    # Renderizar página selecionada
    if "Dashboard" in selected_page:
        dashboard()
    elif "Produtos" in selected_page:
        modulo_produtos()
    elif "Vendas" in selected_page:
        modulo_vendas()
    elif "Relatórios" in selected_page:
        modulo_relatorios()
    elif "Configurações" in selected_page:
        modulo_configuracoes()
    elif "Produção" in selected_page:
        modulo_producao()
    elif "Estoque" in selected_page:
        modulo_estoque()

# Módulo de Configurações
def modulo_configuracoes():
    st.header("⚙️ Configurações do Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🗃️ Backup", "🔄 Dados", "ℹ️ Sistema"])
    
    with tab1:
        st.subheader("Backup dos Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💾 Exportar Dados")
            if st.button("📥 Baixar Backup Completo"):
                # Criar backup em JSON
                backup_data = {}
                
                # Produtos
                produtos = get_dataframe("SELECT * FROM produtos")
                backup_data['produtos'] = produtos.to_dict('records')
                
                # Vendas
                vendas = get_dataframe("SELECT * FROM vendas")
                backup_data['vendas'] = vendas.to_dict('records')
                
                # Ingredientes
                ingredientes = get_dataframe("SELECT * FROM ingredientes")
                backup_data['ingredientes'] = ingredientes.to_dict('records')
                
                backup_json = json.dumps(backup_data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download Backup (JSON)",
                    data=backup_json,
                    file_name=f"paotech_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            st.markdown("### 📈 Exportar Relatórios")
            
            data_inicio = st.date_input("Data Início", value=datetime.now().date().replace(day=1))
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
            
            if st.button("📊 Gerar Relatório Excel"):
                # Relatório de vendas
                vendas_relatorio = get_dataframe("""
                    SELECT v.data_venda, v.hora_venda, p.nome as produto,
                           p.categoria, v.quantidade, v.preco_unitario, v.total,
                           p.custo_producao, (v.preco_unitario - p.custo_producao) as margem_unitaria
                    FROM vendas v
                    JOIN produtos p ON v.produto_id = p.id
                    WHERE v.data_venda BETWEEN ? AND ?
                    ORDER BY v.data_venda DESC
                """, (data_inicio, data_fim))
                
                if not vendas_relatorio.empty:
                    # Converter para CSV para download
                    csv = vendas_relatorio.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Relatório CSV",
                        data=csv,
                        file_name=f"relatorio_vendas_{data_inicio}_a_{data_fim}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Nenhuma venda no período selecionado.")
    
    with tab2:
        st.subheader("Gerenciamento de Dados")
        
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
                # Recalcula totais das vendas
                executar_query("""
                    UPDATE vendas 
                    SET total = quantidade * preco_unitario 
                    WHERE total != quantidade * preco_unitario
                """)
                st.success("✅ Totais recalculados!")
        
        with col2:
            st.markdown("### 📊 Estatísticas do Banco")
            
            # Contar registros
            stats_produtos = executar_query("SELECT COUNT(*) FROM produtos")[0][0]
            stats_vendas = executar_query("SELECT COUNT(*) FROM vendas")[0][0]
            stats_ingredientes = executar_query("SELECT COUNT(*) FROM ingredientes")[0][0]
            
            st.metric("📦 Produtos Cadastrados", stats_produtos)
            st.metric("💰 Vendas Registradas", stats_vendas)
            st.metric("🥖 Ingredientes", stats_ingredientes)
            
            # Tamanho do banco
            try:
                db_size = os.path.getsize('padaria.db') / (1024 * 1024)  # MB
                st.metric("💾 Tamanho do Banco", f"{db_size:.2f} MB")
            except:
                st.metric("💾 Tamanho do Banco", "N/A")
    
    with tab3:
        st.subheader("Informações do Sistema")
        
        st.markdown("""
        ### 🍞 PãoTech v1.0
        
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
        Para dúvidas ou sugestões de melhorias, entre em contato!
        
        ---
        
        ### 📋 Próximas Atualizações:
        - 🏪 Controle de estoque avançado
        - 📱 App móvel
        - 🤖 Análises preditivas
        - 📧 Relatórios por email
        - 🔐 Sistema de usuários
        """)
        
        # Informações técnicas
        with st.expander("🔧 Informações Técnicas"):
            st.code(f"""
Sistema Operacional: {os.name}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Banco de Dados: SQLite (padaria.db)
Versão Python: 3.8+
Dependências: streamlit, pandas, plotly, sqlite3
            """)

# Módulo de Produção
def modulo_producao():
    st.header("🥖 Controle de Produção")
    
    tab1, tab2, tab3 = st.tabs(["➕ Registrar Produção", "📋 Produção Hoje", "📊 Histórico"])
    
    with tab1:
        st.subheader("Registrar Nova Produção")
        
        # Buscar produtos ativos
        produtos = get_dataframe("SELECT id, nome, custo_producao FROM produtos WHERE ativo = 1 ORDER BY nome")
        
        if produtos.empty:
            st.warning("⚠️ Cadastre produtos antes de registrar produção!")
            return
        
        with st.form("form_producao"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                produto_selecionado = st.selectbox("Produto*", 
                                                 options=produtos['id'].tolist(),
                                                 format_func=lambda x: produtos[produtos['id']==x]['nome'].iloc[0])
            
            with col2:
                quantidade = st.number_input("Quantidade Produzida*", min_value=1, value=1)
            
            with col3:
                data_producao = st.date_input("Data da Produção*", value=datetime.now().date())
            
            # Mostrar informações do produto selecionado
            if produto_selecionado:
                produto_info = produtos[produtos['id']==produto_selecionado].iloc[0]
                custo_unitario = produto_info['custo_producao']
                custo_total = custo_unitario * quantidade
                
                st.info(f"🍞 Produto: {produto_info['nome']} | Custo Unit.: R$ {custo_unitario:.2f} | Custo Total: R$ {custo_total:.2f}")
                
                # Mostrar receita se existir
                receita = get_dataframe("""
                    SELECT i.nome, r.quantidade, i.unidade
                    FROM receitas r
                    JOIN ingredientes i ON r.ingrediente_id = i.id
                    WHERE r.produto_id = ?
                """, [produto_selecionado])
                
                if not receita.empty:
                    with st.expander("📋 Ver Receita"):
                        st.write("**Ingredientes necessários por unidade:**")
                        for _, row in receita.iterrows():
                            st.write(f"• {row['nome']}: {row['quantidade']} {row['unidade']}")
                        
                        st.write(f"**Para {quantidade} unidades será necessário:**")
                        for _, row in receita.iterrows():
                            total_ingrediente = row['quantidade'] * quantidade
                            st.write(f"• {row['nome']}: {total_ingrediente} {row['unidade']}")
            
            observacoes = st.text_area("Observações (opcional)")
            
            submitted = st.form_submit_button("✅ Registrar Produção")
            
            if submitted:
                if produto_selecionado and quantidade > 0:
                    try:
                        # Registrar produção
                        executar_query(
                            "INSERT INTO producao (produto_id, quantidade, custo_total, data_producao) VALUES (?, ?, ?, ?)",
                            (produto_selecionado, quantidade, custo_total, data_producao)
                        )
                        
                        # Baixar ingredientes do estoque (se existir receita)
                        receita = get_dataframe("""
                            SELECT r.ingrediente_id, r.quantidade, i.nome
                            FROM receitas r
                            JOIN ingredientes i ON r.ingrediente_id = i.id
                            WHERE r.produto_id = ?
                        """, [produto_selecionado])
                        
                        if not receita.empty:
                            for _, row in receita.iterrows():
                                quantidade_necessaria = row['quantidade'] * quantidade
                                
                                # Baixar do estoque
                                executar_query("""
                                    UPDATE ingredientes 
                                    SET estoque_atual = estoque_atual - ? 
                                    WHERE id = ?
                                """, (quantidade_necessaria, row['ingrediente_id']))
                                
                                # Registrar movimentação
                                motivo = f"Produção: {quantidade}x {produto_info['nome']}"
                                executar_query("""
                                    INSERT INTO movimentacoes_estoque 
                                    (ingrediente_id, tipo, quantidade, motivo, data_movimentacao) 
                                    VALUES (?, 'saida', ?, ?, ?)
                                """, (row['ingrediente_id'], quantidade_necessaria, motivo, datetime.now()))
                        
                        st.success(f"✅ Produção registrada: {quantidade}x {produto_info['nome']} = R$ {custo_total:.2f}")
                        
                        if not receita.empty:
                            st.info("📦 Estoque de ingredientes atualizado automaticamente!")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar produção: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    with tab2:
        st.subheader("Produção de Hoje")
        
        hoje = datetime.now().date()
        producao_hoje = get_dataframe("""
            SELECT p.nome as produto, pr.quantidade, pr.custo_total,
                   (pr.custo_total / pr.quantidade) as custo_unitario
            FROM producao pr
            JOIN produtos p ON pr.produto_id = p.id
            WHERE pr.data_producao = ?
            ORDER BY pr.id DESC
        """, (hoje,))
        
        if not producao_hoje.empty:
            # Resumo do dia
            total_itens = producao_hoje['quantidade'].sum()
            total_custo = producao_hoje['custo_total'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🍞 Itens Produzidos", f"{int(total_itens)}")
            with col2:
                st.metric("💸 Custo Total", f"R$ {total_custo:.2f}")
            
            # Tabela da produção
            st.dataframe(
                producao_hoje.style.format({
                    'custo_unitario': 'R$ {:.2f}',
                    'custo_total': 'R$ {:.2f}'
                }),
                use_container_width=True
            )
            
            # Gráfico de produção por produto
            fig = px.pie(producao_hoje, values='quantidade', names='produto',
                        title="Distribuição da Produção de Hoje")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("😴 Nenhuma produção registrada hoje ainda.")
            
            # Sugestão baseada nas vendas de ontem
            ontem = hoje - timedelta(days=1)
            vendas_ontem = get_dataframe("""
                SELECT p.nome, SUM(v.quantidade) as vendido_ontem
                FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                WHERE v.data_venda = ?
                GROUP BY p.id, p.nome
                ORDER BY vendido_ontem DESC
            """, (ontem,))
            
            if not vendas_ontem.empty:
                st.subheader("💡 Sugestão baseada nas vendas de ontem:")
                for _, row in vendas_ontem.iterrows():
                    st.write(f"• **{row['nome']}**: {int(row['vendido_ontem'])} unidades")
    
    with tab3:
        st.subheader("Histórico de Produção")
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início", value=datetime.now().date() - timedelta(days=7))
        with col2:
            data_fim = st.date_input("Data Fim", value=datetime.now().date())
        
        producao_historico = get_dataframe("""
            SELECT pr.data_producao, p.nome as produto, p.categoria,
                   pr.quantidade, pr.custo_total,
                   (pr.custo_total / pr.quantidade) as custo_unitario
            FROM producao pr
            JOIN produtos p ON pr.produto_id = p.id
            WHERE pr.data_producao BETWEEN ? AND ?
            ORDER BY pr.data_producao DESC, pr.id DESC
        """, (data_inicio, data_fim))
        
        if not producao_historico.empty:
            # Resumo do período
            total_producao = producao_historico['quantidade'].sum()
            total_custo_periodo = producao_historico['custo_total'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🍞 Total Produzido", f"{int(total_producao)}")
            with col2:
                st.metric("💸 Custo Total", f"R$ {total_custo_periodo:.2f}")
            with col3:
                custo_medio = total_custo_periodo / total_producao if total_producao > 0 else 0
                st.metric("📊 Custo Médio", f"R$ {custo_medio:.2f}")
            
            # Gráfico de produção por dia
            producao_diaria = producao_historico.groupby('data_producao').agg({
                'quantidade': 'sum',
                'custo_total': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(producao_diaria, x='data_producao', y='quantidade',
                             title="Produção Diária (Unidades)",
                             markers=True)
                fig.update_traces(line_color='#FF6B6B')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(producao_diaria, x='data_producao', y='custo_total',
                             title="Custo de Produção Diária",
                             markers=True)
                fig.update_traces(line_color='#4ECDC4')
                st.plotly_chart(fig, use_container_width=True)
            
            # Ranking de produtos mais produzidos
            ranking_producao = producao_historico.groupby('produto').agg({
                'quantidade': 'sum',
                'custo_total': 'sum'
            }).reset_index().sort_values('quantidade', ascending=False)
            
            st.subheader("🏆 Produtos Mais Produzidos no Período")
            fig = px.bar(ranking_producao.head(10), x='produto', y='quantidade',
                        color='custo_total',
                        title="Ranking de Produção por Produto",
                        color_continuous_scale='Oranges')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("📋 Detalhes da Produção")
            st.dataframe(
                producao_historico.style.format({
                    'custo_unitario': 'R$ {:.2f}',
                    'custo_total': 'R$ {:.2f}'
                }),
                use_container_width=True
            )
        else:
            st.info("Nenhuma produção registrada no período selecionado.")

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



if __name__ == "__main__":
    main()