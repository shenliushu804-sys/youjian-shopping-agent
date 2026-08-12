/**
 * 简易全局状态 — 后期可换 Pinia
 */
import { PRODUCTS } from './constants'

const state = {
  need: '',
  budgetMin: 1000,
  budgetMax: 3000,
  platformJd: true,
  platformTmall: true,
  background: '',
  picked: 'a',      // 当前选中商品 key
  taskId: null
}

export function getState() { return state }

export function setState(patch) { Object.assign(state, patch) }

export function getPickedProduct() { return PRODUCTS[state.picked] }
