from .db_manager import connect_db, create_table
from dotenv import load_dotenv
import logging
from pytz import timezone
from datetime import datetime
from tornado.log import LogFormatter
from pathlib import Path
from os import getenv, _exit # type: ignore
from secrets import token_hex
from time import sleep

load_dotenv()

# Criar pasta para salvar os arquivos e logs
Path("./uploads").mkdir(parents=True, exist_ok=True)
Path("./logs").mkdir(parents=True, exist_ok=True)

# Configurar o log
logging.Formatter.converter = lambda *args: datetime.now(tz=timezone("America/Sao_Paulo")).timetuple()  # type: ignore

consoleHandler = logging.StreamHandler()

consoleHandler.setFormatter(
    LogFormatter(
        fmt="%(color)s%(asctime)s - %(levelname)s%(end_color)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )
)

fileHandler = logging.FileHandler("./logs/web_form.log")
fileHandler.setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="[ %d/%m/%Y %H:%M:%S ]",
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[fileHandler, consoleHandler],
)

if not Path(".env").exists():
    Path(".env").touch()
    logging.warning('Arquivo ".env" criado. Por favor, insira as variáveis de ambiente necessárias. Leia o arquivo README.md para mais informações. ')
    sleep(5)
    _exit(0)

# Inserir chave secreta no .env
if not getenv("FLASK_SECRET_KEY"):
    with open(".env", "a") as env:
        secret_key = token_hex(32)
        env.write(f"\n#CHAVE SECRETA DO FLASK\nFLASK_SECRET_KEY={secret_key}")
        logging.warning('Chave secreta do Flask inserida no arquivo ".env". Por favor, considere reiniciar o esse programa. ')
        sleep(5)
        
    load_dotenv()
        

# Criar as tabelas no banco de dados
create_table(connect_db())
