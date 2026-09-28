from flask import Flask, render_template, request, redirect, session, make_response, send_from_directory, jsonify
import mysql.connector
import bcrypt
import csv
import io
import datetime
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
    if session.get("tipo") != "admin":
        return redirect("/estoque.html")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT id, email, tipo FROM usuarios ORDER BY id ASC")
    usuarios = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template("criar_conta.html", usuarios=usuarios)


@app.route("/salvar_conta", methods=["POST"])
def salvar_conta():
    email = request.form["email"]
    senha = request.form["senha"]
    tipo = request.form.get("tipo", "usuario")

    # Se tentar criar conta de admin mas a sessão não for admin, força para usuario
    if tipo == "admin" and session.get("tipo") != "admin":
        tipo = "usuario"

    senha_criptografada = bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO usuarios (email, senha, tipo)
        VALUES (%s, %s, %s)
        """,
        (email, senha_criptografada, tipo)
    )

    conexao.commit()
    cursor.close()
    conexao.close()

    if session.get("tipo") == "admin":
        return redirect("/criar_conta")
    return redirect("/")


@app.route("/salvar_conta_admin", methods=["POST"])
def salvar_conta_admin():
    # Verifica se quem está logado é admin
    if session.get("tipo") != "admin":
        return "Acesso negado! Apenas administradores podem criar outros administradores.", 403

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
        VALUES (%s, %s, 'admin')
        """,
        (email, senha_criptografada)
    )

    conexao.commit()
    cursor.close()
    conexao.close()

    return redirect("/criar_conta")


@app.route("/excluir_usuario/<int:id>", methods=["POST", "GET"])
def excluir_usuario(id):
    # 1. Verifica se está logado
    if "email" not in session:
        return redirect("/")

    # 2. Verifica se é administrador
    if session.get("tipo") != "admin":
        return "Acesso negado! Apenas administradores podem excluir contas.", 403

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/criar_conta")


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

    # Zera as quantidades do estoque sem apagar o histórico de movimentações
    cursor.execute("UPDATE itens SET quantidade = 0")

    conexao.commit()

    cursor.close()
    conexao.close()

    atualizar_csv_local()

    return redirect("/estoque.html")

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


