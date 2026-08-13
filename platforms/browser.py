"""Playwright 浏览器管理：Cookie 加载/保存/复用、登录态探测"""

import json
from pathlib import Path

from playwright.async_api import async_playwright

from config import COOKIE_FILE, PROXY, HEADLESS, DATA_DIR


def load_cookies() -> list:
    if COOKIE_FILE.exists():
        return json.loads(COOKIE_FILE.read_text())
    return []


def save_cookies(cookies: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    COOKIE_FILE.chmod(0o600)


def has_cookies() -> bool:
    return bool(load_cookies())


async def create_browser():
    """启动 Chromium（持久化 profile），加载已有 Cookie"""
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=str(DATA_DIR / "chromium_profile"),
        headless=HEADLESS,
        args=["--disable-blink-features=AutomationControlled"],
        proxy={"server": PROXY} if PROXY else None,
    )
    cookies = load_cookies()
    if cookies:
        await context.add_cookies(cookies)
    return pw, context


async def check_login(context, platform: str) -> bool:
    """通过 Cookie 检测登录态（不访问页面，避免触发跳转/刷新）"""
    cookies = await context.cookies()
    names = {c["name"] for c in cookies}
    if platform == "jd":
        # 京东登录关键 Cookie
        return bool(names & {"pt_key", "pt_pin", "thor"})
    if platform == "tmall":
        # 淘宝/天猫登录关键 Cookie
        return bool(names & {"cookie2", "_tb_token_"}) and bool(names & {"unb", "uc1", "lgc"})
    return False


async def save_session_cookies(context):
    """把当前浏览器上下文里的 Cookie 保存到文件"""
    cookies = await context.cookies()
    save_cookies(cookies)
