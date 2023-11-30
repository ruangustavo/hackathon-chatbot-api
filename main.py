from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import openai
from dotenv import load_dotenv
import json
import os
import httpx

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
            "name": "get_best_promotion",
            "description": "Pega a melhor promoção de um produto",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "O nome do produto",
                    },
                },
                "required": ["product_name"],
            },
        },
    }
]


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


def get_best_promotion(product_name):
    print(f"Chamou get_best_promotion com args {product_name}")
    products = fetch_products(product_name)
    if products is None:
        return "Não temos promoções para esse produto"
    products = filter_and_sort_products(products)
    if len(products) == 0:
        return "Não temos promoções para esse produto"
    best_product = products[0]
    return f"Encontrei uma promoção para {best_product['title']} com {best_product['price_discount']}% de desconto, acesse {best_product['short_url']} para conferir!"


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
        await websocket.send_text(message)


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

                if run.status not in ["queued", "in_progress", "cancelling"]:
                    break

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = globals()[function_name](**function_args)

                    print(f"Chamou '{function_name}' com args {function_args}")
                    print(f"Respondeu '{function_response}'")

                    # run = openai.beta.threads.runs.submit_tool_outputs(
                    #     thread_id=thread.id,
                    #     run_id=run.id,
                    #     tool_outputs=[
                    #         {"tool_call_id": tool_call.id, "output": function_response}
                    #     ],
                    # )

                    await websocket.send_text(function_response)

                continue

            messages = openai.beta.threads.messages.list(
                thread_id=thread.id,
                limit=1,
            )

            chat_response = messages.data[0].content[0].text.value
            await websocket.send_text(f"ChatGPT: {chat_response}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
