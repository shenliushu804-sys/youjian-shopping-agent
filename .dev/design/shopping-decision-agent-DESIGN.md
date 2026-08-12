# 技术方案: 购物决策代理 Agent

## 元数据

| 字段 | 内容 |
|------|------|
| 关联 PRD | [shopping-decision-agent-PRD.md](../prd/shopping-decision-agent-PRD.md) |
| 版本 | v1.0 |
| 创建日期 | 2026-08-01 |
| 状态 | 草案 |

## 1. 技术选型

| 决策 | 选择 | 理由 | 备选方案 |
|------|------|------|----------|
| 开发语言 | Python 3.14 | 已安装 Playwright/Qwen SDK 生态，脚本与后端统一 | Node.js |
| 浏览器自动化 | Python Playwright 1.60 | 以本机无沙箱权限运行；自带 Chromium，Cookie 可持久化 | Selenium / requests 直连 |
| 登录态管理 | 独立 Chromium profile + Cookie JSON | 不依赖用户真实 Chrome，避免 profile 锁/调试端口问题；Cookie 明文 JSON 可跨会话复用 | Chrome CDP / 真实 profile |
| LLM | 本地 Qwen3.5-2B（MLX）优先 + Qwen API（qwen-turbo）兜底 | 本地模型 0 成本，已部署可用（mlx 0.31.2 + mlx_vlm）；复杂推理/效果不足时自动切 API | DeepSeek / GPT |
| 本地推理服务 | mlx_vlm + Qwen3.5-2B（OpenAI 兼容 HTTP 接口） | 复用已有本地部署（4.5GB 模型），避免重复部署 | llama.cpp / Ollama |
| 数据存储 | SQLite（可选，V1 暂不强制） | 轻量本地，历史记录后续加 | JSON 文件 |
| 交互形态 | CLI + Agent 对话 | V1 快速验证核心流程；服务层预留 API 接口 | Web 前端（二期） |

## 2. 架构设计

### 2.1 整体流程

```
用户输入（商品 + 场景 + 预算）
        ↓
   ┌─────────────────┐
   │  intent.py      │  Qwen 意图解析 → 搜索词 + 关键参数 + 预算约束
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  searcher.py    │  Playwright 检索（京东 + 天猫）→ 候选商品列表
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  detail.py      │  进详情页采集 → 参数/价格/评价/品牌口碑
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  analyzer.py    │  Qwen 对比分析 → 推荐 Top 2-3 + 理由
   └────────┬────────┘
            ↓
   ┌─────────────────┐
   │  order.py       │  用户确认 → 加购 → 跳转支付页（人工确认支付）
   └─────────────────┘
```

### 2.2 模块划分

```
my-shopping/
├── main.py               # CLI 入口 + 全流程编排
├── login.py              # 一次运行：打开 Chromium 扫码登录 → 保存 Cookie
├── config.py             # 配置（平台、预算、路径、Qwen Key）
├── models.py             # 数据模型（Product / ProductDetail / Recommendation）
   ├── llm/
   │   ├── __init__.py
   │   ├── client.py         # LLM 统一客户端（local/api/auto 三模式，OpenAI 兼容）
   │   ├── local_server.py   # 本地 Qwen3.5-2B 推理服务（mlx_vlm，127.0.0.1:8001）
   │   ├── intent.py         # 意图解析（本地优先，API 兜底）
   │   └── analyzer.py       # 对比推荐（本地优先，API 兜底）
├── platforms/
│   ├── __init__.py
│   ├── base.py           # 平台适配器抽象基类
│   ├── jd.py             # 京东适配器（搜索 + 详情 + 下单）
│   ├── tmall.py          # 天猫适配器（搜索 + 详情 + 下单）
│   └── browser.py        # Playwright 浏览器管理（Cookie 加载/保存/复用）
├── data/
│   └── cookies.json      # 登录态（login.py 生成）
└── requirements.txt
```

### 2.3 平台适配器接口

```python
class PlatformAdapter(ABC):
    platform: str  # "jd" / "tmall"

    @abstractmethod
    async def search(self, query: str, max_results: int = 20) -> list[Product]:
        """平台搜索，返回候选商品"""

    @abstractmethod
    async def fetch_detail(self, product: Product) -> ProductDetail:
        """读取商品详情页参数/评价/品牌信息"""

    @abstractmethod
    async def prepare_order(self, product: Product) -> str:
        """加购并跳转结算，返回支付页 URL（不自动支付）"""
```

## 3. 数据模型

```python
class Product:
    title: str
    price: float
    shop_name: str
    shop_type: str          # 旗舰店/专卖店/普通店
    product_url: str
    platform: str           # jd / tmall
    review_count: int = 0
    rating: float = 0.0

class ProductDetail:
    product: Product
    params: dict[str, str]  # 详情页参数表，如 {"椅背类型": "高背", "材质": "网布"}
    brand: str
    rating: float
    review_summary: str     # 评价口碑摘要
    price: float
    missing_params: list[str]  # 未获取到的关键参数

class Recommendation:
    product: Product
    detail: ProductDetail
    score: float            # 综合评分
    reason: str             # 推荐理由（必须引用真实参数/价格/评价）
    concerns: list[str]     # 需要注意的点
```

