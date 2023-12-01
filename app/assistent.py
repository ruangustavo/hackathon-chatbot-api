import openai
from fastapi import WebSocket
import json
import os
from dotenv import load_dotenv

load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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


async def run_assistent(websocket: WebSocket):
    thread = openai.beta.threads.create()
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

            openai.beta.threads.runs.submit_tool_outputs(
                run_id=run.id, thread_id=thread.id, tool_outputs=tool_outputs
            )

            continue

        messages = openai.beta.threads.messages.list(
            thread_id=thread.id,
            limit=1,
        )

        chat_response = messages.data[0].content[0].text.value
        await websocket.send_text(
            json.dumps({"type": "chat", "content": {"message": chat_response}})
        )
