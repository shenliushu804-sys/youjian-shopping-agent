<template>
  <view class="page">
    <view class="brand-row">
      <view class="brand-mark"><text class="brand-mark-text">优</text></view>
      <text class="brand-name">优拣</text>
      <AiChip />
    </view>

    <text class="s1-title">AI 帮你挑，<text class="s1-title-em">更省心</text></text>
    <text class="s1-sub">告诉我想买什么，我来对比筛选</text>

    <view class="scroll">
      <view class="card">
        <view class="field-label"><text>购物需求</text></view>
        <input class="text-input" v-model="need" placeholder="例如：人体工学椅" @input="onNeedInput" />
        <view class="chip-row">
          <view v-for="c in quickChips" :key="c.label" class="q-chip" @tap="fillNeed(c.fill)">
            <text>{{ c.label }}</text>
          </view>
        </view>

        <view class="sub-label"><text>购物背景</text><text class="dim">选填</text></view>
        <textarea class="bg-note-area" v-model="background" placeholder="如：久坐、腰椎不适、送礼…" :maxlength="200" auto-height />
        <view class="chip-row" v-if="bgChips.length">
          <view v-for="(c, i) in bgChips" :key="i" class="q-chip" @tap="appendBg(c)">
            <text>{{ c }}</text>
          </view>
        </view>

        <view class="sub-label"><text>预算区间</text></view>
        <view class="preset-grid">
          <view v-for="(p, i) in budgetPresets" :key="i" :class="['preset', presetIdx === i ? 'on' : '']" @tap="pickPreset(i)">
            <text>{{ p.label }}</text>
            <text class="preset-sub">{{ p.sub }}</text>
          </view>
        </view>
        <view class="range-row">
          <view class="range-input">
            <text class="range-prefix">¥</text>
            <input type="number" v-model="budgetMin" class="range-field" placeholder="最低" @input="clearPreset" />
          </view>
          <view class="range-dash"><text>–</text></view>
          <view class="range-input">
            <text class="range-prefix">¥</text>
            <input type="number" v-model="budgetMax" class="range-field" placeholder="最高" @input="clearPreset" />
          </view>
        </view>

        <view class="sub-label"><text>抓取平台</text></view>
        <view class="switch-row">
          <view class="dot jd-dot"></view>
          <text class="name">京东</text>
          <switch :checked="platformJd" @change="platformJd = $event.detail.value" color="#0d0d0d" />
        </view>
        <view class="switch-row">
          <view class="dot tmall-dot"></view>
          <text class="name">天猫淘宝</text>
          <switch :checked="platformTmall" @change="platformTmall = $event.detail.value" color="#0d0d0d" />
        </view>
      </view>
    </view>

    <view class="cta-bar safe-bottom">
      <BtnPrimary label="开始 AI 选品" @tap="startAnalysis" />
      <text class="cta-note">AI 将对比京东 + 天猫商品，为你筛选出 3 款</text>
    </view>
  </view>
</template>

<script>
import { BG_SETS, BG_DEFAULT, BUDGET_PRESETS, categoryOf } from '../../utils/constants'
import { setState } from '../../utils/store'
import { createTask } from '../../api/tasks'
import BtnPrimary from '../../components/BtnPrimary.vue'
import AiChip from '../../components/AiChip.vue'

