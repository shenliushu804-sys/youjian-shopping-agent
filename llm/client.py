"""LLM 统一客户端：本地 Qwen3.5-2B 优先，API 兜底"""

import asyncio
import json

import httpx

from config import (
    LLM_MODE,
    LOCAL_LLM_URL,
    LOCAL_LLM_MODEL,
    QIANWEN_API_KEY,
    QWEN_MODEL,
    QWEN_BASE_URL,
    QWEN_PROXY,
    TIMEOUT_MS,
)


class LLMError(Exception):
    pass


def _chat_local(client: httpx.Client, messages: list, temperature: float, max_tokens: int) -> str:
    resp = client.post(
        f"{LOCAL_LLM_URL}/v1/chat/completions",
        json={
            "model": LOCAL_LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _chat_api(client: httpx.Client, messages: list, temperature: float, max_tokens: int) -> str:
    if not QIANWEN_API_KEY:
        raise LLMError("QIANWEN_API_KEY 未配置")
    resp = client.post(
        f"{QWEN_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {QIANWEN_API_KEY}"},
        json={
            "model": QWEN_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=TIMEOUT_MS / 1000,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def chat(messages: list, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    """统一入口：auto 模式先本地，失败自动切 API"""
    errors = []

    if LLM_MODE in ("auto", "local"):
        try:
            return await asyncio.to_thread(
                _chat_local_sync, messages, temperature, max_tokens
            )
        except Exception as e:
            errors.append(f"local: {e}")
            if LLM_MODE == "local":
                raise LLMError(f"本地 LLM 不可用: {e}\n请先启动: python3 llm/local_server.py")

    if LLM_MODE in ("auto", "api"):
        try:
            return await asyncio.to_thread(
                _chat_api_sync, messages, temperature, max_tokens
            )
        except Exception as e:
            errors.append(f"api: {e}")
            raise LLMError(f"所有 LLM 都不可用: {'; '.join(errors)}")

    raise LLMError(f"LLM_MODE={LLM_MODE} 无效，可选 auto/local/api")


def _chat_local_sync(messages: list, temperature: float, max_tokens: int) -> str:
    with httpx.Client() as client:
        return _chat_local(client, messages, temperature, max_tokens)


def _chat_api_sync(messages: list, temperature: float, max_tokens: int) -> str:
    with httpx.Client(proxy=QWEN_PROXY) as client:
        return _chat_api(client, messages, temperature, max_tokens)


async def chat_json(messages: list, temperature: float = 0.1, max_tokens: int = 2048) -> dict:
    """返回 JSON 对象。本地模型输出非纯 JSON 时自动清洗并重试一次。"""
    content = await chat(messages, temperature, max_tokens)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        import re
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            return json.loads(m.group(0))
        # 重试一次，要求严格 JSON
        messages = messages + [
            {"role": "assistant", "content": content},
            {"role": "user", "content": "请只输出 JSON，不要包含其他文字。"},
        ]
        content2 = await chat(messages, temperature, max_tokens)
        m2 = re.search(r"\{.*\}", content2, re.S)
        if m2:
            return json.loads(m2.group(0))
        raise LLMError(f"LLM 输出不是有效 JSON: {content[:200]}")
