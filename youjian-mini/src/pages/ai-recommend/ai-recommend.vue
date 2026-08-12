<template>
  <view class="page">
    <TopBar title="AI 推荐" sub="综合最优选择" @back="goBack" />
    <view class="scroll">
      <view class="card rec-hero">
        <view class="rec-badge"><text class="rec-badge-text">AI 推荐</text></view>
        <view class="rec-main">
          <view class="rec-thumb"><text class="rec-thumb-icon">🪑</text></view>
          <view class="rec-info">
            <PlatformBadge :platform="current.platform" />
            <text class="rec-name">{{ current.name }}</text>
            <text class="rec-price num">{{ formatPrice(current.price) }}</text>
            <text class="rec-sub">{{ current.sub || ratingText }}</text>
          </view>
        </view>
      </view>

      <view class="card reason-box">
        <text class="card-title">为什么推荐它</text>
        <view class="reason-list">
          <view v-for="(r, i) in allReasons" :key="i" class="reason-item">
            <view class="reason-dot"></view>
            <text class="reason-text">{{ r }}</text>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="card-title">切换备选</text>
        <view class="alt-list">
          <view v-for="p in products" :key="p.id" :class="['alt-item', picked === p.id ? 'on' : '']" @tap="switchPick(p.id)">
            <text class="alt-label">{{ p.id === 'a' ? '首选' : p.id === 'b' ? '备选 B' : '备选 C' }}</text>
            <text class="alt-name">{{ p.name }}</text>
            <text class="alt-price num">{{ formatPrice(p.price) }}</text>
          </view>
        </view>
      </view>
    </view>
    <view class="cta-bar safe-bottom">
      <BtnPrimary :label="'确认下单 · ' + formatPrice(current.price)" @tap="goCheckout" />
    </view>
  </view>
</template>

<script>
import { PRODUCTS, formatPrice, shortNote } from '../../utils/constants'
import { getState, setState } from '../../utils/store'
import TopBar from '../../components/TopBar.vue'
import BtnPrimary from '../../components/BtnPrimary.vue'
import PlatformBadge from '../../components/PlatformBadge.vue'

const BG_REASONS = {
  a: (note) => note ? `结合你的背景：针对「${note}」，双向可调腰托与透气网布正对应，椅身紧凑不挑空间` : '结合常见久坐场景：双向可调腰托与透气网布够用，椅身紧凑不挑空间',
  b: (note) => note ? `结合你的背景：悬浮腰托动态贴合，对「${note}」这类诉求更友好，长时间久坐更省力` : '结合常见久坐场景：悬浮腰托动态贴合，长时间久坐更省力',
  c: (note) => note ? `结合你的背景：支撑与调节上限最高，应对「${note}」更从容，但价格贴近预算上限` : '支撑与调节上限最高，长期耐用性最好，但价格贴近预算上限'
}

export default {
  components: { TopBar, BtnPrimary, PlatformBadge },
  data() {
    const s = getState()
    // 从 store 获取 API 返回的 products 或用本地
    const products = s.products || [PRODUCTS.a, PRODUCTS.b, PRODUCTS.c]
    return {
      products,
      picked: s.picked || s.recommendedId || 'a',
      state: s
    }
  },
  computed: {
    current() {
      return this.products.find(p => p.id === this.picked) || this.products[0]
    },
    ratingText() {
      const p = this.current
      return `好评率 ${p.rating}% · 质保 ${p.params?.['质保'] || '—'}`
    },
    allReasons() {
      const p = this.current
      const bg = shortNote(this.state.background)
      const reasons = [...(p.reasons || [])]
      const bgFn = BG_REASONS[this.picked]
      if (bgFn) reasons.push(bgFn(bg))
      return reasons
    }
  },
  methods: {
    formatPrice,
    switchPick(key) { this.picked = key; setState({ picked: key }) },
    goBack() { uni.navigateBack() },
    goCheckout() {
      setState({ picked: this.picked })
      uni.navigateTo({ url: '/pages/checkout/checkout' })
    }
  }
}
</script>

<style lang="scss" scoped>
.page { background: $bg; padding-bottom: 80px; }
.scroll { width: 100%; padding: 0 $page-margin 20px; }
.card { background: $surface; border: 1px solid $border-soft; border-radius: $radius-l; padding: $pad; margin-bottom: $gap; }
.card-title { font-size: $fs-small; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 12px; color: $fg; }
.rec-hero { position: relative; border-color: $primary-soft; }
.rec-badge { position: absolute; top: -10px; left: 16px; background: $primary; padding: 3px 12px; border-radius: 999px; }
.rec-badge-text { color: #fff; font-size: 10.5px; font-weight: 600; letter-spacing: 0.03em; }
.rec-main { display: flex; gap: 16px; align-items: flex-start; padding-top: 8px; }
.rec-thumb { width: 72px; height: 72px; border-radius: $radius; background: $fg-soft; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rec-thumb-icon { font-size: 32px; }
.rec-info { flex: 1; min-width: 0; }
.rec-name { display: block; font-size: $fs-h2; font-weight: 600; line-height: 1.3; margin: 6px 0 4px; }
.rec-price { font-size: 20px; font-weight: 700; }
.rec-sub { display: block; font-size: $fs-meta; color: $muted; margin-top: 4px; }
.reason-box { background: $primary-soft; border-color: $primary-soft; }
.reason-item { display: flex; gap: 10px; padding: 6px 0; align-items: flex-start; }
.reason-dot { width: 6px; height: 6px; border-radius: 999px; background: $primary; flex-shrink: 0; margin-top: 7px; }
.reason-text { font-size: $fs-body; color: $fg; line-height: 1.5; }
.alt-list { }
.alt-item { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid $border-soft; &:last-child { border-bottom: 0; } }
.alt-label { font-size: $fs-meta; color: $muted; width: 40px; flex-shrink: 0; }
.alt-name { flex: 1; font-size: $fs-body; font-weight: 500; min-width: 0; }
.alt-price { font-size: $fs-body; font-weight: 600; flex-shrink: 0; }
.alt-item.on { background: $fg-soft; margin: 0 -16px; padding: 12px 16px; border-radius: $radius; border-bottom-color: transparent; }
.alt-item.on .alt-label { color: $primary-text; font-weight: 600; }
.alt-item.on .alt-name { font-weight: 600; }
.cta-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px $page-margin 0; background: $bg; z-index: 100; }
</style>
