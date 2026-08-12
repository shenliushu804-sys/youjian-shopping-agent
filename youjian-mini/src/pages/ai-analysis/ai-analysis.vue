<template>
  <view class="page">
    <TopBar title="AI 分析中" :sub="elapsedText" :showBack="false" />
    <view class="scroll">
      <view class="task-chips">
        <view class="task-chip"><text class="task-chip-b">{{ state.need }}</text></view>
        <view class="task-chip num"><text>¥{{ state.budgetMin }} – {{ state.budgetMax }}</text></view>
        <view class="task-chip"><text>{{ platformLabel }}</text></view>
        <view v-if="bgShort" class="task-chip"><text>背景 · {{ bgShort }}</text></view>
      </view>

      <view class="card">
        <view v-for="(step, i) in displaySteps" :key="i" :class="['ana-step', step.status]">
          <view class="mark">
            <view v-if="step.status === 'running'" class="spinner"></view>
            <text v-else-if="step.status === 'done'" class="check">✓</text>
            <text v-else class="mark-num">{{ i + 1 }}</text>
          </view>
          <view class="txt">
            <text class="txt-main">{{ step.name }}</text>
            <text class="txt-sub">{{ step.sub || step.subText }}</text>
          </view>
          <text class="cnt num">{{ step.displayCount || step.count || '' }}</text>
        </view>
      </view>

      <view class="card funnel">
        <text class="f-title">候选收敛</text>
        <view class="f-row">
          <text class="f-lbl">抓取</text>
          <view class="f-bar" :style="{ width: funnelFetched + '%' }"></view>
          <text class="f-val num">{{ funnel.fetched }}</text>
        </view>
        <view class="f-row">
          <text class="f-lbl">初筛</text>
          <view class="f-bar short" :style="{ width: funnelShort + '%' }"></view>
          <text class="f-val num">{{ funnel.shortlisted }}</text>
        </view>
        <view class="f-row final">
          <text class="f-lbl">终选</text>
          <view class="f-bar final-bar" :style="{ width: '30%' }"></view>
          <text class="f-val num">{{ funnel.final || 0 }}</text>
        </view>
      </view>
      <text class="ana-note">AI 正在读取商品详情与用户评价…</text>
    </view>

    <view class="cta-bar safe-bottom">
      <BtnPrimary :label="doneLabel" :disabled="!allDone" @tap="goCompare" />
    </view>
  </view>
</template>

<script>
import { ANA_STEPS, shortNote } from '../../utils/constants'
import { getState, setState } from '../../utils/store'
import { watchTaskProgress } from '../../api/tasks'
import TopBar from '../../components/TopBar.vue'
import BtnPrimary from '../../components/BtnPrimary.vue'

