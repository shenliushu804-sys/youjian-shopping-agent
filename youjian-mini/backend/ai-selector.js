/**
 * AI 选品模块 — 调用千问大模型筛选 + 生成推荐理由
 * 使用通义千问 OpenAI 兼容接口
 */

const QIANWEN_API_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'

/**
 * AI 筛选：从候选商品中选出 3 款最优 + 生成推荐理由
 * @param {Array} candidates - 候选商品列表
 * @param {object} context - { need, budgetMin, budgetMax, background }
 * @returns {object} { products: [3款], recommendedId, reasons }
 */
async function aiSelect(candidates, context) {
  const apiKey = process.env.QIANWEN_API_KEY

  if (!apiKey) {
    console.warn('[AI] QIANWEN_API_KEY not set, using rule-based fallback')
    return ruleBasedSelect(candidates, context)
  }

  try {
    const prompt = buildPrompt(candidates, context)
    const response = await callQianWen(prompt, apiKey)
    return parseAIResponse(response, candidates)
  } catch (err) {
    console.error('[AI] QianWen call failed, fallback to rule-based:', err.message)
    return ruleBasedSelect(candidates, context)
  }
}

function buildPrompt(candidates, context) {
  const productList = candidates.map((p, i) => 
    `[${i+1}] ${p.name} | ${p.platformLabel} | ¥${p.price} | 好评${p.rating}% | ${p.reviewCount}条评价\n    参数: ${JSON.stringify(p.params)}\n    好评摘要: ${p.reviewQuote}\n    槽点: ${p.reviewCon}`
  ).join('\n\n')

  return `你是一个专业的购物决策助手。用户想买「${context.need}」，预算 ¥${context.budgetMin}-${context.budgetMax}。
${context.background ? '用户背景：' + context.background : ''}

以下是抓取到的候选商品：

${productList}

请从中选出 3 款最优商品（按综合评分排序），并为首选款生成推荐理由。

输出格式（严格 JSON）：
{
  "selectedIndices": [首选编号, 次选编号, 第三编号],
  "reasons": [
    "理由1（参数/性能维度）",
    "理由2（口碑/评价维度）",
    "理由3（性价比维度）",
    "理由4（结合用户背景的个性化推荐理由）"
  ]
}

只输出 JSON，不要其他内容。`
}

async function callQianWen(prompt, apiKey) {
  const resp = await fetch(QIANWEN_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'qwen-plus',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.3,
      response_format: { type: 'json_object' }
    })
  })

  if (!resp.ok) {
    const err = await resp.text()
    throw new Error(`QianWen API ${resp.status}: ${err.slice(0, 200)}`)
  }

  const data = await resp.json()
  return data.choices?.[0]?.message?.content || ''
}

function parseAIResponse(responseText, candidates) {
  try {
    const parsed = JSON.parse(responseText)
    const selected = parsed.selectedIndices.map(i => candidates[i - 1]).filter(Boolean)
    const recommendedId = selected[0]?.id || 'a'

    // 给选中的商品分配 id
    selected.forEach((p, i) => {
      if (!p.id) p.id = ['a', 'b', 'c'][i]
    })

    return {
      products: selected.slice(0, 3),
      recommendedId,
      reasons: parsed.reasons || []
    }
  } catch (err) {
    console.error('[AI] Failed to parse AI response, fallback:', err.message)
    return ruleBasedSelect(candidates, {})
  }
}

/**
 * 基于规则的选择 — 无 API key 时降级
 */
function ruleBasedSelect(candidates, context) {
  // 按评分 × 价格性价比排序
  const scored = candidates.map(p => ({
    ...p,
    score: p.rating * 0.6 + (1 / (p.price / 1000)) * 20
  }))
  scored.sort((a, b) => b.score - a.score)

  const top3 = scored.slice(0, 3)
  top3.forEach((p, i) => { if (!p.id) p.id = ['a', 'b', 'c'][i] })

  const recommended = top3[0]
  const reasons = [...(recommended.reasons || [])]
  if (reasons.length === 0) {
    reasons.push(`参数综合最优：${recommended.name} 在核心维度表现突出`)
    reasons.push(`好评率 ${recommended.rating}%，用户口碑稳定`)
    reasons.push(`到手价 ¥${recommended.price}，性价比在同类中较优`)
  }
  if (context.background) {
    reasons.push(`结合你的背景「${context.background}」：${recommended.name} 的参数配置与你的使用场景匹配度最高`)
  }

  return { products: top3, recommendedId: top3[0]?.id || 'a', reasons }
}

module.exports = { aiSelect }
