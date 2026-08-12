"""登录工具：打开 Chromium 让用户扫码登录京东/天猫，保存 Cookie

用法: python3 login.py [jd|tmall|all]
登录完成后自动检测并保存 Cookie
"""

import asyncio
import sys

from platforms.browser import create_browser, save_session_cookies, has_cookies
from platforms.browser import check_login


LOGIN_URLS = {
    "jd": "https://passport.jd.com/new/login.aspx",
    "tmall": "https://login.taobao.com/member/login.jhtml",
}


async def main():
    targets = sys.argv[1] if len(sys.argv) > 1 else "all"
    platforms = ["jd", "tmall"] if targets == "all" else [targets]

    pw, context = await create_browser()
    print("=" * 50)
    print("请在打开的浏览器窗口中完成登录")
    print("目标平台: " + ", ".join(platforms))
    print("扫码/登录完成后会自动检测并保存，无需操作")
    print("=" * 50)

    try:
        # 打开登录页
        for p in platforms:
            if p not in LOGIN_URLS:
                continue
            page = await context.new_page()
            await page.goto(LOGIN_URLS[p], wait_until="domcontentloaded", timeout=30000)
            print(f"已打开 {p} 登录页，请扫码/输入登录...")

        # 轮询检测登录完成（最多 10 分钟）
        logged_in = {}
        for i in range(120):
            for p in platforms:
                if p in logged_in:
                    continue
                if await check_login(context, p):
                    logged_in[p] = True
                    print(f"✅ {p} 已登录")
            if len(logged_in) == len(platforms):
                break
            await asyncio.sleep(5)

        if not logged_in:
            print("⏰ 超时未检测到登录，请重试")
            return

        await save_session_cookies(context)
        cookie_count = len(await context.cookies())
        print(f"✅ Cookie 已保存（{cookie_count} 个）")
        print("现在可以运行: python3 main.py \"商品需求 场景 预算\"")
    finally:
        await context.close()
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