@app.route("/importar_estoque_csv", methods=["POST"])
def importar_estoque_csv():
    if "tipo" not in session:
        return redirect("/")

    file = request.files.get("arquivo_csv")
    if not file or not file.filename.endswith(".csv"):
        return redirect("/estoque.html")

    try:
        raw_bytes = file.stream.read()
        if not raw_bytes.strip():
            return redirect("/estoque.html")

        # Tenta decodificar primeiro com UTF-8-SIG, depois com Latin-1 (padrão Excel Windows)
        try:
            conteudo = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                conteudo = raw_bytes.decode("latin-1")
            except Exception:
                conteudo = raw_bytes.decode("utf-8", errors="replace")

        linhas_texto = [l for l in conteudo.splitlines() if l.strip()]
        if not linhas_texto:
            return redirect("/estoque.html")

        # Detecta o delimitador (, ou ; ou tabulação \t)
        primeira = linhas_texto[0]
        if "\t" in primeira:
            delimitador = "\t"
        elif ";" in primeira:
            delimitador = ";"
        else:
            delimitador = ","

        stream = io.StringIO(conteudo, newline=None)
        csv_reader = csv.reader(stream, delimiter=delimitador)
        
        primeira_linha = next(csv_reader, None)
        if not primeira_linha:
            return redirect("/estoque.html")

        # Verifica se a primeira linha é cabeçalho ou dado real
        header_test = "".join(primeira_linha).lower()
        if not ("id" in header_test or "nome" in header_test or "item" in header_test or "quantidade" in header_test):
            stream.seek(0)
            csv_reader = csv.reader(stream, delimiter=delimitador)

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        import re
        itens_processados = 0

        for num_linha, linha in enumerate(csv_reader, start=1):
            if not linha:
                continue

            try:
                linha_limpa = [c.strip() for c in linha if c is not None]
                if not linha_limpa or all(len(c) == 0 for c in linha_limpa):
                    continue

                # Inteligência de colunas:
                # Se a 1ª coluna for um número (ID), assume formato [ID, Nome, Qtd, Horario, Responsavel]
                if linha_limpa[0].isdigit() and len(linha_limpa) >= 3:
                    nome = linha_limpa[1]
                    qtd_str = linha_limpa[2]
                    horario = linha_limpa[3] if len(linha_limpa) >= 4 and linha_limpa[3] else None
                    responsavel = linha_limpa[4] if len(linha_limpa) >= 5 and linha_limpa[4] else "Sistema"
                # Se a 1ª coluna for texto (Nome), assume formato [Nome, Qtd, Responsavel...]
                else:
                    nome = linha_limpa[0]
                    qtd_str = linha_limpa[1] if len(linha_limpa) >= 2 else "1"
                    responsavel = linha_limpa[2] if len(linha_limpa) >= 3 and linha_limpa[2] else "Sistema"
                    horario = linha_limpa[3] if len(linha_limpa) >= 4 and linha_limpa[3] else None

                if not nome or nome.lower() in ["id", "nome", "item", "quantidade"]:
                    continue

                # Extrai apenas os números da quantidade (ex: "10un" vira 10)
                numeros = re.findall(r'\d+', qtd_str)
                qtd = int(numeros[0]) if numeros else 1

                cursor.execute("SELECT id FROM itens WHERE nome = %s", (nome,))
                item_existente = cursor.fetchone()

                if item_existente:
                    cursor.execute("""
                        UPDATE itens 
                        SET quantidade = quantidade + %s, responsavel = %s
                        WHERE id = %s
                    """, (qtd, responsavel, item_existente["id"]))
                else:
                    cursor.execute("""
                        INSERT INTO itens (nome, quantidade, responsavel, horario) 
                        VALUES (%s, %s, %s, %s)
                    """, (nome, qtd, responsavel, horario))

                itens_processados += 1

            except Exception as err_linha:
                print(f"Aviso linha {num_linha}: {err_linha}")
                continue

        conexao.commit()
        cursor.close()
        conexao.close()

        print(f"Sucesso! {itens_processados} itens importados do CSV.")
        atualizar_csv_local()

    except Exception as e:
        print(f"Erro geral ao importar CSV: {str(e).encode('utf-8', errors='ignore').decode('utf-8')}")



    return redirect("/estoque.html")


@app.route("/historico.html")
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
        "historico.html",
        retiradas=retiradas,
        adicionados=adicionados
    )

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

def atualizar_csv_local():
    try:
        diretorio = os.path.dirname(os.path.abspath(__file__))
        
        # CORREÇÃO AQUI: Mudado de "exportações" para "exportacoes"
        pasta_exportacao = os.path.join(diretorio, "exportacoes")
        
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
        print(f"Erro ao atualizar CSVs locais: {repr(e)}") # Adicionado repr para evitar travar o terminal se houver outro erro

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


@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory(app.static_folder, "sw.js"))
    response.headers["Content-Type"] = "application/javascript"
    return response


#API'S EXTERNAS
@app.route("/api/estoque", methods=["GET"])
def listar_estoque():
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM itens")
        itens = cursor.fetchall()
        cursor.close()
        conexao.close()

        # Converte timedelta, datetime, time e data para string
        for item in itens:
            for chave, valor in item.items():
                if isinstance(valor, (datetime.timedelta, datetime.date, datetime.time, datetime.datetime)):
                    item[chave] = str(valor)  # <--- Correção aqui (item no singular)
                    
        return jsonify(itens), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    

