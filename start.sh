#!/bin/bash
"""购物决策代理一键启动脚本"""

set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "  购物决策代理 Agent"
echo "=============================================="

# 1. 检查登录态
if [ ! -f "data/cookies.json" ]; then
    echo "⚠️  未找到登录 Cookie，请先登录京东/天猫"
    python3 login.py
else
    echo "✅ 登录态存在 (data/cookies.json)"
fi

# 2. 检查并启动本地 LLM（可选）
if curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
    echo "✅ 本地 LLM 服务已运行"
elif [ "$LLM_MODE" != "api" ]; then
    echo "🌐 本地 LLM 未启动，尝试启动 Qwen3.5-2B 服务..."
    nohup python3 llm/local_server.py > /tmp/shopping_llm.log 2>&1 &
    sleep 2
    echo "   本地 LLM 启动中 (日志: /tmp/shopping_llm.log)"
    echo "   如需强制使用 API，请设置 LLM_MODE=api"
fi

# 3. 运行主流程
if [ -z "$1" ]; then
    echo ""
    echo "用法: ./start.sh \"商品需求 使用场景 预算\""
    echo "示例: ./start.sh \"人体工学椅 腰椎间盘突出 预算1000 日常办公打游戏\""
    exit 0
fi

python3 main.py "$@"
