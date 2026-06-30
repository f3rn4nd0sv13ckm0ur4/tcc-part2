import mysql.connector
import csv
import sys
import os

configuracao = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "almox"
}

def exportar_da_db():
    print("Tentando conectar ao banco de dados MySQL...")
    try:
        conexao = mysql.connector.connect(**configuracao)
        cursor = conexao.cursor(dictionary=True)
        
        # 1. Exportar Usuarios
        cursor.execute("SELECT id, email, tipo FROM usuarios")
        usuarios = cursor.fetchall()
        with open("usuarios.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Email", "Tipo"])
            for u in usuarios:
                writer.writerow([u["id"], u["email"], u["tipo"]])
        print("[OK] usuarios.csv gerado com sucesso a partir do banco de dados!")
        
        # 2. Exportar Itens (Estoque)
        cursor.execute("SELECT id, nome, quantidade, horario, responsavel FROM itens")
        itens = cursor.fetchall()
        with open("estoque.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nome", "Quantidade", "Horario", "Responsavel"])
            for i in itens:
                writer.writerow([
                    i["id"], i["nome"], i["quantidade"],
                    i["horario"], i["responsavel"]
                ])
        print("[OK] estoque.csv gerado com sucesso a partir do banco de dados!")
        
        # 3. Exportar Movimentacoes
        cursor.execute("""
            SELECT movimentacoes.id, itens.nome AS item_nome, movimentacoes.tipo, 
                   movimentacoes.quantidade, movimentacoes.responsavel, movimentacoes.data_hora
            FROM movimentacoes
            JOIN itens ON movimentacoes.item_id = itens.id
            ORDER BY movimentacoes.data_hora DESC
        """)
        movs = cursor.fetchall()
        with open("historico_movimentacoes.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Item", "Tipo", "Quantidade", "Responsavel", "Data/Hora"])
            for m in movs:
                writer.writerow([
                    m["id"], m["item_nome"], m["tipo"], m["quantidade"],
                    m["responsavel"], m["data_hora"]
                ])
        print("[OK] historico_movimentacoes.csv gerado com sucesso a partir do banco de dados!")
        
        cursor.close()
        conexao.close()
        return True
    except Exception as e:
        print(f"Erro ao conectar ou exportar do banco de dados: {e}")
        return False

def gerar_arquivos_exemplo():
    print("\nGerando arquivos CSV de exemplo na pasta do projeto (Mock)...")
    
    # 1. usuarios.csv
    with open("usuarios.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Email", "Tipo"])
        writer.writerow([1, "admin@gmail.com", "admin"])
        writer.writerow([2, "usuario@gmail.com", "usuario"])
    print("[OK] usuarios.csv de exemplo criado!")
    
    # 2. estoque.csv
    with open("estoque.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Nome", "Quantidade", "Horario", "Responsavel"])
        writer.writerow([1, "Parafuso Phillips", 150, "08:30:00", "Carlos Silva"])
        writer.writerow([2, "Chave de Fenda 3/16", 20, "09:15:00", "Ana Souza"])
        writer.writerow([3, "Fita Isolante 20m", 45, "14:20:00", "Roberto Santos"])
        writer.writerow([4, "Multimetro Digital", 8, "10:00:00", "Carlos Silva"])
    print("[OK] estoque.csv de exemplo criado!")
    
    # 3. historico_movimentacoes.csv
    with open("historico_movimentacoes.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Item", "Tipo", "Quantidade", "Responsavel", "Data/Hora"])
        writer.writerow([1, "Parafuso Phillips", "ADICIONAR", 200, "Carlos Silva", "2026-06-30 08:30:00"])
        writer.writerow([2, "Parafuso Phillips", "RETIRAR", 50, "Ana Souza", "2026-06-30 09:00:00"])
        writer.writerow([3, "Chave de Fenda 3/16", "ADICIONAR", 20, "Ana Souza", "2026-06-30 09:15:00"])
        writer.writerow([4, "Fita Isolante 20m", "ADICIONAR", 50, "Roberto Santos", "2026-06-30 14:20:00"])
        writer.writerow([5, "Fita Isolante 20m", "RETIRAR", 5, "Carlos Silva", "2026-06-30 15:00:00"])
        writer.writerow([6, "Multimetro Digital", "ADICIONAR", 8, "Carlos Silva", "2026-06-30 10:00:00"])
    print("[OK] historico_movimentacoes.csv de exemplo criado!")

if __name__ == "__main__":
    sucesso = exportar_da_db()
    if not sucesso:
        gerar_arquivos_exemplo()
    print("\nTodos os arquivos CSV estao prontos no diretorio!")
