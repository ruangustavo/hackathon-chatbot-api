import openai
import httpx
import json

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PECHINCHOU_SEARCH_URL = "https://admin.pechinchou.com.br/api/v2/produto/listar_produtos_por_opcao/search/{product}/?page=1"


def get_most_important_product_word(sentence):
    openai.api_key = OPENAI_API_KEY
    prompt = prompt = f"""Extraia da frase a palavra mais importante relacionada a produto: "{sentence}". 
            Retorne a palavra do produto e suas especificações, como por exemplo: 'celular roxo 4GB 128GB' em formato de JSON. Por exemplo:
            {{"status": "fetching_products", "content": "<a palavra do produto e suas especificações>"}}
            Caso o usuário não esteja procurando por produto, e sim, uma pergunta sobre a Pechinchou, responda em formato de JSON. Por exemplo:
            {{"status": "answering_doubt", "content": "<resposta sobre a pechinchou>"}}
            """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Você é um chat-bot de uma empresa chamada Pechinchou que divulga promoções de produtos em variados e-commerces.  A Pechinchou tem mais de um milhão de usuários. A Pechinchou tem mais de trezentas lojas cadastradas. A Pechinchou tem mais de cem mil promoções postadas.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    string_to_json = json.loads(response.choices[0].message.content)
    return string_to_json


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

        price_discount = int(100 - ((price * 100) / old_price))
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


def process(user_sentence):
    result = get_most_important_product_word(user_sentence)
    data = result["content"]

    if result["status"] == "fetching_products":
        products = fetch_products(data)
        products = filter_and_sort_products(products)
        return {
            "status": "fetching_products",
            "content": products,
        }
    return {"status": "answering_doubt", "content": data}
