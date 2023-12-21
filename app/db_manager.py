from os import getenv
from psycopg2.extensions import connection
from traceback import format_exc
from datetime import datetime
from typing import Any, Union
import psycopg2
import bcrypt
import logging
from psycopg2.errors import UniqueViolation
def connect_db() -> connection:
    """Função para conectar ao banco de dados

    Returns:
        connection: conexão com o banco de dados
    """
    try:
        conn = psycopg2.connect(
            dbname=getenv("DB_NAME"),
            user=getenv("DB_USERNAME"),
            password=getenv("DB_PASSWORD"),
            host=getenv("DB_HOST"),
        )
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}", exc_info=True)
        return None


def create_table(conn: connection) -> None:
    """Função para criar as tabelas no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS curriculos (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                telefone BIGINT NOT NULL,
                cargo TEXT NOT NULL,
                escolaridade TEXT NOT NULL,
                observacoes TEXT,
                url_arquivo TEXT NOT NULL,
                ip TEXT NOT NULL,
                data_e_hora TIMESTAMP NOT NULL
                )"""
            )

            c.execute(
                """CREATE TABLE IF NOT EXISTS limitar_tentativa_login (
                id SERIAL PRIMARY KEY,
                ip TEXT NOT NULL UNIQUE,
                contar_tentativas INT NOT NULL,
                ultima_tentativa TIMESTAMP NOT NULL
                )"""
            )

            # Crie um tipo de usuário para limitar o acesso

            c.execute(
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_usuario') THEN 
                        CREATE TYPE tipo_usuario AS ENUM ('normal', 'admin');
                    END IF;
                END
                $$ LANGUAGE plpgsql;
            """
            )

            # Crie uma tabela para armazenar os dados de acesso
            c.execute(
                """CREATE TABLE IF NOT EXISTS grupo_de_acesso (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                ip_de_cadastro TEXT NOT NULL,
                tipo_de_usuario tipo_usuario NOT NULL,
                data_criacao TIMESTAMP NOT NULL,
                data_ultimo_login TIMESTAMP
                )"""
            )

            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao criar tabelas: {e}", exc_info=True)


def cadastrar_candidato(
    conn: connection, data: dict[str, str | int | datetime | None]
) -> None:
    """Função para cadastrar os dados do candidato no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
        data (dict): dicionário com os dados do candidato
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """INSERT INTO curriculos (nome, email, telefone, cargo, escolaridade, observacoes, url_arquivo, ip, data_e_hora) 
                VALUES (%(nome)s, %(email)s, %(telefone)s, %(cargo)s, %(escolaridade)s, %(observacoes)s, %(url_arquivo)s, %(ip)s, %(data_e_hora)s)""",
                data,
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao cadastrar candidato: {e}", exc_info=True)


def listar_candidatos(
    conn: connection, offset: int, limit: int
) -> list[tuple[Any, ...]]:
    """Função para listar os candidatos cadastrados no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
        offset (int): número de linhas para ignorar
        limit (int): número máximo de linhas para retornar

    Returns:
        list: lista com os candidatos cadastrados
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """SELECT * FROM curriculos ORDER BY id LIMIT %s OFFSET %s""",
                (limit, offset),
            )
            return c.fetchall()

    except Exception as e:
        logging.error(f"Erro ao listar candidatos: {e}", exc_info=True)


def cadastrar_novo_usuário(conn: connection, data: dict[str, str | datetime]) -> dict[str]:
    """Função para cadastrar o entrevistador no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
        data (dict): dicionário com os dados do entrevistador
    """
    try:
        with conn.cursor() as c:
            # Gere um salt e crie um hash da senha
            salt = bcrypt.gensalt()
            senha_hashed = bcrypt.hashpw(data["senha"].strip().encode(), salt).decode()
            # Substitua a senha em texto puro pela versão hashed
            data["senha"] = senha_hashed
            data["email"] = data["email"].lower().strip()
            data["tipo_de_usuario"] = data["tipo_de_usuario"].strip()

            c.execute(
                """INSERT INTO grupo_de_acesso (nome, email, senha, ip_de_cadastro, tipo_de_usuario, data_criacao) 
                VALUES (%(nome)s, %(email)s, %(senha)s, %(ip_de_cadastro)s, %(tipo_de_usuario)s, %(data_criacao)s)""",
                data,
            )
            conn.commit()
            return {"success": "Entrevistador cadastrado com sucesso"}
    except UniqueViolation:
        return {"error": "E-mail já cadastrado"}
    except Exception as e:
        logging.error(f"Erro ao cadastrar entrevistador: {format_exc()}", exc_info=True)
        return {"error": f"Erro ao cadastrar entrevistador: {e}"}


def ultimo_login_de_usuário(conn: connection, data: dict[datetime, str]) -> None:
    """Função para atualizar o último login do usuário no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
        data (dict): dicionário com os dados do usuário (acesso)
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """UPDATE grupo_de_acesso SET ultimo_login = %(ultimo_login)s WHERE email = %(email)s""",
                data,
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao atualizar último login de usuário: {e}", exc_info=True)


def registrar_tentativa_login(conn: connection, data: dict[int, int, datetime]) -> None:
    """Função para registrar uma nova tentativa de login no banco de dados

    Args:
        conn (connection): conexão com o banco de dados
        data (dict): dicionário com os dados da tentativa de login
    """
    try:
        with conn.cursor() as c:
            c = conn.cursor()
            c.execute(
                """INSERT INTO limitar_tentativa_login (ip, contar_tentativas, ultima_tentativa) 
                VALUES (%(ip)s, %(contar_tentativas)s, %(ultima_tentativa)s)""",
                data,
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao registrar tentativa de login: {e}")


def atualizar_tentativa_login(conn: connection, data: dict[int, int]) -> None:
    """
    Atualiza o registro de tentativa de login já existente no banco de dados.

    Esta função incrementa o contador de tentativas de login e atualiza a data e hora da última tentativa para um determinado IP.

    Args:
        conn (connection): Conexão ativa com o banco de dados.
        data (dict): Dicionário contendo os dados da tentativa de login. Deve incluir as chaves 'ip' e 'ultima_tentativa'.

    Raises:
        Exception: Se ocorrer um erro ao tentar atualizar o registro no banco de dados, uma exceção será registrada no log.

    Returns:
        None
    """
    try:
        with conn.cursor() as c:
            c = conn.cursor()
            c.execute(
                """UPDATE limitar_tentativa_login SET contar_tentativas = contar_tentativas + 1, ultima_tentativa = %(ultima_tentativa)s WHERE ip = %(ip)s""",
                data,
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao atualizar tentativa de login: {e}", exc_info=True)


def buscar_tentativas_de_login(
    conn: connection, ip: str
) -> dict[str, Union[int, datetime]] | None:
    """
    Retorna os dados de tentativas de login de um determinado IP.

    Esta função executa uma consulta SQL no banco de dados para obter o número de tentativas de login e a data da última tentativa associadas ao IP fornecido.
    Se nenhum registro for encontrado com o IP fornecido, a função retorna None.

    Args:
        conn (connection): A conexão com o banco de dados.
        ip (str): O endereço IP do usuário.

    Returns:
        dict: Um dicionário contendo as seguintes chaves:
            - 'numero_tentativas': O número de tentativas de login.
            - 'ultima_tentativa': A data e hora da última tentativa de login.
        None: Se nenhum registro for encontrado com o IP fornecido.

    Raises:
        Exception: Se ocorrer um erro ao executar a consulta SQL.
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """SELECT * FROM limitar_tentativa_login WHERE ip = %s""",
                (ip,),
            )

            if c.rowcount == 0:
                return None

            row = c.fetchone()
            return {"numero_tentativas": row[2], "ultima_tentativa": row[3]}

    except Exception as e:
        logging.error(f"Erro ao retornar tentativas de login: {e}", exc_info=True)


def resetar_tentativas_de_login(conn: connection, ip: str) -> None:
    """
    Reseta as tentativas de login de um determinado IP.

    Esta função executa uma consulta SQL no banco de dados para deletar as tentativas de login associadas ao IP fornecido.
    Isso é útil para resetar o contador de tentativas de login após um usuário ter feito login com sucesso.

    Args:
        conn (connection): A conexão com o banco de dados.
        ip (str): O endereço IP do usuário.

    Raises:
        Exception: Se ocorrer um erro ao executar a consulta SQL.
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """DELETE FROM limitar_tentativa_login WHERE ip = %s""",
                (ip,),
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao resetar tentativas de login: {e}", exc_info=True)


def validar_senha(conn: connection, email: str, senha_usuario: str) -> bool:
    """
    Valida a senha de um usuário.

    Esta função executa uma consulta SQL no banco de dados para obter a senha hash do usuário associado ao e-mail fornecido.
    Em seguida, verifica se a senha fornecida corresponde à senha hash. Se a senha estiver correta, a função retorna True.
    Se a senha estiver incorreta, ou se nenhum usuário for encontrado com o e-mail fornecido, a função retorna False.

    Args:
        conn (connection): A conexão com o banco de dados.
        email (str): O e-mail do usuário.
        senha_usuario (str): A senha fornecida pelo usuário.

    Returns:
        bool: True se a senha estiver correta, False se a senha estiver incorreta ou se nenhum usuário for encontrado.

    Raises:
        Exception: Se ocorrer um erro ao executar a consulta SQL.
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """SELECT senha FROM grupo_de_acesso WHERE email = %s""",
                (email,),
            )

            if c.rowcount == 0:
                return False

            senha_hashed = c.fetchone()[0]
            valida = bcrypt.checkpw(senha_usuario.encode(), senha_hashed.encode())

            return valida

    except Exception as e:
        logging.error(f"Erro ao validar senha: {e}", exc_info=True)


def obter_tipo_de_usuario(conn: connection, email: str) -> str:
    """
    Retorna o tipo de usuário para um determinado e-mail.

    Esta função executa uma consulta SQL no banco de dados para obter o tipo de usuário associado ao e-mail fornecido.
    Se nenhum usuário for encontrado com o e-mail fornecido, a função retorna None.

    Args:
        conn (connection): A conexão com o banco de dados.
        email (str): O e-mail do usuário.

    Returns:
        str: O tipo de usuário, ou None se nenhum usuário for encontrado.

    Raises:
        Exception: Se ocorrer um erro ao executar a consulta SQL.
    """
    try:
        with conn.cursor() as c:
            c.execute(
                """SELECT tipo_de_usuario FROM grupo_de_acesso WHERE email = %s""",
                (email,),
            )

            if c.rowcount == 0:
                return None

            tipo_usuario = c.fetchone()[0]
            return tipo_usuario

    except Exception as e:
        logging.error(f"Erro ao obter tipo de usuário: {e}", exc_info=True)


def estatisticas(conn: connection) -> dict[str, int]:
    """
    Retorna as estatísticas de acesso do banco de dados.

    Esta função executa uma consulta SQL no banco de dados para obter o número total de candidatos, entrevistadores e administradores.
    Os resultados são retornados como um dicionário.

    Args:
        conn (connection): A conexão com o banco de dados.

    Returns:
        dict: Um dicionário contendo as seguintes chaves:
            - 'total_candidatos': O número total de candidatos no banco de dados.
            - 'total_entrevistadores': O número total de entrevistadores no banco de dados.
            - 'total_administradores': O número total de administradores no banco de dados.

    """
    try:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT 
                    (SELECT COUNT(*) FROM curriculos) as total_candidatos,
                    (SELECT COUNT(*) FROM grupo_de_acesso WHERE tipo_de_usuario = 'normal') as total_entrevistadores,
                    (SELECT COUNT(*) FROM grupo_de_acesso WHERE tipo_de_usuario = 'admin') as total_administradores
                """
            )

            result = c.fetchone()
            return {
                "total_candidatos": result[0],
                "total_entrevistadores": result[1],
                "total_administradores": result[2],
            }

    except Exception as e:
        logging.error(f"Erro ao retornar estatísticas de acesso: {e}", exc_info=True)