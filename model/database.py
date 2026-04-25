"""
database.py — SIMAD
Gerencia a conexão com o banco de dados MySQL.

Para alterar o banco definitivo, basta editar o arquivo .env
na mesma pasta deste arquivo. Não mude o código aqui.
"""

import os
import mysql.connector
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()


def get_connection():
    """
    Abre e retorna uma conexão com o banco MySQL usando as
    variáveis de ambiente definidas em .env.

    Uso nos controllers:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        ...
        conn.close()
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "simad"),
        port=int(os.getenv("DB_PORT", 3306)),
        # Garante que datas e strings venham formatadas corretamente
        charset="utf8mb4",
        use_pure=True,
    )
