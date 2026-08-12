"""
选品流水线入口 — 供 Node.js 后端通过 subprocess 调用
用法: python3 pipeline.py --need "人体工学椅" --budget-min 1000 --budget-max 3000 --platforms jd,tmall --background "久坐8小时"
输出: JSON 到 stdout（前端契约格式）
"""

import argparse
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_PRODUCTS_PER_PLATFORM, MAX_DETAIL_PRODUCTS, BUDGET_TOLERANCE
from models import Product, ProductDetail, Intent
from platforms import get_adapter
from platforms.browser import create_browser, check_login, has_cookies
from llm.intent import parse_intent
from llm.analyzer import recommend


def product_to_frontend(p, detail=None, idx=0):
    pid = chr(ord('a') + idx)
    platform_label = '京东' if p.platform == 'jd' else '天猫'
    result = {
        'id': pid,
        'name': p.title,
        'platform': p.platform,
        'platformLabel': platform_label,
        'price': p.price,
        'spec': '',
        'eta': '预计 2-5 个工作日送达',
        'rating': detail.rating if detail else p.rating,
        'reviewCount': p.review_count,
        'params': {},
        'bestParams': [],
        'reviewQuote': '',
        'reviewCon': '',
        'image': '',
        'reasons': [],
    }
    if detail:
        result['params'] = detail.params
        if detail.review_summary:
            parts = detail.review_summary.split('|')
            result['reviewQuote'] = parts[0].strip() if parts else ''
            result['reviewCon'] = parts[1].strip() if len(parts) > 1 else ''
    return result


async def run_pipeline(need, budget_min, budget_max, platforms, background):
    if not has_cookies():
        return {'error': 'no_cookies', 'message': '请先运行 python3 login.py 登录京东/天猫'}

    user_input = need
    if background:
        user_input += ' ' + background
    if budget_max > 0:
        user_input += f' 预算{int(budget_max)}'

    try:
        intent = await parse_intent(user_input)
        if budget_max > 0:
            intent.budget_max = budget_max
    except Exception as e:
        print(f'[pipeline] intent parse failed: {e}', file=sys.stderr)
        intent = Intent(search_keywords=need, budget_max=budget_max)

    pw, context = await create_browser()
    all_products = []

    try:
        for plat in platforms:
            adapter = get_adapter(plat)
            if not adapter:
                continue
            if not await check_login(context, plat):
                print(f'[pipeline] {plat} not logged in, skip', file=sys.stderr)
                continue
            page = await context.new_page()
            try:
                products = await adapter.search(page, intent.search_keywords, MAX_PRODUCTS_PER_PLATFORM)
                all_products.extend(products)
                print(f'[pipeline] {plat}: found {len(products)}', file=sys.stderr)
            except Exception as e:
                print(f'[pipeline] {plat} search error: {e}', file=sys.stderr)
            finally:
                await page.close()

        if budget_max > 0:
            filtered = [p for p in all_products if budget_min <= p.price <= budget_max * (1 + BUDGET_TOLERANCE)]
        else:
            filtered = all_products
        print(f'[pipeline] budget filter: {len(all_products)} -> {len(filtered)}', file=sys.stderr)

        details = []
        for p in filtered[:MAX_DETAIL_PRODUCTS]:
            adapter = get_adapter(p.platform)
            if not adapter:
                continue
            page = await context.new_page()
            try:
                detail = await adapter.fetch_detail(page, p)
                details.append(detail)
                print(f'[pipeline] detail: {p.title[:20]}... params={len(detail.params)}', file=sys.stderr)
            except Exception as e:
                print(f'[pipeline] detail error: {e}', file=sys.stderr)
                details.append(ProductDetail(product=p))
            finally:
                await page.close()

        recs = await recommend(intent, details, max_recommendations=3)
        print(f'[pipeline] AI recommended: {len(recs)}', file=sys.stderr)

    finally:
        await context.close()
        await pw.stop()

    products = []
    for i, rec in enumerate(recs):
        fp = product_to_frontend(rec.product, rec.detail, i)
        if rec.reason:
            fp['reasons'] = [rec.reason]
        if rec.concerns:
            fp['reviewCon'] = rec.concerns[0] if rec.concerns else ''
        products.append(fp)

    recommended_id = products[0]['id'] if products else 'a'
    all_reasons = []
    if recs and recs[0].reason:
        all_reasons.append(recs[0].reason)
    if background:
        all_reasons.append(f'结合你的背景「{background}」：{recs[0].product.title[:15]} 的参数配置与你的使用场景匹配度最高')

    return {
        'products': products,
        'recommendedId': recommended_id,
        'reasons': all_reasons
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--need', required=True)
    parser.add_argument('--budget-min', type=float, default=0)
    parser.add_argument('--budget-max', type=float, default=99999)
    parser.add_argument('--platforms', default='jd,tmall')
    parser.add_argument('--background', default='')
    args = parser.parse_args()

    env_file = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    if os.path.exists(env_file):
        for line in open(env_file):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

    platforms = [p.strip() for p in args.platforms.split(',') if p.strip()]
    result = asyncio.run(run_pipeline(
        args.need, args.budget_min, args.budget_max, platforms, args.background
    ))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
