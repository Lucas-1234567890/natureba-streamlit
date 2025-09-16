# Natureba - Sistema de Gestão para Padaria

Sistema completo de gestão desenvolvido em Python/Streamlit para controle operacional e financeiro de padarias artesanais com sistema de autenticação multiusuário.

## 🚀 Funcionalidades

### 📊 Core Business
- **Dashboard Avançado**: Métricas em tempo real com faturamento, vendas e análise de margem
- **Gestão de Produtos**: CRUD completo com controle de preços e categorização
- **Controle de Vendas**: Registro e histórico com análise de performance por período
- **Estoque Inteligente**: Gestão de ingredientes com alertas automáticos e lista de compras
- **Custos Operacionais**: Controle de custos fixos mensais com categorização
- **Relatórios Avançados**: Análises financeiras, KPIs operacionais e insights de negócio

### 🔐 Sistema de Autenticação
- **Login Seguro**: Hash de senhas com salt personalizado
- **Controle de Acesso**: Níveis de usuário (Admin/Operador)
- **Gestão Multiusuário**: Interface completa para administração de usuários
- **Timeout de Sessão**: Controle automático de segurança (8 horas)
- **Último Login**: Rastreamento de atividade dos usuários

### 📈 Analytics e Business Intelligence
- **Margem de Contribuição**: Cálculo automático de rentabilidade
- **Ponto de Equilíbrio**: Análise de viabilidade financeira
- **Margem de Segurança**: Indicadores de risco operacional
- **Análise Temporal**: Vendas por dia da semana e sazonalidade
- **Ranking de Produtos**: Top performers por receita e quantidade

## 🛠 Stack Técnica

### Backend
- **Python 3.8+** com SQLite
- **Pandas** para manipulação e análise de dados
- **Hashlib** para criptografia de senhas
- **DateTime** para controle temporal

### Frontend
- **Streamlit** com interface responsiva
- **Plotly** para visualizações interativas
- **CSS customizado** com tema Natureba

### Banco de Dados
- **SQLite** com schema normalizado
- **7 tabelas principais** com relacionamentos otimizados
- **Controle de integridade** referencial

## 🚀 Setup e Instalação

### Instalação Rápida
```bash
# Clonar repositório
git clone <repo-url>
cd natureba

# Instalar dependências
pip install streamlit pandas plotly xlsxwriter

# Executar aplicação
streamlit run main.py

# Acesso: http://localhost:8501
```

### Dependências
```txt
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
xlsxwriter>=3.1.0
```

### Primeiro Acesso
O sistema criará automaticamente as tabelas necessárias no primeiro uso. Para acessar:

1. Execute `streamlit run main.py`
2. Acesse `http://localhost:8501`
3. Crie o primeiro usuário administrador
4. Faça login e comece a usar!

## 📁 Arquitetura do Projeto

```
natureba/
├── main.py                 # Entry point da aplicação
├── menu.py                 # Roteamento principal
├── sidebar.py              # Componente de navegação
├── auth.py                 # Sistema de autenticação completo
├── banco.py                # Database layer + queries otimizadas
├── .streamlit/
│   └── config.toml         # Tema personalizado Natureba
├── .devcontainer/
│   └── devcontainer.json   # Configuração para desenvolvimento
└── paginas/
    ├── dashboard.py        # Analytics e métricas
    ├── produtos.py         # Gestão de produtos
    ├── vendas.py          # Operações de venda
    ├── estoque.py         # Controle de inventário
    ├── custos.py          # Custos operacionais
    ├── relatórios.py      # Relatórios e insights
    └── configuracao.py    # Configurações do sistema
```

## 🗄 Schema do Banco de Dados

### Tabelas Principais

#### `usuarios` - Sistema de Autenticação
- Controle de acesso com hash de senhas
- Níveis: admin/operador
- Tracking de último login

#### `produtos` - Catálogo
- Nome, categoria, preço de venda
- Status ativo/inativo
- Timestamp de criação

#### `vendas` - Transações
- Produto, quantidade, preços, data/hora
- Cálculo automático de totais
- Relacionamento com produtos

