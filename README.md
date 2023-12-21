## Sobre o Projeto

Este projeto é uma implementação de um formulário web que utiliza tecnologias de segurança modernas para proteger os dados do usuário. O código incorpora tokens CSRF (Cross-Site Request Forgery) nos cookies e nos campos do formulário para prevenir ataques que forçam um usuário endossado a executar ações indesejadas. Além disso, utiliza tokens JWT (JSON Web Token) para autenticação, garantindo que apenas usuários autorizados possam acessar determinados recursos.

Os currículos cadastrados podem ser acessados através do endpoint /login. Por exemplo, para visualizar os currículos em um ambiente de desenvolvimento local, você usaria a URL  `http://127.0.0.1:5000/login`

## Tabela de Conteúdos
- [Sobre o Projeto](#sobre-o-projeto)
- [Instalação](#instalação)
- [Configuração do Projeto](#configuração-do-projeto)
- [Configuração da Base de Dados PostgreSQL](#configuração-da-base-de-dados-postgresql)
- [Executando o Projeto](#executando-o-projeto)
- [Endpoints](#endpoints)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Contato](#contato)

## Aviso Importante

> Durante o primeiro acesso ao endpoint "/" (http://127.0.0.1:5000/ em caso de acesso local), será solicitado que você cadastre o primeiro administrador do sistema. Por favor, seja cauteloso e memorize a senha informada, pois ela será necessária para futuros acessos e operações administrativas. Não há uma funcionalidade de recuperação de senha implementada, portanto, a perda da senha do administrador pode resultar em dificuldades de acesso.

## Instalação

Este projeto é desenvolvido em Python, uma linguagem de programação de alto nível amplamente utilizada para desenvolvimento web. Antes de iniciar a instalação, certifique-se de que o Python e o pip (Package Installer for Python), o gerenciador de pacotes padrão do Python, estão instalados em seu sistema. O pip é usado para instalar e gerenciar pacotes de software escritos em Python.

### Instalando dependencias

Antes de prosseguir com a instalação das dependências, certifique-se de que você está no diretório raiz do projeto.

Para instalar as dependências necessárias, execute o seguinte comando no terminal:
```shell
pip install -r requirements.txt
```

## Configuração da Base de Dados PostgreSQL

Este guia irá ajudá-lo a configurar a base de dados PostgreSQL para o seu projeto.

> <b>Esses passos só são necessários se você não possuir uma base de dados postgresql</b>

### Pré-requisitos

- PostgreSQL instalado. Se você estiver usando um sistema operacional baseado em Unix, pode instalar o PostgreSQL com o seguinte comando: `sudo apt update && sudo apt install postgresql`
- Acesso a um terminal ou linha de comando
- Privilégios de administrador (se estiver em um sistema operacional baseado em Unix)


### Passos 
- 1. <b>Iniciar serviço do postgresql:</b>
        ```shell
        sudo service postgresql start
        ```
- 2. <b>Criar uma nova base de dados: Primeiro, mude para o usuário postgres:</b>
        ```shell
        sudo -i -u postgres || sudo su postgres
        ```
       
        Em seguida, inicie o prompt de comando do PostgreSQL:

        ```shell
        psql
        ```
        Agora, crie a nova base de dados:
        ```shell
        CREATE DATABASE dbname;
        ```
        Substitua `"dbname"` pelo nome que você deseja dar à sua base de dados.
        
- 3. <b>Configurar o acesso à base de dados</b>: Ainda no prompt de comando do PostgreSQL, crie um novo usuário e conceda a ele os privilégios necessários:
        ```shell
        CREATE USER user WITH ENCRYPTED PASSWORD 'password';
        GRANT ALL PRIVILEGES ON DATABASE dbname TO user;
        ```
        Substitua `"user"` pelo nome de usuário desejado e `"password"` pela senha desejada.

- 4. <b>Configurar o host da base de dados:</b> O host da base de dados geralmente é "localhost" para uma base de dados local. Se a sua base de dados estiver em um servidor remoto, você precisará do endereço IP ou do nome do domínio do servidor.

- 5. <b>Sair do PostgreSQL e voltar ao usuário normal</b>:
        ```shell
        \q
        exit
        ```

Agora você deve ter a base de dados PostgreSQL configurada para o seu projeto. Lembre-se de substituir os valores de `"DB_NAME"`, `"DB_USERNAME"`, `"DB_PASSWORD"` e `"DB_HOST"` pelos valores corretos para o seu ambiente. Para mais informações sobre a instalação e uso do postgresql, consulte [este guia](https://www.digitalocean.com/community/tutorials/how-to-install-postgresql-on-ubuntu-20-04-quickstart-pt).

## Configuração do Projeto

Este projeto requer algumas configurações que são definidas no arquivo `.env`. Abaixo estão as variáveis de ambiente que você precisa configurar:

> <b>Importante:</b> Para valores que contêm espaços no arquivo .env, certifique-se de envolvê-los em aspas duplas. Isso garante que o espaço seja interpretado corretamente como parte do valor, e não como um delimitador. Caso restem dúvidas sobre a configuração do arquivo `.env`, veja o arquivo `.env.example`.

### Login de usuario
- `NUMERO_MAXIMO_TENTATIVAS`: Número de tentativas de login incorretas.
- `BLOQUEIO_DE_LOGIN`: Tempo de bloqueio de login em segundos após atingir o número máximo de tentativas de login incorretas. (86400 = 1 dia)

### Dados para autenticar no servidor SMTP

- `NOME_REMETENTE`: Nome do remetente (pode ser o mesmo do email).
- `EMAIL_REMENTENTE`: Email do remetente (gmail).
- `SENHA_REMETENTE`: Senhas de app Gerada pelo Google (<a href="https://myaccount.google.com/signinoptions/two-step-verification">account.google.com</a> - Final da página).

### Dados de recebimento do email

- `EMAIL_DESTINATARIOS:` Email do destinatário. Separe por virgula [","] (dentro das aspas) para mais de um destinatário.

### Autenticação Base de Dados
- `DB_NAME`: Nome da Base de dados.
- `DB_USERNAME`: Nome de usuário da base de dados.
- `DB_PASSWORD`: Senha da Base de dados.
- `DB_HOST`: Host da base de dados.

Por favor, substitua os valores das variáveis de ambiente no arquivo `.env` pelos valores corretos para o seu ambiente. Lembre-se de não compartilhar o arquivo `.env` ou qualquer outro arquivo que contenha informações sensíveis, como senhas ou chaves de API, em repositórios públicos. 

## Executando o projeto

Para executar esse projeto use o seguite comando:
```
python3 -m app
```

## Endpoints

Esse são alguns endpoints desse projeto:

- `GET /login`: Este endpoint é usado para autenticar um usuário. Ele espera receber um nome de usuário e senha no corpo da solicitação e define o token jtw e csrf, ambos validos por 30 minutos.

- `GET /admin`: Este endpoint é usado para renderizar a página de administração. Ele é protegido por JWT e CSRF, o que significa que o cliente deve fornecer um token JWT válido no cabeçalho de autorização da solicitação e um token CSRF no cookie para acessar este endpoint. 

- `GET /candidatos`: Este endpoint é usado para renderizar a página 'candidatos.html', onde onde pode ser encontradas informações sobre as pessoas que enviaram seus curriculos.

- `DELETE /api/logout`: Este endpoint é usado para encerrar a sessão do usuário do lado do servidor

- `GET /api/curriculos`: Esta rota retorna uma lista de currículos de candidatos. Ela é protegida por JWT e CSRF, o que significa que o cliente deve fornecer um token JWT válido no cabeçalho de autorização da solicitação e um token CSRF no cookie para acessar esta rota. A rota aceita dois parâmetros opcionais na URL: `offset` e `limit`, que são usados para implementar a paginação dos resultados. Por padrão, `offset` é 0 e `limit` é 10.

- `GET /api/estatisticas`: Esta rota retorna as estatísticas do sistema. Ela é protegida por JWT e CSRF, o que significa que o cliente deve fornecer um token JWT válido no cabeçalho de autorização da solicitação e um token CSRF no cookie para acessar esta rota. As estatísticas retornadas incluem o número total de candidatos, entrevistadores e administradores no banco de dados. Se ocorrer um erro ao obter as estatísticas, a rota retornará um erro 500 com uma mensagem de erro.

- `POST /api/cadastrar_usuario`: Esta rota é usada para cadastrar um novo usuário admistrativos. Ela é protegida por JWT e CSRF, o que significa que o cliente deve fornecer um token JWT válido no cabeçalho de autorização da solicitação e um token CSRF no cookie para acessar esta rota. A rota espera receber um objeto de usuário no corpo da solicitação com os seguintes campos: `nome`, `email`, `senha` e `tipoUsuario`.

Por favor, note que outros endpoints podem ser encontrados no <b>__ main __.py</b>

## Contribuição
Contribuições são o que fazem a comunidade open source um lugar incrível para aprender, inspirar e criar. Qualquer contribuição que você fizer será <b>muito apreciada</b>.

## Licença

Distribuído sob a licença  GNU GPL. Veja `LICENSE` para mais informações.

## Contato

Elisson Rodrigues - elissonrodrigues98@gmail.com



