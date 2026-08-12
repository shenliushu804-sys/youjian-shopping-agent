/**
 * 商品抓取模块 — 调用 Python Playwright 爬虫流水线
 * 失败时降级到本地模拟数据
 */

const { spawn } = require('child_process')
const path = require('path')

const PIPELINE_SCRIPT = path.resolve(__dirname, '../../pipeline.py')
const PYTHON = 'python3'

/**
 * 调用 Python pipeline 做真实抓取 + AI 筛选
 * @param {object} params - { need, budgetMin, budgetMax, platforms, background }
 * @returns {Promise<object>} - { products, recommendedId, reasons }
 */
function fetchProductsViaPipeline(params) {
  return new Promise((resolve, reject) => {
    const args = [
      PIPELINE_SCRIPT,
      '--need', params.need || '人体工学椅',
      '--budget-min', String(params.budgetMin || 0),
      '--budget-max', String(params.budgetMax || 99999),
      '--platforms', (params.platforms || ['jd', 'tmall']).join(','),
    ]
    if (params.background) {
      args.push('--background', params.background)
    }

    console.log(`[scraper] Spawning: ${PYTHON} ${args.join(' ')}`)

    const proc = spawn(PYTHON, args, {
      cwd: path.resolve(__dirname, '../..'),
      env: { ...process.env },
      timeout: 120000,  // 2 min timeout
    })

    let stdout = ''
    let stderr = ''

    proc.stdout.on('data', (data) => { stdout += data.toString() })
    proc.stderr.on('data', (data) => {
      const text = data.toString()
      stderr += text
      // 实时打印 Python 日志
      text.split('\n').filter(l => l.trim()).forEach(l => console.log(`[pipeline] ${l}`))
    })

    proc.on('close', (code) => {
      if (code !== 0) {
        console.error(`[scraper] pipeline exited with code ${code}`)
        console.error(`[scraper] stderr: ${stderr.slice(-500)}`)
        reject(new Error(`pipeline exit code ${code}`))
        return
      }
      try {
        const result = JSON.parse(stdout.trim())
        if (result.error) {
          reject(new Error(result.message || result.error))
          return
        }
        resolve(result)
      } catch (e) {
        console.error(`[scraper] JSON parse error: ${e.message}`)
        console.error(`[scraper] stdout: ${stdout.slice(-500)}`)
        reject(new Error('pipeline output not valid JSON'))
      }
    })

    proc.on('error', (err) => {
      console.error(`[scraper] spawn error: ${err.message}`)
      reject(err)
    })
  })
}

/**
 * 本地模拟数据降级
 */
function fetchProductsFallback({ need, budgetMin, budgetMax, platforms }) {
  console.log('[scraper] using fallback mock data')
  const jdProducts = platforms.includes('jd') ? mockFetch('jd', need, budgetMin, budgetMax) : []
  const tmallProducts = platforms.includes('tmall') ? mockFetch('tmall', need, budgetMin, budgetMax) : []
  return { jd: jdProducts, tmall: tmallProducts }
}

function mockFetch(platform, keyword, min, max) {
  const pool = platform === 'jd'
    ? [
        { name: '西昊 M57 人体工学椅', price: 1899, rating: 97.2, reviewCount: 12800, platform: 'jd', platformLabel: '京东' },
        { name: '保友 金豪E 人体工学椅', price: 2999, rating: 96.5, reviewCount: 5600, platform: 'jd', platformLabel: '京东' },
        { name: '西昊 Doro C300 人体工学椅', price: 2499, rating: 96.8, reviewCount: 3400, platform: 'jd', platformLabel: '京东' },
      ]
    : [
        { name: '永艺 XY 人体工学椅', price: 2199, rating: 95.8, reviewCount: 8300, platform: 'tmall', platformLabel: '天猫' },
        { name: '西昊 M57 天猫版', price: 1949, rating: 96.9, reviewCount: 6100, platform: 'tmall', platformLabel: '天猫' },
      ]
  return pool.filter(p => p.price >= min && p.price <= max)
}

module.exports = { fetchProductsViaPipeline, fetchProductsFallback }
