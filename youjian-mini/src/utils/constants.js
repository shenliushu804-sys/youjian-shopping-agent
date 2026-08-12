/**
 * 模拟数据 & 常量 — 后期替换为真实接口
 */

// 购物背景联想词组
export const BG_SETS = [
  { match: ['椅', '工学', '办公椅'],
    note: '久坐 8 小时以上，腰椎偶尔不适，放在约 9㎡ 的书房，偏好透气网布',
    chips: ['久坐 8 小时以上', '腰椎偶尔不适', '书房约 9㎡', '偏好透气网布'] },
  { match: ['耳机', '降噪'],
    note: '通勤地铁上用，每天佩戴约 1 小时，戴眼镜，经常开会需要麦克风',
    chips: ['通勤地铁噪声大', '每天佩戴约 1 小时', '戴眼镜', '需要麦克风开会'] },
  { match: ['扫地', '机器人'],
    note: '三室一厅，家里有宠物掉毛，希望自动集尘、能预约清扫',
    chips: ['家里有宠物', '三室一厅', '多地毯', '希望自动集尘'] },
  { match: ['键盘'],
    note: '开放式办公室用，长时间码字，需要无线，怕吵到同事',
    chips: ['开放式办公室', '长时间码字', '需要无线', '怕吵到同事'] },
  { match: ['车载', '车用', '汽车', '行车', '车内'],
    note: '车型是特斯拉 Model Y 2024 款，每天通勤约 1 小时',
    chips: ['车型与年款：', '每天通勤约 1 小时', '经常跑长途', '北方冬季用车'] },
  { match: ['礼物', '送礼', '父亲节', '母亲节', '生日', '纪念日'],
    note: '父亲节送爸爸，55 岁，实用为主，希望预算内显档次',
    chips: ['送礼，包装要体面', '对方 50 岁以上', '实用优先', '预算内显档次'] }
]

export const BG_DEFAULT = { note: '', chips: ['自用', '送礼', '高频使用', '在意售后质保'] }

// 预算档位
export const BUDGET_PRESETS = [
  { label: '百元级', sub: '≤ 999', min: 0, max: 999 },
  { label: '千元级', sub: '1k – 3k', min: 1000, max: 3000 },
  { label: '中高端', sub: '3k – 5k', min: 3000, max: 5000 },
  { label: '旗舰级', sub: '5k+', min: 5000, max: 10000 }
]

// 模拟商品数据
export const PRODUCTS = {
  a: {
    id: 'a', name: '西昊 M57 人体工学椅', platform: '京东', platformClass: 'jd',
    price: 1899, sub: '好评率 97.2% · 质保 5 年',
    spec: '网布款 / 黑色', eta: '预计 2–3 个工作日送达',
    rating: 97.2, reviewCount: 12800,
    params: { '到手价': '¥1,899', '腰托调节': '双向可调', '头枕': '可调', '扶手': '4D 扶手', '椅背材质': '透气网布', '承重': '150 kg', '质保': '5 年' },
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
    id: 'b', name: '永艺 XY 人体工学椅', platform: '天猫', platformClass: 'tmall',
    price: 2199, sub: '好评率 95.8% · 质保 3 年',
    spec: '网布款 / 深灰', eta: '预计 3–5 个工作日送达',
    rating: 95.8, reviewCount: 8300,
    params: { '到手价': '¥2,199', '腰托调节': '自适应', '头枕': '可调', '扶手': '3D 扶手', '椅背材质': '透气网布', '承重': '136 kg', '质保': '3 年' },
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
    id: 'c', name: '保友 金豪E 人体工学椅', platform: '京东', platformClass: 'jd',
    price: 2999, sub: '好评率 96.5% · 质保 5 年',
    spec: '网布款 / 银灰', eta: '预计 2–4 个工作日送达',
    rating: 96.5, reviewCount: 5600,
    params: { '到手价': '¥2,999', '腰托调节': '4档可调', '头枕': '可调 + 前后', '扶手': '4D 扶手', '椅背材质': '高弹网布', '承重': '160 kg', '质保': '5 年' },
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

// 分析步骤
export const ANA_STEPS = [
  { name: '抓取京东', sub: '搜索商品列表与价格', count: '47 款' },
  { name: '抓取天猫淘宝', sub: '搜索商品列表与价格', count: '36 款' },
  { name: '预算需求初筛', sub: '价格区间 + 基础参数过滤', count: '83 → 12 款' },
  { name: '大模型深读参数评价', sub: '逐款读取详情页与评价', count: '12 → 3 款' },
  { name: '生成结论', sub: '综合推荐理由与对比报告', count: '1 份报告' }
]

// 参数对比维度（椅子品类）
export const SPEC_DIMENSIONS = ['到手价', '腰托调节', '头枕', '扶手', '椅背材质', '承重', '质保']

// 支付方式
export const PAY_METHODS = [
  { key: 'alipay', label: '支付宝', color: '#1677ff' },
  { key: 'wechat', label: '微信支付', color: '#09b552' },
  { key: 'unionpay', label: '云闪付', color: '#d43a2f' }
]

// 工具函数
export function formatPrice(n) {
  return '¥' + n.toLocaleString('en-US')
}

export function shortNote(note) {
  if (!note) return ''
  const segs = note.split(/，|,/)
  const s = segs.slice(0, 2).join('，')
  return s.length > 20 ? s.slice(0, 20) + '…' : s
}

export function categoryOf(text) {
  for (const s of BG_SETS) {
    for (const m of s.match) {
      if (text && text.indexOf(m) > -1) return s
    }
  }
  return BG_DEFAULT
}
