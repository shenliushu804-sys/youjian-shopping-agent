"""全局配置"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
COOKIE_FILE = DATA_DIR / "cookies.json"

# 平台
PLATFORMS = ["jd", "tmall"]
MAX_PRODUCTS_PER_PLATFORM = 20
MAX_DETAIL_PRODUCTS = 5

# 预算
BUDGET_TOLERANCE = 0.20  # 超预算 20% 直接淘汰

# LLM 模式: auto / local / api
LLM_MODE = os.environ.get("LLM_MODE", "auto")
LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:8001")
LOCAL_LLM_MODEL = "qwen3.5-2b"

# Qwen API 兜底
QIANWEN_API_KEY = os.environ.get("QIANWEN_API_KEY", "")
QWEN_MODEL = "qwen-turbo"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_PROXY = os.environ.get("QWEN_PROXY", "")

# 浏览器
PROXY = os.environ.get("PROXY", "")
HEADLESS = os.environ.get("HEADLESS", "0") == "1"
TIMEOUT_MS = 30000

# 本地模型
MODEL_PATH = os.environ.get(
    "QWEN_MODEL_PATH",
    str(Path.home() / ".cache/modelscope/hub/models/Qwen--Qwen3.5-2B/snapshots/master"),
)
LOCAL_LLM_PORT = int(os.environ.get("LOCAL_LLM_PORT", "8001"))

# 环境变量加载（.env）
def load_env():
    env_files = (
        BASE_DIR / ".env",
        BASE_DIR / "backend" / ".env",
        BASE_DIR / "youjian-mini" / "backend" / ".env",
    )
    for env_file in env_files:
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()
QIANWEN_API_KEY = os.environ.get("QIANWEN_API_KEY", QIANWEN_API_KEY)