@app.route("/api/estoque/<int:id>", methods=["GET"])
def api_buscar_item(id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nome, quantidade, horario, responsavel
            FROM itens
            WHERE id = %s
        """, (id,))

        item = cursor.fetchone()

        cursor.close()
        conexao.close()

        if not item:
            return jsonify({
                "erro": "Item não encontrado"
            }), 404

        for chave, valor in item.items():
            if isinstance(valor, (
                datetime.timedelta,
                datetime.date,
                datetime.time,
                datetime.datetime
            )):
                item[chave] = str(valor)

        return jsonify(item), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


@app.route("/api/estoque", methods=["POST"])
def api_adicionar_item():
    try:
        dados = request.get_json()

        nome = dados.get("nome")
        quantidade = dados.get("quantidade")
        responsavel = dados.get("responsavel", "API")
        horario = dados.get("horario")

        if not nome or quantidade is None:
            return jsonify({
                "erro": "Nome e quantidade são obrigatórios"
            }), 400

        quantidade = int(quantidade)

        if quantidade <= 0:
            return jsonify({
                "erro": "A quantidade deve ser maior que zero"
            }), 400

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        # Verifica se o item já existe
        cursor.execute(
            "SELECT * FROM itens WHERE nome = %s",
            (nome,)
        )

        item = cursor.fetchone()

        if item:

            cursor.execute("""
                UPDATE itens
                SET quantidade = quantidade + %s,
                    responsavel = %s,
                    horario = %s
                WHERE id = %s
            """, (
                quantidade,
                responsavel,
                horario,
                item["id"]
            ))

            item_id = item["id"]

        else:

            cursor.execute("""
                INSERT INTO itens
                (nome, quantidade, responsavel, horario)
                VALUES (%s, %s, %s, %s)
            """, (
                nome,
                quantidade,
                responsavel,
                horario
            ))

            item_id = cursor.lastrowid

        # Registra movimentação
        cursor.execute("""
            INSERT INTO movimentacoes
            (item_id, tipo, quantidade, responsavel)
            VALUES (%s, 'ADICIONAR', %s, %s)
        """, (
            item_id,
            quantidade,
            responsavel
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        atualizar_csv_local()

        return jsonify({
            "mensagem": "Item adicionado com sucesso",
            "id": item_id
        }), 201

    except ValueError:
        return jsonify({
            "erro": "Quantidade inválida"
        }), 400

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


@app.route("/api/estoque/<int:id>", methods=["PUT"])
def api_atualizar_item(id):
    try:
        dados = request.get_json()

        nome = dados.get("nome")
        quantidade = dados.get("quantidade")
        responsavel = dados.get("responsavel")
        horario = dados.get("horario")

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM itens WHERE id = %s",
            (id,)
        )

        item = cursor.fetchone()

        if not item:
            cursor.close()
            conexao.close()

            return jsonify({
                "erro": "Item não encontrado"
            }), 404

        # Mantém os valores antigos quando não forem enviados
        nome = nome if nome is not None else item["nome"]
        quantidade = quantidade if quantidade is not None else item["quantidade"]
        responsavel = responsavel if responsavel is not None else item["responsavel"]
        horario = horario if horario is not None else item["horario"]

        cursor.execute("""
            UPDATE itens
            SET nome = %s,
                quantidade = %s,
                responsavel = %s,
                horario = %s
            WHERE id = %s
        """, (
            nome,
            quantidade,
            responsavel,
            horario,
            id
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        atualizar_csv_local()

        return jsonify({
            "mensagem": "Item atualizado com sucesso",
            "id": id
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


@app.route("/api/estoque/<int:id>", methods=["DELETE"])
def api_excluir_item(id):
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM itens WHERE id = %s",
            (id,)
        )

        item = cursor.fetchone()

        if not item:
            cursor.close()
            conexao.close()

            return jsonify({
                "erro": "Item não encontrado"
            }), 404

        # Primeiro remove as movimentações
        cursor.execute(
            "DELETE FROM movimentacoes WHERE item_id = %s",
            (id,)
        )

        # Depois remove o item
        cursor.execute(
            "DELETE FROM itens WHERE id = %s",
            (id,)
        )

        conexao.commit()

        cursor.close()
        conexao.close()

        atualizar_csv_local()

        return jsonify({
            "mensagem": "Item excluído com sucesso"
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


# API - RETIRADA
@app.route("/api/estoque/<int:id>/retirar", methods=["POST"])
def api_retirar_item(id):
    try:
        dados = request.get_json()

        quantidade = dados.get("quantidade")
        responsavel = dados.get("responsavel", "API")

        if quantidade is None:
            return jsonify({
                "erro": "Quantidade é obrigatória"
            }), 400

        quantidade = int(quantidade)

        if quantidade <= 0:
            return jsonify({
                "erro": "A quantidade deve ser maior que zero"
            }), 400

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM itens WHERE id = %s",
            (id,)
        )

        item = cursor.fetchone()

        if not item:
            cursor.close()
            conexao.close()

            return jsonify({
                "erro": "Item não encontrado"
            }), 404

        if item["quantidade"] < quantidade:
            cursor.close()
            conexao.close()

            return jsonify({
                "erro": "Estoque insuficiente",
                "estoque_atual": item["quantidade"]
            }), 400

        cursor.execute("""
            UPDATE itens
            SET quantidade = quantidade - %s
            WHERE id = %s
        """, (
            quantidade,
            id
        ))

        cursor.execute("""
            INSERT INTO movimentacoes
            (item_id, tipo, quantidade, responsavel)
            VALUES (%s, 'RETIRAR', %s, %s)
        """, (
            id,
            quantidade,
            responsavel
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        atualizar_csv_local()

        return jsonify({
            "mensagem": "Retirada realizada com sucesso",
            "item_id": id,
            "quantidade_retirada": quantidade
        }), 200

    except ValueError:
        return jsonify({
            "erro": "Quantidade inválida"
        }), 400

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


# API - MOVIMENTAÇÕES
@app.route("/api/movimentacoes", methods=["GET"])
def api_movimentacoes():
    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                movimentacoes.id,
                movimentacoes.item_id,
                itens.nome AS item,
                movimentacoes.tipo,
                movimentacoes.quantidade,
                movimentacoes.responsavel,
                movimentacoes.data_hora
            FROM movimentacoes
            JOIN itens
                ON movimentacoes.item_id = itens.id
            ORDER BY movimentacoes.data_hora DESC
        """)

        movimentacoes = cursor.fetchall()

        cursor.close()
        conexao.close()

        for movimentacao in movimentacoes:
            for chave, valor in movimentacao.items():
                if isinstance(valor, (
                    datetime.timedelta,
                    datetime.date,
                    datetime.time,
                    datetime.datetime
                )):
                    movimentacao[chave] = str(valor)

        return jsonify(movimentacoes), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

