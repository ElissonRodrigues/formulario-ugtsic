from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from os import getenv
import os
from flask import abort
import smtplib, ssl


def enviar_email(
    email_candidato: str,
    nome: str,
    telefone: int,
    cargo: int,
    escolaridade: str,
    observacoes: str,
    nome_arquivo: str,
    ip: str,
    datahora: str,
) -> None:
    """
    Envia um e-mail com os dados do candidato.

    Esta função é usada para enviar um e-mail com os dados do candidato. O e-mail inclui informações como o nome, 
    telefone, cargo pretendido, escolaridade, observações, o nome do arquivo enviado pelo candidato, o endereço IP 
    do candidato e a data e hora do envio do currículo.

    Args:
        email_candidato (str): O e-mail do candidato.
        nome (str): O nome do candidato.
        telefone (int): O telefone do candidato.
        cargo (int): O cargo pretendido pelo candidato.
        escolaridade (str): A escolaridade do candidato.
        observacoes (str): As observações do candidato.
        nome_arquivo (str): O nome do arquivo enviado pelo candidato.
        ip (str): O endereço IP do candidato.
        datahora (str): A data e hora do envio do currículo.

    Returns:
        None
    """
    try:
        context = ssl.create_default_context()  # Criar um contexto SSL
        server = smtplib.SMTP(
            "smtp.gmail.com", 587
        )  # Conectar ao servidor SMTP do Gmail

        server.ehlo()  # Identificar-se com o servidor
        server.starttls(context=context)  # Criar uma conexão segura com o servidor
        server.ehlo()  # Identificar-se novamente com o servidor

        email_rementente = getenv("EMAIL_REMENTENTE")
        password = getenv("SENHA_REMETENTE")
        nome_rementente = getenv("NOME_REMETENTE")
        email_destinatarios = getenv("EMAIL_DESTINATARIOS")
        
        msg = MIMEMultipart()
        
        msg["From"] = f"{nome_rementente} <{email_rementente}>"
        msg["To"] = email_destinatarios
        msg["Subject"] = f"Novo Curriculo enviado por {nome}"
        msg["Reply-To"] = email_candidato
        msg["Content-Type"] = "multipart/mixed"

        body = f"<b>Nome:</b> {nome}<br><b>Email:</b> {email_candidato}<br><b>Telefone:</b> {telefone}<br><b>Cargo:</b> {cargo}<br><b>Escolaridade:</b> {escolaridade}<br><b>Observações:</b> {observacoes}<br><b>IP</b>: {ip}<br><b>Data:</b> {datahora}"

        msg.attach(MIMEText(body, "html"))

        anexo = MIMEBase("application", "octet-stream")

        file_path = os.path.abspath("./uploads" + "/" + nome_arquivo)
        anexo.set_payload(open(file_path, "rb").read())

        encoders.encode_base64(anexo)

        anexo.add_header("Content-Disposition", f"attachment; filename={nome_arquivo}")

        msg.attach(anexo)

        server.login(email_rementente, password)

        message = msg.as_string()

        server.sendmail(email_rementente, email_destinatarios, message.encode("utf-8"))

        server.quit()
    except Exception as e:
        logging.error(f"Ocorreu um erro ao enviar o e-mail: {e}", exc_info=True)
        abort(500)
        
        

