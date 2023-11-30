import openai
from dotenv import load_dotenv
import os

import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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


def get_best_promotion(product_name):
    if product_name == "celular":
        return "O celular mais barato é o iPhone 11"
    elif product_name == "notebook":
        return "O notebook mais barato é o Dell Inspiron"
    elif product_name == "tv":
        return "A TV mais barata é a Samsung 32 polegadas"
    else:
        return "Não temos promoções para esse produto"


assistant = openai.beta.assistants.create(
    model="gpt-3.5-turbo-1106",
    instructions="""Bem-vindo ao Pechinchou! Eu sou o assistente virtual da Pechinchou, a sua plataforma de divulgação de promoções em diversos e-commerces. Com mais de um milhão de usuários satisfeitos, conectamos você às melhores ofertas do mercado. Aqui estão alguns destaques:
    - **Ampla Variedade de Lojas:** Com mais de trezentas lojas parceiras, oferecemos promoções incríveis para atender a todos os gostos e necessidades.
    - **Diversidade de Ofertas:** Temos mais de cem mil promoções postadas, desde eletrônicos a moda, garantindo que você sempre encontre as melhores ofertas.
    Como posso ajudar você hoje? Se precisar de assistência para encontrar a melhor promoção ou informações sobre o Pechinchou, fique à vontade para perguntar!
    """,
    tools=tools,
    # chama funcoes com base em palavras-chave por exemplo produto, ...
    # funcoes que chamam outras funcoes
    # funcoes que chamam api
)

thread = openai.beta.threads.create()

print(f"Assistant ID: {assistant.id}")
print(f"Thread ID: {thread.id}\n")

print("GPT: Bem vindo ao Pechinchou! Como posso ajudar você hoje?")

while True:
    message = input("Você: ")
    print()

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

            run = openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[
                    {"tool_call_id": tool_call.id, "output": function_response}
                ],
            )

    messages = openai.beta.threads.messages.list(
        thread_id=thread.id,
        limit=1,
    )

    print(f"ChatGPT: {messages.data[0].content[0].text.value}")
