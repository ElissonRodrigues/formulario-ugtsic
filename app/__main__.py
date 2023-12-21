from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
    make_response,
    session,
)

from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime
from ferramentas.smtp_server import enviar_email
from .db_manager import (
    connect_db,
    listar_candidatos,
    validar_senha,
    cadastrar_candidato,
    cadastrar_novo_usuário,
    obter_tipo_de_usuario,
    buscar_tentativas_de_login,
    resetar_tentativas_de_login,
    estatisticas,
)
from ferramentas.login_tools import (
    registrar_primeira_tentativa,
    bloquear_ip_se_necessario,
    atualizar_tentativa_login_usuario,
)

from itsdangerous import URLSafeTimedSerializer, BadTimeSignature, SignatureExpired
from pytz import timezone
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    decode_token,
    create_access_token,
    set_access_cookies,
    get_jwt,
)
from jwt.exceptions import ExpiredSignatureError
from werkzeug.exceptions import Forbidden, NotFound
from datetime import timedelta
from typing import Any, Callable
from flask_wtf.csrf import CSRFProtect
from os import getenv
from logging.handlers import RotatingFileHandler
from flask import g
from time import time
from secrets import token_hex
import os
import logging
import pytz


blacklisted_tokens = []
app = Flask(__name__)  # Inicializar o Flask

# Configurar o log de acesso
handler = RotatingFileHandler(
    "./logs/access.log", maxBytes=30 * 1024 * 1024, backupCount=50
)
handler.setLevel(logging.INFO)  # Define o nível de log para INFO

formatter = logging.Formatter(
    "[ %(asctime)s ] %(levelname)s in %(module)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logging.Formatter.converter = lambda *args: datetime.now(tz=pytz.timezone("America/Sao_Paulo")).timetuple()  # type: ignore

handler.setFormatter(formatter)
app.logger.addHandler(handler)  # Adiciona o manipulador ao logger do Flask
app.logger.propagate = (
    False  # Impede a propagação dos logs para manipuladores de nível superior
)

csrf = CSRFProtect(app)  # Inicializar o CSRFProtect

jwt = JWTManager(app)  # Inicializar o JWTManager
app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]  # Definir o local do token
app.config["JWT_COOKIE_CSRF_PROTECT"] = True  # Proteger o cookie contra CSRF
app.config["JWT_CSRF_IN_COOKIES"] = True  # Definir o CSRF como cookie
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    minutes=30
)  # Definir o tempo de expiração do token
app.config["JWT_COOKIE_MAX_AGE"] = timedelta(
    minutes=30
)  # Definir o tempo de expiração do cookie
app.config["JWT_CSRF_METHODS"] = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
]  # Definir os métodos que o CSRF irá proteger


app.config[
    "JWT_ACCESS_COOKIE_NAME"
] = "access_token"  # Definir o nome do cookie do token

app.config["SECRET_KEY"] = getenv(
    "FLASK_SECRET_KEY", token_hex(16)
)  # Definir a chave secreta

serializer = URLSafeTimedSerializer(
    app.config["SECRET_KEY"]
)  # Inicializar o serializer com a chave secreta


def test_admin():
    data = {
        "nome": "admin",
        "email": "test@test.com",
        "senha": "admin",
        "ip_de_cadastro": "192.168.30.1",
        "tipo_de_usuario": "admin",
        "data_criacao": datetime.now(timezone("America/Sao_Paulo")),
    }  # Dicionário com os dados do usuário "admin

    cadastrar_novo_usuário(connect_db(), data)  # Cadastrar o usuário admin


# test_admin()


@app.before_request
def start_timer():
    # Armazena o tempo de início da solicitação no objeto g do Flask
    g.start = time()


@app.after_request
def log_response_info(response):  # type: ignore
    """
    Registra informações detalhadas sobre a resposta HTTP.

    Args:
        response (flask.Response): A resposta HTTP que será registrada.

    Returns:
        flask.Response: A mesma resposta HTTP que foi passada como argumento.
    """
    try:
        # Calcula o tempo de resposta
        try:
            response_time = time() - g.start
        except AttributeError:
            response_time = 0

        app.logger.info(
            "Detalhes do Registro de Acesso:\n"
            "URL Acessada: %s\n"
            "Endereço IP do Cliente: %s\n"
            "Método HTTP Utilizado: %s\n"
            "Agente do Usuário: %s\n"
            "Código de Status da Resposta: %s\n"
            "Tempo de Resposta: %s segundos\n",
            request.path,
            request.remote_addr,
            request.method,
            request.user_agent,
            response.status_code,
            response_time,
        )

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)

    return response


