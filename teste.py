import sqlite3
import hashlib
from datetime import datetime

# Configuração de segurança para senha
SALT = "natureba_padaria_2025"

def hash_password(password):
    return hashlib.sha256((password + SALT).encode()).hexdigest()

# Conectar ao banco (já deve estar criado com as tabelas)
conn = sqlite3.connect('natureba.db')
conn.execute('PRAGMA foreign_keys = ON;')

# Inserir usuário admin
admin_user = "adm"
admin_pass = "admin123"
admin_nome = "Administrador"
password_hash = hash_password(admin_pass)

try:
    conn.execute('''
    INSERT INTO usuarios (username, password_hash, nome_completo, nivel, ativo)
    VALUES (?, ?, ?, 'admin', 1)
    ''', (admin_user, password_hash, admin_nome))
    conn.commit()
    print("Usuário admin criado com sucesso!")
except sqlite3.IntegrityError:
    print("Usuário já existe no banco.")

conn.close()
