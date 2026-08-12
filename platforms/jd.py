"""京东适配器：搜索 + 详情参数采集 + 下单到支付页（新版 DOM）"""

from urllib.parse import urljoin

from models import Product, ProductDetail
from .base import PlatformAdapter, extract_brand_from_title


class JDAdapter(PlatformAdapter):
    platform = "jd"
    search_url = "https://search.jd.com/Search?keyword={q}&enc=utf-8"

    async def search(self, page, query: str, max_results: int = 20) -> list[Product]:
        items = []
        for attempt in range(2):
            await page.goto(
                self.search_url.format(q=query),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await page.wait_for_timeout(6000)
            # 滚动触发懒加载
            for _ in range(4):
                await page.mouse.wheel(0, 1800)
                await page.wait_for_timeout(1000)

            items = await page.evaluate("""(max) => {
            const cards = document.querySelectorAll('[data-sku]');
            const out = [];
            for (const el of cards) {
                if (out.length >= max) break;
                const titleEl = el.querySelector('[class*=title], [class*=Title]');
                let title = (titleEl?.textContent || '').trim();
                if (!title) continue;
                // 标题文本可能带"京东自营"，保留原文
                const priceEl = el.querySelector('[class*=price], [class*=Price]');
                const price = parseFloat((priceEl?.textContent || '').replace(/[^0-9.]/g, '')) || 0;
                const sku = el.getAttribute('data-sku');
                const shopEl = el.querySelector('[class*=shop], [class*=Shop], [class*=store]');
                let shopName = (shopEl?.textContent || '').trim();
                if (!shopName && title.includes('京东自营')) shopName = '京东自营';
                if (!shopName) shopName = '京东';
                out.push({
                    title: title,
                    price: price,
                    shop_name: shopName,
                    shop_type: shopName.includes('旗舰店') ? '旗舰店'
                        : shopName.includes('专卖店') || shopName.includes('专营店') ? '专卖店' : '普通店',
                    product_url: sku ? `https://item.jd.com/${sku}.html` : (titleEl?.closest('a')?.href || ''),
                    platform: 'jd',
                    review_count: 0,
                });
            }
            return out;
        }""", max_results)
            if items:
                break
            await page.wait_for_timeout(2000)
        return [Product(**i) for i in items]

    async def fetch_detail(self, page, product: Product) -> ProductDetail:
        for attempt in range(2):
            await page.goto(product.product_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(7000)
            # 检测频控页（验证码/访问频繁）
            blocked = await page.evaluate("""() => {
                const t = (document.body.innerText || '') + ' ' + location.href;
                return /验证|验证码|访问过于频繁|访问频繁|滑动验证|captcha/i.test(t);
            }""")
            if not blocked:
                break
            print(f"  [jd] 详情页触发频控，重试...")
            await page.wait_for_timeout(8000)

        # 尝试点击"规格参数"缩略图，触发参数渲染
        try:
            await page.evaluate("""() => {
                const el = [...document.querySelectorAll('div.parameter')].find(e =>
                    (e.textContent || '').trim() === '规格参数'
                );
                if (el) el.click();
            }""")
        except Exception:
            pass
        await page.wait_for_timeout(3000)

        data = await page.evaluate("""() => {
            const out = { params: {}, brand: '', rating: 0, review_summary: '' };

            // 新版速览参数：值(.title.text-ellipsis) + 名称(下一个 .desc)
            document.querySelectorAll('div.item .title.text-ellipsis').forEach(el => {
                const nameEl = el.nextElementSibling;
                if (nameEl && nameEl.classList.contains('desc')) {
                    const name = (nameEl.textContent || '').trim();
                    const value = (el.textContent || '').trim();
                    if (name && value) out.params[name] = value;
                }
            });

            // 传统参数表兜底
            document.querySelectorAll('.parameter2 li, .p-parameter li').forEach(li => {
                const text = (li.textContent || '').trim();
                const idx = text.indexOf('：');
                if (idx > 0 && !out.params[text.slice(0, idx).trim()]) {
                    out.params[text.slice(0, idx).trim()] = text.slice(idx + 1).trim();
                }
            });

            // 品牌
            if (out.params['品牌']) {
                out.brand = out.params['品牌'];
            } else {
                const brandEl = document.querySelector('#parameter-brand li, .p-parameter li:first-child, .crumb a:last-child');
                if (brandEl) {
                    out.brand = (brandEl.textContent || '').trim().replace(/^品牌[:：]/, '');
                    // 过滤面包屑噪音（如"家具"）
                    if (['家具', '电脑椅', '椅类'].includes(out.brand)) out.brand = '';
                }
            }

            // 评分
            const rateEl = document.querySelector('.score, .comment-count, .rate');
            if (rateEl) {
                const m = (rateEl.textContent || '').match(/[0-9]+\\.[0-9]+/);
                if (m) out.rating = parseFloat(m[0]);
            }

            // 评价摘要（累计评价 + 前几条评论）
            const bodyText = document.body.innerText || '';
            const m = bodyText.match(/累计评价\\s*[:：]?\\s*([0-9][0-9万+. ]*)/);
            if (m) out.review_summary = '累计评价: ' + m[1].trim();
            const comments = document.querySelectorAll(
                '.comment-item .comment-content, .comment-item .short-comment, .J-comment-content, [class*=comment-content]'
            );
            if (comments.length) {
                const texts = Array.from(comments).slice(0, 3)
                    .map(c => (c.textContent || '').trim()).filter(Boolean);
                if (texts.length) {
                    out.review_summary = (out.review_summary ? out.review_summary + ' | ' : '') + texts.join(' | ');
                }
            }
            return out;
        }""")

        missing = []
        if not data["params"]:
            missing.append("参数表")
        if not data["brand"]:
            data["brand"] = extract_brand_from_title(product.title)
        if not data["brand"]:
            missing.append("品牌")
        if not data["review_summary"]:
            missing.append("评价摘要")

        return ProductDetail(
            product=product,
            params=data["params"],
            brand=data["brand"],
            rating=data["rating"],
            review_summary=data["review_summary"],
            price=product.price,
            missing_params=missing,
        )

    async def prepare_order(self, page, product: Product) -> str:
        """打开商品页 → 加购 → 结算页 → 提交订单 → 收银台（停在确认支付）"""
        for attempt in range(2):
            await page.goto(product.product_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            blocked = await page.evaluate("""() => {
                const t = (document.body.innerText || '') + ' ' + location.href;
                return /验证码|访问过于频繁|captcha/i.test(t);
            }""")
            if not blocked:
                break
            await page.wait_for_timeout(8000)

        # 检测是否被频控（URL 含 pf.jd.com 或页面内容异常）
        is_blocked = "pf.jd.com" in page.url
        if not is_blocked:
            is_blocked = await page.evaluate("""() => {
                const t = (document.body.innerText || '') + ' ' + location.href;
                return /验证码|访问过于频繁|captcha/i.test(t);
            }""")

        added = False
        if is_blocked:
            # 频控：跳过商品页，直接用购物车 API 加购
            import re
            m = re.search(r'(\d{6,})', product.product_url)
            if m:
                pid = m.group(1)
                await page.goto(f"https://cart.jd.com/gate.action?pid={pid}&pcount=1&ptype=1",
                                wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)
                added = True
        else:
            # 正常流程：商品页点加购按钮
            for sel in ["#add-to-cart", "#InitCartUrl", ".btn-addtocart", "#button-cart", ".add-cart"]:
                btn = page.locator(sel).first
                if await btn.count():
                    try:
                        await btn.click(timeout=5000)
                        added = True
                        break
                    except Exception:
                        continue

        if not added:
            # 最终兜底：尝试购物车 API
            import re
            m = re.search(r'(\d{6,})', product.product_url)
            if m:
                pid = m.group(1)
                await page.goto(f"https://cart.jd.com/gate.action?pid={pid}&pcount=1&ptype=1",
                                wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)
                added = True
        if not added:
            raise RuntimeError("未找到京东加购按钮，请手动加购")

        # 直接打开结算页（商品已在购物车，默认地址自动选中）
        if "trade.jd.com" not in page.url and "cart.jd.com" not in page.url:
            try:
                await page.goto("https://trade.jd.com/shopping/order/getOrderInfo.action",
                                wait_until="domcontentloaded", timeout=20000)
            except Exception:
                pass
        await page.wait_for_timeout(5000)

        # 点击"提交订单"，跳转收银台（支付确认页，不点支付）
        submitted = False
        for attempt in range(2):
            try:
                # 新版结算页提交按钮 .payment-action-submit，文本匹配兜底
                btn = page.locator(".payment-action-submit").first
                if await btn.count():
                    # React 合成事件需真实鼠标点击
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    else:
                        await btn.click(timeout=5000)
                else:
                    await page.evaluate("""() => {
                        const el = [...document.querySelectorAll('button, a, div, span')].find(e => {
                            const t = (e.textContent || '').trim();
                            return t === '提交订单' && e.offsetParent !== null;
                        });
                        if (el) el.click();
                    }""")
                await page.wait_for_timeout(6000)
                if "cashier" in page.url or "pay.jd.com" in page.url or "trade.jd.com" in page.url:
                    submitted = True
                    break
            except Exception:
                pass
            await page.wait_for_timeout(3000)

        if not submitted:
            raise RuntimeError("提交订单失败，请手动在结算页完成")
        return page.url