@app.route("/api/login", methods=["POST"])
def api_login():
        try:
            dados = request.get_json()
            if not dados:
                return jsonify({"erro": "Corpo da requisição deve ser JSON"}), 400

            email = dados.get("email")
            senha = dados.get("senha")
            tipo = dados.get("tipo", "usuario")

            if not email or not senha:
                return jsonify({"erro": "Email e senha são obrigatórios"}), 400

            conexao = conectar()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute(
                "SELECT id, email, senha, tipo FROM usuarios WHERE email = %s AND tipo = %s",
                (email, tipo)
            )
            usuario = cursor.fetchone()

            cursor.close()
            conexao.close()

            # Validação da senha com bcrypt
            if usuario and bcrypt.checkpw(senha.encode("utf-8"), usuario["senha"].encode("utf-8")):
                return jsonify({
                    "mensagem": "Login realizado com sucesso",
                    "usuario": {
                        "id": usuario["id"],
                        "email": usuario["email"],
                        "tipo": usuario["tipo"]
                    }
                }), 200

            return jsonify({"erro": "Email, senha ou tipo de usuário incorretos"}), 401

        except Exception as e:
            return jsonify({"erro": str(e)}), 500

# API - CRIAR CONTA
@app.route("/api/usuarios", methods=["POST"])
def api_criar_conta():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "JSON não enviado"
            }), 400

        email = dados.get("email")
        senha = dados.get("senha")

        if not email or not senha:
            return jsonify({
                "erro": "Email e senha são obrigatórios"
            }), 400

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM usuarios WHERE email = %s",
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario:
            cursor.close()
            conexao.close()

            return jsonify({
                "erro": "Este email já está cadastrado"
            }), 409

        senha_criptografada = bcrypt.hashpw(
            senha.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO usuarios (email, senha, tipo)
            VALUES (%s, %s, 'usuario')
            """,
            (email, senha_criptografada)
        )

        conexao.commit()

        novo_id = cursor.lastrowid

        cursor.close()
        conexao.close()

        return jsonify({
            "mensagem": "Conta criada com sucesso",
            "usuario": {
                "id": novo_id,
                "email": email,
                "tipo": "usuario"
            }
        }), 201

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


# API - CRIAR CONTA DE ADMINISTRADOR
@app.route("/api/admin/criar_conta", methods=["POST"])
def api_criar_admin():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "JSON não enviado"
            }), 400

        email = dados.get("email")
        senha = dados.get("senha")

        if not email or not senha:
            return jsonify({
                "erro": "Email e senha são obrigatórios"
            }), 400

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM usuarios WHERE email = %s",
            (email,)
        )

        usuario = cursor.fetchone()

        if usuario:
            cursor.close()
            conexao.close()
            return jsonify({
                "erro": "Este email já está cadastrado"
            }), 409

        senha_criptografada = bcrypt.hashpw(
            senha.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO usuarios (email, senha, tipo)
            VALUES (%s, %s, 'admin')
            """,
            (email, senha_criptografada)
        )

        conexao.commit()

        novo_id = cursor.lastrowid

        cursor.close()
        conexao.close()

        return jsonify({
            "mensagem": "Conta de administrador criada com sucesso",
            "usuario": {
                "id": novo_id,
                "email": email,
                "tipo": "admin"
            }
        }), 201

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


