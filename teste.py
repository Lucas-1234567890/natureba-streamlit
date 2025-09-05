import random
from datetime import datetime, timedelta
from banco import executar_query  # supondo que seu código acima está em main.py

# ---------------------------
# Inserir produtos
# ---------------------------
produtos = [
    ("Shampoo Natural", 25.0, 10.0, "Higiene"),
    ("Sabonete Vegano", 8.0, 2.5, "Higiene"),
    ("Creme Facial", 35.0, 12.0, "Cosmético"),
    ("Óleo Corporal", 50.0, 20.0, "Cosmético")
]

for nome, preco_venda, custo, categoria in produtos:
    executar_query(
        "INSERT OR IGNORE INTO produtos (nome, preco_venda, custo_producao, categoria) VALUES (?, ?, ?, ?)",
        (nome, preco_venda, custo, categoria)
    )

# ---------------------------
# Inserir ingredientes
# ---------------------------
ingredientes = [
    ("Aloe Vera", 30.0, 50, "kg", "Fornecedor A"),
    ("Óleo de Coco", 25.0, 100, "kg", "Fornecedor B"),
    ("Manteiga de Karité", 40.0, 30, "kg", "Fornecedor C"),
    ("Extrato de Camomila", 20.0, 70, "kg", "Fornecedor D")
]

for nome, preco_kg, estoque, unidade, fornecedor in ingredientes:
    executar_query(
        "INSERT OR IGNORE INTO ingredientes (nome, preco_kg, estoque_atual, unidade, fornecedor) VALUES (?, ?, ?, ?, ?)",
        (nome, preco_kg, estoque, unidade, fornecedor)
    )

# ---------------------------
# Inserir receitas
# ---------------------------
for produto_id in range(1, 5):
    for ingrediente_id in range(1, 5):
        quantidade = round(random.uniform(0.1, 1.0), 2)
        executar_query(
            "INSERT OR IGNORE INTO receitas (produto_id, ingrediente_id, quantidade) VALUES (?, ?, ?)",
            (produto_id, ingrediente_id, quantidade)
        )

# ---------------------------
# Inserir produção diária (100 linhas)
# ---------------------------
for _ in range(100):
    produto_id = random.randint(1, 4)
    quantidade = random.randint(1, 20)
    custo_total = round(random.uniform(10, 200), 2)
    data_producao = (datetime.now() - timedelta(days=random.randint(0, 30))).date()
    executar_query(
        "INSERT INTO producao (produto_id, quantidade, custo_total, data_producao) VALUES (?, ?, ?, ?)",
        (produto_id, quantidade, custo_total, data_producao)
    )

# ---------------------------
# Inserir vendas (100 linhas)
# ---------------------------
for _ in range(100):
    produto_id = random.randint(1, 4)
    quantidade = random.randint(1, 10)
    preco_unitario = round(random.uniform(5, 50), 2)
    total = round(preco_unitario * quantidade, 2)
    data_venda = (datetime.now() - timedelta(days=random.randint(0, 30))).date()
    executar_query(
        "INSERT INTO vendas (produto_id, quantidade, preco_unitario, total, data_venda) VALUES (?, ?, ?, ?, ?)",
        (produto_id, quantidade, preco_unitario, total, data_venda)
    )

# ---------------------------
# Inserir custos operacionais (20 linhas)
# ---------------------------
custos = ["Energia", "Água", "Aluguel", "Internet", "Marketing"]
for _ in range(20):
    descricao = random.choice(custos)
    valor = round(random.uniform(100, 1000), 2)
    categoria = "Operacional"
    data_custo = (datetime.now() - timedelta(days=random.randint(0, 30))).date()
    recorrente = random.choice([0, 1])
    executar_query(
        "INSERT INTO custos_operacionais (descricao, valor, categoria, data_custo, recorrente) VALUES (?, ?, ?, ?, ?)",
        (descricao, valor, categoria, data_custo, recorrente)
    )

# ---------------------------
# Inserir movimentações de estoque (100 linhas)
# ---------------------------
tipos = ["entrada", "saida"]
motivos = ["Reposição", "Produção", "Venda", "Perda"]
for _ in range(100):
    ingrediente_id = random.randint(1, 4)
    tipo = random.choice(tipos)
    quantidade = round(random.uniform(0.1, 5.0), 2)
    motivo = random.choice(motivos)
    executar_query(
        "INSERT INTO movimentacoes_estoque (ingrediente_id, tipo, quantidade, motivo) VALUES (?, ?, ?, ?)",
        (ingrediente_id, tipo, quantidade, motivo)
    )

print("Inserção de dados de teste concluída!")
