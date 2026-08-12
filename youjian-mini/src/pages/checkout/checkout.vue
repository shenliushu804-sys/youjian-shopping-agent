<template>
  <view class="page">
    <TopBar title="确认支付" sub="订单结算" @back="goBack" />
    <view class="scroll">
      <view class="card">
        <text class="card-title">订单摘要</text>
        <view class="order-row">
          <view class="order-thumb"><text class="order-thumb-icon">🪑</text></view>
          <view class="order-info">
            <text class="order-name">{{ product.name }}</text>
            <text class="order-spec">{{ orderSpec }}</text>
          </view>
        </view>
        <view class="bill-row"><text class="bill-label">商品金额</text><text class="bill-val num">{{ formatPrice(goodsAmount) }}</text></view>
        <view class="bill-row">
          <text class="bill-label">优惠</text>
          <text class="bill-val discount num">{{ discountText }}</text>
        </view>
        <view class="bill-row"><text class="bill-label">运费</text><text class="bill-val">{{ shipping > 0 ? formatPrice(shipping) : '免运费' }}</text></view>
        <view class="bill-total-row"><text class="bill-label">实付</text><text class="bill-total num">{{ formatPrice(payAmount) }}</text></view>
      </view>

      <view class="card">
        <text class="card-title">支付方式</text>
        <view v-for="m in payMethods" :key="m.key" :class="['pay-method', payPick === m.key ? 'on' : '']" @tap="payPick = m.key">
          <view class="pay-dot" :style="{ background: m.color }"></view>
          <text class="pay-name">{{ m.label }}</text>
          <view v-if="payPick === m.key" class="pay-check"><text class="pay-check-icon">✓</text></view>
        </view>
      </view>
    </view>

    <view class="cta-bar safe-bottom">
      <BtnPrimary :label="'立即支付 · ' + formatPrice(payAmount)" @tap="doPay" />
    </view>

    <view v-if="paySuccess" class="done-overlay" @tap="dismiss">
      <view class="done-card" @tap.stop>
        <text class="done-icon">✓</text>
        <text class="done-title">支付成功</text>
        <text class="done-order">订单号：{{ orderId }}</text>
        <text class="done-eta">{{ product.eta }}</text>
        <view class="done-btn" @tap="restart"><text class="done-btn-text">再体验一次</text></view>
      </view>
    </view>
  </view>
</template>

<script>
import { PRODUCTS, PAY_METHODS, formatPrice } from '../../utils/constants'
import { getState, setState } from '../../utils/store'
import { createOrder, createPayment } from '../../api/orders'
import TopBar from '../../components/TopBar.vue'
import BtnPrimary from '../../components/BtnPrimary.vue'

export default {
  components: { TopBar, BtnPrimary },
  data() {
    const s = getState()
    const product = (s.products || [PRODUCTS.a, PRODUCTS.b, PRODUCTS.c]).find(p => p.id === s.picked) || PRODUCTS[s.picked] || PRODUCTS.a
    return {
      product,
      payMethods: PAY_METHODS,
      payPick: 'alipay',
      paySuccess: false,
      orderId: '',
      goodsAmount: product.price,
      discount: 100,
      shipping: 0,
      orderSpec: product.spec || ''
    }
  },
  computed: {
    payAmount() { return this.goodsAmount - this.discount + this.shipping },
    discountText() { return `-¥${this.discount} 新客券` }
  },
  async onLoad() {
    // 尝试通过 API 创建订单
    try {
      const result = await createOrder({ productId: this.product.id })
      if (result) {
        this.orderId = result.orderId
        this.goodsAmount = result.goodsAmount
        this.discount = result.discounts?.reduce((sum, d) => sum + d.amount, 0) || 0
        this.shipping = result.shipping || 0
        this.orderSpec = result.spec || this.orderSpec
      }
    } catch (err) {
      console.warn('[API] createOrder failed, use local calc', err)
    }
  },
  methods: {
    formatPrice,
    goBack() { uni.navigateBack() },
    async doPay() {
      try {
        if (this.orderId) {
          const result = await createPayment({ orderId: this.orderId, method: this.payPick })
          if (result && result.status === 'success') {
            this.paySuccess = true
            return
          }
        }
      } catch (err) {
        console.warn('[API] createPayment failed, simulate success', err)
      }
      // 降级：模拟支付成功
      if (!this.orderId) {
        this.orderId = 'YJ' + Date.now().toString(36).toUpperCase()
      }
      this.paySuccess = true
    },
    dismiss() {},
    restart() {
      this.paySuccess = false
      setState({ picked: 'a', products: null, taskId: null })
      uni.reLaunch({ url: '/pages/need-input/need-input' })
    }
  }
}
</script>

<style lang="scss" scoped>
.page { display: flex; flex-direction: column; min-height: 100vh; max-width: 100vw; overflow-x: hidden; background: $bg; position: relative; }
.scroll { width: 100%; padding: 0 $page-margin 20px; }
.card { background: $surface; border: 1px solid $border-soft; border-radius: $radius-l; padding: $pad; margin-bottom: $gap; }
.card-title { font-size: $fs-small; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 12px; color: $fg; }
.order-row { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid $border-soft; }
.order-thumb { width: 48px; height: 48px; border-radius: $radius; background: $fg-soft; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.order-thumb-icon { font-size: 22px; }
.order-info { flex: 1; min-width: 0; }
.order-name { font-size: $fs-body; font-weight: 600; display: block; }
.order-spec { font-size: $fs-meta; color: $muted; margin-top: 2px; display: block; }
.bill-row { display: flex; justify-content: space-between; padding: 6px 0; }
.bill-label { font-size: $fs-small; color: $muted; }
.bill-val { font-size: $fs-small; }
.bill-val.discount { color: $primary-text; }
.bill-total-row { display: flex; justify-content: space-between; padding-top: 12px; margin-top: 8px; border-top: 1px solid $border-soft; }
.bill-total { font-size: $fs-h2; font-weight: 700; }
.pay-method { display: flex; align-items: center; gap: 10px; padding: 14px 0; border-bottom: 1px solid $border-soft; &:last-child { border-bottom: 0; } }
.pay-dot { width: 8px; height: 8px; border-radius: 999px; flex-shrink: 0; }
.pay-name { flex: 1; font-size: $fs-body; font-weight: 500; }
.pay-check { width: 22px; height: 22px; border-radius: 999px; background: $fg; display: flex; align-items: center; justify-content: center; }
.pay-check-icon { color: $bg; font-size: 13px; font-weight: 700; }
.pay-method.on .pay-name { font-weight: 600; }
.cta-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px $page-margin 0; background: $bg; z-index: 100; }
.done-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.done-card { width: 280px; background: $surface; border-radius: $radius-l; padding: 32px 24px; display: flex; flex-direction: column; align-items: center; }
.done-icon { width: 48px; height: 48px; border-radius: 999px; background: $fg; color: $bg; font-size: 24px; font-weight: 700; text-align: center; line-height: 48px; margin-bottom: 16px; }
.done-title { font-size: $fs-h2; font-weight: 600; margin-bottom: 8px; }
.done-order { font-size: $fs-meta; color: $muted; margin-bottom: 4px; }
.done-eta { font-size: $fs-meta; color: $muted; margin-bottom: 20px; }
.done-btn { width: 100%; min-height: 44px; display: flex; align-items: center; justify-content: center; border: 1px solid $border-c; border-radius: $radius; }
.done-btn-text { font-size: $fs-body; font-weight: 500; color: $fg; }
</style>
