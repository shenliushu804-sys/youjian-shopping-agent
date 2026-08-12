"""平台适配器抽象基类"""

from abc import ABC, abstractmethod

from models import Product, ProductDetail


COMMON_BRANDS = [
    "京东京造", "京东", "西昊", "黑白调", "网易严选", "永艺", "保友",
    "全品屋", "得力", "小米", "网易智造", "赫曼米勒", "冈村", "乐歌",
    "林氏家居", "顾家家居", "芝华仕", "维意", "喜临门", "爱果乐",
]


def extract_brand_from_title(title: str) -> str:
    """从商品标题前缀提取品牌"""
    t = (title or "").strip()
    for brand in COMMON_BRANDS:
        if t.startswith(brand) or (brand in t and t.index(brand) < 6):
            return brand
    return ""


class PlatformAdapter(ABC):
    platform: str = ""

    @abstractmethod
    async def search(self, page, query: str, max_results: int = 20) -> list[Product]:
        """平台搜索，返回候选商品（不负责预算过滤）"""

    @abstractmethod
    async def fetch_detail(self, page, product: Product) -> ProductDetail:
        """读取商品详情页参数/评价/品牌信息"""

    @abstractmethod
    async def prepare_order(self, page, product: Product) -> str:
        """加购并跳转结算，返回支付页 URL（不自动支付）"""
