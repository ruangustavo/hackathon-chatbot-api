import json
import openai
from dotenv import load_dotenv
from fastapi import WebSocket
from app.promotions import get_best_promotion

load_dotenv()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_best_promotion",
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

assistant = openai.beta.assistants.create(
    model="gpt-3.5-turbo-1106",
    instructions="""Bem-vindo ao Pechinchou! Eu sou o assistente virtual da Pechinchou, a sua plataforma de divulgação de promoções em diversos e-commerces. Com mais de um milhão de usuários satisfeitos, conectamos você às melhores ofertas do mercado. Aqui estão alguns destaques:
    - **Ampla Variedade de Lojas:** Com mais de trezentas lojas parceiras, oferecemos promoções incríveis para atender a todos os gostos e necessidades.
    - **Diversidade de Ofertas:** Temos mais de cem mil promoções postadas, desde eletrônicos a moda, garantindo que você sempre encontre as melhores ofertas.
    Como posso ajudar você hoje? Se precisar de assistência para encontrar a melhor promoção ou informações sobre o Pechinchou, fique à vontade para perguntar!
    """,
    tools=tools,
)


async def run_assistant(websocket: WebSocket):
    thread = openai.beta.threads.create()

    while True:
        message = await websocket.receive_text()
        await process_user_message(thread, message, websocket)


async def process_user_message(thread, message, websocket):
    openai.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant.id
    )
    await wait_for_run_completion(run, thread, websocket)


async def wait_for_run_completion(run, thread, websocket):
    while run.status in ["queued", "in_progress", "cancelling"]:
        run = openai.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)

    if run.status == "requires_action":
        await handle_requires_action(run, thread, websocket)
    else:
        await send_assistant_response(thread, websocket)


async def handle_requires_action(run, thread, websocket):
    tool_calls = run.required_action.submit_tool_outputs.tool_calls
    tool_outputs = []

    for tool_call in tool_calls:
        function_name, function_args = await get_function_info(tool_call)
        function_response = call_function(function_name, function_args)
        await websocket.send_text(
            json.dumps({"type": "chat", "content": function_response})
        )

        tool_outputs.append(
            {"tool_call_id": tool_call.id, "output": json.dumps(function_response)}
        )

    await submit_tool_outputs(run, thread, tool_outputs)


async def get_function_info(tool_call):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    return function_name, function_args


def call_function(function_name, function_args):
    if function_name == "get_best_promotion":
        return get_best_promotion(**function_args)
    return None


async def submit_tool_outputs(run, thread, tool_outputs):
    openai.beta.threads.runs.submit_tool_outputs(
        run_id=run.id, thread_id=thread.id, tool_outputs=tool_outputs
    )


async def send_assistant_response(thread, websocket):
    messages = openai.beta.threads.messages.list(thread_id=thread.id, limit=1)
    chat_response = messages.data[0].content[0].text.value

    await websocket.send_text(
        json.dumps({"type": "chat", "content": {"message": chat_response}})
    )
