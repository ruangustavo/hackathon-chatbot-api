from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import openai
from dotenv import load_dotenv
import json
import os
import httpx

from datetime import datetime

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PECHINCHOU_SEARCH_URL = "https://admin.pechinchou.com.br/api/v2/produto/listar_produtos_por_opcao/search/{product}/?page=1"

app = FastAPI()


class MessageInput(BaseModel):
    content: str = Field(..., max_length=100)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_best_promotion_with_params",
            "description": "Pega a melhor promoção de um produto com os parâmetros especificados, promocoes boas sao aquelas que tem mais likes",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Nome do produto a ser buscado, retorna uma lista de produtos",
                    }
                },
                "required": ["product_name"],
            },
        },
    }
]

# QUERIES
# melhor promocao de ar condicionado hoje
# melhor promocao de ar condicionado
# melhor promocao de celular xiami 4GB
# melhor suporte e comunicacao como o envio do email da penchinchou em caso de denuncia ou outras coisas
# bot atuar como feedback de uma promocao ou quando um usuario quer ter mais informacoes sobre uma promocao.


def str_to_date(date_str):
    datetime_str = "2023-10-07T12:22:17.268138-03:00"
    format_str = "%Y-%m-%dT%H:%M:%S.%f%z"
    datetime = datetime.strptime(datetime_str, format_str)
    return datetime


def filter_by_params(products, params={}):
    if params == {}:
        return products

    if "store" in params:
        products = [
            product
            for product in products
            if product["store"]["name"] == params["store"]
        ]
    if "category" in params:
        products = [
            product
            for product in products
            if product["category"]["name"] == params["category"]
        ]
    if "price_max" in params:
        products = [
            product for product in products if product["price"] <= params["price_max"]
        ]
    if "price_min" in params:
        products = [
            product for product in products if product["price"] >= params["price_min"]
        ]
    if "discount" in params:
        products = [
            product
            for product in products
            if product["price_discount"] >= params["discount"]
        ]
    if "date_max" in params:
        products = [
            product
            for product in products
            if str_to_date(product["created_at"]) <= str_to_date(params["datetime_max"])
        ]
    if "date_min" in params:
        products = [
            product
            for product in products
            if str_to_date(product["created_at"]) >= str_to_date(params["date_min"])
        ]
    if "likes" in params:
        products = [
            product for product in products if product["total_likes"] >= params["likes"]
        ]
    return products


def fetch_products(product):
    api_url = PECHINCHOU_SEARCH_URL.format(product=product)
    response = httpx.get(api_url).json()

    if "results" not in response:
        return None

    return response["results"]


def filter_and_sort_products(products):
    for product in products:
        old_price = float(product["old_price"])
        price = float(product["price"])

        price_discount = int(99 - ((price * 100) / old_price))
        total_likes = len(product["likes"])

        product["price_discount"] = price_discount
        product["total_likes"] = total_likes
    products = [
        product
        for product in products
        if product["status"] == "ACTIVE" and not product["warning"]
    ]
    products.sort(key=lambda x: x["total_likes"], reverse=True)
    return products


def get_best_promotion_with_params(product_name):
    print(f"Chamou get_best_promotion com args {product_name}")
    products = fetch_products(product_name)
    if products is None:
        return {"products": []}
    products = filter_and_sort_products(products)
    if len(products) == 0:
        return {"products": []}
    best_product = products[0]
    return {"products": products, "best_product": best_product}


assistant = openai.beta.assistants.create(
    model="gpt-3.5-turbo-1106",
    instructions="""Bem-vindo ao Pechinchou! Eu sou o assistente virtual da Pechinchou, a sua plataforma de divulgação de promoções em diversos e-commerces. Com mais de um milhão de usuários satisfeitos, conectamos você às melhores ofertas do mercado. Aqui estão alguns destaques:
    - **Ampla Variedade de Lojas:** Com mais de trezentas lojas parceiras, oferecemos promoções incríveis para atender a todos os gostos e necessidades.
    - **Diversidade de Ofertas:** Temos mais de cem mil promoções postadas, desde eletrônicos a moda, garantindo que você sempre encontre as melhores ofertas.
    Como posso ajudar você hoje? Se precisar de assistência para encontrar a melhor promoção ou informações sobre o Pechinchou, fique à vontade para perguntar!
    """,
    tools=tools,
)


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    thread = openai.beta.threads.create()

    try:
        while True:
            message = await websocket.receive_text()

            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message,
            )

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            while True:
                run = openai.beta.threads.runs.retrieve(
                    run_id=run.id,
                    thread_id=thread.id,
                )

                print("run status", run.status)

                if run.status not in ["queued", "in_progress", "cancelling"]:
                    break

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls

                tool_outputs = []
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print("function name", function_name)
                    print("function args", function_args)
                    function_response = globals()[function_name](**function_args)
                    await websocket.send_text(
                        json.dumps({"type": "chat", "content": function_response})
                    )

                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(function_response),
                        }
                    )

                print("tool outputs", tool_outputs)
                openai.beta.threads.runs.submit_tool_outputs(
                    run_id=run.id, thread_id=thread.id, tool_outputs=tool_outputs
                )

            messages = openai.beta.threads.messages.list(
                thread_id=thread.id,
                limit=1,
            )

            chat_response = messages.data[0].content[0].text.value
            await websocket.send_text(
                json.dumps({"type": "chat", "content": {"message": chat_response}})
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