export default {
  components: { TopBar, BtnPrimary },
  data() {
    return {
      state: getState(),
      displaySteps: ANA_STEPS.map(s => ({ ...s, status: 'pending', displayCount: '' })),
      elapsed: 0,
      elapsedTimer: null,
      allDone: false,
      funnel: { fetched: 0, shortlisted: 0, final: 0 },
      streamHandle: null,
      useApi: false
    }
  },
  computed: {
    taskId() { return this.state.taskId },
    platformLabel() {
      const pf = []
      if (this.state.platformJd) pf.push('京东')
      if (this.state.platformTmall) pf.push('天猫')
      return pf.length ? pf.join(' + ') : '双平台'
    },
    bgShort() { return shortNote(this.state.background) },
    elapsedText() {
      const m = Math.floor(this.elapsed / 60), s = this.elapsed % 60
      return `已用时 ${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`
    },
    doneLabel() { return this.allDone ? '查看 3 款对比结果' : '生成结果中…' },
    funnelFetched() { return Math.min(100, (this.funnel.fetched / 83) * 100) },
    funnelShort() { return Math.min(100, (this.funnel.shortlisted / 83) * 100) }
  },
  onLoad(options) {
    this.elapsedTimer = setInterval(() => { this.elapsed++ }, 1000)

    if (options.taskId && options.taskId !== 'undefined') {
      this.useApi = true
      this.startApiProgress(options.taskId)
    } else {
      this.startLocalSimulation()
    }
  },
  onUnload() {
    this.cleanup()
  },
  methods: {
    cleanup() {
      if (this.elapsedTimer) clearInterval(this.elapsedTimer)
      if (this.streamHandle) this.streamHandle.close()
    },

    // API 模式：SSE / 轮询
    startApiProgress(taskId) {
      this.streamHandle = watchTaskProgress(
        taskId,
        (data) => {
          if (data.steps) {
            this.displaySteps = data.steps.map((s, i) => ({
              ...ANA_STEPS[i],
              ...s,
              displayCount: s.count || ''
            }))
          }
          if (data.funnel) this.funnel = data.funnel
        },
        () => { this.allDone = true },
        () => {
          console.warn('[SSE/poll error] fallback to local simulation')
          this.useApi = false
          this.startLocalSimulation()
        }
      )
    },

    // 本地模拟模式（API 不可用时降级）
    startLocalSimulation() {
      this.displaySteps = ANA_STEPS.map(s => ({ ...s, status: 'pending', displayCount: '' }))
      this.funnel = { fetched: 0, shortlisted: 0, final: 0 }
      this.allDone = false
      const timers = []
      const STEP_MS = 820

      this.displaySteps.forEach((_, i) => {
        timers.push(setTimeout(() => { this.displaySteps[i].status = 'running' }, i * STEP_MS))
        timers.push(setTimeout(() => {
          this.displaySteps[i].status = 'done'
          this.displaySteps[i].displayCount = ANA_STEPS[i].count
          if (i === 0) this.funnel.fetched = 47
          if (i === 1) this.funnel.fetched = 83
          if (i === 2) this.funnel.shortlisted = 12
        }, (i + 1) * STEP_MS))
      })

      timers.push(setTimeout(() => {
        this.allDone = true
        this.funnel.final = 3
        timers.push(setTimeout(() => { this.goCompare() }, 1900))
      }, (this.displaySteps.length + 0.4) * STEP_MS))

      this._localTimers = timers
    },

    goCompare() {
      if (!this.allDone) return
      this.cleanup()
      if (this._localTimers) this._localTimers.forEach(t => clearTimeout(t))

      const url = this.taskId
        ? `/pages/product-compare/product-compare?taskId=${this.taskId}`
        : '/pages/product-compare/product-compare'
      uni.navigateTo({ url })
    }
  }
}
</script>

<style lang="scss" scoped>
.page { background: $bg; padding-bottom: 80px; }
.scroll { width: 100%; padding: 0 $page-margin 20px; }
.task-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: $gap; }
.task-chip { display: inline-flex; align-items: center; padding: 4px 11px; border-radius: 999px; background: $surface; border: 1px solid $border-c; font-size: $fs-meta; color: $muted; letter-spacing: 0.01em; }
.task-chip-b { color: $fg; font-weight: 600; }
.card { background: $surface; border: 1px solid $border-soft; border-radius: $radius-l; padding: $pad; margin-bottom: $gap; }
.ana-step { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid $border-soft; &:first-child { border-top: 0; } }
.mark { width: 24px; height: 24px; border-radius: 999px; display: flex; align-items: center; justify-content: center; border: 1.5px solid $border-c; color: transparent; font-size: 11px; flex-shrink: 0; }
.mark-num { color: $faint; font-size: 11px; }
.check { color: $bg; font-size: 13px; font-weight: 700; }
.ana-step.done .mark { background: $fg; border-color: $fg; color: $bg; }
.spinner { width: 20px; height: 20px; border-radius: 999px; border: 2.5px solid $border-c; border-top-color: $primary; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.txt { flex: 1; min-width: 0; }
.txt-main { display: block; font-size: $fs-body; color: $faint; }
.txt-sub { display: block; font-size: $fs-meta; color: $faint; letter-spacing: 0.01em; margin-top: 1px; }
.ana-step.running .txt-main { color: $fg; font-weight: 500; }
.ana-step.running .txt-sub { color: $muted; }
.ana-step.done .txt-main { color: $fg; }
.ana-step.done .txt-sub { color: $muted; }
.cnt { font-size: $fs-small; color: $faint; flex-shrink: 0; }
.ana-step.done .cnt { color: $muted; }
.f-title { font-size: $fs-meta; color: $muted; letter-spacing: 0.04em; margin-bottom: 10px; }
.f-row { display: flex; align-items: center; gap: 10px; padding: 5px 0; }
.f-lbl { width: 40px; font-size: $fs-meta; color: $muted; flex-shrink: 0; }
.f-bar { flex: 1; height: 14px; border-radius: 5px; background: $fg-soft; transition: width 0.5s; }
.f-bar.final-bar { background: $fg; }
.f-val { width: 30px; text-align: right; font-size: $fs-small; flex-shrink: 0; }
.f-row.final .f-val { font-weight: 600; }
.ana-note { font-size: $fs-meta; color: $muted; text-align: center; letter-spacing: 0.01em; margin-top: 12px; }
.cta-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px $page-margin 0; background: $bg; z-index: 100; }
</style>
