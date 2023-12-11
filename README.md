# Hackathon: Chat-bot API

Chat-bot alimentado por inteligência artificial para atendimento de clientes e integração com mecanismo de busca do [Pechinchou](https://pechinchou.com.br/)

## Introdução 

O projeto foi desenvolvido para o Hackathon do [ETAL](https://etal.nadic.ifrn.edu.br/) com o objetivo de criar um chat-bot para atendimento de clientes e integração com mecanismo de busca do [Pechinchou](https://pechinchou.com.br/). A empresa Pechinchou é uma plataforma de busca de produtos e comparação de preços, que tem como objetivo facilitar a vida do consumidor na hora de fazer suas compras. O projeto não seria possível sem a ajuda dos meus colegas de equipe: Jackson Vieira e Heitor Queiroga. 

## Tecnologias
- [Python](https://www.python.org/): Linguagem de programação utilizada para desenvolver o projeto.
- [FastAPI](https://fastapi.tiangolo.com/): Framework utilizado para desenvolver a API.
- [Docker](https://www.docker.com/): Ferramenta utilizada para criar, testar e implantar aplicativos rapidamente.

## Instalação

### Como executar via Docker?

Partindo do princípio que você já tenha o Docker instalado e clonou o repositório em sua máquina , siga os passos abaixo:

1. Execute o Docker Compose:
```bash
$ docker-compose up --build -d
```

### Como executar via Python?

Partindo do princípio que você já tenha o Python instalado e clonou o repositório em sua máquina , siga os passos abaixo:

1. Crie o ambiente virtual:
```bash
$ python -m venv venv
```

2. Ative o ambiente virtual:
```bash
$ source venv/bin/activate
```

3. Instale as dependências:
```bash
$ pip install -r requirements.txt
```

2. Execute o servidor:
```bash
$ uvicorn main:app --reload
```

### Considerações

A API foi desenvolvida para ser consumida pelo cliente do chat-bot, que foi desenvolvido em Next.js. O código do cliente pode ser encontrado [aqui](https://github.com/ruangustavo/hackathon-chatbot-front).