# API - EXCLUIR CONTA (Apenas Administradores)
@app.route("/api/usuarios/<int:id>", methods=["DELETE"])
def api_excluir_usuario(id):
    try:
        dados = request.get_json(silent=True) or {}

        # 1. Verifica se o usuário autenticado na sessão web é admin
        is_admin = session.get("tipo") == "admin"

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        # 2. Se não estiver logado por sessão, permite autenticar via credenciais de admin no JSON
        if not is_admin:
            admin_email = dados.get("admin_email")
            admin_senha = dados.get("admin_senha")

            if admin_email and admin_senha:
                cursor.execute(
                    "SELECT senha, tipo FROM usuarios WHERE email = %s AND tipo = 'admin'",
                    (admin_email,)
                )
                admin_user = cursor.fetchone()

                if admin_user and bcrypt.checkpw(
                    admin_senha.encode("utf-8"),
                    admin_user["senha"].encode("utf-8")
                ):
                    is_admin = True

        if not is_admin:
            cursor.close()
            conexao.close()
            return jsonify({
                "erro": "Acesso negado! Apenas administradores podem excluir contas."
            }), 403

        # Verifica se o usuário a ser excluído existe
        cursor.execute(
            "SELECT id, email, tipo FROM usuarios WHERE id = %s",
            (id,)
        )
        usuario_alvo = cursor.fetchone()

        if not usuario_alvo:
            cursor.close()
            conexao.close()
            return jsonify({
                "erro": "Usuário não encontrado"
            }), 404

        # Remove o usuário do banco
        cursor.execute(
            "DELETE FROM usuarios WHERE id = %s",
            (id,)
        )
        conexao.commit()

        cursor.close()
        conexao.close()

        return jsonify({
            "mensagem": f"Usuário '{usuario_alvo['email']}' excluído com sucesso",
            "id_excluido": id
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

# API - RESETAR BANCO DE DADOS
@app.route("/api/admin/resetar_banco", methods=["POST"])
def api_resetar_banco():
    try:
        conexao = conectar()
        cursor = conexao.cursor()

        # Zera o estoque
        cursor.execute("UPDATE itens SET quantidade = 0")

        conexao.commit()

        cursor.close()
        conexao.close()

        # Atualiza os arquivos CSV
        atualizar_csv_local()

        return jsonify({
            "mensagem": "Banco de dados resetado com sucesso"
        }), 200

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
