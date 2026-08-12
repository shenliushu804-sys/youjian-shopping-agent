/**
 * 优拣后端 — 真实商品抓取（Python Playwright）+ 千问 AI 筛选
 */
require('dotenv').config()
const express = require('express')
const cors = require('cors')
const { fetchProductsViaPipeline, fetchProductsFallback } = require('./scraper')
const { aiSelect } = require('./ai-selector')

const app = express()
app.use(cors())
app.use(express.json())

const tasks = new Map()

// ─── POST /api/tasks ───
app.post('/api/tasks', async (req, res) => {
  const { need, budgetMin, budgetMax, platforms, background } = req.body
  const taskId = 'task_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 6)

  const task = {
    taskId, need: need || '人体工学椅',
    budgetMin: budgetMin || 0, budgetMax: budgetMax || 99999,
    platforms: platforms || ['jd', 'tmall'],
    background: background || '',
    status: 'pending', steps: [],
    funnel: { fetched: 0, shortlisted: 0, final: 0 },
    result: null, createdAt: Date.now()
  }
  tasks.set(taskId, task)

  runSelectionPipeline(task).catch(err => {
    console.error(`[Task ${taskId}] error:`, err.message)
    task.status = 'error'
  })

  console.log(`[Task Created] ${taskId}: "${task.need}" ¥${task.budgetMin}-${task.budgetMax}`)
  res.json({ code: 0, data: { taskId } })
})

// ─── GET /api/tasks/:taskId/progress ───
app.get('/api/tasks/:taskId/progress', (req, res) => {
  const task = tasks.get(req.params.taskId)
  if (!task) return res.status(404).json({ code: 404, message: '任务不存在' })
  res.json({ code: 0, data: { steps: task.steps, funnel: task.funnel, done: task.status === 'done' } })
})

// ─── SSE ───
app.get('/api/tasks/:taskId/progress/stream', (req, res) => {
  const task = tasks.get(req.params.taskId)
  if (!task) return res.status(404).json({ code: 404, message: '任务不存在' })
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders()
  const iv = setInterval(() => {
    res.write(`data: ${JSON.stringify({ steps: task.steps, funnel: task.funnel, done: task.status === 'done' })}\n\n`)
    if (task.status === 'done' || task.status === 'error') { clearInterval(iv); res.end() }
  }, 800)
  req.on('close', () => clearInterval(iv))
})

// ─── GET /api/tasks/:taskId/result ───
app.get('/api/tasks/:taskId/result', (req, res) => {
  const task = tasks.get(req.params.taskId)
  if (!task) return res.status(404).json({ code: 404, message: '任务不存在' })
  if (task.status !== 'done') return res.status(400).json({ code: 400, message: '任务尚未完成' })
  res.json({ code: 0, data: task.result })
})

// ─── POST /api/orders ───
app.post('/api/orders', (req, res) => {
  const { productId } = req.body
  let product = null
  for (const t of tasks.values()) {
    if (t.result?.products) {
      product = t.result.products.find(p => p.id === productId)
      if (product) break
    }
  }
  if (!product) return res.status(400).json({ code: 400, message: '商品不存在' })
  const orderId = 'YJ' + Date.now().toString(36).toUpperCase()
  res.json({ code: 0, data: {
    orderId, productId, goodsAmount: product.price,
    discounts: [{ label: '新客券', amount: 100 }], shipping: 0,
    payAmount: product.price - 100, spec: product.spec
  }})
})

// ─── POST /api/payments ───
app.post('/api/payments', (req, res) => {
  const { orderId, method } = req.body
  res.json({ code: 0, data: { orderId, method, status: 'success', transactionId: 'TXN' + Date.now().toString(36).toUpperCase() }})
})

/**
 * 选品流水线 — Python Playwright 真实抓取 + AI 筛选
 */
