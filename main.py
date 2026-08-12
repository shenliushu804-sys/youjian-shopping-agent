"""购物决策代理 CLI 主流程

用法: python3 main.py "人体工学椅 腰椎间盘突出 预算1000"
"""

import asyncio
import random
import sys

from config import (
    PLATFORMS,
    MAX_PRODUCTS_PER_PLATFORM,
    MAX_DETAIL_PRODUCTS,
    BUDGET_TOLERANCE,
)
from llm.intent import parse_intent
from llm.analyzer import recommend
from models import Product
from platforms import get_adapter
from platforms.browser import create_browser, save_session_cookies, has_cookies, check_login


def _fmt_price(p):
    return f"¥{p:.2f}" if p else "价格未获取"


def _print_product(i, p: Product):
    shop = p.shop_name or "未知店铺"
    print(f"  [{i}] {p.title}")
    print(f"      {_fmt_price(p.price)} | {shop} | 评价 {p.review_count or '未知'}")
    print(f"      {p.product_url}")


async def run(user_input: str):
    if not has_cookies():
        print("⚠️  未找到登录 Cookie，请先运行: python3 login.py")
        return

    print("\n[1/5] 解析购物需求...")
    intent = await parse_intent(user_input)
    print(f"  搜索关键词: {intent.search_keywords}")
    if intent.critical_params:
        print(f"  关键参数: {', '.join(intent.critical_params)}")
    if intent.budget_max:
        print(f"  预算上限: ¥{intent.budget_max}")

    pw, context = await create_browser()
    try:
        print("\n[2/5] 检索商品...")
        all_products: list[Product] = []
        for platform in PLATFORMS:
            adapter = get_adapter(platform)
            if not adapter:
                continue
            if not await check_login(context, platform):
                print(f"  [{platform}] 未登录或登录失效，跳过")
                continue
            page = await context.new_page()
            try:
                products = await adapter.search(page, intent.search_keywords, MAX_PRODUCTS_PER_PLATFORM)
                print(f"  [{platform}] 找到 {len(products)} 个商品")
                all_products.extend(products)
            except Exception as e:
                print(f"  [{platform}] 搜索失败: {str(e)[:80]}")
            finally:
                await page.close()

        if not all_products:
            print("\n❌ 未检索到商品，请检查登录态或稍后重试")
            return

        # 预算预过滤
        if intent.budget_max > 0:
            limit = intent.budget_max * (1 + BUDGET_TOLERANCE)
            before = len(all_products)
            all_products = [p for p in all_products if p.price <= limit or p.price == 0]
            print(f"\n  预算过滤: {before} → {len(all_products)} 个（上限 ¥{limit:.0f}）")

        print(f"\n[3/5] 采集详情参数（Top {MAX_DETAIL_PRODUCTS}）...")
        top = all_products[:MAX_DETAIL_PRODUCTS]
        details = []
        for i, p in enumerate(top, 1):
            # 降低访问频率，避免平台频控
            await asyncio.sleep(random.uniform(2.0, 4.0))
            adapter = get_adapter(p.platform)
            page = await context.new_page()
            try:
                detail = await adapter.fetch_detail(page, p)
                details.append(detail)
                missing = f"（缺: {', '.join(detail.missing_params)}）" if detail.missing_params else ""
                print(f"  {i}/{len(top)} {p.title[:30]}... {missing}")
            except Exception as e:
                print(f"  {i}/{len(top)} {p.title[:30]}... 详情失败: {str(e)[:60]}")
            finally:
                await page.close()

        if not details:
            print("\n❌ 详情采集失败，无法推荐")
            return

        print("\n[4/5] LLM 对比分析...")
        recommendations = await recommend(intent, details)
        if not recommendations:
            print("⚠️  未生成推荐，请尝试更换关键词")
            return

        print("\n" + "=" * 60)
        print("推荐结果")
        print("=" * 60)
        for i, r in enumerate(recommendations, 1):
            print(f"\n推荐 #{i} | 评分 {r.score:.0f}/100")
            print(f"  {r.product.title}")
            print(f"  {_fmt_price(r.product.price)} | {r.product.shop_name}")
            print(f"  理由: {r.reason}")
            if r.concerns:
                print(f"  注意: {'；'.join(r.concerns)}")
            print(f"  链接: {r.product.product_url}")

        print("\n" + "=" * 60)
        choice = ""
        try:
            choice = input("\n输入要购买的商品编号（1-3），或直接回车跳过下单: ").strip()
        except EOFError:
            print("\n非交互模式：跳过下单")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(recommendations):
                target = recommendations[idx].product
                print(f"\n[5/5] 开始下单: {target.title}")
                adapter = get_adapter(target.platform)
                page = await context.new_page()
                try:
                    payment_url = await adapter.prepare_order(page, target)
                    print(f"✅ 已跳转到结算页: {payment_url}")
                    print("请在浏览器中确认支付（不会自动支付）")
                except Exception as e:
                    print(f"❌ 下单失败: {str(e)[:100]}")
                    print("请手动打开商品页购买:")
                    print(f"  {target.product_url}")
                finally:
                    await page.close()
    finally:
        await save_session_cookies(context)
        await context.close()
        await pw.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 main.py \"商品需求 使用场景 预算\"")
        sys.exit(1)
    asyncio.run(run(" ".join(sys.argv[1:])))
