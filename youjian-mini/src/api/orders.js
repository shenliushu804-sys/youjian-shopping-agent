/**
 * 订单 & 支付 API — 对应 HANDOFF.md §5 接口契约
 */
import { post } from './request'

/** 创建订单 */
export function createOrder({ productId }) {
  return post('/api/orders', { productId })
}

/** 发起支付 */
export function createPayment({ orderId, method }) {
  return post('/api/payments', { orderId, method })
}
