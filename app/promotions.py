from typing import Dict, Optional
from urllib.parse import urljoin

import httpx

PECHINCHOU_BASE_URL = "https://admin.pechinchou.com.br/api/v2/"
PECHINCHOU_SEARCH_URL = urljoin(
    PECHINCHOU_BASE_URL,
    "produto/listar_produtos_por_opcao/search/{product}/?page=1",
)


def search_promotions(product: str) -> Optional[Dict]:
    url = PECHINCHOU_SEARCH_URL.format(product=product)
    response = httpx.get(url).json()
    return response.get("results")


def filter_active_promotions(promotions):
    for promotion in promotions:
        old_price = float(promotion["old_price"])
        price = float(promotion["price"])
        promotion["price_discount"] = int(99 - ((price * 100) / old_price))
        promotion["total_likes"] = len(promotion["likes"])

    active_promotions = [
        product
        for product in promotions
        if product["status"] == "ACTIVE" and not product["warning"]
    ]

    return active_promotions


def get_best_promotion(product_name):
    print(f"get_best_promotion {product_name}")
    promotions = search_promotions(product_name)

    if promotions is None or promotions == []:
        return {
            "products": [],
        }

    active_promotions = filter_active_promotions(promotions)

    # Ordenando as promoções por likes em ordem decrescente
    active_promotions.sort(
        key=lambda x: x["total_likes"],
        reverse=True,
    )

    best_promotion = active_promotions[0]

    return {
        "products": active_promotions,
        "best_product": best_promotion,
    }
