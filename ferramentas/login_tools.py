from flask import flash
from datetime import timedelta, datetime
from pytz import timezone
from ferramentas.datetime_tools import formatar_tempo
from psycopg2.extensions import connection

from app.db_manager import (
    registrar_tentativa_login,
    resetar_tentativas_de_login,
    atualizar_tentativa_login,
)


def registrar_primeira_tentativa(
    db: connection, ip: str, agora: int, max_tentativas: int
):
    data = {
        "ip": ip,
        "contar_tentativas": 1,
        "ultima_tentativa": agora,
    }
    registrar_tentativa_login(db, data)
    flash(
        f"Nome de usuário ou senha incorretos! tentativas restantes: {max_tentativas}",
        "error",
    )


def bloquear_ip_se_necessario(
    db: connection,
    ip: str,
    dados_tentativas: dict[int, datetime],
    agora: datetime,
    tempo_bloqueio: timedelta,
):
    ultima_tentativa = dados_tentativas["ultima_tentativa"]
    if (
        ultima_tentativa.tzinfo is None
        or ultima_tentativa.tzinfo.utcoffset(ultima_tentativa) is None
    ):
        ultima_tentativa = timezone("America/Sao_Paulo").localize(ultima_tentativa)
    if agora - ultima_tentativa > tempo_bloqueio:
        resetar_tentativas_de_login(db, ip)

    else:
        tempo_restante = tempo_bloqueio - (agora - ultima_tentativa)
        formato_tempo_restante = formatar_tempo(tempo_restante)
        flash(
            f"Tentativas excedidas. Tente em: {formato_tempo_restante}",
            "error",
        )


def atualizar_tentativa_login_usuario(
    db: connection,
    ip: str,
    agora: timedelta,
    dados_tentativas: dict[int, datetime],
    max_tentativas: int,
):
    dados = {
        "ip": ip,
        "ultima_tentativa": agora,
    }
    atualizar_tentativa_login(db, dados)
    flash(
        f"Nome de usuário ou senha incorretos! Tentativas restantes: {max_tentativas - dados_tentativas['numero_tentativas']}",
        "error",
    )
