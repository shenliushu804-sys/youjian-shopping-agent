"""数据模型"""

from dataclasses import dataclass, field, asdict


@dataclass
class Product:
    title: str
    price: float
    shop_name: str = ""
    shop_type: str = "普通店"  # 旗舰店/专卖店/普通店
    product_url: str = ""
    platform: str = ""  # jd / tmall
    review_count: int = 0
    rating: float = 0.0

    def to_dict(self):
        return asdict(self)


@dataclass
class ProductDetail:
    product: Product
    params: dict = field(default_factory=dict)  # {"参数名": "参数值"}
    brand: str = ""
    rating: float = 0.0
    review_summary: str = ""
    price: float = 0.0
    missing_params: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["product"] = self.product.to_dict()
        return d


@dataclass
class Recommendation:
    product: Product
    detail: ProductDetail
    score: float = 0.0
    reason: str = ""
    concerns: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["product"] = self.product.to_dict()
        d["detail"] = self.detail.to_dict()
        return d


@dataclass
class Intent:
    search_keywords: str
    critical_params: list = field(default_factory=list)
    budget_max: float = 0.0
    scenario: str = ""
    shop_type_priority: list = field(default_factory=lambda: ["旗舰店", "专卖店", "普通店"])

    def to_dict(self):
        return asdict(self)
