/**
 * 请求封装 — 基于 uni.request
 * - 自动拼 baseURL
 * - 统一错误处理
 * - loading 状态管理
 * - 请求/响应拦截器
 */

const BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:3001'

let loadingCount = 0

function showLoading() {
  if (loadingCount === 0) {
    uni.showLoading({ title: '加载中', mask: true })
  }
  loadingCount++
}

function hideLoading() {
  loadingCount = Math.max(0, loadingCount - 1)
  if (loadingCount === 0) {
    uni.hideLoading()
  }
}

/**
 * 通用请求方法
 * @param {string} path - 接口路径，如 /api/tasks
 * @param {object} options - { method, data, header, showLoading }
 */
export function request(path, options = {}) {
  const {
    method = 'GET',
    data = null,
    header = {},
    showLoad = true,
    timeout = 30000
  } = options

  if (showLoad) showLoading()

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + path,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      timeout,
      success(res) {
        if (showLoad) hideLoading()

        const { statusCode, data: body } = res

        // HTTP 错误
        if (statusCode < 200 || statusCode >= 300) {
          const err = new Error(body?.message || `请求失败 (${statusCode})`)
          err.status = statusCode
          err.data = body
          handleError(err)
          reject(err)
          return
        }

        // 业务错误（后端统一 { code, message, data } 格式）
        if (body && body.code !== undefined && body.code !== 0 && body.code !== 200) {
          const err = new Error(body.message || '业务错误')
          err.code = body.code
          err.data = body
          handleError(err)
          reject(err)
          return
        }

        resolve(body?.data !== undefined ? body.data : body)
      },
      fail(err) {
        if (showLoad) hideLoading()
        const e = new Error(err.errMsg || '网络请求失败')
        e.isNetworkError = true
        handleError(e)
        reject(e)
      }
    })
  })
}

function handleError(err) {
  console.error('[API Error]', err.message, err)
  if (err.isNetworkError) {
    uni.showToast({ title: '网络连接失败', icon: 'none', duration: 2000 })
  } else if (err.status >= 500) {
    uni.showToast({ title: '服务器开小差了', icon: 'none', duration: 2000 })
  } else if (err.status === 401) {
    uni.showToast({ title: '请先登录', icon: 'none', duration: 2000 })
  }
}

// 便捷方法
export const get = (path, opts) => request(path, { ...opts, method: 'GET' })
export const post = (path, data, opts) => request(path, { ...opts, method: 'POST', data })
export const put = (path, data, opts) => request(path, { ...opts, method: 'PUT', data })
export const del = (path, opts) => request(path, { ...opts, method: 'DELETE' })

export { BASE_URL }
