from flask import Flask, render_template, request, redirect, session
import mysql.connector
import bcrypt

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

    cursor.close()
    conexao.close()

    return render_template(
        "retirados.html",
        retiradas=retiradas
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

    conexao.commit()

    cursor.close()
    conexao.close()

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

    return redirect("/estoque.html")


@app.route("/sair")
def sair():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)