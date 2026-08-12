"""意图解析：把用户购物需求转为搜索关键词 + 关键参数 + 预算"""

from llm.client import chat_json
from models import Intent


SYSTEM_PROMPT = """你是购物决策助手的意图解析器。根据用户描述，输出严格 JSON：
{
  "search_keywords": "用于电商搜索的关键词",
  "critical_params": ["关键参数1", "关键参数2"],
  "budget_max": 0,
  "scenario": "用户使用场景一句话总结"
}

要求：
- search_keywords 简洁，适合京东/天猫搜索（如"人体工学椅"）
- critical_params 从使用场景推导，如腰椎间盘突出→["腰椎支撑","高背","透气网布"]
- budget_max 从用户预算中提取，没有则为 0
- 非具体需求（如相亲伴手礼）也要给出合理的 search_keywords 和参数方向
"""


async def parse_intent(user_input: str) -> Intent:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    data = await chat_json(messages, temperature=0.1, max_tokens=800)

    # 本地小模型输出字段可能不完整，做兜底
    return Intent(
        search_keywords=str(data.get("search_keywords") or user_input.split()[0] if user_input else ""),
        critical_params=[str(x) for x in data.get("critical_params", [])],
        budget_max=float(data.get("budget_max") or 0),
        scenario=str(data.get("scenario") or ""),
    )