## 4. API 定义（预留，V1 为 CLI）

### 4.1 接口定义

```
POST /api/v1/request
Request:  { "query": "人体工学椅 预算1000 腰椎间盘突出", "platforms": ["jd", "tmall"] }
Response: { "intent": {...}, "products": [...], "recommendations": [...], "status": "awaiting_confirm" }

POST /api/v1/confirm
Request:  { "product_url": "...", "platform": "jd" }
Response: { "payment_url": "...", "status": "payment_pending" }
```

### 4.2 错误码

| 状态码 | 场景 | 说明 |
|--------|------|------|
| 200 | 成功 | |
| 400 | 参数错误 | 缺少必要字段 |
| 401 | 登录失效 | Cookie 过期，需重新运行 login.py |
| 404 | 商品失效 | 商品下架或链接无效 |
| 429 | 频率限制 | 平台反爬，稍后重试 |

## 5. 关键实现路径

### 5.1 核心流程

```
1. 用户输入需求 → intent.py 调 Qwen 解析
   → 输出: search_keywords, critical_params, budget_max, scenario
2. searcher.py 用 Cookie 启动浏览器，对每个平台搜索
   → 过滤掉超预算商品 → 取 Top N
3. detail.py 对候选商品逐个进详情页
   → 采集参数表、价格、评价摘要、品牌
   → 缺失参数标注"未获取"
4. analyzer.py 把真实采集数据 + 用户场景交给 Qwen
   → 输出 Top 2-3 推荐，理由必须引用具体参数
5. 用户确认 → order.py 打开商品页 → 加购 → 跳结算 → 停在支付页
```

### 5.2 LLM 调用策略

```
llm/client.py (统一入口)
  mode = "auto"（默认）
    ├── 尝试本地: http://127.0.0.1:8001/v1/chat/completions (Qwen3.5-2B)
    ├── 本地不可用/超时/JSON 解析失败 → 自动切 API
    └── API: Qwen qwen-turbo (dashscope)
```

- 本地服务 `llm/local_server.py`：用 mlx_vlm 加载 Qwen3.5-2B，暴露 OpenAI 兼容 `/v1/chat/completions`
- 轻量任务（意图解析、简单分类）优先本地，省 API 消耗
- 复杂任务（多商品对比、深度推荐理由）如本地效果不足，自动走 API
- 可在 config 中通过 `LLM_MODE=local|api|auto` 手动指定

### 5.3 技术难点与方案

| 难点 | 解决方案 |
|------|----------|
| 平台登录态获取 | `login.py` 打开独立 Chromium，用户扫码登录一次，Cookie 存 JSON；过期检测后提示重新登录 |
| 平台反爬/验证码 | 真实浏览器 + 真实登录态 + 低频操作；遇验证码暂停并提示用户处理 |
| 详情页参数解析 | 各平台 DOM 不同，封装在 adapter 内；用通用规则（参数表 `ul/li` 结构）+ 平台兜底 |
| LLM 编造参数 | prompt 明确"只能使用提供的 JSON 数据，缺失标未获取"；推荐逻辑做参数存在性校验 |
| Cookie 跨会话失效 | 启动时访问平台首页探测登录态，失败则提示重跑 login.py |

## 6. 风险与回退方案

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| 平台改版导致选择器失效 | 高 | 中 | adapter 隔离，单平台失败不影响另一平台 |
| Cookie 过期/被封 | 中 | 高 | 检测失效自动提示；重新 login.py |
| 下单流程平台限制（风控） | 中 | 高 | V1 只到支付页；失败提示手动下单 |
| LLM 推荐不可靠 | 中 | 高 | 只允许基于真实采集数据推理；结果需用户确认才下单 |
| 详情参数采集不全 | 高 | 中 | 缺失标"未获取"，推荐时降权处理 |

## 7. 测试策略

- 单元测试：intent 解析、预算过滤、推荐 prompt 组装
- 集成测试：`login.py` → `main.py` 全流程跑通（真实平台）
- 手动测试场景：
  1. 具体品类需求（人体工学椅）→ 检索 → 对比 → 推荐 → 下单到支付页
  2. 非具体需求（相亲伴手礼）→ 场景理解 → 推荐
  3. Cookie 过期 → 提示重新登录
  4. 商品下架 → 给出备选

## 8. 部署注意事项

- V1 本地运行：`python3 login.py`（一次性）+ `python3 main.py "需求"` 
- 无需数据库迁移；Cookie 文件属于敏感数据，加入 `.gitignore`
- 回滚方案：平台 adapter 独立，回滚单一平台不影响整体
