from fastapi import FastAPI, status
from pydantic import BaseModel, Field

from chat import process

app = FastAPI()


class MessageInput(BaseModel):
    content: str = Field(..., max_length=100)


@app.get("/")
async def health_check():
    return {"pai": "ta on"}


@app.post("/promotions", status_code=status.HTTP_200_OK)
async def chat(message_input: MessageInput):
    message_input = process(message_input.content)
    return {"message": message_input}


# Voce e uma loja?
# Voce e confiavel?
# O que e a penchichou?
# Quem e voce?
# Me recomende um produto aleatorio
# Me recomende uma loja aleatoria
# Me recomende uma promocao aleatoria
# Me recomende uma promocao de um produto especifico
# Que celular voce me recomenda?
# Que loja voce me recomenda?
# Quais produtos ultimamente tem tido mais promocoes?
# Voces tem promocoes de geladeiras?
# Voces tem promocoes de notebooks?
# Voces tem promocoes de TVs?
# Quem sao voces?

"""
+1 milhão
de usuários

+300
Lojas cadastradas

+100.000
Promoções postadas
"""
