# 任务列表: shopping-decision-agent

创建日期: 2026-08-01
关联 PRD: [shopping-decision-agent-PRD.md](../prd/shopping-decision-agent-PRD.md)
关联技术方案: [shopping-decision-agent-DESIGN.md](../design/shopping-decision-agent-DESIGN.md)

## 优先级说明

- P0: 必须，第一版核心（检索 + 对比推荐）
- P1: 重要，第一版完整（下单到支付页）
- P2: 可选，后续迭代

---

## 阶段 A: 基础设施

### A1. 项目骨架与数据模型（P0）

- **依赖**: 无
- **预估**: 0.5 天
- **内容**:
  - 创建 `config.py`（平台配置、预算、路径、LLM 模式）
  - 创建 `models.py`（Product / ProductDetail / Recommendation）
  - 创建 `requirements.txt`（playwright、httpx、mlx、mlx-vlm）
  - `.gitignore`（排除 cookies.json、.dev 非必需）

### A2. LLM 统一客户端（P0）

- **依赖**: A1
- **预估**: 1 天
- **内容**:
  - `llm/client.py`: OpenAI 兼容统一入口，`LLM_MODE=auto|local|api`
  - `llm/local_server.py`: 用 mlx_vlm 加载本地 Qwen3.5-2B，暴露 `/v1/chat/completions`（127.0.0.1:8001）
  - API 兜底: Qwen qwen-turbo（dashscope），本地超时/失败/JSON 异常自动切换
  - 提供 `chat(messages, response_format="json")` 通用函数

---

## 阶段 B: 平台采集

### B1. 登录与 Cookie 管理（P0）

- **依赖**: A1
- **预估**: 1 天
- **内容**:
  - `login.py`: 打开独立 Chromium → 用户扫码登录京东/天猫 → Cookie 存 `data/cookies.json`
  - `platforms/browser.py`: Playwright 浏览器管理（Cookie 加载/保存/复用、登录态探测、失败提示重登录）

### B2. 平台适配器基类（P0）

- **依赖**: A1
- **预估**: 0.5 天
- **内容**:
  - `platforms/base.py`: `PlatformAdapter` 抽象基类（search / fetch_detail / prepare_order）
  - `platforms/__init__.py`: 适配器注册表

### B3. 京东适配器（P0）

- **依赖**: B1, B2
- **预估**: 1.5 天
- **内容**:
  - `search()`: 京东搜索列表采集（标题/价格/店铺/链接/评价数），预算过滤
  - `fetch_detail()`: 详情页参数表采集（关键参数、品牌、评分、评价摘要）
  - `prepare_order()`: 加购 → 跳结算 → 返回支付页 URL（不自动支付）

### B4. 天猫适配器（P1）

- **依赖**: B1, B2
- **预估**: 1.5 天
- **内容**:
  - `search()`: 天猫搜索列表采集（标题/价格/店铺/链接/评价数），预算过滤
  - `fetch_detail()`: 详情页参数表采集
  - `prepare_order()`: 加购 → 跳结算 → 返回支付页 URL

---

## 阶段 C: LLM 业务逻辑

### C1. 意图解析（P0）

- **依赖**: A2
- **预估**: 0.5 天
- **内容**:
  - `llm/intent.py`: 从用户需求解析出 `search_keywords`、`critical_params`、`budget_max`、`scenario`
  - 场景理解示例: "腰椎间盘突出" → 关键参数"腰椎支撑/高背/透气网布"

### C2. 对比推荐（P0）

- **依赖**: A2
- **预估**: 1 天
- **内容**:
  - `llm/analyzer.py`: 基于真实采集数据（参数/价格/评价/品牌）对比，输出 Top 2-3 推荐 + 理由
  - 约束: 只能使用提供的 JSON 数据，缺失标"未获取"，禁止编造
  - 预算硬约束（超预算淘汰）、店铺类型权重

---

## 阶段 D: 流程编排与验证

### D1. CLI 主流程（P0）

- **依赖**: B3, B4(可后补), C1, C2
- **预估**: 1 天
- **内容**:
  - `main.py`: 全流程编排（输入 → 意图 → 检索 → 详情 → 对比 → 推荐 → 确认 → 下单）
  - 用户确认推荐后才进入下单流程
  - 结果展示（推荐、理由、链接）

### D2. 集成测试与验收（P0）

- **依赖**: D1
- **预估**: 1 天
- **内容**:
  - 真实场景 E2E: 人体工学椅（具体品类）+ 相亲伴手礼（非具体需求）
  - Cookie 过期提示、商品下架备选、本地 LLM 降级 API
  - 修复测试中发现的问题

---

## 建议执行顺序

```
A1 → A2 → C1, C2（LLM 逻辑可并行）
   ↘ B1 → B2 → B3 → D1
                    ↘ B4（P1，可并行）
                          ↘ D2
```

关键路径: A1 → B1 → B3 → D1 → D2
总计预估: P0 约 6.5 天，加 P1 约 8 天

## 执行进度

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| A1 项目骨架与数据模型 | ✅ | 2026-08-01 | |
| A2 LLM 统一客户端 | ✅ | 2026-08-01 | 本地 Qwen3.5-2B 推理 3.3s + API 兜底 |
| B1 登录与 Cookie 管理 | ✅ | 2026-08-02 | Cookie 检测替代页面轮询 |
| B2 平台适配器基类 | ✅ | 2026-08-01 | |
| B3 京东适配器 | ✅ | 2026-08-02 | 新版 DOM（data-sku + 速览参数），防频控重试 |
| B4 天猫适配器 | ✅ | 2026-08-02 | 新版淘宝搜索 DOM（doubleCardWrapper） |
| C1 意图解析 | ✅ | 2026-08-01 | 3 场景实测通过 |
| C2 对比推荐 | ✅ | 2026-08-02 | 标题匹配修复 index 错位 |
| D1 CLI 主流程 | ✅ | 2026-08-02 | 非交互模式支持 |
| D2 集成测试 | ✅ | 2026-08-05 | 人体工学椅/路由器/相亲伴手礼通过 |
