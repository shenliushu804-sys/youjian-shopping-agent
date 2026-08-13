import unittest

from models import Product
from selection import filter_by_budget, merge_products


def product(platform, url, price):
    return Product(title=url, price=price, platform=platform, product_url=url)


class MergeProductsTest(unittest.TestCase):
    def test_round_robin_mixes_platforms(self):
        jd = [product("jd", f"jd-{i}", 100 + i) for i in range(5)]
        tmall = [product("tmall", f"tmall-{i}", 200 + i) for i in range(5)]
        merged = merge_products(jd + tmall, max_products=5)
        self.assertEqual([p.platform for p in merged], ["jd", "tmall", "jd", "tmall", "jd"])

    def test_dedupe_by_url(self):
        merged = merge_products(
            [product("jd", "same-url", 100), product("jd", "same-url", 120)],
            max_products=5,
        )
        self.assertEqual(len(merged), 1)

    def test_max_products_cap(self):
        merged = merge_products([product("jd", str(i), 10) for i in range(10)], max_products=3)
        self.assertEqual(len(merged), 3)


class BudgetFilterTest(unittest.TestCase):
    def test_drops_unknown_price_when_budget_set(self):
        unknown = product("jd", "unknown", 0)
        cheap = product("jd", "cheap", 100)
        expensive = product("jd", "expensive", 500)
        filtered = filter_by_budget([unknown, cheap, expensive], budget_max=200, tolerance=0.2)
        self.assertEqual(filtered, [cheap])

    def test_keeps_all_without_budget(self):
        unknown = product("jd", "unknown", 0)
        self.assertEqual(filter_by_budget([unknown], budget_max=0), [unknown])


if __name__ == "__main__":
    unittest.main()
