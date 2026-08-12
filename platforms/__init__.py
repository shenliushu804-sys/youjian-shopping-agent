"""平台适配器：京东 / 天猫"""

from .jd import JDAdapter
from .tmall import TmallAdapter


def get_adapter(platform: str):
    adapters = {
        "jd": JDAdapter,
        "tmall": TmallAdapter,
    }
    cls = adapters.get(platform)
    return cls() if cls else None