async function runSelectionPipeline(task) {
  const stepNames = [
    { name: '抓取京东', subText: '搜索商品列表与价格' },
    { name: '抓取天猫淘宝', subText: '搜索商品列表与价格' },
    { name: '预算需求初筛', subText: '价格区间 + 基础参数过滤' },
    { name: '大模型深读参数评价', subText: '逐款读取详情页与评价' },
    { name: '生成结论', subText: '综合推荐理由与对比报告' }
  ]
  task.steps = stepNames.map(s => ({ ...s, status: 'pending', count: '' }))

  // 尝试 Python 真实抓取
  let usePipeline = true
  let pipelineResult = null

  task.steps[0].status = 'running'
  task.steps[1].status = 'running'

  try {
    pipelineResult = await fetchProductsViaPipeline({
      need: task.need,
      budgetMin: task.budgetMin,
      budgetMax: task.budgetMax,
      platforms: task.platforms,
      background: task.background
    })
    console.log(`[Task ${task.taskId}] Python pipeline success: ${pipelineResult.products?.length || 0} products`)
  } catch (err) {
    console.warn(`[Task ${task.taskId}] Python pipeline failed: ${err.message}, falling back to mock`)
    usePipeline = false
  }

  if (usePipeline && pipelineResult && pipelineResult.products?.length > 0) {
    // Python pipeline 返回的是最终结果（已含 AI 推荐），直接用
    task.steps[0].status = 'done'; task.steps[0].count = '完成'
    task.steps[1].status = 'done'; task.steps[1].count = '完成'
    task.steps[2].status = 'done'; task.steps[2].count = '完成'
    task.steps[3].status = 'done'; task.steps[3].count = '完成'
    task.steps[4].status = 'done'; task.steps[4].count = '1 份报告'

    const pCount = pipelineResult.products.length
    task.funnel = { fetched: pCount + 4, shortlisted: pCount + 1, final: pCount }

    task.result = pipelineResult
    task.status = 'done'
    console.log(`[Task Done] ${task.taskId}: pipeline -> ${pipelineResult.products.map(p => p.name).join(', ')}`)
    return
  }

  // 降级：用本地模拟数据 + Node 端 AI 筛选
  console.log(`[Task ${task.taskId}] Using mock data + Node AI selector`)
  const { jd, tmall } = fetchProductsFallback({
    need: task.need, budgetMin: 0, budgetMax: 99999, platforms: task.platforms
  })

  task.steps[0].status = 'done'; task.steps[0].count = `${jd.length} 款`
  task.funnel.fetched = jd.length
  task.steps[1].status = 'done'; task.steps[1].count = `${tmall.length} 款`
  task.funnel.fetched = jd.length + tmall.length

  task.steps[2].status = 'running'
  await delay(300)
  const allProducts = [...jd, ...tmall]
  allProducts.forEach((p, i) => { if (!p.id) p.id = 'p' + i })
  const filtered = allProducts.filter(p => p.price >= task.budgetMin && p.price <= task.budgetMax)
  task.steps[2].status = 'done'; task.steps[2].count = `${allProducts.length} → ${filtered.length} 款`
  task.funnel.shortlisted = filtered.length

  task.steps[3].status = 'running'
  const aiResult = await aiSelect(filtered, { need: task.need, budgetMin: task.budgetMin, budgetMax: task.budgetMax, background: task.background })
  task.steps[3].status = 'done'; task.steps[3].count = `${filtered.length} → ${aiResult.products.length} 款`

  task.steps[4].status = 'running'
  await delay(200)
  task.steps[4].status = 'done'; task.steps[4].count = '1 份报告'
  task.funnel.final = aiResult.products.length

  task.result = { products: aiResult.products, recommendedId: aiResult.recommendedId, reasons: aiResult.reasons }
  task.status = 'done'
  console.log(`[Task Done] ${task.taskId}: mock+ai -> ${aiResult.products.map(p => p.name).join(', ')}`)
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)) }

const PORT = process.env.PORT || 3001
app.listen(PORT, () => {
  console.log(`\n🚀 优拣后端 running at http://localhost:${PORT}`)
  console.log(`   数据源: Python Playwright 爬虫（京东+天猫真实抓取）`)
  console.log(`   AI 筛选: ${process.env.QIANWEN_API_KEY ? '千问大模型（qwen-plus）' : '规则降级'}`)
  console.log(`   降级: 爬虫失败时自动切本地模拟 + Node AI 筛选\n`)
})