export default {
  components: { BtnPrimary, AiChip },
  data() {
    return {
      need: '',
      background: '',
      budgetMin: '1,000',
      budgetMax: '3,000',
      presetIdx: 1,
      platformJd: true,
      platformTmall: true,
      quickChips: [
        { label: '人体工学椅', fill: '人体工学椅' },
        { label: '降噪耳机', fill: '降噪耳机' },
        { label: '扫地机器人', fill: '扫地机器人' },
        { label: '机械键盘', fill: '机械键盘' }
      ],
      bgChips: [],
      budgetPresets: BUDGET_PRESETS
    }
  },
  onLoad() { this.updateBgChips() },
  methods: {
    onNeedInput() { this.updateBgChips() },
    updateBgChips() {
      const set = categoryOf(this.need)
      this.bgChips = set.chips || []
    },
    fillNeed(text) {
      this.need = text
      const set = categoryOf(text)
      if (set.note) this.background = set.note
      this.updateBgChips()
    },
    appendBg(frag) {
      const cur = this.background.trim()
      const clean = frag.replace(/[：:]$/, '')
      if (cur.indexOf(clean) > -1) return
      this.background = cur ? cur + '，' + frag : frag
    },
    pickPreset(idx) {
      this.presetIdx = idx
      const p = BUDGET_PRESETS[idx]
      this.budgetMin = p.min.toLocaleString('en-US')
      this.budgetMax = p.max.toLocaleString('en-US')
    },
    clearPreset() { this.presetIdx = -1 },
    async startAnalysis() {
      const min = parseInt(String(this.budgetMin).replace(/,/g, '')) || 0
      const max = parseInt(String(this.budgetMax).replace(/,/g, '')) || 99999
      const platforms = []
      if (this.platformJd) platforms.push('jd')
      if (this.platformTmall) platforms.push('tmall')

      setState({
        need: this.need || '人体工学椅',
        budgetMin: min,
        budgetMax: max,
        platformJd: this.platformJd,
        platformTmall: this.platformTmall,
        background: this.background
      })

      try {
        const { taskId } = await createTask({
          need: this.need || '人体工学椅',
          budgetMin: min,
          budgetMax: max,
          platforms,
          background: this.background
        })
        setState({ taskId })
        uni.navigateTo({ url: `/pages/ai-analysis/ai-analysis?taskId=${taskId}` })
      } catch (err) {
        // 降级：即使 API 失败也跳转，用本地模拟
        console.warn('[API] createTask failed, fallback to local', err)
        setState({ taskId: null })
        uni.navigateTo({ url: '/pages/ai-analysis/ai-analysis' })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.page { background: $bg; padding-bottom: 80px; }
.scroll { width: 100%; padding: 0 $page-margin 20px; }
.brand-row { display: flex; align-items: center; gap: 8px; padding: 12px $page-margin 10px; }
.brand-mark { width: 26px; height: 26px; border-radius: 8px; background: $fg; display: flex; align-items: center; justify-content: center; }
.brand-mark-text { color: $bg; font-size: 14px; font-weight: 600; }
.brand-name { font-size: 15px; font-weight: 600; letter-spacing: 0.01em; }
.s1-title { font-size: $fs-h1; font-weight: 650; letter-spacing: -0.02em; line-height: 1.2; padding: 0 $page-margin; }
.s1-title-em { color: $primary; }
.s1-sub { font-size: $fs-small; color: $muted; margin: 6px 0 14px; padding: 0 $page-margin; }
.card { background: $surface; border: 1px solid $border-soft; border-radius: $radius-l; padding: $pad; overflow: hidden; box-sizing: border-box; }
.field-label { display: flex; align-items: baseline; justify-content: space-between; font-size: $fs-small; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 8px; }
.text-input { width: 100%; padding: 12px 14px; background: $surface; border: 1px solid $border-c; border-radius: $radius; font-size: 15px; }
.chip-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.q-chip { padding: 6px 12px; border-radius: 999px; background: $fg-soft; color: $muted; font-size: $fs-meta; letter-spacing: 0.01em; }
.sub-label { display: flex; align-items: baseline; gap: 6px; font-size: $fs-meta; color: $muted; letter-spacing: 0.02em; margin: 15px 0 8px; }
.dim { color: $faint; }
.bg-note-area { width: 100%; min-height: 64px; padding: 11px 13px; border: 1px solid $border-c; border-radius: $radius; background: $surface; font-size: $fs-small; line-height: 1.5; color: $fg; }
.preset-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.preset { min-width: 0; min-height: 44px; padding: 10px 12px; border-radius: $radius; border: 1px solid $border-c; background: $surface; color: $fg; font-size: $fs-small; font-weight: 500; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; }
.preset-sub { font-size: 10.5px; color: $muted; font-weight: 400; }
.preset.on { border-color: $fg; background: $fg-soft; font-weight: 600; }
.range-row { display: flex; align-items: center; gap: 6px; margin-top: 10px; }
.range-input { flex: 1; position: relative; }
.range-prefix { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: $faint; font-size: $fs-small; z-index: 1; }
.range-field { width: 100%; padding: 10px 10px 10px 26px; border: 1px solid $border-c; border-radius: $radius; background: $surface; font-size: $fs-body; }
.range-dash { display: flex; align-items: center; justify-content: center; color: $faint; font-size: 16px; width: 20px; flex-shrink: 0; }
.switch-row { display: flex; align-items: center; gap: 10px; padding: 11px 0; border-top: 1px solid $border-soft; }
.dot { width: 8px; height: 8px; border-radius: 999px; }
.jd-dot { background: $jd; }
.tmall-dot { background: $tmall; }
.name { font-size: $fs-body; font-weight: 500; }
.cta-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px $page-margin 0; background: $bg; z-index: 100; }
.cta-note { display: block; text-align: center; font-size: $fs-meta; color: $muted; letter-spacing: 0.01em; padding: 8px 0; }
</style>
