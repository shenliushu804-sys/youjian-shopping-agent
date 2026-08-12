/**
 * Mock 数据 — 与前端 constants.js PRODUCTS 对齐，后端视角
 */

let taskIdCounter = 1
const tasks = {}

// 模拟商品库
const PRODUCT_DB = {
  a: {
    id: 'a', name: '西昊 M57 人体工学椅', platform: 'jd', platformLabel: '京东',
    price: 1899, spec: '网布款 / 黑色', eta: '预计 2–3 个工作日送达',
    rating: 97.2, reviewCount: 12800,
    params: {
      '到手价': '¥1,899', '腰托调节': '双向可调', '头枕': '可调',
      '扶手': '4D 扶手', '椅背材质': '透气网布', '承重': '150 kg', '质保': '5 年'
    },
    bestParams: ['腰托调节', '椅背材质'],
    reviewQuote: '腰托很舒服，久坐不累，安装简单',
    reviewCon: '网布久用略松，头枕稍硬',
    reasons: [
      '参数综合最优：双向可调腰托 + 4D 扶手 + 透气网布，三项核心维度领先',
      '好评率 97.2%（1.2 万+ 评价），长期口碑稳定',
      '到手价 ¥1,899，性价比在同类中最优'
    ]
  },
  b: {
    id: 'b', name: '永艺 XY 人体工学椅', platform: 'tmall', platformLabel: '天猫',
    price: 2199, spec: '网布款 / 深灰', eta: '预计 3–5 个工作日送达',
    rating: 95.8, reviewCount: 8300,
    params: {
      '到手价': '¥2,199', '腰托调节': '自适应', '头枕': '可调',
      '扶手': '3D 扶手', '椅背材质': '透气网布', '承重': '136 kg', '质保': '3 年'
    },
    bestParams: ['腰托调节'],
    reviewQuote: '悬浮腰托很聪明，自动贴合',
    reviewCon: '扶手调节有限，质保稍短',
    reasons: [
      '自适应腰托对久坐更友好，无需手动微调',
      '天猫好评率 95.8%，评价一致性高',
      '到手价 ¥2,199，功能/价格均衡'
    ]
  },
  c: {
    id: 'c', name: '保友 金豪E 人体工学椅', platform: 'jd', platformLabel: '京东',
    price: 2999, spec: '网布款 / 银灰', eta: '预计 2–4 个工作日送达',
    rating: 96.5, reviewCount: 5600,
    params: {
      '到手价': '¥2,999', '腰托调节': '4档可调', '头枕': '可调 + 前后',
      '扶手': '4D 扶手', '椅背材质': '高弹网布', '承重': '160 kg', '质保': '5 年'
    },
    bestParams: ['头枕', '承重'],
    reviewQuote: '用料扎实，承重强，调节范围大',
    reviewCon: '价格较高，入门门槛高',
    reasons: [
      '调节上限最高：4档腰托 + 前后头枕 + 160kg 承重',
      '高弹网布 + 5 年质保，长期耐用性最好',
      '到手价 ¥2,999，功能最全但价格偏高'
    ]
  }
}

// 分析步骤模板
const STEP_TEMPLATES = [
  { name: '抓取京东', subText: '搜索商品列表与价格', finalCount: '47 款' },
  { name: '抓取天猫淘宝', subText: '搜索商品列表与价格', finalCount: '36 款' },
  { name: '预算需求初筛', subText: '价格区间 + 基础参数过滤', finalCount: '83 → 12 款' },
  { name: '大模型深读参数评价', subText: '逐款读取详情页与评价', finalCount: '12 → 3 款' },
  { name: '生成结论', subText: '综合推荐理由与对比报告', finalCount: '1 份报告' }
]

function generateReasons(productKey, background) {
  const p = PRODUCT_DB[productKey]
  const reasons = [...p.reasons]
  const bgReasonMap = {
    a: background
      ? `结合你的背景：针对「${background}」，双向可调腰托与透气网布正对应，椅身紧凑不挑空间`
      : '结合常见久坐场景：双向可调腰托与透气网布够用，椅身紧凑不挑空间',
    b: background
      ? `结合你的背景：悬浮腰托动态贴合，对「${background}」这类诉求更友好，长时间久坐更省力`
      : '结合常见久坐场景：悬浮腰托动态贴合，长时间久坐更省力',
    c: background
      ? `结合你的背景：支撑与调节上限最高，应对「${background}」更从容，但价格贴近预算上限`
      : '支撑与调节上限最高，长期耐用性最好，但价格贴近预算上限'
  }
  reasons.push(bgReasonMap[productKey] || '')
  return reasons
}

module.exports = {
  PRODUCT_DB,
  STEP_TEMPLATES,
  generateReasons,

  createTask({ need, budgetMin, budgetMax, platforms, background }) {
    const taskId = 'task_' + (taskIdCounter++)
    tasks[taskId] = {
      taskId,
      need: need || '人体工学椅',
      budgetMin, budgetMax,
      platforms: platforms || ['jd', 'tmall'],
      background: background || '',
      createdAt: Date.now(),
      progressStep: 0,
      done: false
    }
    return taskId
  },

  getTask(taskId) {
    return tasks[taskId] || null
  },

  advanceProgress(taskId) {
    const task = tasks[taskId]
    if (!task || task.done) return task
    task.progressStep++
    if (task.progressStep >= STEP_TEMPLATES.length) {
      task.done = true
    }
    return task
  },

  getProgress(taskId) {
    const task = tasks[taskId]
    if (!task) return null

    const steps = STEP_TEMPLATES.map((tpl, i) => ({
      name: tpl.name,
      subText: tpl.subText,
      status: i < task.progressStep ? 'done' : i === task.progressStep && !task.done ? 'running' : 'pending',
      count: i < task.progressStep ? tpl.finalCount : ''
    }))

    const fetchedCount = Math.min(task.progressStep, 2) === 2 ? 83 : (task.progressStep >= 1 ? 47 : 0)
    const shortlistCount = task.progressStep >= 3 ? 12 : 0

    return {
      steps,
      funnel: { fetched: fetchedCount, shortlisted: shortlistCount, final: task.done ? 3 : 0 },
      done: task.done
    }
  },

  getResult(taskId) {
    const task = tasks[taskId]
    if (!task) return null

    const products = Object.values(PRODUCT_DB).map(p => ({
      ...p,
      image: '' // 无真实图片，前端用 emoji 占位
    }))

    return {
      products,
      recommendedId: 'a',
      reasons: generateReasons('a', task.background)
    }
  }
}
