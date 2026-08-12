<template>
  <view class="page">
    <TopBar title="三款对比" sub="AI 筛选出的候选商品" @back="goBack" />
    <view class="scroll">
      <view class="card">
        <view v-for="p in products" :key="p.id" :class="['p-card', p.id === recommendedId ? 'rec' : '']">
          <view class="p-thumb"><text class="p-thumb-text">🪑</text></view>
          <view class="p-info">
            <text class="p-name">{{ p.name }}</text>
            <view class="p-meta">
              <PlatformBadge :platform="p.platform" />
              <text class="rate">好评 {{ p.rating }}%（{{ formatCount(p.reviewCount) }}）</text>
            </view>
          </view>
          <view class="p-price"><text class="num price-val">{{ formatPrice(p.price) }}</text></view>
          <view v-if="p.id === recommendedId" class="rec-tag"><text class="rec-tag-text">AI 首选</text></view>
        </view>
      </view>

      <view class="card">
        <text class="card-title">参数对比</text>
        <view class="spec-table">
          <view class="spec-header">
            <view class="spec-dim"></view>
            <view v-for="p in products" :key="p.id" class="spec-col">
              <text class="spec-col-label">{{ p.id === 'a' ? '首选' : p.id === 'b' ? '备选B' : '备选C' }}</text>
            </view>
          </view>
          <view v-for="dim in specDimensions" :key="dim" class="spec-row">
            <view class="spec-dim"><text>{{ dim }}</text></view>
            <view v-for="p in products" :key="p.id" class="spec-col">
              <text :class="['spec-val', p.bestParams && p.bestParams.indexOf(dim) > -1 ? 'best' : '']">{{ p.params[dim] }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="card-title">评价摘要</text>
        <view v-for="p in products" :key="p.id" class="review-item">
          <text class="review-name">{{ p.name }}</text>
          <view class="review-row"><text class="review-icon">👍</text><text class="review-text">{{ p.reviewQuote }}</text></view>
          <view class="review-row"><text class="review-icon">⚠️</text><text class="review-text con">{{ p.reviewCon }}</text></view>
          <view class="rate-bar"><view class="rate-fill" :style="{ width: p.rating + '%' }"></view></view>
        </view>
      </view>
    </view>
    <view class="cta-bar safe-bottom">
      <BtnPrimary label="查看 AI 推荐" @tap="goRecommend" />
    </view>
  </view>
</template>

<script>
import { PRODUCTS, SPEC_DIMENSIONS, formatPrice } from '../../utils/constants'
import { getState, setState } from '../../utils/store'
import { getTaskResult } from '../../api/tasks'
import TopBar from '../../components/TopBar.vue'
import BtnPrimary from '../../components/BtnPrimary.vue'
import PlatformBadge from '../../components/PlatformBadge.vue'

export default {
  components: { TopBar, BtnPrimary, PlatformBadge },
  data() {
    return {
      products: [PRODUCTS.a, PRODUCTS.b, PRODUCTS.c],
      recommendedId: 'a',
      specDimensions: SPEC_DIMENSIONS,
      loaded: false
    }
  },
  async onLoad(options) {
    const state = getState()
    if (options.taskId && options.taskId !== 'undefined') {
      try {
        const result = await getTaskResult(options.taskId)
        if (result && result.products) {
          this.products = result.products
          this.recommendedId = result.recommendedId || 'a'
          setState({ products: result.products, recommendedId: result.recommendedId })
        }
      } catch (err) {
        console.warn('[API] getTaskResult failed, use local data', err)
      }
    }
    // 动态生成参数维度
    if (this.products.length && this.products[0].params) {
      this.specDimensions = Object.keys(this.products[0].params)
    }
    this.loaded = true
  },
  methods: {
    formatPrice,
    formatCount(n) { return n >= 10000 ? (n / 10000).toFixed(1) + '万' : n.toLocaleString() },
    goBack() { uni.navigateBack() },
    goRecommend() { uni.navigateTo({ url: '/pages/ai-recommend/ai-recommend' }) }
  }
}
</script>

<style lang="scss" scoped>
.page { background: $bg; padding-bottom: 80px; }
.scroll { width: 100%; padding: 0 $page-margin 20px; }
.card { background: $surface; border: 1px solid $border-soft; border-radius: $radius-l; padding: $pad; margin-bottom: $gap; overflow: hidden; }
.card-title { font-size: $fs-small; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 12px; color: $fg; }
.p-card { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid $border-soft; position: relative; overflow: hidden; .p-card { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid $border-soft; position: relative; &:last-child { border-bottom: 0; } }:last-child { border-bottom: 0; } }
.p-card.rec { border-color: $primary-soft; }
.p-thumb { width: 48px; height: 48px; border-radius: $radius; background: $fg-soft; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.p-thumb-text { font-size: 24px; }
.p-info { flex: 1; min-width: 0; }
.p-name { font-size: $fs-body; font-weight: 600; line-height: 1.3; margin-bottom: 4px; }
.p-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.rate { font-size: $fs-meta; color: $muted; }
.p-price { flex-shrink: 0; text-align: right; padding-right: 2px; }
.price-val { font-size: 17px; font-weight: 600; }
.rec-tag { position: absolute; top: 0; right: 8px; background: $primary-soft; padding: 2px 8px; border-radius: 999px; }
.rec-tag-text { font-size: 10px; font-weight: 600; color: $primary-text; }
.spec-table { width: 100%; }
.spec-header { display: flex; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid $border-soft; }
.spec-dim { width: 72px; flex-shrink: 0; font-size: $fs-meta; color: $muted; }
.spec-col { flex: 1; text-align: center; }
.spec-col-label { font-size: $fs-meta; font-weight: 600; color: $fg; }
.spec-row { display: flex; padding: 6px 0; border-bottom: 1px solid $border-soft; &:last-child { border-bottom: 0; } }
.spec-val { font-size: $fs-small; color: $fg; &.best { font-weight: 700; text-decoration: underline; } }
.review-item { padding: 10px 0; border-bottom: 1px solid $border-soft; &:last-child { border-bottom: 0; } }
.review-name { font-size: $fs-small; font-weight: 600; margin-bottom: 6px; }
.review-row { display: flex; gap: 6px; margin-bottom: 4px; }
.review-icon { font-size: 13px; flex-shrink: 0; }
.review-text { font-size: $fs-small; color: $fg; &.con { color: $muted; } }
.rate-bar { height: 6px; border-radius: 3px; background: $fg-soft; margin-top: 6px; }
.rate-fill { height: 100%; border-radius: 3px; background: $fg; }
.cta-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px $page-margin 0; background: $bg; z-index: 100; }
</style>