#### `ingredientes` - Inventário
- Nome, preço/kg, estoque atual
- Unidades de medida flexíveis
- Controle de fornecedores

#### `movimentacoes_estoque` - Audit Trail
- Entradas e saídas de estoque
- Motivos e timestamps
- Rastreabilidade completa

#### `custos_operacionais` - Despesas
- Custos fixos e variáveis
- Categorização e recorrência
- Controle temporal

## 💡 Features Avançadas

### 🔐 Segurança
- **Hash SHA-256** com salt personalizado
- **Timeout automático** de sessão
- **Controle de acesso** por níveis
- **Validação de dados** em todas as operações

### 📊 Analytics
- **Cálculos automáticos** de margem e rentabilidade
- **Análise de sazonalidade** por período
- **KPIs financeiros** em tempo real
- **Alertas de estoque** configuráveis

### 🎨 UX/UI
- **Tema personalizado** com cores Natureba
- **Interface responsiva** e intuitiva
- **Validações visuais** e feedback imediato
- **Navegação fluida** entre módulos

### 💾 Backup e Exportação
- **Backup automático** do banco SQLite
- **Exportação Excel** de relatórios
- **Configurações centralizadas** de sistema
- **Limpeza automática** de dados antigos

## 📈 KPIs e Métricas Calculadas

### Financeiros
- **Receita Total** por período
- **Margem de Contribuição** (absoluta e percentual)
- **Ponto de Equilíbrio** operacional
- **Margem de Segurança** do negócio
- **Lucro Líquido** e margem líquida

### Operacionais
- **Top produtos** por receita/quantidade
- **Análise de sazonalidade** semanal
- **Controle de estoque** com alertas
- **Performance por categoria** de produto

## 🔧 Configurações do Sistema

### Tema Natureba
```toml
[theme]
base = "light"
primaryColor = "#5C977C"            # Verde Natureba
backgroundColor = "#F6FAF8"         # Fundo claro
secondaryBackgroundColor = "#EAF3EF" # Cards/sidebars
textColor = "#1F2A27"               # Texto escuro
font = "sans serif"
```

### Parâmetros de Segurança
- **SESSION_TIMEOUT**: 480 minutos (8 horas)
- **SALT**: Hash personalizado para senhas
- **Níveis de usuário**: admin/operador

## 🚀 Deploy e Produção

### Streamlit Cloud
```bash
# Fazer push para GitHub
# Conectar repositório no Streamlit Cloud
# Deploy automático
```

### Docker (Opcional)
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD streamlit run main.py --server.port 8501
```

## 🛡 Backup e Manutenção

### Backup Automático
- Exportação do banco SQLite completo
- Relatórios Excel por período
- Configurações do sistema

### Limpeza de Dados
- Remoção de vendas antigas (>1 ano)
- Recálculo de totais automatizado
- Otimização de performance

## 📞 Suporte e Contato

**Desenvolvido por**: Lucas Amorim | Engenheiro de Dados e IA

### Conecte-se:
- 📧 **Email**: lucas.amorim.porciuncula@gmail.com
- 💼 **LinkedIn**: [lucas-amorim-powerbi](https://linkedin.com/in/lucas-amorim-powerbi)
- 🌐 **Portfólio**: [Xperiun](https://app.xperiun.com/in/lucas-amorim-portfólio)
- 💻 **GitHub**: [Lucas-1234567890](https://github.com/Lucas-1234567890)
- 📱 **Instagram**: [@engdados.lucas_amorim](https://instagram.com/engdados.lucas_amorim)

### Suporte
- 💬 **WhatsApp**: [Clique aqui](https://wa.me/5571996420649)
- 📧 **Email**: Suporte técnico via email

---

## 📋 Roadmap Futuro

- [ ] 📱 **App móvel** React Native
- [ ] 🤖 **ML para previsão** de demanda
- [ ] 📧 **Relatórios automáticos** por email
- [ ] 🔄 **Integração ERP** externa
- [ ] 📊 **Dashboard executivo** avançado
- [ ] 🛒 **E-commerce** integrado

---

**© 2025 Natureba - Sistema de Gestão para Padaria**  
*Transformando dados em crescimento sustentável* 🌱