def jwt_csrf_check(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorador para verificar o token JWT e CSRF.

    Este decorador verifica se o token JWT e CSRF são válidos. Se os tokens não forem válidos,
    ele redirecionará o usuário para a página de login.

    Args:
        func (function): A função que será decorada.

    Returns:
        function: A função decorada que inclui a verificação do token JWT e CSRF.
    """

    @wraps(func)
    def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]):
        access_token = request.cookies.get("access_token")
        csrf_token = request.cookies.get("csrf_access_token")

        if access_token and csrf_token:
            try:
                # Decodifica o token JWT
                decoded_token = decode_token(access_token.encode())

                if csrf_token != decoded_token["csrf"]:
                    json = jsonify({"error": "Token CSRF inválido"})
                    return json, 403
            except ExpiredSignatureError:
                flash("Sua sessão expirou! Faça login novamente.", "error")
                return redirect(url_for("login"))
            except Exception as e:
                flash(f"Ocorreu um erro: {e}", "error")
                logging.error(e, exc_info=True)
                return redirect(url_for("login"))
        else:
            abort(403)

        return func(*args, **kwargs, decoded_token=decoded_token)

    return wrapper


@jwt.expired_token_loader
def expired_token_callback(jwt_header: dict[Any], jwt_payload: dict[Any]):
    """
    Callback para lidar com tokens JWT expirados.

    Esta função é chamada automaticamente quando um token JWT expirado é acessado. Ela redireciona o usuário
    para a página de login.

    Args:
        jwt_header (dict): O cabeçalho do token JWT.
        jwt_payload (dict): O payload do token JWT.

    Returns:
        Response: Uma resposta Flask que redireciona o usuário para a página de login.
    """
    return redirect(url_for("login"))  # Redirecionar para a página de login


## API ##
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(_, jwt_payload: dict[Any]):
    jti = jwt_payload["jti"]

    return jti in blacklisted_tokens


@app.route("/api/logout", methods=["DELETE"])
@csrf.exempt
@jwt_required()
def logout():
    """
    Função para fazer logout.

    Esta função é chamada quando a rota '/logout' é acessada. Ela redireciona o usuário para a página de login e
    remove o cookie de acesso.

    Returns:
        Response: Uma resposta Flask que redireciona o usuário para a página de login.
    """
    try:
        current_token = get_jwt()  # Obtém o token JWT atual
        jti = current_token["jti"]  # Obtém o JTI do token
        blacklisted_tokens.append(jti)  # Adiciona o JTI à lista negra

        return jsonify({"msg": "Deslogado com sucesso"}), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)
        return jsonify({"error": "Erro ao fazer logout"}), 500


@app.route("/api/curriculos", methods=["GET"])
@jwt_required()  # Proteger a rota com JWT
def get_curriculos():
    """Retorna uma lista paginada de currículos de candidatos.

    A função aceita os seguintes parâmetros via query string:
    - offset: O número inicial de registros a serem pulados. O padrão é 0.
    - limit: O número máximo de registros a serem retornados. O padrão é 10.

    A função chama a função 'listar_candidatos' que se conecta ao banco de dados e recupera os dados dos candidatos.

    Returns:
        JSON: Um objeto JSON que contém uma lista de currículos de candidatos.
              Retorna um objeto JSON com uma mensagem de erro em caso de exceção.

    HTTP Status Code:
        200: Se os dados foram obtidos com sucesso, mesmo que a lista esteja vazia.
        500: Se ocorrer uma exceção ao tentar listar os candidatos.
    """
    try:
        offset = request.args.get("offset", default=0, type=int)
        limit = request.args.get("limit", default=10, type=int)

        # Chama a função listar_candidatos e obtém os dados
        data = listar_candidatos(connect_db(), offset, limit)

        # Verifica se os dados foram obtidos corretamente
        if not data:
            return jsonify({"message": "Nenhum candidato encontrado"}), 200

        return jsonify(data), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)
        return jsonify({"error": "Erro ao listar candidatos"}), 500


# Definir rota para obter estatísticas
@app.route("/api/estatisticas", methods=["GET"])
@jwt_required()  # Proteger a rota com JWT
def get_estatisticas():
    """Retorna as estatísticas do sistema.

    Essa função é chamada quando a rota '/api/estatisticas' é acessada. Ela retorna as estatísticas do sistema.

    Returns:
        json: Retorna um JSON com as estatísticas do sistema.
            - 'total_candidatos': O número total de candidatos no banco de dados.
            - 'total_entrevistadores': O número total de entrevistadores no banco de dados.
            - 'total_administradores': O número total de administradores no banco de dados.
    """
    try:
        data = estatisticas(connect_db())

        return jsonify(data), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)
        return jsonify({"error": "Erro ao obter estatísticas"}), 500


## INTERFACE WEB ##
@app.route("/")
def index():
    """
    Renderiza a página inicial.

    Esta função é chamada quando a rota '/' é acessada. Ela renderiza a página inicial usando o template "index.html".

    Returns:
        str: O HTML renderizado da página inicial.
    """
    try:
        dados = estatisticas(connect_db())

        if dados["total_administradores"] == 0:
            response = make_response(redirect(url_for("cadastrar_administrador")))

            access_token = create_access_token(
                identity="test@test.com", expires_delta=timedelta(minutes=4)
            )

            # Define o cookie
            response.set_cookie(
                "access_token",
                value=access_token,
                path="/",
                httponly=True,  # O cookie só pode ser acessado pelo servidor
                secure=True,  # O cookie só pode ser acessado por HTTPS
                samesite="Strict",  # O cookie não pode ser enviado em requisições cross-site
            )
            # Define o CSRF
            set_access_cookies(response, access_token)

            return response

        return render_template("index.html")
    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)
        return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/submit", methods=["POST"])
def submit():
    """
    Manipulador de rota para receber os dados do formulário e enviar o e-mail.

    Esta função é chamada quando um formulário é submetido. Ela recebe os dados do formulário,
    envia um e-mail e, em seguida, redireciona o usuário para a página inicial.

    Returns:
        Response: Uma resposta Flask que redireciona o usuário para a página inicial.
    """
    try:
        # checar tentativas de login

        # Obter os valores dos campos do formulário
        nome = request.form["nome"]
        email_candidato = request.form["email_candidato"]
        telefone = int(request.form["telefone"])
        cargo = request.form["cargo"]
        escolaridade = request.form["escolaridade"]
        observacoes = request.form["observacoes"]

        # arquivo enviado pelo usuário
        arquivo_anexado = request.files["file"]

        if arquivo_anexado:
            filename = secure_filename(
                f"{datetime.now().strftime('%d-%m-%Y %H%M%S')}_{arquivo_anexado.filename}"
            )
            arquivo_anexado.save(os.path.join("./uploads", filename))
        else:
            flash("Nenhum arquivo enviado!")
            return redirect(url_for("index"))

        # Obter o endereço IP do usuário
        if "X-Forwarded-For" in request.headers:
            ip = request.headers.getlist("X-Forwarded-For")[0].rpartition(" ")[-1]
        else:
            ip = request.remote_addr

        # Obter a data e hora atual
        datahora = datetime.now(timezone("America/Sao_Paulo"))
        token = serializer.dumps(filename)

        arquivo_url = url_for("arquivo", nome_arquivo=filename, token=token)

        data = {
            "nome": nome,
            "email": email_candidato,
            "telefone": telefone,
            "cargo": cargo,
            "escolaridade": escolaridade,
            "observacoes": observacoes,
            "url_arquivo": arquivo_url,
            "ip": ip,
            "data_e_hora": datahora,
        }  # Dicionário com os dados do candidato

        cadastrar_candidato(connect_db(), data)  # Cadastrar os dados no banco de dados

        # Enviar o e-mail com os dados do candidato
        enviar_email(
            email_candidato,
            nome,
            telefone,
            cargo,
            escolaridade,
            observacoes,
            filename,
            ip,
            datahora.strftime("%d/%m/%Y %H:%M:%S"),
        )

        flash("Currículo enviado com sucesso!", "success")
        return redirect(url_for("index"))  # Redirecionar para a página inicial

    except Exception as e:
        flash(f"Ocorreu um erro: {e}", "error")
        logging.error(e, exc_info=True)
        return redirect(url_for("index"))


# Cadastrar usuário adminstrativos
@app.route("/cadastrar_usuario", methods=["POST"])
@jwt_csrf_check
def cadastrar_usuario(decoded_token):  # type: ignore
    try:
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        tipo_de_usuario = request.form["tipoUsuario"]

        data = {
            "nome": nome,
            "email": email,
            "senha": senha,
            "ip_de_cadastro": request.remote_addr,
            "tipo_de_usuario": tipo_de_usuario,
            "data_criacao": datetime.now(timezone("America/Sao_Paulo")),
        }  # Dicionário com os dados do usuário

        resp = cadastrar_novo_usuário(connect_db(), data)  # Cadastrar o usuário
        new_admin = request.form.get("new_admin", "False")

        if resp.get("error"):
            flash(resp["error"], "error")
            if new_admin == "False":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("cadastrar_administrador"))

        if new_admin == "True":
            return redirect(url_for("login"))
        else:
            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(url_for("admin"))

    except Exception as e:
        flash(f"Ocorreu um erro: {e}", "error")
        logging.error(e, exc_info=True)
        return redirect(url_for("cadastrar_administrador"))


@app.route("/login")
def login():
    """
    Renderiza a página de login.

    Esta função é chamada quando a rota '/login' é acessada. Ela renderiza a página de login usando o template "login.html".

    Returns:
        str: O HTML renderizado da página de login.
    """

    email = session.get("email", "")
    return render_template("login.html", email=email)


@app.route("/candidatos")
@jwt_csrf_check
def candidatos(decoded_token):  # type: ignore
    """
    Manipulador de rota para renderizar a página 'candidatos.html'.

    Esta função é chamada quando a rota '/candidatos' é acessada. Ela renderiza a página 'candidatos.html'.

    Returns:
        Response: Uma resposta Flask que inclui o conteúdo da página 'candidatos.html'.
    """
    return render_template("candidatos.html")


@app.route("/admin")
@jwt_csrf_check
def admin(decoded_token):  # type: ignore
    """
    Manipulador de rota para renderizar a página 'admin.html'.

    Esta função é chamada quando a rota '/admin' é acessada. Ela renderiza a página 'admin.html'.

    Returns:
        Response: Uma resposta Flask que inclui o conteúdo da página 'admin.html'.
    """

    if obter_tipo_de_usuario(connect_db(), decoded_token["sub"]) != "admin":
        return make_response(
            "<h1>Você não tem permissão para acessar essa página</h1>", 403
        )

    return render_template("administrador.html")


@app.route("/auth", methods=["POST"])
def auth():
    """Função para autenticar o usuário.

    essa função é chamada quando a rota '/auth' é acessada. Ela verifica se o usuário existe no banco de dados e se a senha está correta.
    Se o usuário existir e a senha estiver correta, ela cria um token de acesso e define o cookie. Se o usuário não existir ou a senha estiver incorreta,
    ela redireciona o usuário para a página de login.

    Se o usuário exceder o número máximo de tentativas de login, ela bloqueia o IP do usuário por um determinado período de tempo.

    Returns:
        _type_: _description_
    """
    try:
        db = connect_db()
        dados_tentativas = buscar_tentativas_de_login(db, request.remote_addr)
        max_tentativas = int(getenv("NUMERO_MAXIMO_TENTATIVAS", 3))
        agora = datetime.now(timezone("America/Sao_Paulo"))
        tempo_bloqueio = timedelta(seconds=int(getenv("BLOQUEIO_DE_LOGIN", 86400)))

        username = request.form.get("email").lower()
        password = request.form.get("senha").strip()

        # Verifica a senha com a função validar_senha
        if (
            not validar_senha(connect_db(), username, password)
            or dados_tentativas
            and dados_tentativas["numero_tentativas"] >= max_tentativas
        ):
            if not dados_tentativas or dados_tentativas["numero_tentativas"] == 0:
                registrar_primeira_tentativa(
                    db, request.remote_addr, agora, max_tentativas
                )
            elif dados_tentativas["numero_tentativas"] >= max_tentativas:
                bloquear_ip_se_necessario(
                    db, request.remote_addr, dados_tentativas, agora, tempo_bloqueio
                )
            else:
                atualizar_tentativa_login_usuario(
                    db, request.remote_addr, agora, dados_tentativas, max_tentativas
                )

            session["email"] = request.form["email"]

            return redirect(url_for("login"))

        if dados_tentativas:
            resetar_tentativas_de_login(db, request.remote_addr)

        # Cria o token de acesso
        access_token = create_access_token(
            identity=username, expires_delta=timedelta(minutes=30)
        )

        # Cria a resposta
        if obter_tipo_de_usuario(db, username) == "admin":
            response = make_response(redirect(url_for("admin")))
        else:
            response = make_response(redirect(url_for("candidatos")))

        # Define o cookie
        response.set_cookie(
            "access_token",
            value=access_token,
            path="/",
            httponly=True,  # O cookie só pode ser acessado pelo servidor
            secure=True,  # O cookie só pode ser acessado por HTTPS
            samesite="Strict",  # O cookie não pode ser enviado em requisições cross-site
        )
        # Define o CSRF
        set_access_cookies(response, access_token)

        return response

    except Exception as e:
        flash(f"Ocorreu um erro: {e}", "error")
        logging.error(e, exc_info=True)
        return redirect(url_for("login"))


@app.route("/cadastrar_administrador", methods=["GET"])
@csrf.exempt
def cadastrar_administrador():
    """Função para renderizar a página de cadastro de administradores.

    Returns:
        Response: Uma resposta Flask que inclui o conteúdo da página 'cadastrar_administrador.html'.
    """    
    try:
        dados = estatisticas(connect_db())

        if dados["total_administradores"] == 0:
            return render_template("cadastrar_administrador.html")
        else:
            return redirect(url_for("login"))
        
    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}", exc_info=True)
        return redirect(url_for("login"))


@app.route("/arquivo/<nome_arquivo>")
def arquivo(nome_arquivo: str):
    """
    Manipulador de rota para servir um arquivo do diretório de uploads.

    Esta função é chamada quando a rota '/arquivo/<nome_arquivo>' é acessada. Ela verifica se um token válido
    foi fornecido e se o nome do arquivo no token corresponde ao nome do arquivo solicitado. Se o token for válido
    e os nomes dos arquivos corresponderem, ela serve o arquivo do diretório de uploads. Se o token não for fornecido,
    estiver expirado ou inválido, ou se os nomes dos arquivos não corresponderem, ela retorna um erro 403.

    Args:
        nome_arquivo (str): O nome do arquivo que deve ser servido.

    Returns:
        Response: Uma resposta Flask que inclui o arquivo solicitado, ou um erro 403 se o token for inválido
        ou os nomes dos arquivos não corresponderem.
    """
    try:
        token = request.args.get("token")
        if not token:
            abort(404)  # Se não houver token, retorne um erro 403

        try:
            arquivo_nome = serializer.loads(
                token, max_age=2592000
            )  # O token expira após 1 mês
        except (SignatureExpired, BadTimeSignature):
            abort(404)  # Se o token estiver expirado ou inválido, retorne um erro 403

        if arquivo_nome != nome_arquivo:
            abort(
                404
            )  # Se o nome do arquivo não corresponder ao nome do arquivo no token, retorne um erro 403
        uploadFolder_path = os.path.abspath("./uploads")

        return send_from_directory(uploadFolder_path, nome_arquivo)
    except (Forbidden, NotFound):
        return (
            jsonify(
                {"error": "O arquivo solicitado não existe ou não está disponível"}
            ),
            404,
        )

    except Exception as e:
        logging.error(
            f'Ocorreu um erro na rota "/arquivo/<nome_arquivo>": {e}', exc_info=True
        )
        abort(404)


if __name__ == "__main__":
    app.run(
        debug=True,
    )
