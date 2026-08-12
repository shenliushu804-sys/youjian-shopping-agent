"""天猫/淘宝适配器：搜索 + 详情参数采集 + 下单到支付页（新版淘宝搜索 DOM）"""

from models import Product, ProductDetail
from .base import PlatformAdapter, extract_brand_from_title


class TmallAdapter(PlatformAdapter):
    platform = "tmall"
    search_url = "https://s.taobao.com/search?q={q}"

    async def search(self, page, query: str, max_results: int = 20) -> list[Product]:
        await page.goto(
            self.search_url.format(q=query),
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await page.wait_for_timeout(6000)
        # 滚动触发懒加载
        for _ in range(3):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(1200)

        items = await page.evaluate("""(max) => {
            // 新版淘宝搜索：商品链接卡片
            const links = document.querySelectorAll(
                'a[href*="detail.tmall.com"], a[href*="item.taobao.com"]'
            );
            const out = [];
            const seen = new Set();
            for (const a of links) {
                if (out.length >= max) break;
                // 标题：line-clamp 容器或 14px span
                let titleEl = a.querySelector('div[style*="line-clamp"]');
                if (!titleEl) titleEl = a.querySelector('span[style*="14px"]');
                const title = (titleEl?.textContent || '').trim();
                if (!title || title.length < 8 || seen.has(title)) continue;
                seen.add(title);

                // 价格：取第一个 ¥数字
                const priceEl = a.querySelector('[class*=price]');
                const priceText = (priceEl?.textContent || a.textContent || '');
                let pm = priceText.match(/¥\\s*([0-9]+(?:\\.[0-9]{1,2})?)/);
                let price = pm ? parseFloat(pm[1]) : 0;
                // 价格异常大时，尝试'优惠后'价格
                if (price > 100000) {
                    const m2 = priceText.match(/优惠后¥?\\s*([0-9]+(?:\\.[0-9]{1,2})?)/);
                    if (m2) price = parseFloat(m2[1]);
                }

                // 店铺：优先含'旗舰店/专卖店'的文本
                const shopEl = a.querySelector('[class*=shop], [class*=Shop], [class*=store]');
                let shopName = (shopEl?.textContent || '').trim();
                if (!shopName || !/旗舰店|专卖店|专营店/.test(shopName)) {
                    const m = a.textContent.match(/([\\u4e00-\\u9fa5A-Za-z0-9]{2,20}(?:旗舰店|专卖店|专营店))/);
                    if (m) shopName = m[1];
                }
                if (!shopName) shopName = '淘宝/天猫';

                out.push({
                    title: title,
                    price: price,
                    shop_name: shopName,
                    shop_type: shopName.includes('旗舰店') ? '旗舰店'
                        : shopName.includes('专卖店') || shopName.includes('专营店') ? '专卖店' : '普通店',
                    product_url: a.href,
                    platform: 'tmall',
                    review_count: 0,
                });
            }
            return out;
        }""", max_results)
        return [Product(**i) for i in items]

    async def fetch_detail(self, page, product: Product) -> ProductDetail:
        await page.goto(product.product_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        data = await page.evaluate("""() => {
            const out = { params: {}, brand: '', rating: 0, review_summary: '' };

            // 参数表（天猫常见选择器）
            document.querySelectorAll(
                '#J_AttrUL li, .tb-parameter li, .tm-parameter li, .attributes-list li'
            ).forEach(li => {
                const text = (li.textContent || '').trim();
                const idx = text.indexOf('：');
                if (idx > 0) out.params[text.slice(0, idx).trim()] = text.slice(idx + 1).trim();
            });

            // 品牌（详情页面包屑/标题前缀）
            const brandEl = document.querySelector('#J_DetailMeta .tb-detail-hd a, .tb-breadcrumb a:last-child');
            if (brandEl) out.brand = (brandEl.textContent || '').trim();

            // 评分
            const rateEl = document.querySelector(
                '.tb-rate-summary, .tb-ratings, .score, [class*="rate"]'
            );
            if (rateEl) {
                const m = (rateEl.textContent || '').match(/[0-9]+\\.[0-9]+/);
                if (m) out.rating = parseFloat(m[0]);
            }

            // 评价摘要（累计评价数 + 评论内容，评论内容通常需异步签名接口，先取数量）
            const bodyText = document.body.innerText || '';
            const m = bodyText.match(/评价\\s*[:：]?\\s*([0-9][0-9万+. ]*)/);
            if (m) out.review_summary = '累计评价: ' + m[1].trim();
            const comments = document.querySelectorAll(
                '.tm-rate-content, .rate-content, .comment-content'
            );
            if (comments.length) {
                out.review_summary = Array.from(comments).slice(0, 3)
                    .map(c => (c.textContent || '').trim()).filter(Boolean).join(' | ');
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
        """打开商品页 → 加购 → 购物车勾选 → 结算 → 提交订单 → 收银台"""
        keyword = (product.title or "")[:6]
        if not keyword:
            keyword = "西昊"

        # 1. 详情页选规格 + 加购（最多重试2次）
        added = False
        for attempt in range(2):
            await page.goto(product.product_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(6000)
            # 选规格
            await page.evaluate("""() => {
                const opts = [...document.querySelectorAll('[class*="valueItem"]')].filter(e =>
                    !e.className.includes('disabled') &&
                    e.offsetParent !== null &&
                    !/咨询|客服|推荐官|专属/.test(e.textContent || '')
                );
                if (opts.length) opts[0].click();
            }""").catch(lambda: None)
            await page.wait_for_timeout(1500)
            # 加购
            try:
                btn = page.locator('button:has-text("加入购物车")').first
                if await btn.count():
                    await btn.click(timeout=5000)
                    added = True
            except Exception:
                pass
            await page.wait_for_timeout(3000)
            # 验证加购：购物车含目标商品
            await page.goto("https://cart.taobao.com/cart.htm", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            has = await page.evaluate("(kw) => (document.body.innerText || '').includes(kw)", keyword)
            if has:
                break

        # 2. 购物车勾选目标商品
        picked = False
        for attempt in range(2):
            picked = await page.evaluate("""(kw) => {
                const rows = [...document.querySelectorAll('tr, [class*=item], [class*=row]')];
                for (const r of rows) {
                    if ((r.textContent || '').includes(kw)) {
                        const box = r.querySelector('.ant-checkbox');
                        if (box && !box.className.includes('disabled')) {
                            box.click();
                            return true;
                        }
                    }
                }
                return false;
            }""", keyword)
            if picked:
                break
            await page.wait_for_timeout(3000)
        if not picked:
            raise RuntimeError("购物车未找到目标商品，请检查是否加购成功")
        await page.wait_for_timeout(2000)

        # 3. 结算 → 确认订单页（重试2次）
        confirmed = False
        for attempt in range(2):
            try:
                settle = page.locator('div.btn--QDjHtErD, button:has-text("结算")').first
                if await settle.count():
                    await settle.click(timeout=5000)
                    await page.wait_for_timeout(12000)
                if "confirm_order" in page.url:
                    confirmed = True
                    break
            except Exception:
                pass
            await page.wait_for_timeout(3000)
        if not confirmed:
            raise RuntimeError("结算未跳转确认订单页")
        await page.wait_for_timeout(5000)

        # 确认订单页：点击"立即支付"提交按钮 → 收银台
        submitted = False
        for attempt in range(2):
            try:
                btn = page.locator('[class*="trade-buy-btn-submit"], [class*="SettlementSubmit"]').first
                if await btn.count():
                    # React 合成事件需真实鼠标点击
                    await btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(800)
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.click(
                            box["x"] + box["width"] / 2,
                            box["y"] + box["height"] / 2,
                        )
                    else:
                        await btn.click(timeout=5000)
                else:
                    await page.evaluate("""() => {
                        const el = [...document.querySelectorAll('button, a, div, span')].find(e => {
                            const t = (e.textContent || '').trim();
                            return t.includes('立即支付') && e.offsetParent !== null;
                        });
                        if (el) el.click();
                    }""")
                await page.wait_for_timeout(15000)
                if "cashier" in page.url or "auth" in page.url and "alipay" in page.url:
                    submitted = True
                    break
            except Exception:
                pass
            await page.wait_for_timeout(3000)

        if not submitted:
            raise RuntimeError("提交订单失败，请手动在确认订单页完成")
        return page.url
