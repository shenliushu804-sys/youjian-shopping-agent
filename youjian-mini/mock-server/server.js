/**
 * Mock API 服务器 — 遵循 HANDOFF.md §5 接口契约
 * 端口 3001，支持 SSE 进度推送
 */
const express = require('express')
const cors = require('cors')
const data = require('./data')

const app = express()
app.use(cors())
app.use(express.json())

// ─── POST /api/tasks — 创建选品任务 ───
app.post('/api/tasks', (req, res) => {
  const { need, budgetMin, budgetMax, platforms, background } = req.body
  const taskId = data.createTask({ need, budgetMin, budgetMax, platforms, background })
  console.log(`[Task Created] ${taskId}: "${need}" ¥${budgetMin}-${budgetMax}`)
  res.json({ code: 0, data: { taskId } })
})

// ─── GET /api/tasks/:taskId/progress — 轮询进度 ───
app.get('/api/tasks/:taskId/progress', (req, res) => {
  const { taskId } = req.params
  const progress = data.getProgress(taskId)
  if (!progress) {
    return res.status(404).json({ code: 404, message: '任务不存在' })
  }
  res.json({ code: 0, data: progress })
})

// ─── GET /api/tasks/:taskId/progress/stream — SSE 进度流 ───
app.get('/api/tasks/:taskId/progress/stream', (req, res) => {
  const { taskId } = req.params
  const task = data.getTask(taskId)
  if (!task) {
    return res.status(404).json({ code: 404, message: '任务不存在' })
  }

  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders()

  // 每步 820ms 推送一次进度
  const STEP_MS = 820
  const totalSteps = data.STEP_TEMPLATES.length

  let step = 0
  const interval = setInterval(() => {
    if (step < totalSteps) {
      data.advanceProgress(taskId)
      const progress = data.getProgress(taskId)
      res.write(`data: ${JSON.stringify(progress)}\n\n`)
      step++
    } else {
      clearInterval(interval)
      res.write(`data: ${JSON.stringify({ ...data.getProgress(taskId), done: true })}\n\n`)
      res.end()
    }
  }, STEP_MS)

  req.on('close', () => {
    clearInterval(interval)
  })
})

// ─── GET /api/tasks/:taskId/result — 获取结果 ───
app.get('/api/tasks/:taskId/result', (req, res) => {
  const { taskId } = req.params
  const result = data.getResult(taskId)
  if (!result) {
    return res.status(404).json({ code: 404, message: '任务不存在或未完成' })
  }
  res.json({ code: 0, data: result })
})

// ─── POST /api/orders — 创建订单 ───
app.post('/api/orders', (req, res) => {
  const { productId } = req.body
  const product = data.PRODUCT_DB[productId]
  if (!product) {
    return res.status(400).json({ code: 400, message: '商品不存在' })
  }

  const orderId = 'YJ' + Date.now().toString(36).toUpperCase()
  const discount = 100 // 新客券

  res.json({
    code: 0,
    data: {
      orderId,
      productId,
      goodsAmount: product.price,
      discounts: [{ label: '新客券', amount: discount }],
      shipping: 0,
      payAmount: product.price - discount,
      spec: product.spec
    }
  })
})

// ─── POST /api/payments — 发起支付 ───
app.post('/api/payments', (req, res) => {
  const { orderId, method } = req.body
  // 模拟支付成功
  res.json({
    code: 0,
    data: {
      orderId,
      method,
      status: 'success',
      transactionId: 'TXN' + Date.now().toString(36).toUpperCase()
    }
  })
})

// ─── 启动 ───
const PORT = 3001
app.listen(PORT, () => {
  console.log(`\n🚀 优拣 Mock API running at http://localhost:${PORT}`)
  console.log(`   POST /api/tasks           — 创建选品任务`)
  console.log(`   GET  /api/tasks/:id/progress — 查询进度（轮询）`)
  console.log(`   GET  /api/tasks/:id/progress/stream — SSE 进度流`)
  console.log(`   GET  /api/tasks/:id/result   — 获取结果`)
  console.log(`   POST /api/orders          — 创建订单`)
  console.log(`   POST /api/payments        — 发起支付\n`)
})
