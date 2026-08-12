"""对比推荐：基于真实采集数据，输出 Top 2-3 推荐 + 理由"""

import json

from llm.client import chat_json
from models import Intent, ProductDetail, Recommendation


SYSTEM_PROMPT = """你是购物决策专家。基于用户场景和候选商品的真实数据，推荐最合适的商品。

输出严格 JSON：
{
  "recommendations": [
    {
      "index": 0,
      "title": "候选商品完整标题（必须与提供的商品数据完全一致）",
      "score": 0.0,
      "reason": "推荐理由（必须引用该商品的具体参数/价格/评价/品牌，不得编造）",
      "concerns": ["需要注意的点"]
    }
  ]
}

规则：
- 必须输出 2-3 个推荐（按综合评分从高到低排列），除非候选商品不足 2 个
- 只允许使用提供的商品数据，缺失参数写"未获取"，禁止编造任何参数或评价
- 用户预算为硬约束，超预算直接淘汰
- 优先旗舰店/官方店，但参数匹配度优先于店铺类型
- 综合评分 0-100，参数匹配 > 价格 > 评价口碑 > 品牌
"""


def _build_user_prompt(intent: Intent, details: list[ProductDetail]) -> str:
    products_json = json.dumps(
        [d.to_dict() for d in details],
        ensure_ascii=False,
    )
    return f"""用户需求：{intent.scenario}
搜索关键词：{intent.search_keywords}
关键参数：{json.dumps(intent.critical_params, ensure_ascii=False)}
预算上限：{intent.budget_max}

候选商品真实数据（JSON）：
{products_json}

请输出推荐（只基于以上真实数据）。"""


async def recommend(intent: Intent, details: list[ProductDetail], max_recommendations: int = 3) -> list[Recommendation]:
    if not details:
        return []

    # 预算硬约束过滤（本地小模型可能不稳定，先用规则保证）
    if intent.budget_max > 0:
        budget = intent.budget_max * 1.20
        details = [d for d in details if d.price <= budget or d.price == 0]

    if not details:
        return []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(intent, details)},
    ]
    data = await chat_json(messages, temperature=0.1, max_tokens=2048)

    recs = []
    raw_list = data.get("recommendations", [])[:max_recommendations]
    for r in raw_list:
        # 优先用标题精确匹配，避免 index 错位
        matched = None
        title = str(r.get("title", "")).strip()
        if title:
            for d in details:
                if d.product.title.strip() == title:
                    matched = d
                    break
        if matched is None:
            try:
                idx = int(r.get("index", 0))
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(details):
                continue
            matched = details[idx]
        d = matched
        recs.append(Recommendation(
            product=d.product,
            detail=d,
            score=float(r.get("score", 0)),
            reason=str(r.get("reason", "")),
            concerns=[str(c) for c in r.get("concerns", [])],
        ))
    return recs
