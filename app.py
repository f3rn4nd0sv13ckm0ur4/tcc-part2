from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================
app.secret_key = os.urandom(24)

# =========================
# CONFIG MYSQL
# =========================
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tcc_1"
}

# =========================
# FUNÇÃO CONEXÃO MYSQL
# =========================
def conectar_db():

    try:

        conexao = mysql.connector.connect(**MYSQL_CONFIG)

        return conexao

    except Error as erro:

        print(f"Erro ao conectar no MySQL: {erro}")

        return None

# =========================
# VERIFICA LOGIN
# =========================
def usuario_logado():

    return "usuario" in session

# =========================
# LOGIN PAGE
# =========================
@app.route('/')
def login_page():

    return render_template("login.html")

# =========================
# LOGIN API
# =========================
@app.route('/login', methods=['POST'])
def login():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({
                "mensagem": "JSON inválido"
            }), 400

        usuario = dados.get("usuario")
        senha = dados.get("senha")

        if not usuario or not senha:

            return jsonify({
                "mensagem": "Preencha usuário e senha"
            }), 400

        conexao = conectar_db()

        if not conexao:

            return jsonify({
                "mensagem": "Erro ao conectar no banco"
            }), 500

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM administrador WHERE usuario = %s",
            (usuario,)
        )

        user = cursor.fetchone()

        cursor.close()
        conexao.close()

        # Usuário não encontrado
        if not user:

            return jsonify({
                "mensagem": "Usuário não encontrado"
            }), 401

        # Verifica senha
        if check_password_hash(user["senha"], senha):

            session["usuario"] = user["usuario"]
            session["id"] = user["id"]

            return jsonify({
                "mensagem": "Login realizado com sucesso"
            }), 200

        return jsonify({
            "mensagem": "Senha incorreta"
        }), 401

    except Exception as erro:

        return jsonify({
            "mensagem": "Erro interno",
            "erro": str(erro)
        }), 500

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for("login_page"))

# =========================
# ROTAS PROTEGIDAS
# =========================
@app.route('/estoque.html')
def estoque():

    if not usuario_logado():

        return redirect(url_for("login_page"))

    return render_template("estoque.html")

@app.route('/retirados.html')
def retirados():

    if not usuario_logado():

        return redirect(url_for("login_page"))

    return render_template("retirados.html")

@app.route('/adicionar.html')
def adicionar():

    if not usuario_logado():

        return redirect(url_for("login_page"))

    return render_template("adicionar.html")

@app.route('/retirar.html')
def retirar():

    if not usuario_logado():

        return redirect(url_for("login_page"))

    return render_template("retirar.html")

@app.route('/devolver.html')
def devolver():

    if not usuario_logado():

        return redirect(url_for("login_page"))

    return render_template("devolver.html")

# =========================
# CRIAR ADMIN
# =========================
@app.route('/criar_admin')
def criar_admin():

    try:

        conexao = conectar_db()

        if not conexao:

            return "Erro ao conectar no banco"

        cursor = conexao.cursor(dictionary=True)

        # Verifica se admin existe
        cursor.execute(
            "SELECT * FROM administrador WHERE usuario = %s",
            ("admin",)
        )

        existe = cursor.fetchone()

        if existe:

            cursor.close()
            conexao.close()

            return "Administrador já existe"

        senha_hash = generate_password_hash("123")

        cursor.execute("""
            INSERT INTO administrador (usuario, senha)
            VALUES (%s, %s)
        """, (
            "admin",
            senha_hash
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        return "Administrador criado com sucesso"

    except Exception as erro:

        return f"Erro: {str(erro)}"

# =========================
# INICIAR SERVIDOR
# =========================
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )