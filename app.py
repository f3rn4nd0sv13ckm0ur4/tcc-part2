from flask import Flask, render_template, request, redirect, session, make_response
import mysql.connector
import bcrypt
import csv
import io
import os


app = Flask(__name__)
app.secret_key = "chave_secreta_do_tcc"

configuracao = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "almox"
}

def conectar():
    return mysql.connector.connect(**configuracao)


def atualizar_csv_local():
    try:
        diretorio = os.path.dirname(os.path.abspath(__file__))
        pasta_exportacao = os.path.join(diretorio, "exportações")
        if not os.path.exists(pasta_exportacao):
            os.makedirs(pasta_exportacao)
        estoque_path = os.path.join(pasta_exportacao, "estoque.csv")
        historico_path = os.path.join(pasta_exportacao, "historico_movimentacoes.csv")
        
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        
        # 1. Atualizar estoque.csv
        cursor.execute("SELECT id, nome, quantidade, horario, responsavel FROM itens")
        itens = cursor.fetchall()
        with open(estoque_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nome", "Quantidade", "Horario", "Responsavel"])
            for i in itens:
                writer.writerow([
                    i["id"], i["nome"], i["quantidade"],
                    i["horario"], i["responsavel"]
                ])
                
        # 2. Atualizar historico_movimentacoes.csv
        cursor.execute("""
            SELECT movimentacoes.id, itens.nome AS item_nome, movimentacoes.tipo, 
                   movimentacoes.quantidade, movimentacoes.responsavel, movimentacoes.data_hora
            FROM movimentacoes
            JOIN itens ON movimentacoes.item_id = itens.id
            ORDER BY movimentacoes.data_hora DESC
        """)
        movs = cursor.fetchall()
        with open(historico_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Item", "Tipo", "Quantidade", "Responsavel", "Data/Hora"])
            for m in movs:
                writer.writerow([
                    m["id"], m["item_nome"], m["tipo"], m["quantidade"],
                    m["responsavel"], m["data_hora"]
                ])
                
        cursor.close()
        conexao.close()
    except Exception as e:
        print(f"Erro ao atualizar CSVs locais: {e}")


@app.route("/")
def login():
    if "tipo" in session:
        return redirect("/estoque.html")
    return render_template("login.html")


@app.route("/verificar_login", methods=["POST"])
def verificar_login():

    email = request.form["email"]
    senha = request.form["senha"]
    tipo = request.form["tipo"]

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM usuarios WHERE email = %s AND tipo = %s",
        (email, tipo)
    )

    usuario = cursor.fetchone()

    cursor.close()
    conexao.close()

    if usuario and bcrypt.checkpw(
        senha.encode("utf-8"),
        usuario["senha"].encode("utf-8")
    ):
        session["email"] = usuario["email"]
        session["tipo"] = usuario["tipo"]

        return redirect("/estoque.html")

    return redirect("/")


@app.route("/estoque.html")
def estoque():

    if "tipo" not in session:
        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT * FROM itens WHERE quantidade > 0")
    itens = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("estoque.html", itens=itens)


@app.route("/criar_conta")
def criar_conta():
    return render_template("criar_conta.html")


@app.route("/salvar_conta", methods=["POST"])
def salvar_conta():
    email = request.form["email"]
    senha = request.form["senha"]

    senha_criptografada = bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO usuarios (email, senha, tipo)
        VALUES (%s, %s, 'usuario')
        """,
        (email, senha_criptografada)
    )

    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/")


@app.route("/resetar_banco", methods=["POST"])
def resetar_banco():

    # Verifica se está logado
    if "email" not in session:
        return redirect("/")

    # Verifica se é administrador
    if session.get("tipo") != "admin":
        return "Acesso negado! Apenas administradores podem resetar o banco.", 403

    conexao = conectar()
    cursor = conexao.cursor()

    # Remove movimentações
    cursor.execute("DELETE FROM movimentacoes")

    # Remove itens
    cursor.execute("DELETE FROM itens")

    # Reinicia os IDs
    cursor.execute("ALTER TABLE movimentacoes AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE itens AUTO_INCREMENT = 1")

    conexao.commit()

    cursor.close()
    conexao.close()

    atualizar_csv_local()

    return redirect("/estoque.html")


@app.route("/retirados.html")
def retirados():

    if "tipo" not in session:
        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("""
        SELECT itens.nome,
               movimentacoes.quantidade,
               movimentacoes.responsavel,
               movimentacoes.data_hora
        FROM movimentacoes
        JOIN itens
            ON movimentacoes.item_id = itens.id
        WHERE movimentacoes.tipo = 'RETIRAR'
        ORDER BY movimentacoes.data_hora DESC
    """)

    retiradas = cursor.fetchall()

    cursor.execute("""
        SELECT itens.nome,
               movimentacoes.quantidade,
               movimentacoes.responsavel,
               movimentacoes.data_hora
        FROM movimentacoes
        JOIN itens
            ON movimentacoes.item_id = itens.id
        WHERE movimentacoes.tipo = 'ADICIONAR'
        ORDER BY movimentacoes.data_hora DESC
    """)

    adicionados = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
        "retirados.html",
        retiradas=retiradas,
        adicionados=adicionados
    )


@app.route("/adicionar.html")
def adicionar():

    if "tipo" not in session:
        return redirect("/")

    return render_template("adicionar.html")


@app.route("/retirar.html")
def retirar():

    if "tipo" not in session:
        return redirect("/")

    return render_template("retirar.html")


@app.route("/salvar_item", methods=["POST"])
def salvar_item():

    item = request.form["item"]
    qtd = int(request.form["qtd"])
    pessoa = request.form["pessoa"]
    hora = request.form["hora"]

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM itens WHERE nome = %s",
        (item,)
    )

    produto = cursor.fetchone()

    if produto:

        cursor.execute("""
            UPDATE itens
            SET quantidade = quantidade + %s,
                responsavel = %s,
                horario = %s
            WHERE id = %s
        """, (
            qtd,
            pessoa,
            hora,
            produto["id"]
        ))
        item_id = produto["id"]

    else:

        cursor.execute("""
            INSERT INTO itens
            (nome, quantidade, responsavel, horario)
            VALUES (%s, %s, %s, %s)
        """, (
            item,
            qtd,
            pessoa,
            hora
        ))
        item_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO movimentacoes
        (item_id, tipo, quantidade, responsavel)
        VALUES (%s, 'ADICIONAR', %s, %s)
    """, (
        item_id,
        qtd,
        pessoa
    ))

    conexao.commit()

    cursor.close()
    conexao.close()

    atualizar_csv_local()

    return redirect("/estoque.html")


