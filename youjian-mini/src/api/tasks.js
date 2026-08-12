/**
 * 选品任务 API — 对应 HANDOFF.md §5 接口契约
 */
import { get, post, BASE_URL } from './request'

/** 创建选品任务 */
export function createTask({ need, budgetMin, budgetMax, platforms, background }) {
  return post('/api/tasks', {
    need,
    budgetMin,
    budgetMax,
    platforms,
    background
  }, { showLoad: false })
}

/** 获取任务进度 — 轮询模式 */
export function getTaskProgress(taskId) {
  return get(`/api/tasks/${taskId}/progress`, { showLoad: false })
}

/** 获取任务结果 */
export function getTaskResult(taskId) {
  return get(`/api/tasks/${taskId}/result`)
}

/**
 * SSE 进度流 — 用于屏2实时推送
 * H5 用 EventSource，小程序降级轮询
 */
export function watchTaskProgress(taskId, onUpdate, onDone, onError) {
  // #ifdef H5
  const source = new EventSource(`${BASE_URL}/api/tasks/${taskId}/progress/stream`)

  source.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onUpdate(data)
      if (data.done) {
        source.close()
        onDone && onDone(data)
      }
    } catch (err) {
      console.error('[SSE parse error]', err)
    }
  }

  source.onerror = () => {
    source.close()
    onError && onError(new Error('SSE connection error'))
  }

  return { close: () => source.close() }
  // #endif

  // #ifndef H5
  let stopped = false
  const POLL_MS = 1500

  async function poll() {
    if (stopped) return
    try {
      const data = await getTaskProgress(taskId)
      onUpdate(data)
      if (data.done) {
        onDone && onDone(data)
        return
      }
    } catch (err) {
      onError && onError(err)
      return
    }
    setTimeout(poll, POLL_MS)
  }

  poll()

  return { close: () => { stopped = true } }
  // #endif
}
