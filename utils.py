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
