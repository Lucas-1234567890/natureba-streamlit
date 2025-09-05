# Natureba - Sistema de Gestão para Padaria

Sistema completo de gestão desenvolvido em Python/Streamlit para controle operacional e financeiro de padarias artesanais.

## Funcionalidades

- **Dashboard**: Métricas em tempo real com faturamento, vendas e margem
- **Produtos**: CRUD completo com controle de custos e precificação
- **Vendas**: Registro e histórico com análise de performance
- **Estoque**: Controle de ingredientes com alertas e lista de compras
- **Produção**: Gestão de receitas com débito automático de ingredientes
- **Relatórios**: Análises financeiras e KPIs operacionais

## Stack Técnica

- **Backend**: Python 3.8+ com SQLite
- **Frontend**: Streamlit com Plotly para visualizações
- **Dados**: Pandas para manipulação e análise

## Setup Rápido

```bash
# Instalar dependências
pip install streamlit pandas plotly xlsxwriter

# Executar aplicação
streamlit run main.py

# Acesso: http://localhost:8501
```

## Arquitetura

```
├── main.py              # Entry point
├── banco.py             # Database layer + queries
├── menu.py              # App routing
├── sidebar.py           # Navigation component
└── paginas/             # Feature modules
    ├── dashboard.py     # Analytics dashboard
    ├── produtos.py      # Product management
    ├── vendas.py        # Sales operations
    ├── estoque.py       # Inventory control
    ├── producao.py      # Production management
    ├── relatórios.py    # Reports & insights
    └── configuracao.py  # System config
```

## Base de Dados

Schema normalizado com 7 tabelas principais:
- `produtos`: Catálogo com preços e custos
- `vendas`: Transações de venda
- `ingredientes`: Inventário de matéria-prima
- `receitas`: Composição produto-ingrediente
- `producao`: Registros de fabricação
- `movimentacoes_estoque`: Audit trail de estoque
- `custos_operacionais`: Despesas fixas

## Features Técnicas

- **Cache de queries** para performance otimizada
- **Validação de dados** com tratamento de erros
- **Backup automático** com exportação Excel
- **Interface responsiva** com tema customizado
- **Cálculos automáticos** de margem e rentabilidade

## KPIs Calculados

- Faturamento diário/mensal/período
- Margem de lucro por produto
- Top performers por categoria
- Análise de sazonalidade
- Controle de break-even

---

**Desenvolvido por**: Lucas Amorim | Eng. Dados e IA  
**Contato**: lucas.amorim.porciuncula@gmail.com | [LinkedIn](https://linkedin.com/in/lucas-amorim-powerbi)
