# 购物决策代理 Agent

> 用自然语言描述购物需求，Agent 自动检索京东/天猫，采集商品参数，结合场景对比推荐，用户确认后代为下单到支付页。

## 功能

- 自然语言理解购物需求（品类 + 场景 + 预算）
- 京东 / 天猫双平台实时搜索
- 商品详情参数采集（参数表、品牌、价格、评价数）
- LLM 场景化对比推荐（Top 3 + 推荐理由）
- 用户确认后自动加购，跳转支付页（不自动支付）

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt --break-system-packages
python3 -m playwright install chromium
```

### 2. 首次登录（只需一次）

```bash
python3 login.py
```

会弹出 Chromium 窗口，扫码登录京东和天猫。登录完成后自动保存 Cookie 到 `data/cookies.json`。

### 3. 使用

```bash
./start.sh "人体工学椅 腰椎间盘突出 预算1000 日常在家办公打游戏"
```

或直接：

```bash
python3 main.py "路由器 120平米全屋覆盖 预算300"
```

流程：解析需求 → 搜索京东+天猫 → 采集 Top 5 详情参数 → LLM 对比推荐 → 输入编号下单到支付页。

## LLM 配置

默认 **本地模型优先，API 兜底**：

| 模式 | 说明 |
|------|------|
| `LLM_MODE=auto`（默认） | 先尝试本地 Qwen3.5-2B，不可用时自动切 Qwen API |
| `LLM_MODE=local` | 强制本地模型 |
| `LLM_MODE=api` | 强制 Qwen API（dashscope，需 `QIANWEN_API_KEY`） |

本地模型：

```bash
python3 llm/local_server.py
```

按以下顺序查找 `.env`（先找到的键生效，已有环境变量优先）：

1. 项目根目录 `.env`
2. `backend/.env`
3. `youjian-mini/backend/.env`

也可以直接设置环境变量 `QIANWEN_API_KEY`。

## 项目结构

```
my-shopping/
├── main.py              # CLI 主流程
├── login.py             # 登录 + Cookie 保存
├── start.sh             # 一键启动
├── config.py            # 配置
├── models.py            # 数据模型
├── selection.py         # 跨平台混排 + 预算过滤
├── llm/
│   ├── client.py        # LLM 统一入口（本地/API）
│   ├── local_server.py  # 本地 Qwen3.5-2B 服务
│   ├── intent.py        # 意图解析
│   └── analyzer.py      # 对比推荐
└── platforms/
    ├── browser.py       # Playwright 浏览器管理
    ├── base.py          # 适配器基类 + 品牌提取
    ├── jd.py            # 京东适配器
    └── tmall.py         # 天猫/淘宝适配器
```

## 注意事项

- Cookie 是京东/天猫账号登录态，等同于账号操作权限；保存文件权限为 `0600`，请勿提交、分享或用于多用户对外服务
- Cookie 会过期，失效时重新运行 `python3 login.py`
- 高频访问会触发平台频控，详情采集已限速（Top 5 + 随机延迟）
- 商品参数缺失时标注"未获取"，LLM 不会编造数据
- 评价内容受平台反爬限制，当前采集"累计评价数"作为评价信号
- 下单只到支付确认页，支付必须本人操作
- 推荐排序由 LLM 综合判断，仅用于排序，不对外展示精确量化评分

## 免责声明

本项目仅供个人学习与本地自用。模拟登录、自动采集与加购可能违反京东/天猫等平台的用户协议与 robots 约定，个人自用属灰色地带；请勿将本项目改造为面向公众的付费/免费服务，否则需自行评估法律与平台风控风险。

## 开发文档

需求、技术方案、任务进度见 `.dev/` 目录：

- [PRD](.dev/prd/shopping-decision-agent-PRD.md)
- [技术方案](.dev/design/shopping-decision-agent-DESIGN.md)
- [任务清单](.dev/tasks/shopping-decision-agent-TASKS.md)