@app.route("/retirar_item", methods=["POST"])
def retirar_item():

    item = request.form["item"]
    qtd = int(request.form["qtd"])
    pessoa = request.form["pessoa"]

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM itens WHERE nome = %s AND quantidade > 0",
        (item,)
    )

    produto = cursor.fetchone()

    if produto and produto["quantidade"] >= qtd:

        cursor.execute("""
            UPDATE itens
            SET quantidade = quantidade - %s
            WHERE id = %s
        """, (
            qtd,
            produto["id"]
        ))

        cursor.execute("""
            INSERT INTO movimentacoes
            (item_id, tipo, quantidade, responsavel)
            VALUES (%s, 'RETIRAR', %s, %s)
        """, (
            produto["id"],
            qtd,
            pessoa
        ))

        conexao.commit()

    cursor.close()
    conexao.close()

    atualizar_csv_local()

    return redirect("/estoque.html")


@app.route("/sair")
def sair():

    session.clear()

    return redirect("/")


@app.route("/exportar_estoque_csv")
def exportar_estoque_csv():
    if "tipo" not in session:
        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, quantidade, horario, responsavel FROM itens")
    itens = cursor.fetchall()
    cursor.close()
    conexao.close()

    si = io.StringIO()
    cw = csv.writer(si)
    # Escreve o BOM para compatibilidade com Excel em português
    si.write('\ufeff')
    cw.writerow(["ID", "Nome", "Quantidade", "Horário", "Responsável"])
    for item in itens:
        cw.writerow([
            item['id'],
            item['nome'],
            item['quantidade'],
            item['horario'],
            item['responsavel']
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=estoque.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


@app.route("/exportar_movimentacoes_csv")
def exportar_movimentacoes_csv():
    if "tipo" not in session:
        return redirect("/")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("""
        SELECT movimentacoes.id, itens.nome AS item_nome, movimentacoes.tipo, 
               movimentacoes.quantidade, movimentacoes.responsavel, movimentacoes.data_hora
        FROM movimentacoes
        JOIN itens ON movimentacoes.item_id = itens.id
        ORDER BY movimentacoes.data_hora DESC
    """)
    movs = cursor.fetchall()
    cursor.close()
    conexao.close()

    si = io.StringIO()
    cw = csv.writer(si)
    # Escreve o BOM para compatibilidade com Excel em português
    si.write('\ufeff')
    cw.writerow(["ID", "Item", "Tipo", "Quantidade", "Responsável", "Data/Hora"])
    for m in movs:
        cw.writerow([
            m['id'],
            m['item_nome'],
            m['tipo'],
            m['quantidade'],
            m['responsavel'],
            m['data_hora']
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=historico_movimentacoes.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)