# 🍞 Natureba — Sistema de Gestão para Padarias Artesanais

Sistema completo para controle de **custos, estoque, receitas e margens em tempo real**.

**Por:** Lucas Amorim – Eng. Dados & IA  
📧 lucas.amorim.porciuncula@gmail.com  
🔗 LinkedIn • GitHub

---

## 🚀 O Problema
A maioria das padarias **não sabe o custo real** de cada produto e perde dinheiro sem perceber.

**O Natureba resolve isso:**
- Calcula custo e margem automaticamente
- Controla estoque e ingredientes
- Ajuda a precificar corretamente
- Informa lucros, prejuízos e break-even

---

## 🔑 Credenciais Demo
Login: adm
Senha: admin123

---

## ⚡ Instalação
```bash
pip install streamlit pandas plotly xlsxwriter
python teste.py        # Cria usuário admin
streamlit run main.py  # Inicia sistema
```
## 📊 Funcionalidades

### Painel (Dashboard)
- KPIs em tempo real  
- Margem de Contribuição  
- Lucro Líquido  
- Break-even  
- Alertas de estoque  

### Produtos & Receitas
- Cadastro de produtos  
- Cálculo automático de custo:

- Alerta de margem baixa (<20%)

### Vendas
- Carrinho multi-itens  
- Valida estoque antes de vender  
- Baixa estoque automático  

### Estoque
- Controle de ingredientes e produtos prontos  
- Histórico completo de movimentação  
- Lista automática de compras  

### Usuários
- Admin e Operador  
- Senhas com hash SHA-256  

### Backup & Relatórios
- Backup do SQLite  
- Planilhas Excel multi-aba  

---

## 📈 Métricas Principais

- Margem de Contribuição = (Receita - Custos Variáveis) / Receita
- Break-Even = Custos Fixos / Margem de Contribuição
- Ticket Médio = Faturamento Total / Nº de Vendas
- 
```bash
natureba/
├── main.py # Ponto de entrada
├── banco.py # Banco (SQLite)
├── funcoesAux.py # Lógica de negócio
├── paginas/ # Módulos (dashboard, vendas, estoque...)
└── natureba.db # Base local
```


---

## 📚 Fluxo de Uso

### Setup Inicial

### Operação Diária
- Registrar produção (baixa ingredientes)  
- Registrar vendas (baixa produtos)  

### Gestão Mensal
- Analisar margens  
- Ajustar preços  
- Registrar custos fixos  
- Exportar relatórios  

---

## 🔐 Segurança
- Hash SHA-256 + salt  
- Níveis de permissão  
- Auditoria com timestamp  
- Expiração de sessão (8h)  

---

## 🧭 Roadmap
- App Mobile (offline)  
- Previsão de demanda (IA)  
- Multi-tenancy (SaaS)  
- API REST  
- Emissão de NF-e  

---

## 📄 Licença
MIT License © 2025 Lucas Amorim  

---

<div align="center">
Feito com ❤️ em Python  
<br>
Se gostou, deixe uma ⭐ no repositório!
</div>
