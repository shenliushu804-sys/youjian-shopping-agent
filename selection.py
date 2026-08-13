"""选品合并与过滤"""

from models import Product


def merge_products(products: list[Product], max_products: int = 5) -> list[Product]:
    """跨平台轮转合并，保证详情名额不被单一平台占满。"""
    seen = set()
    per_platform: dict[str, list[Product]] = {}
    for p in products:
        key = (p.platform, p.product_url or p.title)
        if key in seen:
            continue
        seen.add(key)
        per_platform.setdefault(p.platform, []).append(p)

    merged = []
    for i in range(max_products):
        added = False
        for platform_products in per_platform.values():
            if i < len(platform_products):
                merged.append(platform_products[i])
                added = True
        if not added:
            break
    return merged[:max_products]


def filter_by_budget(products: list[Product], budget_max: float, tolerance: float = 0.20) -> list[Product]:
    """有预算时淘汰超预算商品；价格未抓取到的商品不放行。"""
    if budget_max <= 0:
        return products
    limit = budget_max * (1 + tolerance)
    return [p for p in products if p.price > 0 and p.price <= limit]
