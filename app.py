from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "segredo_super_importante"

# CONFIG MYSQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # coloque sua senha
app.config['MYSQL_DB'] = 'tcc_1'

mysql = MySQL(app)

# =========================
# LOGIN PAGE
# =========================
@app.route('/')
def login_page():
    return render_template("login.html")

# =========================
# API LOGIN (POST)
# =========================
@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()

    usuario = dados.get("usuario")
    senha = dados.get("senha")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM monotype WHERE nome = %s", (usuario,))
    user = cursor.fetchone()
    cursor.close()

    if user and check_password_hash(user[4], senha):
        session["usuario"] = usuario
        return jsonify({"mensagem": "Login realizado com sucesso"}), 200
    else:
        return jsonify({"mensagem": "Usuário ou senha inválidos"}), 401

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login_page"))

# =========================
# PROTEÇÃO DE ROTAS
# =========================
def usuario_logado():
    return "usuario" in session

# =========================
# PÁGINAS PROTEGIDAS
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
# CRIAR USUÁRIO (TESTE)
# =========================
@app.route('/criar_usuario')
def criar_usuario():
    cursor = mysql.connection.cursor()

    senha_hash = generate_password_hash("123")

    cursor.execute(
        "INSERT INTO monotype (nome, email, idade, senha) VALUES (%s, %s, %s, %s)",
        ("admin", "admin@gmail.com", 20, senha_hash)
    )

    mysql.connection.commit()
    cursor.close()

    return "Usuário criado!"

# =========================
# RODAR SERVIDOR
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)